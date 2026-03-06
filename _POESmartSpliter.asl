state("PathOfExile_x64") {}
state("PathOfExileSteam") {}
state("PathOfExile") {}

startup {
    // ==========================================
    //           USER CONFIGURATION
    // ==========================================
    // Set your Path of Exile log path here. If poe_config.txt exists in the
    // same folder as this file, it overrides this value (useful for keeping
    // your personal path out of a shared repo). Leave empty to use the default.
    vars.poeLogPath = @""; // <-- edit this if you don't use poe_config.txt
    // Example: vars.poeLogPath = @"V:\SteamLibrary\steamapps\common\Path of Exile\logs\LatestClient.txt";

    // How many splits ahead the engine looks to recover from a missed split (default: 3)
    vars.lookaheadDistance = 3;

    // Dead-end exit timeout: threshold = base - perAct * actNumber, minimum minTime seconds.
    // Raise these if a dead-end zone keeps splitting too early.
    vars.deadEndTimeoutBase   = 40.0f;
    vars.deadEndTimeoutPerAct = 2.5f;
    vars.deadEndTimeoutMin    = 15.0f;

    // ==========================================
    //           INTERNAL STATE
    // ==========================================
    vars.debugLogPath = Directory.GetCurrentDirectory() + @"\Assets\asl_debug_log.txt";
    
    vars.Normalize = (Func<string, string>)((name) => {
        if (string.IsNullOrEmpty(name)) return "";
        string result = "";
        foreach(char c in name) {
            if (char.IsLetterOrDigit(c)) {
                result += char.ToLower(c);
            }
        }
        return result;
    });
    
    vars.Log = (Action<string>)((message) => {
        try {
            string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            System.IO.File.AppendAllText(vars.debugLogPath, "[" + timestamp + "] " + message + Environment.NewLine);
        } catch {}
    });

    vars.currentZoneId = "";
    vars.previousZoneId = "";
    vars.beforePreviousZoneId = "";
    vars.zoneChanged = false;
    vars.lastCheckedSplit = "";
    
    // Advanced backtracking protection
    vars.timeSpentInPreviousZone = 0f;
    vars.timeEnteredZone = 0f;
    vars.skipQueue = 0;

    // Kitava defeat flags (set by resistance-penalty log line, consumed in split block)
    vars.kitavaAct5Defeated  = false; // "-30% to all Resistances" (Act 5 Kitava)
    vars.kitavaAct10Defeated = false; // "-60%" total (Act 10 Kitava)

    vars.DeadEndIDs = new HashSet<string>();
    vars.PassthroughIDs = new HashSet<string>(); // Zones where exit fires regardless of next zone's math (geographic order != ID order)
    vars.HubIDs = new HashSet<string>(); // Zones that split ONLY on exact arrival (like towns, but geographically not towns)

    // Mathematical ID Progression Engine
    vars.CompareZoneIDs = (Func<string, string, int>)((currentId, targetId) => {
        if (string.IsNullOrEmpty(currentId) || string.IsNullOrEmpty(targetId)) return 0;
        
        string[] currentParts = currentId.Split('_');
        string[] targetParts = targetId.Split('_');
        
        // 1. Act Comparison MUST happen first (even for towns) so multi-act skips are calculated correctly
        if (currentParts.Length > 1 && targetParts.Length > 1) {
            int currentAct = 0, targetAct = 0;
            if (int.TryParse(currentParts[1], out currentAct) && int.TryParse(targetParts[1], out targetAct)) {
                if (currentAct != targetAct) return currentAct > targetAct ? 1 : -1;
            }
        }
        
        // 1.5 Town Math Evaluation
        bool currentIsTown = currentId.EndsWith("_town");
        bool targetIsTown = targetId.EndsWith("_town");
        
        // If they are the exact same town, they are equal.
        if (currentIsTown && targetIsTown) return 0;
        
        // If we established we are in the same Act (from block 1), 
        // ANY physical Map progression is mathematically greater than the Town.
        if (targetIsTown && !currentIsTown) return 1;
        if (currentIsTown && !targetIsTown) return -1;

        // 2. Map Progression Comparison
        if (currentParts.Length > 2 && targetParts.Length > 2) {
            int currentMap = 0, targetMap = 0;
            string cMapStr = "", tMapStr = "";
            foreach (char c in currentParts[2]) if (char.IsDigit(c)) cMapStr += c;
            foreach (char c in targetParts[2]) if (char.IsDigit(c)) tMapStr += c;
            
            if (int.TryParse(cMapStr, out currentMap) && int.TryParse(tMapStr, out targetMap)) {
                if (currentMap != targetMap) return currentMap > targetMap ? 1 : -1;
                
                // If numeric progression is equal, 'a'/'b' side areas are mathematically EQUIVALENT to base areas
                bool currentIsSide = currentParts[2].Contains("a") || currentParts[2].Contains("b");
                bool targetIsSide = targetParts[2].Contains("a") || targetParts[2].Contains("b");
                if (currentIsSide != targetIsSide) return 0;
            }
        }
        
        // 3. Sub-level Comparison
        if (currentParts.Length > 3 || targetParts.Length > 3) {
            int currentSub = 0, targetSub = 0;
            if (currentParts.Length > 3) int.TryParse(currentParts[3], out currentSub);
            if (targetParts.Length > 3) int.TryParse(targetParts[3], out targetSub);
            
            if (currentSub != targetSub) return currentSub > targetSub ? 1 : -1;
        }
        
        return 0; // Exactly equal (not > )
    });

    vars.GetSplitDetails = (Func<string, string[]>)((splitName) => {
        if (string.IsNullOrEmpty(splitName)) return new string[] { null, "None", "None" };
        string normSplit = vars.Normalize(splitName);
        
        if (vars.ZoneIDs.ContainsKey(normSplit)) {
            return new string[] { vars.ZoneIDs[normSplit][0], normSplit, string.Join(", ", vars.ZoneIDs[normSplit]) };
        }
        
        foreach (var kvp in vars.ZoneIDs) {
            string alias = kvp.Key;
            bool aliasMatch = false;
            if (alias.StartsWith("act") && alias.Length <= 5) {
                if (normSplit.Contains(alias)) {
                    int idx = normSplit.IndexOf(alias) + alias.Length;
                    if (idx >= normSplit.Length || !char.IsDigit(normSplit[idx])) aliasMatch = true;
                }
            } else if (alias.Length >= 4) {
                if (normSplit.Contains(alias)) aliasMatch = true;
            }
            if (aliasMatch) return new string[] { kvp.Value[0], alias, string.Join(", ", kvp.Value) };
        }
        
        // Direct ID fallback
        if (normSplit.Contains("_") || char.IsDigit(normSplit[0])) {
            return new string[] { normSplit, "Raw ID", normSplit };
        }
        return new string[] { null, "None", "None" };
    });

    vars.GetAreaDetails = (Func<string, string>)((id) => {
        if (string.IsNullOrEmpty(id)) return "Unknown Area";
        
        string baseName = "Unknown";
        List<string> tags = new List<string>();
        
        foreach (var kvp in vars.ZoneIDs) {
            if (kvp.Value.Contains(id)) {
                if (baseName == "Unknown") baseName = kvp.Key;
                tags.Add(kvp.Key);
            }
        }
        
        string actNum = "?";
        string[] parts = id.Split('_');
        if (parts.Length > 1) actNum = parts[1];
        
        string tagStr    = tags.Count > 0 ? string.Join(", ", tags) : "None";
        string deadEndStr = vars.DeadEndIDs.Contains(id) ? "Yes" : "No";
        string passThrStr = vars.PassthroughIDs.Contains(id) ? "Yes" : "No";
        
        return string.Format("Act {0} - {1} - id: {2}  |  Tags : {3}  |  Dead End ? : {4}  |  Passthrough ? : {5}",
            actNum, baseName, id, tagStr, deadEndStr, passThrStr);
    });

    vars.ZoneIDs = new Dictionary<string, List<string>>();

    Action<string, string, string[], bool, bool> AddZone = (zoneName, idStr, aliases, isDeadEnd, isPassthrough) => {
        if (!vars.ZoneIDs.ContainsKey(zoneName)) vars.ZoneIDs[zoneName] = new List<string>();
        if (!vars.ZoneIDs[zoneName].Contains(idStr)) vars.ZoneIDs[zoneName].Add(idStr);
        foreach(var alias in aliases) {
            if (!vars.ZoneIDs.ContainsKey(alias)) vars.ZoneIDs[alias] = vars.ZoneIDs[zoneName];
        }
        if (isDeadEnd) vars.DeadEndIDs.Add(idStr);
        if (isPassthrough) vars.PassthroughIDs.Add(idStr);
    };

    // ==========================================
    //                 PART 1
    // ==========================================

    // --- Act 1 ---
    AddZone("lioneyeswatch",           "1_1_town",  new string[] { "lioneye" },                             false, false);
    AddZone("thetwilightstrand",        "1_1_1",     new string[] { "twilightstrand" },                      false, false);
    AddZone("thecoast",                 "1_1_2",     new string[] { "coast" },                               false, false);
    AddZone("thetidalisland",           "1_1_2a",    new string[] { "tidalisland", "hailrake", "island" },   true,  false);
    AddZone("themudflats",              "1_1_3",     new string[] { "mudflats" },                            false, false);
    AddZone("thefloodeddepths",         "1_1_4_0",   new string[] { "floodeddepths" },                       true,  false);
    AddZone("thesubmergedpassage",      "1_1_4_1",   new string[] { "submergedpassage" },                    false, false);
    AddZone("theledge",                 "1_1_5",     new string[] { "ledge" },                               false, false);
    AddZone("theclimb",                 "1_1_6",     new string[] { "climb" },                               false, false);
    AddZone("thelowerprison",           "1_1_7_1",   new string[] { "lowerprison", "prison" },               false, false);
    AddZone("theupperprison",           "1_1_7_2",   new string[] { "upperprison", "brutus", "warden" },     false, false);
    AddZone("prisonersgate",            "1_1_8",     new string[0],                                          false, false);
    AddZone("theshipgraveyard",         "1_1_9",     new string[] { "shipgraveyard" },                       false, false);
    AddZone("thefetidpool",             "1_1_3a",    new string[] { "fetidpool" },                           true,  false);
    AddZone("theshipgraveyardcave",     "1_1_9a",    new string[] { "shipgraveyardcave" },                   true,  false);
    AddZone("thecavernofwrath",         "1_1_11_1",  new string[] { "cavernofwrath" },                       false, false);
    AddZone("thecavernofanger",         "1_1_11_2",  new string[] { "cavernofanger", "merveil" },            false, false);

    // --- Act 2 ---
    AddZone("theforestencampment",      "1_2_town",  new string[] { "forestencampment" },                    false, false);
    AddZone("thesouthernforest",        "1_2_1",     new string[] { "southernforest", "southern" },          false, false);
    AddZone("theoldfields",             "1_2_2",     new string[] { "oldfields" },                           false, false);
    AddZone("thecrossroads",            "1_2_3",     new string[] { "crossroads" },                          false, false);
    AddZone("thebrokenbridge",          "1_2_4",     new string[] { "brokenbridge" },                        true,  false);
    AddZone("thecryptlevel1",           "1_2_5_1",   new string[] { "cryptlevel1" },                         false, false);
    AddZone("thecryptlevel2",           "1_2_5_2",   new string[] { "cryptlevel2" },                         true,  false);
    AddZone("thechamberofsinslevel1",   "1_2_6_1",   new string[] { "chamberofsinslevel1" },                 false, false);
    AddZone("thechamberofsinslevel2",   "1_2_6_2",   new string[] { "chamberofsinslevel2" },                 true,  false);
    AddZone("theriverways",             "1_2_7",     new string[] { "riverways" },                           false, false);
    AddZone("thenorthernforest",        "1_2_8",     new string[] { "northernforest", "northern" },          false, false);
    AddZone("thewesternforest",         "1_2_9",     new string[] { "westernforest", "western" },            false, false);
    AddZone("theweaverschambers",       "1_2_10",    new string[] { "weaverschambers", "weaver", "spider" }, true,  false);
    // [PASSTHROUGH] Act 2: Riverways(7)→Wetlands(12)→VaalRuins(11)→NorthernForest(8) — two backward exits.
    // Rule 7 fires on exit with backtrack protection. Northern Forest NOT flagged (exits to Caverns 14_2 = forward).
    AddZone("thevaalruins",             "1_2_11",    new string[] { "vaalruins", "vaalruin" },               false, true);
    AddZone("thewetlands",              "1_2_12",    new string[] { "wetlands" },                            false, true);
    AddZone("thedreadthicket",          "1_2_13",    new string[] { "dreadthicket" },                        true,  false);
    AddZone("thecaverns",               "1_2_14_2",  new string[] { "caverns" },                             false, false);
    AddZone("theancientpyramid",        "1_2_14_3",  new string[] { "ancientpyramid", "vaal", "vaaloversoul", "pyramid" }, false, false);
    // [PASSTHROUGH] Fell Shrine (id=15) leads to Crypt L1 (id=5) — exiting goes mathematically backward.
    // Rule 7 fires when you LEAVE Fell Shrine (previousZoneId=1_2_15) with backtrack protection.
    // To flag future out-of-order zones: set the 5th param to true.
    AddZone("thefellshrineruins",       "1_2_15",    new string[] { "fellshrineruins" },                     false, true);

    // --- Act 3 ---
    AddZone("thesarnencampment",        "1_3_town",  new string[] { "sarnencampment" },                      false, false);
    AddZone("thecityofsarn",             "1_3_1",     new string[] { "cityofsarn" },                          false, false);
    AddZone("theslums",                  "1_3_2",     new string[] { "slums" },                               false, false);
    AddZone("thecrematorium",            "1_3_3_1",   new string[] { "crematorium" },                         true,  false);
    AddZone("themarketplace",            "1_3_5",     new string[] { "marketplace" },                         false, false);
    AddZone("thecatacombs",              "1_3_6",     new string[] { "catacombs" },                           true,  false);
    AddZone("thebattlefront",            "1_3_7",     new string[] { "battlefront" },                         false, false);
    AddZone("thesolaristemplelevel1",    "1_3_8_1",   new string[] { "solaristemplelevel1", "solaris1" },      false, false);
    AddZone("thesolaristemplelevel2",    "1_3_8_2",   new string[] { "solaristemplelevel2", "solaris2" },      true,  false);
    AddZone("thedocks",                  "1_3_9",     new string[] { "docks" },                               true,  false);
    AddZone("thesewers",                 "1_3_10_1",  new string[] { "sewers" },                              false, true);
    AddZone("theebonybarracks",          "1_3_13",    new string[] { "ebonybarracks" },                       false, false);
    AddZone("thelunaristemplelevel1",    "1_3_14_1",  new string[] { "lunaristemplelevel1", "lunaris1" },      false, false);
    AddZone("thelunaristemplelevel2",    "1_3_14_2",  new string[] { "lunaristemplelevel2", "piety", "lunaristemple2", "lunaris2" }, true, false);
    AddZone("theimperialgardens",        "1_3_15",    new string[] { "imperialgardens" },                     false, false);
    AddZone("thelibrary",               "1_3_17_1",  new string[] { "library" },                             false, false);
    AddZone("thearchives",              "1_3_17_2",  new string[] { "archives" },                             true,  false);
    AddZone("thesceptreofgod",          "1_3_18_1",  new string[] { "sceptreofgod" },                        false, false);
    AddZone("theuppersceptreofgod",     "1_3_18_2",  new string[] { "uppersceptreofgod", "dominus", "sceptreofgod" }, false, false);

    // --- Act 4 ---
    AddZone("highgate",                  "1_4_town",  new string[0],                                          false, false);
    AddZone("theaqueduct",               "1_4_1",     new string[] { "aqueduct" },                            false, false);
    AddZone("thedriedlake",              "1_4_2",     new string[] { "driedlake" },                           true,  false);
    AddZone("themineslevel1",            "1_4_3_1",   new string[] { "mineslevel1" },                         false, false);
    AddZone("themineslevel2",            "1_4_3_2",   new string[] { "mineslevel2" },                         false, false);
    AddZone("thecrystalveins",           "1_4_3_3",   new string[] { "crystalveins" },                        false, false);
    AddZone("kaomsdream",                "1_4_4_1",   new string[0],                                          false, false);
    AddZone("kaomsstronghold",           "1_4_4_3",   new string[0],                                          true,  false);
    AddZone("daressosdream",             "1_4_5_1",   new string[0],                                          false, false);
    AddZone("thegrandarena",             "1_4_5_2",   new string[] { "grandarena" },                          true,  false);
    AddZone("thebellyofthebeastlevel1",  "1_4_6_1",   new string[] { "bellyofthebeastlevel1", "belly1" },     false, false);
    AddZone("thebellyofthebeastlevel2",  "1_4_6_2",   new string[] { "bellyofthebeastlevel2", "belly2" },     false, false);
    AddZone("theharvest",                "1_4_6_3",   new string[] { "harvest", "malachai" },                 false, false);
    AddZone("theascent",                 "1_4_7",     new string[] { "ascent" },                              false, false);
    
    // --- Act 5 ---
    AddZone("overseerstower",            "1_5_town",  new string[0],                                          false, false);
    AddZone("theslavepens",              "1_5_1",     new string[] { "slavepens" },                           false, false);
    AddZone("thecontrolblocks",          "1_5_2",     new string[] { "controlblocks" },                       false, false);
    AddZone("oriathsquare",              "1_5_3",     new string[0],                                          false, false);
    AddZone("theruinedsquare",           "1_5_3b",    new string[] { "ruinedsquare" },                        false, false); // Hub — registered via vars.HubIDs.Add below
    AddZone("thetemplarcourts",          "1_5_4",     new string[] { "templarcourts" },                       false, false);
    // [PASSTHROUGH] Torched Courts: post-Innocence state of Templar Courts. Exits to Ruined Square (lower id) — Rule 7 handles split on exit.
    AddZone("thetorchedcourts",          "1_5_4b",    new string[] { "torchedcourts" },                       false, true);
    // [PASSTHROUGH] Chamber of Innocence: only exit is Torched Courts (lower id) after boss kill — Rule 7 handles split on exit.
    AddZone("thechamberofinnocence",     "1_5_5",     new string[] { "chamberofinnocence", "innocence" },     false, true);
    AddZone("theossuary",                "1_5_6",     new string[] { "ossuary" },                             true,  false);
    AddZone("thereliquary",              "1_5_7",     new string[] { "reliquary" },                           true,  false);
    AddZone("thecathedralrooftop",       "1_5_8",     new string[] { "cathedralrooftop", "kitava", "rooftop" },false, false);


    // ==========================================
    //                 PART 2
    // ==========================================

    // --- Act 6 ---
    AddZone("lioneyeswatch",            "2_6_town",  new string[] { "lioneye" },                             false, false);
    AddZone("thetwilightstrand",         "2_6_1",     new string[0],                                          false, false);
    AddZone("thecoast",                  "2_6_2",     new string[0],                                          false, false);
    AddZone("thetidalisland",            "2_6_3",     new string[] { "tidalisland" },                         true,  false);
    AddZone("themudflats",               "2_6_4",     new string[0],                                          false, false);
    AddZone("thekaruifortress",          "2_6_5",     new string[] { "karuifortress" },                       false, false);
    AddZone("theridge",                  "2_6_6",     new string[] { "ridge" },                               false, false);
    AddZone("thelowerprison",            "2_6_7_1",   new string[0],                                          false, false);
    AddZone("shavronnestower",           "2_6_7_2",   new string[] { "shavronne", "tower" },                  true,  false);
    AddZone("prisonersgate",             "2_6_8",     new string[0],                                          false, false);
    AddZone("thewesternforest",          "2_6_9",     new string[0],                                          false, false);
    AddZone("theriverways",              "2_6_10",    new string[0],                                          false, false);
    AddZone("thewetlands",              "2_6_11",    new string[0],                                          false, false);
    AddZone("thesouthernforest",         "2_6_12",    new string[0],                                          false, false);
    AddZone("thecavernofanger",          "2_6_13",    new string[] { "cavernofanger", "merveil" },            false, false);
    AddZone("thebeacon",                 "2_6_14",    new string[] { "beacon" },                              false, false);
    AddZone("thebrinekingsreef",         "2_6_15",    new string[] { "brinekingsreef", "brineking", "reef" }, false, false);
    // --- Act 7 ---
    AddZone("thebridgeencampment",       "2_7_town",  new string[] { "bridgeencampment" },                    false, false);
    AddZone("thebrokenbridge",           "2_7_1",     new string[0],                                          false, false);
    AddZone("thecrossroads",             "2_7_2",     new string[0],                                          false, false);
    AddZone("thefellshrineruins",        "2_7_3",     new string[0],                                          false, false);
    AddZone("thecrypt",                  "2_7_4",     new string[] { "crypt" },                               true,  false);
    //Commented out due to incoherent splitting behaviour. Entering the map shouldn't mean end of chamber of sins level 1.
    //Expect misbehaviour if uncommented due to the id ending in "_map"
    //AddZone("maligarossanctum",        "2_7_5_map", new string[] { "sanctum" },                             true,  false);
    AddZone("thechamberofsinslevel1",    "2_7_5_1",   new string[] { "maligaro" },                            false, false);
    AddZone("thechamberofsinslevel2",    "2_7_5_2",   new string[0],                                          false, false);
    AddZone("theden",                    "2_7_6",     new string[] { "den" },                                 false, false);
    AddZone("theashenfields",            "2_7_7",     new string[] { "ashenfields" },                         false, false);
    AddZone("thenorthernforest",         "2_7_8",     new string[0],                                          false, false);
    AddZone("thedreadthicket",           "2_7_9",     new string[0],                                          true,  false);
    AddZone("thecauseway",               "2_7_10",    new string[] { "causeway" },                            false, false);
    AddZone("thevaalcity",               "2_7_11",    new string[] { "vaalcity" },                            false, false);
    AddZone("thetempleofdecaylevel1",    "2_7_12_1",  new string[] { "templeofdecaylevel1", "decay1" },       false, false);
    AddZone("thetempleofdecaylevel2",    "2_7_12_2",  new string[] { "templeofdecaylevel2", "arakaali", "templeofdecay", "decay2" }, true, false);
    // --- Act 8 ---
    AddZone("thesarnencampment",         "2_8_town",  new string[0],                                          false, false);
    AddZone("thesarnramparts",           "2_8_1",     new string[] { "sarnramparts" },                        false, false);
    AddZone("thetoxicconduits",          "2_8_2_1",   new string[] { "toxicconduits", "conduits" },           false, false);
    AddZone("doedrescesspool",           "2_8_2_2",   new string[] { "doedre", "cesspool" },                  false, false);
    AddZone("thegrandpromenade",         "2_8_3",     new string[] { "grandpromenade" },                      false, false);
    AddZone("thehighgardens",            "2_8_4",     new string[] { "highgardens" },                         true,  false);
    AddZone("thebathhouse",              "2_8_5",     new string[] { "bathhouse" },                           false, false);
    AddZone("thelunarisconcourse",       "2_8_6",     new string[] { "lunarisconcourse" },                    false, false);
    AddZone("thelunaristemplelevel1",    "2_8_7_1",   new string[0],                                          false, false);
    AddZone("thelunaristemplelevel2",    "2_8_7_2",   new string[0],                                          true,  false);
    AddZone("thequay",                   "2_8_8",     new string[] { "quay" },                                false, false);
    AddZone("thegraingate",              "2_8_9",     new string[] { "graingate" },                           false, false);
    AddZone("theimperialfields",         "2_8_10",    new string[] { "imperialfields" },                      false, false);
    AddZone("thesolarisconcourse",       "2_8_11",    new string[] { "solarisconcourse" },                    false, false);
    AddZone("thesolaristemplelevel1",    "2_8_12_1",  new string[0],                                          false, false);
    AddZone("thesolaristemplelevel2",    "2_8_12_2",  new string[0],                                          true,  false);
    AddZone("theharbourbridge",          "2_8_13",    new string[] { "harbourbridge", "lunarisandsolaris" },   false, false);
    AddZone("thehiddenunderbelly",       "2_8_14",    new string[] { "hiddenunderbelly" },                    true,  false);
    // --- Act 9 ---
    AddZone("highgate",                  "2_9_town",  new string[0],                                          false, false);
    AddZone("thebloodaqueduct",          "2_9_1",     new string[] { "bloodaqueduct", "blood" },              false, false);
    AddZone("thedescent",                "2_9_2",     new string[] { "descent" },                             false, false);
    AddZone("thevastiridesert",          "2_9_3",     new string[] { "vastiridesert" },                       false, false);
    AddZone("theoasis",                  "2_9_4",     new string[] { "oasis" },                               true,  false);
    AddZone("thefoothills",              "2_9_5",     new string[] { "foothills" },                           false, false);
    AddZone("theboilinglake",            "2_9_6",     new string[] { "boilinglake", "lake" },                 true,  false);
    AddZone("thetunnel",                 "2_9_7",     new string[] { "tunnel" },                              false, false);
    AddZone("thequarry",                 "2_9_8",     new string[] { "quarry" },                              false, false);
    AddZone("therefinery",               "2_9_9",     new string[] { "refinery" },                            true,  false);
    AddZone("thebellyofthebeast",        "2_9_10_1",  new string[] { "bellyofthebeast" },                     false, false);
    AddZone("therottingcore",            "2_9_10_2",  new string[] { "rottingcore", "depravedtrinity", "core" },true, false);
    // --- Act 10 ---
    AddZone("oriathdocks",               "2_10_town", new string[0],                                          false, false);
    AddZone("thecathedralrooftop",       "2_10_1",    new string[0],                                          false, false);
    AddZone("theravagedsquare",          "2_10_2",    new string[] { "ravagedsquare" },                       false, false);
    AddZone("thetorchedcourts",          "2_10_3",    new string[] { "torchedcourts" },                       false, false);
    AddZone("thedesecratedchambers",     "2_10_4",    new string[] { "desecratedchambers", "desecrated" },    true,  false);
    AddZone("thecanals",                 "2_10_5",    new string[] { "canals" },                              false, false);
    AddZone("thefeedingtrough",          "2_10_6",    new string[] { "feedingtrough", "kitava2", "trough" },  false, false);
    AddZone("thecontrolblocks",          "2_10_7",    new string[0],                                          true,  false);
    AddZone("thereliquary",              "2_10_8",    new string[0],                                          true,  false);
    AddZone("theossuary",                "2_10_9",    new string[0],                                          true,  false);

    // ==========================================
    //                 ACT COMPLETIONS 
    // ==========================================
    // --- Act 1-10 completions ---
    // Each alias targets the FIRST zone of the NEXT act (= the exact moment you cross the act boundary).
    // act5 and act10 have a secondary trigger: Kitava resistance-penalty log lines (see update/split blocks).
    AddZone("thesouthernforest",         "1_2_1",     new string[] { "act1" },                                false, false);
    AddZone("thecityofsarn",             "1_3_1",     new string[] { "act2" },                                false, false);
    AddZone("theaqueduct",               "1_4_1",     new string[] { "act3" },                                false, false);
    // act4 = entering Act 5 (Slave Pens), NOT The Ascent which is still Act 4.
    AddZone("theslavepens",              "1_5_1",     new string[] { "act4" },                                false, false);
    AddZone("thetwilightstrand",         "2_6_1",     new string[0],                                          false, false); // act5 registered separately below
    AddZone("thebridgeencampment",       "2_7_town",  new string[] { "act6" },                                false, false);
    AddZone("thesarnramparts",           "2_8_1",     new string[] { "act7" },                                false, false);
    AddZone("thebloodaqueduct",          "2_9_1",     new string[] { "act8" },                                false, false);
    AddZone("oriathdocks",               "2_10_town", new string[] { "act9" },                                false, false);

    // ── act5 alias fix ────────────────────────────────────────────────────────
    // AddZone("thetwilightstrand",...) would append 2_6_1 to a list already containing 1_1_1 (Act 1).
    // GetSplitDetails returns ids[0], so act5 would target 1_1_1 and fire on ANY Act 5+ zone
    // via cross-act forward math. We force it to its own dedicated single-entry list instead.
    vars.ZoneIDs["act5"] = new List<string>() { "2_6_1" };

    // ── act10 alias registration ──────────────────────────────────────────────
    // act10 split fires ONLY on Kitava's resistance-penalty log line ("merciless affliction").
    // Zone entry (Feeding Trough) must NOT trigger the split — Kitava is fought INSIDE that zone.
    // We still register the alias so GetSplitDetails can resolve any split named "act10",
    // but Rule 6 is gated with '&& curMatchedKey != "act10"' to block zone-entry firing.
    vars.ZoneIDs["act10"] = new List<string>() { "2_10_6" };

    // Ruined Square: post-Innocence hub with 3 entries (Torched Courts, Ossuary, Reliquary) and 1 exit (Cathedral Rooftop).
    // Exact-match arrival only — no forward math bypass, handles portal/waypoint re-entry correctly.
    vars.HubIDs.Add("1_5_3b");

    
    // Validate Aliases for within-Act collisions
    foreach (var kvp in vars.ZoneIDs) {
        if (kvp.Value.Count > 1) {
            Dictionary<string, List<string>> actGroups = new Dictionary<string, List<string>>();
            foreach (string id in kvp.Value) {
                string[] parts = id.Split('_');
                if (parts.Length > 1) {
                    string actPrefix = parts[0] + "_" + parts[1];
                    if (!actGroups.ContainsKey(actPrefix)) actGroups[actPrefix] = new List<string>();
                    actGroups[actPrefix].Add(id);
                }
            }
            foreach (var actGroup in actGroups) {
                if (actGroup.Value.Count > 1) {
                    vars.Log("!!! WARNING: Duplicate alias '" + kvp.Key + "' detected within Act " + actGroup.Key.Split('_')[1] + " for zones: " + string.Join(", ", actGroup.Value));
                }
            }
        }
    }

    vars.Log("--- Starting POE Smart Splitter ---");
}

init {
    // Path resolution — three priorities:
    //   1. poe_config.txt  (gitignored sidecar — personal setups / repo hygiene)
    //   2. vars.poeLogPath (inline variable at the top of this file — simple one-file setup)
    //   3. Steam default   (works out of the box for most installs)
    string logPath = @"C:\Program Files (x86)\Steam\steamapps\common\Path of Exile\logs\LatestClient.txt";
    string configPath = Directory.GetCurrentDirectory() + @"\Assets\poe_config.txt";
    if (System.IO.File.Exists(configPath)) {
        foreach (string cfgLine in System.IO.File.ReadAllLines(configPath)) {
            string trimmed = cfgLine.Trim();
            if (!string.IsNullOrEmpty(trimmed) && !trimmed.StartsWith("#") && trimmed.StartsWith("POE_LOG_PATH=")) {
                logPath = trimmed.Substring("POE_LOG_PATH=".Length).Trim();
                vars.Log("Path from poe_config.txt: " + logPath);
                break;
            }
        }
    } else if (!string.IsNullOrEmpty(vars.poeLogPath)) {
        logPath = vars.poeLogPath;
        vars.Log("Path from inline variable: " + logPath);
    } else {
        vars.Log("Using default Steam path: " + logPath);
    }

    if (System.IO.File.Exists(logPath)) {
        // Pre-seed currentZoneId from the last 8KB of the log so that the VERY FIRST zone change
        // (e.g. Twilight Strand → Lioneye's Watch) is not silently dropped.
        // Without this, currentZoneId starts empty, the first transition sets previousZoneId="",
        // the split guard (previousZoneId != "") fails, and Hillock's split is never registered.
        try {
            var seedFs = new System.IO.FileStream(logPath, System.IO.FileMode.Open, System.IO.FileAccess.Read, System.IO.FileShare.ReadWrite);
            long scanStart = Math.Max(0, seedFs.Length - 8192);
            seedFs.Seek(scanStart, System.IO.SeekOrigin.Begin);
            var seedReader = new System.IO.StreamReader(seedFs);
            string seedLine;
            while ((seedLine = seedReader.ReadLine()) != null) {
                if (seedLine.Contains("Generating level ") && seedLine.Contains(" area \"")) {
                    int si = seedLine.IndexOf("area \"") + 6;
                    int ei = seedLine.IndexOf("\" with seed");
                    if (ei > si) vars.currentZoneId = seedLine.Substring(si, ei - si);
                }
            }
            seedReader.Close();
            seedFs.Close();
            if (!string.IsNullOrEmpty(vars.currentZoneId))
                vars.Log("Pre-seeded current zone from log history: " + vars.currentZoneId);
        } catch {}

        // Open the main reader positioned at the end of the file for live reading
        var fs = new System.IO.FileStream(logPath, System.IO.FileMode.Open, System.IO.FileAccess.Read, System.IO.FileShare.ReadWrite);
        vars.reader = new System.IO.StreamReader(fs);
        vars.reader.BaseStream.Seek(0, System.IO.SeekOrigin.End);
        vars.Log("Stream opened on: " + logPath);
    } else {
        vars.Log("ERREUR : Fichier log introuvable (LatestClient.txt requis)");
    }
}

update {
    if (vars.reader == null) return false;

    vars.zoneChanged = false;
    string line;
    while ((line = vars.reader.ReadLine()) != null) {
        if (line.Contains("Generating level ") && line.Contains(" area \"")) {
            int startIndex = line.IndexOf("area \"") + 6;
            int endIndex = line.IndexOf("\" with seed");
            if (endIndex > startIndex) {
                string newId = line.Substring(startIndex, endIndex - startIndex);
                
                if (newId != vars.currentZoneId) {
                    vars.beforePreviousZoneId = vars.previousZoneId;
                    vars.previousZoneId = vars.currentZoneId;
                    vars.currentZoneId = newId;
                    vars.zoneChanged = true;
                    
                    if (timer.CurrentTime.RealTime.HasValue) {
                        float currentTime = (float)timer.CurrentTime.RealTime.Value.TotalSeconds;
                        vars.timeSpentInPreviousZone = currentTime - vars.timeEnteredZone;
                        vars.timeEnteredZone = currentTime;
                    } else {
                        vars.timeSpentInPreviousZone = 0f;
                        vars.timeEnteredZone = 0f;
                    }
                }
            }
        }
        // Kitava Act 5 defeat: resistance penalty "-30% to all Resistances"
        if (line.Contains("Kitava's cruel affliction") && line.Contains("-30% to all Resistances")) {
            vars.kitavaAct5Defeated = true;
            vars.Log(">>> Kitava Act 5 resistance penalty detected in log");
        }
        // Kitava Act 10 defeat: resistance penalty "-60%" total
        if (line.Contains("Kitava's merciless affliction") && line.Contains("-60%")) {
            vars.kitavaAct10Defeated = true;
            vars.Log(">>> Kitava Act 10 resistance penalty detected in log");
        }
    }

    if (vars.skipQueue > 0 && timer.CurrentPhase == TimerPhase.Running) {
        var model = new TimerModel { CurrentState = timer };
        model.SkipSplit();
        vars.skipQueue--;
        vars.Log(">>> SKIP PROCESSED. Remaining skips in queue: " + vars.skipQueue);
    }
}

split {
    // ── KITAVA DEFEAT DETECTION (zone-change independent) ────────────────────
    // Fires on the resistance-penalty log line, not on a zone transition.
    // Community standard: Act 5 / Act 10 runs end exactly when Kitava is slain.
    // Dual matching — handles both common LSS layouts:
    //   A) Split targets Kitava's arena zone directly (id 1_5_8 / 2_10_6):
    //      e.g. "Cathedral Rooftop", "kitava", "rooftop", "feedingtrough", "kitava2"
    //   B) Split uses the act-completion alias (key "act5" / "act10"):
    //      e.g. a split literally named "act5" which resolves to 2_6_1 (Twilight Strand P2)
    if (timer.CurrentPhase == TimerPhase.Running && timer.CurrentSplit != null) {
        if (vars.kitavaAct5Defeated || vars.kitavaAct10Defeated) {
            string[] kitavaDetails = vars.GetSplitDetails(timer.CurrentSplit.Name);
            string kitavaTargetId = kitavaDetails[0];
            string kitavaKey      = kitavaDetails[1];
            bool isKitava5Split  = (kitavaTargetId == "1_5_8") || (kitavaKey == "act5");
            bool isKitava10Split = (kitavaTargetId == "2_10_6") || (kitavaKey == "act10");
            if (vars.kitavaAct5Defeated && isKitava5Split) {
                vars.kitavaAct5Defeated = false;
                vars.Log(">>> KITAVA ACT 5 | Split triggered by resistance penalty (-30%) for split: " + timer.CurrentSplit.Name);
                return true;
            }
            if (vars.kitavaAct10Defeated && isKitava10Split) {
                vars.kitavaAct10Defeated = false;
                vars.Log(">>> KITAVA ACT 10 | Split triggered by resistance penalty (-60%) for split: " + timer.CurrentSplit.Name);
                return true;
            }
        }
    }

    if (vars.zoneChanged && vars.previousZoneId != "") {
        if (timer.CurrentSplit == null) return false;
        
        string normCurrentSplit = vars.Normalize(timer.CurrentSplit.Name);
        
        bool isMatch = false;
        string triggerReason = "";
        
        // ==========================================
        //       FORWARD PROGRESSION ENGINE
        // ==========================================
        
        string[] curDetails = vars.GetSplitDetails(timer.CurrentSplit.Name);
        string targetId = curDetails[0];
        string curMatchedKey = curDetails[1];
        string curAssociatedValues = curDetails[2];
        string curDeadEnd = (targetId != null && vars.DeadEndIDs.Contains(targetId)) ? "Yes" : "No";

        string nextSplitName = "None";
        string nextMatchedKey = "None";
        string nextAssociatedValues = "None";
        string nextDeadEnd = "No";
        string nextTargetId = null;

        int currentIndex = timer.CurrentSplitIndex;
        if (currentIndex + 1 < timer.Run.Count) {
            nextSplitName = timer.Run[currentIndex + 1].Name;
            string[] nextDetails = vars.GetSplitDetails(nextSplitName);
            nextTargetId = nextDetails[0];
            nextMatchedKey = nextDetails[1];
            nextAssociatedValues = nextDetails[2];
            nextDeadEnd = (nextTargetId != null && vars.DeadEndIDs.Contains(nextTargetId)) ? "Yes" : "No";
        }

        if (targetId != null) {
            // Rule 1: LOOKAHEAD BYPASS (Handles skipped splits up to +3 ahead)
            bool lookaheadMatch = false;
            
            for (int offset = 1; offset <= vars.lookaheadDistance; offset++) {
                if (currentIndex + offset < timer.Run.Count) {
                    string futureSplitName = timer.Run[currentIndex + offset].Name;
                    string[] futureDetails = vars.GetSplitDetails(futureSplitName);
                    string futureTargetId = futureDetails[0];
                    
                    if (futureTargetId != null && futureTargetId == vars.currentZoneId) {
                        // Anti-Town Skip: Never use a Town Entry to automatically bypass active splits.
                        if (futureTargetId.EndsWith("_town")) {
                            vars.Log(">>> LOOKAHEAD REJECTED: Entering a Town cannot bypass uncompleted splits.");
                            continue;
                        }

                        // Crucial check: Magic bypass ONLY ALLOWED if the bypassed zone is >= the target. No backwards skipping!
                        // Because towns evaluate to 0 mathematically, entering a non-town will always be > town.
                        if (vars.CompareZoneIDs(vars.currentZoneId, targetId) >= 0) {
                            lookaheadMatch = true;
                            isMatch = true;
                            vars.skipQueue = offset - 1;
                            triggerReason = "LOOKAHEAD BYPASS | Reached future split " + futureTargetId + " (+" + offset + "). Queued " + vars.skipQueue + " skips.";
                            break;
                        } else {
                            vars.Log(">>> LOOKAHEAD REJECTED: Next split " + futureTargetId + " is mathematically backwards from target " + targetId);
                        }
                    }
                }
            }

            // Rule 2: DEFAULT FORWARD MATH
            // Guard: passthrough zones split via Rule 7 on EXIT — never via forward math.
            // Block Rule 2 entirely for all passthrough targets. This covers:
            //   A) A→B→A direct backtracks (original guard)
            //   B) "future zone" false positives: e.g. entering CoI (1_5_5) while targeting
            //      Torched Courts (1_5_4b) — CoI has a higher ID but TC hasn't been reached yet.
            // Hub zones (Ruined Square) are NOT in PassthroughIDs, so Rule 2 still applies to them.
            if (!lookaheadMatch && vars.CompareZoneIDs(vars.currentZoneId, targetId) > 0) {
                bool isPassthroughBacktrack = vars.PassthroughIDs.Contains(targetId);
                if (!isPassthroughBacktrack) {
                    isMatch = true;
                    triggerReason = "FORWARD MATH | ID " + vars.currentZoneId + " mathematically supersedes Target ID " + targetId;
                }
            }

            // Rule 3: DEAD-END EXITS
            if (!lookaheadMatch && !isMatch && vars.DeadEndIDs.Contains(targetId) && vars.previousZoneId == targetId) {
                bool isTown = vars.currentZoneId.EndsWith("_town");
                
                int actNumber = 1;
                string[] parts = vars.currentZoneId.Split('_');
                if (parts.Length > 1) int.TryParse(parts[1], out actNumber);
                float requiredTime = vars.deadEndTimeoutBase - (vars.deadEndTimeoutPerAct * (float)actNumber);
                if (requiredTime < vars.deadEndTimeoutMin) requiredTime = vars.deadEndTimeoutMin;
                
                bool timeOut = vars.timeSpentInPreviousZone > requiredTime;

                if (isTown || timeOut) {
                    isMatch = true;
                    triggerReason = "DEAD-END EXIT | Exited to Town: " + isTown + " | Timeout elapsed: " + timeOut + " (" + vars.timeSpentInPreviousZone + "s / " + requiredTime + "s)";
                }
            }

            // Rule 4: TOWN / HUB ENTRY
            // Towns are mathematically neutral — must physically match target ID.
            // Hub zones (e.g. Ruined Square) share the same exact-match semantics: no math bypass.
            // Anti-waypoint guard for Hubs: if the player arrived FROM a town (waypoint/portal back),
            // do NOT split — that's a return visit, not a progression step.
            // (Town splits themselves are unaffected since town→town transitions don't occur.)
            bool isHubTarget  = vars.HubIDs.Contains(targetId);
            bool fromTown     = vars.previousZoneId.EndsWith("_town");
            if (!lookaheadMatch && !isMatch && (targetId.EndsWith("_town") || isHubTarget) && vars.currentZoneId == targetId) {
                if (isHubTarget && fromTown) {
                    // Waypoint return to hub — swallow silently, do not split.
                } else {
                    isMatch = true;
                    string entryType = isHubTarget ? "HUB ENTRY" : "TOWN ENTRY";
                    triggerReason = entryType + " | Entered required zone: " + vars.currentZoneId;
                }
            }

            // Rule 5: FIRST ZONE EXIT (Twilight Strand -> Lioneye's Watch)
            // Entering a town from the first zone of an Act doesn't mathematically forward-match because town IDs are treated as 0. 
            // If the target is an Act's first zone (e.g., 1_1_1) and we just entered that Act's town (e.g., 1_1_town), force the split.
            if (!lookaheadMatch && !isMatch && vars.currentZoneId.EndsWith("_town")) {
                string[] parts = targetId.Split('_');
                // Target must be strictly Act_Chapter_1 (Length 3)
                if (parts.Length == 3 && parts[2] == "1") {
                    string targetAct = parts[1];
                    string currentAct = vars.currentZoneId.Split('_')[1];
                    if (targetAct == currentAct) {
                        isMatch = true;
                        triggerReason = "FIRST ZONE EXIT | Left first zone " + targetId + " and entered Town " + vars.currentZoneId;
                    }
                }
            }

            // Rule 6: ACT COMPLETION / ENTER ZONE
            // Handles actX aliases where compare() returns 0 (current == target) so Rule 2 never fires.
            // Only triggers for explicit act completion aliases ("act1".."act10") to avoid
            // turning all zone arrivals into entry-splits.
            // act10 is EXCLUDED: Kitava is fought inside Feeding Trough (2_10_6), so entering
            // that zone must never trigger the split. act10 fires exclusively via the Kitava
            // resistance-penalty log line detected in the update block.
            if (!lookaheadMatch && !isMatch && vars.currentZoneId == targetId) {
                bool isActAlias = curMatchedKey.StartsWith("act") && curMatchedKey.Length >= 4
                    && curMatchedKey.Substring(3).All(char.IsDigit)
                    && curMatchedKey != "act10"; // act10: log-line-only, never zone-entry
                if (isActAlias) {
                    isMatch = true;
                    triggerReason = "ACT COMPLETION | Entered precise target zone " + vars.currentZoneId + " for Act alias: " + curMatchedKey;
                }
            }

            // Rule 7: PASSTHROUGH EXIT
            // For zones whose map ID is out of geographic order.
            // Fires when you DEPART the flagged zone (previousZoneId == targetId).
            // Two anti-backtrack guards:
            //   A) beforePreviousZoneId catches A→B→A (immediate return to exact origin).
            //   B) compare(current, target) < 0: legitimate passthrough exits ALWAYS go to
            //      a mathematically LOWER id. A higher-id exit means you’re moving backward.
            //      e.g. Vaal Ruins(11)→Wetlands(12) compare=+1 → reject.
            //           Wetlands(12)→Vaal Ruins(11) compare=-1 → accept.
            // To add more zones: set isPassthrough=true (5th param) in their AddZone call.
            if (!lookaheadMatch && !isMatch && vars.PassthroughIDs.Contains(targetId) && vars.previousZoneId == targetId) {
                bool isDirectBacktrack = vars.currentZoneId == vars.beforePreviousZoneId;
                bool isHigherIdExit    = vars.CompareZoneIDs(vars.currentZoneId, targetId) > 0;
                if (!isDirectBacktrack && !isHigherIdExit) {
                    isMatch = true;
                    triggerReason = "PASSTHROUGH EXIT | Left geo-exception zone " + vars.previousZoneId + " → " + vars.currentZoneId;
                }
            }
        }

        // --- NEW TELEMETRY LOG FORMAT ---
        string checkKey = vars.previousZoneId + ">" + vars.currentZoneId + "|" + timer.CurrentSplit.Name;
        if (vars.lastCheckedSplit != checkKey || isMatch) {
            vars.Log("==========================================================================");
            vars.Log("Previous Area : " + vars.GetAreaDetails(vars.previousZoneId)
                + "  |  beforePrev: " + (string.IsNullOrEmpty(vars.beforePreviousZoneId) ? "(none)" : vars.beforePreviousZoneId));
            vars.Log("Current Area  : " + vars.GetAreaDetails(vars.currentZoneId));
            vars.Log(string.Format("Current Split : {0}  |  Found Matching Area : {1} - id: {2}  |  Dead End : {3}", 
                timer.CurrentSplit.Name, curMatchedKey, curAssociatedValues, curDeadEnd));
            vars.Log(string.Format("Next Split    : {0}  |  Found Matching Area : {1} - id: {2}  |  Dead End : {3}", 
                nextSplitName, nextMatchedKey, nextAssociatedValues, nextDeadEnd));
            
            if (isMatch) {
                vars.Log(">>> " + triggerReason);
            }
            
            vars.lastCheckedSplit = checkKey;
        }

        if (isMatch) {
            return true;
        }
    }
}

reset {
    if (vars.zoneChanged && vars.currentZoneId == "1_1_1") {
        vars.previousZoneId = "";
        vars.beforePreviousZoneId = "";
        vars.kitavaAct5Defeated  = false;
        vars.kitavaAct10Defeated = false;
        vars.Log(">>> RESET");
        return true;
    }
}

exit {
    if (vars.reader != null) vars.reader.Dispose();
}

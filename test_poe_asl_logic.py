import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# =============================================================================
#   POE Smart Splitter — Python Test Harness (Full Rebuild)
#   Mirrors _POESmartSpliter_dev.asl exactly:
#     - Zone dictionary with aliases and dead-end flags
#     - Alias resolution (get_split_details)
#     - All 5 split rules with correct control flow
#     - Comprehensive test suite
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Zone Database (exact mirror of ASL startup block)
# ─────────────────────────────────────────────────────────────────────────────

zone_ids   = {}   # str -> list[str]   (exit-match zones)
dead_end_ids = set()  # set of zone ID strings
passthrough_ids = set()  # zones where exit fires regardless of next zone's math (geo order != ID order)
hub_ids = set()  # zones that split ONLY on exact arrival (like towns, but geographically not towns)

def add_zone(zone_name, id_str, aliases, is_dead_end, is_passthrough=False, is_hub=False):
    if zone_name not in zone_ids:
        zone_ids[zone_name] = []
    if id_str not in zone_ids[zone_name]:
        zone_ids[zone_name].append(id_str)
    for alias in aliases:
        if alias not in zone_ids:
            zone_ids[alias] = zone_ids[zone_name]
    if is_dead_end:
        dead_end_ids.add(id_str)
    if is_passthrough:
        passthrough_ids.add(id_str)
    if is_hub:
        hub_ids.add(id_str)

# --- Act 1 ---
add_zone("lioneyeswatch",        "1_1_town",  ["lioneye"],                            False)
add_zone("thetwilightstrand",    "1_1_1",     ["twilightstrand"],                     False)
add_zone("thecoast",             "1_1_2",     ["coast"],                              False)
add_zone("thetidalisland",       "1_1_2a",    ["tidalisland", "hailrake", "island"],  True)
add_zone("themudflats",          "1_1_3",     ["mudflats"],                           False)
add_zone("thefloodeddepths",     "1_1_4_0",   ["floodeddepths"],                      True)
add_zone("thesubmergedpassage",  "1_1_4_1",   ["submergedpassage"],                   False)
add_zone("theledge",             "1_1_5",     ["ledge"],                              False)
add_zone("theclimb",             "1_1_6",     ["climb"],                              False)
add_zone("thelowerprison",       "1_1_7_1",   ["lowerprison", "prison"],              False)
add_zone("theupperprison",       "1_1_7_2",   ["upperprison", "brutus", "warden"],    False)
add_zone("prisonersgate",        "1_1_8",     [],                                     False)
add_zone("theshipgraveyard",     "1_1_9",     ["shipgraveyard"],                      False)
add_zone("thefetidpool",         "1_1_3a",    ["fetidpool"],                          True)
add_zone("theshipgraveyardcave", "1_1_9a",    ["shipgraveyardcave", "cave"],          True)
add_zone("thecavernofwrath",     "1_1_11_1",  ["cavernofwrath"],                      False)
add_zone("thecavernofanger",     "1_1_11_2",  ["cavernofanger", "merveil"],           False)
# --- Act 2 ---
add_zone("theforestencampment",  "1_2_town",  ["forestencampment"],                   False)
add_zone("thesouthernforest",    "1_2_1",     ["southernforest", "southern", "act1"], False)
add_zone("theoldfields",         "1_2_2",     ["oldfields"],                          False)
add_zone("thecrossroads",        "1_2_3",     ["crossroads"],                         False)
add_zone("thebrokenbridge",      "1_2_4",     ["brokenbridge"],                       True)
add_zone("thecryptlevel1",       "1_2_5_1",   ["cryptlevel1"],                        False)
add_zone("thecryptlevel2",       "1_2_5_2",   ["cryptlevel2"],                        True)
add_zone("thechamberofsinslevel1","1_2_6_1",  ["chamberofsinslevel1"],                False)
add_zone("thechamberofsinslevel2","1_2_6_2",  ["chamberofsinslevel2"],                True)
add_zone("theriverways",         "1_2_7",     ["riverways"],                          False)
add_zone("thenorthernforest",    "1_2_8",     ["northernforest", "northern"],         False)
add_zone("thewesternforest",     "1_2_9",     ["westernforest", "western"],           False)
add_zone("theweaverschambers",   "1_2_10",    ["weaverschambers", "weaver", "spider"],True)
# [PASSTHROUGH] Act 2: Riverways(7)→Wetlands(12)→VaalRuins(11)→NorthernForest(8) — two backward exits
add_zone("thevaalruins",         "1_2_11",    ["vaalruins", "vaalruin"],              False, True)
add_zone("thewetlands",          "1_2_12",    ["wetlands"],                           False, True)
add_zone("thedreadthicket",      "1_2_13",    ["dreadthicket"],                       True)
add_zone("thecaverns",           "1_2_14_2",  ["caverns"],                            False)
add_zone("theancientpyramid",    "1_2_14_3",  ["ancientpyramid", "vaal", "vaaloversoul", "pyramid"], False)
add_zone("thefellshrineruins",   "1_2_15",    ["fellshrineruins"],                    False, True)  # [PASSTHROUGH] id=15 leads to Crypt (id=5) — exit math backward
# --- Act 3 ---
add_zone("thesarnencampment",    "1_3_town",  ["sarnencampment"],                     False)
add_zone("thecityofsarn",        "1_3_1",     ["cityofsarn", "act2"],                 False)
add_zone("theslums",             "1_3_2",     ["slums"],                              False)
add_zone("thecrematorium",       "1_3_3_1",   ["crematorium"],                        True)
add_zone("themarketplace",       "1_3_5",     ["marketplace"],                        False)
add_zone("thecatacombs",         "1_3_6",     ["catacombs"],                          True)
add_zone("thebattlefront",       "1_3_7",     ["battlefront"],                        False)
add_zone("thesolaristemplelevel1","1_3_8_1",  ["solaristemplelevel1", "solaris1"],    False)
add_zone("thesolaristemplelevel2","1_3_8_2",  ["solaristemplelevel2", "solaris2"],    True)
add_zone("thedocks",             "1_3_9",     ["docks"],                              True)
add_zone("thesewers",            "1_3_10_1",  ["sewers"],                             False)
add_zone("theebonybarracks",     "1_3_13",    ["ebonybarracks"],                      False)
add_zone("thelunaristemplelevel1","1_3_14_1", ["lunaristemplelevel1", "lunaris1"],    False)
add_zone("thelunaristemplelevel2","1_3_14_2", ["lunaristemplelevel2", "piety", "lunaristemple2", "lunaris2"], True)
add_zone("theimperialgardens",   "1_3_15",    ["imperialgardens"],                    False)
add_zone("thelibrary",           "1_3_17_1",  ["library"],                            False)
add_zone("thearchives",          "1_3_17_2",  ["archives"],                           True)
add_zone("thesceptreofgod",      "1_3_18_1",  ["sceptreofgod"],                       False)
add_zone("theuppersceptreofgod", "1_3_18_2",  ["uppersceptreofgod", "dominus", "sceptreofgod"], False)
# --- Act 4 ---
add_zone("highgate",             "1_4_town",  [],                                     False)
add_zone("theaqueduct",          "1_4_1",     ["aqueduct", "act3"],                   False)
add_zone("thedriedlake",         "1_4_2",     ["driedlake"],                          True)
add_zone("themineslevel1",       "1_4_3_1",   ["mineslevel1"],                        False)
add_zone("themineslevel2",       "1_4_3_2",   ["mineslevel2"],                        False)
add_zone("thecrystalveins",      "1_4_3_3",   ["crystalveins"],                       False)
add_zone("kaomsdream",           "1_4_4_1",   [],                                     False)
add_zone("kaomsstronghold",      "1_4_4_3",   [],                                     True)
add_zone("daressosdream",        "1_4_5_1",   [],                                     False)
add_zone("thegrandarena",        "1_4_5_2",   ["grandarena"],                         True)
add_zone("thebellyofthebeastlevel1","1_4_6_1",["bellyofthebeastlevel1", "belly1"],   False)
add_zone("thebellyofthebeastlevel2","1_4_6_2",["bellyofthebeastlevel2", "belly2"],   False)
add_zone("theharvest",           "1_4_6_3",   ["harvest", "malachai"],                False)
add_zone("theascent",            "1_4_7",     ["ascent"],                              False)
# --- Act 5 ---
add_zone("overseerstower",       "1_5_town",  [],                                     False)
add_zone("theslavepens",         "1_5_1",     ["slavepens", "act4"],                  False)
add_zone("thecontrolblocks",     "1_5_2",     ["controlblocks"],                      False)
add_zone("oriathsquare",         "1_5_3",     [],                                     False)
add_zone("theruinedsquare",      "1_5_3b",    ["ruinedsquare"],                       False)  # hub — registered via hub_ids.add below
add_zone("thetemplarcourts",     "1_5_4",     ["templarcourts"],                      False)
# [PASSTHROUGH] Torched Courts: post-Innocence Templar Courts. Exits to Ruined Square (lower id) — Rule 7 on exit.
add_zone("thetorchedcourts",     "1_5_4b",    ["torchedcourts"],                      False, True)
# [PASSTHROUGH] Chamber of Innocence: only exit is Torched Courts (lower id) after boss kill — Rule 7 on exit.
add_zone("thechamberofinnocence","1_5_5",     ["chamberofinnocence", "innocence"],     False, True)
add_zone("theossuary",           "1_5_6",     ["ossuary"],                            True)
add_zone("thereliquary",         "1_5_7",     ["reliquary"],                          True)
add_zone("thecathedralrooftop",  "1_5_8",     ["cathedralrooftop", "kitava", "rooftop"], False)
# --- Act 6 ---
add_zone("lioneyeswatch",        "2_6_town",  ["lioneye"],                            False)
add_zone("thetwilightstrand",    "2_6_1",     [],                                     False)  # act5 forced separately below
add_zone("thecoast",             "2_6_2",     [],                                     False)
add_zone("thetidalisland",       "2_6_3",     ["tidalisland"],                        True)
add_zone("themudflats",          "2_6_4",     [],                                     False)
add_zone("thekaruifortress",     "2_6_5",     ["karuifortress"],                      False)
add_zone("theridge",             "2_6_6",     ["ridge"],                              False)
add_zone("thelowerprison",       "2_6_7_1",   [],                                     False)
add_zone("shavronnestower",      "2_6_7_2",   ["shavronne", "tower"],                 True)
add_zone("prisonersgate",        "2_6_8",     [],                                     False)
add_zone("thewesternforest",     "2_6_9",     [],                                     False)
add_zone("theriverways",         "2_6_10",    [],                                     False)
add_zone("thewetlands",          "2_6_11",    [],                                     False)
add_zone("thesouthernforest",    "2_6_12",    [],                                     False)
add_zone("thecavernofanger",     "2_6_13",    ["cavernofanger", "merveil"],           False)
add_zone("thebeacon",            "2_6_14",    ["beacon"],                             False)
add_zone("thebrinekingsreef",    "2_6_15",    ["brinekingsreef", "brineking", "reef"],False)
# --- Act 7 ---
add_zone("thebridgeencampment",  "2_7_town",  ["bridgeencampment", "act6"],           False)
add_zone("thebrokenbridge",      "2_7_1",     [],                                     False)
add_zone("thecrossroads",        "2_7_2",     [],                                     False)
add_zone("thefellshrineruins",   "2_7_3",     [],                                     False)
add_zone("thecrypt",             "2_7_4",     ["crypt"],                              True)
# maligarossanctum commented out in ASL — id '2_7_5_map' has sub-level 0 which is < Chamber L1 (sub 1),
# causing Rule 2 to false-fire on first entry to Chamber L1. 'maligaro' alias moved to Chamber L1 instead.
# add_zone("maligarossanctum",  "2_7_5_map", ["sanctum"],                            True)
add_zone("thechamberofsinslevel1","2_7_5_1",  ["maligaro"],                           False)
add_zone("thechamberofsinslevel2","2_7_5_2",  [],                                     False)
add_zone("theden",               "2_7_6",     ["den"],                                False)
add_zone("theashenfields",       "2_7_7",     ["ashenfields"],                        False)
add_zone("thenorthernforest",    "2_7_8",     [],                                     False)
add_zone("thedreadthicket",      "2_7_9",     [],                                     True)
add_zone("thecauseway",          "2_7_10",    ["causeway"],                           False)
add_zone("thevaalcity",          "2_7_11",    ["vaalcity"],                           False)
add_zone("thetempleofdecaylevel1","2_7_12_1", ["templeofdecaylevel1", "decay1"],      False)
add_zone("thetempleofdecaylevel2","2_7_12_2", ["templeofdecaylevel2", "arakaali", "templeofdecay", "decay2"], True)
# --- Act 8 ---
add_zone("thesarnencampment",    "2_8_town",  [],                                     False)
add_zone("thesarnramparts",      "2_8_1",     ["sarnramparts", "act7"],               False)
add_zone("thetoxicconduits",     "2_8_2_1",   ["toxicconduits", "conduits"],          False)
add_zone("doedrescesspool",      "2_8_2_2",   ["doedre", "cesspool"],                 False)
add_zone("thegrandpromenade",    "2_8_3",     ["grandpromenade"],                     False)
add_zone("thehighgardens",       "2_8_4",     ["highgardens"],                        True)
add_zone("thebathhouse",         "2_8_5",     ["bathhouse"],                          False)
add_zone("thelunarisconcourse",  "2_8_6",     ["lunarisconcourse"],                   False)
add_zone("thelunaristemplelevel1","2_8_7_1",  [],                                     False)  # Fixed: was "2_8_7_1_"
add_zone("thelunaristemplelevel2","2_8_7_2",  [],                                     True)
add_zone("thequay",              "2_8_8",     ["quay"],                               False)
add_zone("thegraingate",         "2_8_9",     ["graingate"],                          False)
add_zone("theimperialfields",    "2_8_10",    ["imperialfields"],                     False)
add_zone("thesolarisconcourse",  "2_8_11",    ["solarisconcourse"],                   False)
add_zone("thesolaristemplelevel1","2_8_12_1", [],                                     False)
add_zone("thesolaristemplelevel2","2_8_12_2", [],                                     True)
add_zone("theharbourbridge",     "2_8_13",    ["harbourbridge", "lunarisandsolaris"],  False)
add_zone("thehiddenunderbelly",  "2_8_14",    ["hiddenunderbelly"],                   True)
# --- Act 9 ---
add_zone("highgate",             "2_9_town",  [],                                     False)
add_zone("thebloodaqueduct",     "2_9_1",     ["bloodaqueduct", "blood", "act8"],     False)
add_zone("thedescent",           "2_9_2",     ["descent"],                            False)
add_zone("thevastiridesert",     "2_9_3",     ["vastiridesert"],                      False)
add_zone("theoasis",             "2_9_4",     ["oasis"],                              True)
add_zone("thefoothills",         "2_9_5",     ["foothills"],                          False)
add_zone("theboilinglake",       "2_9_6",     ["boilinglake", "lake"],                True)
add_zone("thetunnel",            "2_9_7",     ["tunnel"],                             False)
add_zone("thequarry",            "2_9_8",     ["quarry"],                             False)
add_zone("therefinery",          "2_9_9",     ["refinery"],                           True)
add_zone("thebellyofthebeast",   "2_9_10_1",  ["bellyofthebeast"],                    False)
add_zone("therottingcore",       "2_9_10_2",  ["rottingcore", "depravedtrinity", "core"], True)
# --- Act 10 ---
add_zone("oriathdocks",          "2_10_town", ["act9"],                               False)
add_zone("thecathedralrooftop",  "2_10_1",    [],                                     False)
add_zone("theravagedsquare",     "2_10_2",    ["ravagedsquare"],                      False)
add_zone("thetorchedcourts",     "2_10_3",    ["torchedcourts"],                      False)
add_zone("thedesecratedchambers","2_10_4",    ["desecratedchambers", "desecrated"],   True)
add_zone("thecanals",            "2_10_5",    ["canals"],                             False)
add_zone("thefeedingtrough",     "2_10_6",    ["feedingtrough", "kitava2", "trough", "act10"], False)
add_zone("thecontrolblocks",     "2_10_7",    [],                                     True)
add_zone("thereliquary",         "2_10_8",    [],                                     True)
add_zone("theossuary",           "2_10_9",    [],                                     True)

# ── Post-registration overrides ──────────────────────────────────────────────
# act5: thetwilightstrand shares a list with '1_1_1' (Act 1 Part 1). Without this
# override, ids[0] = '1_1_1' and act5 would fire on ANY Act 5+ zone via cross-act math.
zone_ids["act5"] = ["2_6_1"]
# Ruined Square: post-Innocence hub with 3 entries (TC, Ossuary, Reliquary), 1 exit (Rooftop). Exact-match only.
hub_ids.add("1_5_3b")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Normalize (strip non-alphanumeric, lowercase) — mirrors ASL
# ─────────────────────────────────────────────────────────────────────────────

def normalize(name):
    if not name:
        return ""
    return ''.join(c.lower() for c in name if c.isalnum())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: get_split_details — mirrors ASL GetSplitDetails exactly
# Returns: (target_id, matched_key, associated_ids_str)
# ─────────────────────────────────────────────────────────────────────────────

def get_split_details(split_name):
    if not split_name:
        return (None, "None", "None")

    # Raw ID fallback FIRST (before normalization, which strips underscores):
    # If the split name looks like a raw zone ID (contains '_' or starts with digit),
    # check it directly before attempting alias resolution.
    raw = split_name.strip()
    if '_' in raw or (raw and raw[0].isdigit()):
        # Check if it matches any known ID
        raw_lower = raw.lower()
        # Search all zone lists for this exact ID
        matched_key = None
        matched_ids = None
        for key, ids in zone_ids.items():
            if raw_lower in [i.lower() for i in ids]:
                if matched_key is None:
                    matched_key = key
                    matched_ids = ids
        if matched_ids:
            return (raw_lower, matched_key, ", ".join(matched_ids))
        # Not in any list but looks like a raw ID — return as-is
        return (raw_lower, "Raw ID", raw_lower)

    norm = normalize(split_name)
    if not norm:
        return (None, "None", "None")

    # Direct key lookup
    if norm in zone_ids:
        ids = zone_ids[norm]
        return (ids[0], norm, ", ".join(ids))

    # Alias scan
    for alias, ids in zone_ids.items():
        alias_match = False
        if alias.startswith("act") and len(alias) <= 5:
            if alias in norm:
                idx = norm.index(alias) + len(alias)
                if idx >= len(norm) or not norm[idx].isdigit():
                    alias_match = True
        elif len(alias) >= 4:
            if alias in norm:
                alias_match = True
        if alias_match:
            return (ids[0], alias, ", ".join(ids))

    return (None, "None", "None")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: CompareZoneIDs — faithful mirror of ASL math engine
# ─────────────────────────────────────────────────────────────────────────────

def compare_zone_ids(current_id, target_id):
    if not current_id or not target_id:
        return 0

    cp = current_id.split('_')
    tp = target_id.split('_')

    # 1. Act comparison (must happen first, even for towns)
    if len(cp) > 1 and len(tp) > 1:
        if cp[1].isdigit() and tp[1].isdigit():
            ca, ta = int(cp[1]), int(tp[1])
            if ca != ta:
                return 1 if ca > ta else -1

    # 1.5 Town math
    ci = current_id.endswith('_town')
    ti = target_id.endswith('_town')
    if ci and ti:  return 0
    if ti and not ci: return 1   # non-town > town in same act
    if ci and not ti: return -1  # town < non-town in same act

    # 2. Map progression
    if len(cp) > 2 and len(tp) > 2:
        cs = ''.join(c for c in cp[2] if c.isdigit())
        ts = ''.join(c for c in tp[2] if c.isdigit())
        if cs and ts:
            cm, tm2 = int(cs), int(ts)
            if cm != tm2:
                return 1 if cm > tm2 else -1
            cside = 'a' in cp[2] or 'b' in cp[2]
            tside = 'a' in tp[2] or 'b' in tp[2]
            if cside != tside:
                return 0   # side area == base area numerically

    # 3. Sub-level comparison
    if len(cp) > 3 or len(tp) > 3:
        cs2 = int(cp[3]) if len(cp) > 3 and cp[3].isdigit() else 0
        ts2 = int(tp[3]) if len(tp) > 3 and tp[3].isdigit() else 0
        if cs2 != ts2:
            return 1 if cs2 > ts2 else -1

    return 0  # identical


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: split() logic — faithful reimplementation of ASL split block
# Returns: (is_match: bool, trigger_reason: str)
# ─────────────────────────────────────────────────────────────────────────────

def test_split_logic(
    current_zone_id,        # vars.currentZoneId
    previous_zone_id,       # vars.previousZoneId
    split_name,             # timer.CurrentSplit.Name  (human-readable or raw ID)
    future_splits=None,     # [timer.Run[i+1].Name, timer.Run[i+2].Name, ...]  (up to 3)
    time_spent=0.0,         # vars.timeSpentInPreviousZone
    before_previous_id="",  # vars.beforePreviousZoneId  (for Rule 7 backtrack guard)
    kitava_act5_defeated=False,   # vars.kitavaAct5Defeated  (log-line flag)
    kitava_act10_defeated=False,  # vars.kitavaAct10Defeated (log-line flag)
):
    if future_splits is None:
        future_splits = []

    target_details  = get_split_details(split_name)
    target_id       = target_details[0]
    cur_matched_key = target_details[1]

    is_match        = False
    trigger_reason  = ""
    skip_queue      = 0

    if target_id is None:
        return False, "UNRESOLVED | Split name did not map to any zone ID"

    # ── KITAVA DEFEAT DETECTION (mirrors ASL split block, runs first) ─────────
    # Dual matching: A) zone-id match (cathedralrooftop/feedingtrough),
    #               B) act-alias key match (act5/act10).
    if kitava_act5_defeated or kitava_act10_defeated:
        is_kitava5_split  = (target_id == "1_5_8") or (cur_matched_key == "act5")
        is_kitava10_split = (target_id == "2_10_6") or (cur_matched_key == "act10")
        if kitava_act5_defeated and is_kitava5_split:
            return True, f"KITAVA ACT 5 | Split triggered by resistance penalty (-30%) for split: {split_name}"
        if kitava_act10_defeated and is_kitava10_split:
            return True, f"KITAVA ACT 10 | Split triggered by resistance penalty (-60%) for split: {split_name}"

    # ── Rule 1: LOOKAHEAD BYPASS ──────────────────────────────────────────────
    lookahead_match = False
    for offset, future_split_name in enumerate(future_splits[:3], 1):
        future_details  = get_split_details(future_split_name)
        future_target_id = future_details[0]

        if future_target_id is None:
            continue
        if future_target_id != current_zone_id:
            continue

        # Anti-town skip: entering a town cannot bypass uncompleted splits
        if future_target_id.endswith('_town'):
            # ASL: continue (not return) — keep checking other offsets
            continue

        # Math check: bypass only allowed if current >= target (no backwards skipping)
        if compare_zone_ids(current_zone_id, target_id) >= 0:
            lookahead_match = True
            is_match        = True
            skip_queue      = offset - 1
            trigger_reason  = (
                f"LOOKAHEAD BYPASS | Reached future split {future_target_id}"
                f" (+{offset}). Queued {skip_queue} skips."
            )
            break
        else:
            # ASL: continue (not return) — keep checking further offsets
            continue

    # ── Rule 2: FORWARD MATH ──────────────────────────────────────────────────
    # Guard: passthrough zones split via Rule 7 on EXIT — never via forward math.
    # Block Rule 2 entirely for passthrough targets (covers A→B→A AND future-zone false positives).
    if not lookahead_match and compare_zone_ids(current_zone_id, target_id) > 0:
        is_passthrough_backtrack = (target_id in passthrough_ids)
        if not is_passthrough_backtrack:
            is_match       = True
            trigger_reason = (
                f"FORWARD MATH | ID {current_zone_id} mathematically supersedes"
                f" Target ID {target_id}"
            )

    # ── Rule 3: DEAD-END EXIT ────────────────────────────────────────────────
    if not lookahead_match and not is_match:
        if target_id in dead_end_ids and previous_zone_id == target_id:
            is_town = current_zone_id.endswith('_town')

            act_number = 1
            parts = current_zone_id.split('_')
            if len(parts) > 1 and parts[1].isdigit():
                act_number = int(parts[1])

            required_time = max(40.0 - 2.5 * act_number, 15.0)
            time_out = time_spent > required_time

            if is_town or time_out:
                is_match       = True
                trigger_reason = (
                    f"DEAD-END EXIT | Exited to Town: {is_town}"
                    f" | Timeout elapsed: {time_out}"
                    f" ({time_spent}s / {required_time}s)"
                )

    # ── Rule 4: TOWN / HUB ENTRY ────────────────────────────────────────
    # Hub zones share the same exact-match semantics as towns: no math bypass.
    # Two guards prevent false fires for hubs:
    #   A) Anti-waypoint: player came FROM a town (waypoint/portal back)
    #   B) Anti-backtrack: player came FROM a higher-ID zone (e.g. Rooftop→RS after Kitava kill)
    if not lookahead_match and not is_match:
        is_hub_target     = target_id in hub_ids
        from_town         = previous_zone_id.endswith('_town')
        is_backward_entry = is_hub_target and compare_zone_ids(previous_zone_id, target_id) > 0
        if (target_id.endswith('_town') or is_hub_target) and current_zone_id == target_id:
            if is_hub_target and (from_town or is_backward_entry):
                pass  # Waypoint/portal return or backward re-entry — swallow silently
            else:
                is_match       = True
                entry_type = "HUB ENTRY" if is_hub_target else "TOWN ENTRY"
                trigger_reason = f"{entry_type} | Entered required zone: {current_zone_id}"

    # ── Rule 5: FIRST ZONE EXIT ───────────────────────────────────────────────
    # Twilight Strand -> Lioneye's Watch edge case:
    # If target is act_X_1 (first zone of an act) and we just entered that act's town.
    if not lookahead_match and not is_match:
        if current_zone_id.endswith('_town'):
            t_parts = target_id.split('_')
            if len(t_parts) == 3 and t_parts[2] == '1':
                target_act  = t_parts[1]
                current_act = current_zone_id.split('_')[1]
                if target_act == current_act:
                    is_match       = True
                    trigger_reason = (
                        f"FIRST ZONE EXIT | Left first zone {target_id}"
                        f" and entered Town {current_zone_id}"
                    )

    # ── Rule 6: ACT COMPLETION ENTER ZONE ─────────────────────────────────
    # Handles actX aliases where current==target so compare()==0 (Rule 2 fails).
    # act10 is EXCLUDED: Kitava is fought inside Feeding Trough (2_10_6), so
    # zone-entry must never fire the split. act10 is log-line only.
    if not lookahead_match and not is_match:
        if current_zone_id == target_id:
            is_act_alias = (
                cur_matched_key.startswith('act')
                and len(cur_matched_key) >= 4
                and cur_matched_key[3:].isdigit()
                and cur_matched_key != 'act10'   # act10: log-line-only, never zone-entry
            )
            if is_act_alias:
                is_match       = True
                trigger_reason = (
                    f"ACT COMPLETION | Entered precise target zone"
                    f" {current_zone_id} for Act alias: {cur_matched_key}"
                )

    # ── Rule 7: PASSTHROUGH EXIT ──────────────────────────────────
    # Two anti-backtrack guards:
    #   A) before_previous_id == current: catches A→B→A.
    #   B) compare(current, target) > 0: a legitimate passthrough exit ALWAYS
    #      moves to a lower-ID zone. A higher-ID exit is a backtrack.
    if not lookahead_match and not is_match:
        if target_id in passthrough_ids and previous_zone_id == target_id:
            is_direct_backtrack = current_zone_id == before_previous_id
            is_higher_id_exit   = compare_zone_ids(current_zone_id, target_id) > 0
            if not is_direct_backtrack and not is_higher_id_exit:
                is_match       = True
                trigger_reason = (
                    f"PASSTHROUGH EXIT | Left geo-exception zone"
                    f" {previous_zone_id} → {current_zone_id}"
                )

    return is_match, trigger_reason


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Test Runner
# ─────────────────────────────────────────────────────────────────────────────

_passed = 0
_failed = 0
_total  = 0

def assert_test(name, result, expected_match, expected_rule=None):
    global _passed, _failed, _total
    _total += 1
    is_match, reason = result
    rule_ok = (expected_rule is None) or (expected_rule in reason)
    if is_match == expected_match and rule_ok:
        print(f"  [PASS] {name}")
        _passed += 1
    else:
        rule_note = f" | Expected rule containing: '{expected_rule}', Got: '{reason}'" if not rule_ok and expected_rule else ""
        print(f"  [FAIL] {name} | Expected: {expected_match}, Got: {is_match}{rule_note}")
        print(f"         Reason: {reason}")
        _failed += 1

def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")

def run_tests():
    global _passed, _failed, _total

    print("=" * 60)
    print("  POE Smart Splitter — Full Logic Test Suite")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────
    section("RULE 2 — Forward Math (Expected Successes)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Basic forward step (1_1_3 > 1_1_2)",
        test_split_logic("1_1_3", "1_1_2", "1_1_2"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Cross-act forward (Act 2 > Act 1 zone)",
        test_split_logic("1_2_1", "1_1_11_2", "1_1_11_2"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Sub-level forward (Upper Prison > Lower Prison)",
        test_split_logic("1_1_7_2", "1_1_7_1", "lowerprison"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Human-readable split name resolves (Mud Flats via forward move)",
        # current=1_1_4_1 (Submerged Passage), previous=1_1_3, target='The Mud Flats' -> 1_1_3
        # compare(1_1_4_1, 1_1_3): map 4 > 3 -> 1 -> Rule 2 fires
        test_split_logic("1_1_4_1", "1_1_2", "The Mud Flats"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Alias resolves (merveil -> 1_1_11_2)",
        test_split_logic("1_2_1", "1_1_11_2", "Merveil"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Cross-part forward (Act 6 > Act 5)",
        test_split_logic("2_6_1", "1_5_8", "1_5_8"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Non-town > town in same act (map supersedes town)",
        test_split_logic("1_1_2", "1_1_town", "1_1_town"),
        True, "FORWARD MATH"
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 2 — Forward Math (Expected Failures / Guards)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "No split on backward zone (1_1_2 does NOT supersede 1_1_3)",
        test_split_logic("1_1_2", "1_1_1", "1_1_3"),
        False
    )
    assert_test(
        "Town does NOT supersede non-town in same act",
        test_split_logic("1_1_town", "1_1_2", "1_1_3"),
        False
    )
    assert_test(
        "Exact same zone ID returns 0 (no forward match)",
        test_split_logic("1_1_3", "1_1_2", "1_1_3"),
        False
    )
    assert_test(
        "Side area == base area numerically (1_1_2a does NOT beat 1_1_2)",
        test_split_logic("1_1_2a", "1_1_1", "1_1_2"),
        False
    )
    assert_test(
        "Sub-level backward: lower sublevel does NOT trigger upper split",
        test_split_logic("1_1_7_1", "1_1_6", "upperprison"),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 1 — Lookahead Bypass (Expected Successes)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Lookahead at offset+1 (skip 1_1_1, land on 1_1_2)",
        test_split_logic("1_1_2", "1_1_town", "1_1_1", future_splits=["1_1_2"]),
        True, "LOOKAHEAD BYPASS"
    )
    assert_test(
        "Lookahead at offset+2 (skip two splits)",
        test_split_logic("1_1_3", "1_1_1", "1_1_1", future_splits=["1_1_2", "1_1_3"]),
        True, "LOOKAHEAD BYPASS"
    )
    assert_test(
        "Lookahead at offset+3 (skip three splits)",
        test_split_logic("1_1_4_1", "1_1_2", "1_1_2", future_splits=["1_1_3", "1_1_4_0", "1_1_4_1"]),
        True, "LOOKAHEAD BYPASS"
    )
    assert_test(
        "Lookahead with resolved split name (Coast at +1)",
        test_split_logic("1_1_2", "1_1_town", "1_1_1", future_splits=["The Coast"]),
        True, "LOOKAHEAD BYPASS"
    )
    assert_test(
        "Lookahead: bad offset+1 town is skipped, valid offset+2 fires",
        test_split_logic("1_1_3", "1_1_town", "1_1_1",
                         future_splits=["1_1_town", "1_1_3"]),  # offset+1=town(skip), offset+2=valid
        True, "LOOKAHEAD BYPASS"
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 1 — Lookahead Bypass (Expected Failures / Guards)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Anti-town skip: entering a town never bypasses uncompleted splits",
        test_split_logic("1_1_town", "1_1_1", "1_1_2", future_splits=["1_1_town"]),
        False
    )
    assert_test(
        "Lookahead backwards guard: future split is behind target",
        test_split_logic("1_1_1", "1_1_2", "1_1_3", future_splits=["1_1_1"]),
        False
    )
    assert_test(
        "Lookahead: future splits don't match current zone, no fire",
        # current=1_1_3, target=1_1_3 (compare=0, Rule 2 fails).
        # future=[1_1_5, 1_1_6]: neither is current (1_1_3), so lookahead skips all. Result: False.
        test_split_logic("1_1_3", "1_1_2", "1_1_3", future_splits=["1_1_5", "1_1_6"]),
        False
    )
    assert_test(
        "Lookahead: future split unresolvable (typo), no fire",
        # current=1_1_3, target=1_1_3 (compare=0). future=['xyzZone'] -> None -> skip. Result: False.
        test_split_logic("1_1_3", "1_1_2", "1_1_3", future_splits=["xyzZone"]),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 3 — Dead-End Exit (Expected Successes)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Dead-End exit to town (Fetid Pool -> Lioneye's Watch)",
        test_split_logic("1_1_town", "1_1_3a", "fetidpool"),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Dead-End exit to town (Tidal Island -> Lioneye's Watch)",
        test_split_logic("1_1_town", "1_1_2a", "tidalisland"),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Dead-End timeout > 37.5s (Act 1, previous zone = dead end)",
        test_split_logic("1_1_2", "1_1_3a", "fetidpool", time_spent=40.0),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Dead-End timeout: Act 10 threshold is 15s (40-25=15)",
        test_split_logic("2_10_2", "2_10_4", "desecratedchambers", time_spent=16.0),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Dead-End exit: Crypt (2_7_4) -> town (Act 7, dead-end to town)",
        test_split_logic("2_7_town", "2_7_4", "crypt"),
        True, "DEAD-END EXIT"
    )

    assert_test(
        "Dead-End exit: Docks -> town (Act 3)",
        test_split_logic("1_3_town", "1_3_9", "docks"),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Dead-End exit: Ship Graveyard Cave -> Ship Graveyard (timeout 57.5s Act 1 -> used 60s)",
        test_split_logic("1_1_9", "1_1_9a", "shipgraveyardcave", time_spent=60.0),
        True, "DEAD-END EXIT"
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 3 — Dead-End Exit (Expected Failures / Guards)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Dead-End timeout NOT elapsed Act 1 (< 37.5s, no town)",
        test_split_logic("1_1_2", "1_1_3a", "fetidpool", time_spent=20.0),
        False
    )
    assert_test(
        "Dead-End timeout NOT elapsed Act 10 (< 15s, no town)",
        test_split_logic("2_10_2", "2_10_4", "desecratedchambers", time_spent=10.0),
        False
    )
    assert_test(
        "Dead-End: previous zone does NOT match target (no exit from that zone)",
        test_split_logic("1_1_2", "1_1_2", "fetidpool", time_spent=60.0),
        False
    )
    assert_test(
        "Non-dead-end zone does NOT fire Rule 3 regardless of timeout",
        # Use a scenario where current and target are the same (no Rule 2), and target is not dead end
        # current=1_1_6 (Climb), previous=1_1_5, target=1_1_6: compare=0, not dead end, should be False
        test_split_logic("1_1_6", "1_1_5", "1_1_6", time_spent=999.0),
        False
    )
    assert_test(
        "Dead-End: side area (1_1_2a) is dead end, but current NOT from it (previous != target)",
        # current=1_1_town (same act but not > 1_1_2a by math: town < map),
        # previous=1_1_2 (not 1_1_2a), target=1_1_2a: Rule 3 needs previous==target, fails
        test_split_logic("1_1_town", "1_1_2", "tidalisland", time_spent=0.0),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 4 — Town Entry (Expected Successes)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Town Entry: entering Lioneye's Watch as split target",
        # Use human-readable name rather than raw ID (raw ID loses '_' in norm)
        test_split_logic("1_1_town", "1_1_1", "lioneyeswatch"),
        True, "TOWN ENTRY"
    )
    assert_test(
        "Town Entry: Entering Forest Encampment as split target",
        test_split_logic("1_2_town", "1_2_1", "theforestencampment"),
        True, "TOWN ENTRY"
    )
    assert_test(
        "Town Entry: Act 7 Bridge Encampment via alias (bridgeencampment)",
        test_split_logic("2_7_town", "2_6_15", "bridgeencampment"),
        True, "TOWN ENTRY"
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 4 — Town Entry (Expected Failures)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Town Entry: current zone is NOT the target town (same act, wrong town)",
        # Both in same act to prevent Rule 2 firing. current=1_2_town, split wants 1_2_town but it's the same town,
        # actually we want current != target. Use current=1_1_town (Act 1 town), target=1_2_town (Act 2 town).
        # compare(1_1_town, 1_2_town): act 1 < act 2 -> returns -1 -> Rule 2 fails.
        # Rule 4: target endswith _town but current (1_1_town) != target (1_2_town) -> Rule 4 also fails. Correct!
        test_split_logic("1_1_town", "1_1_10", "theforestencampment"),
        False
    )
    assert_test(
        "Town Entry: target is not a town, rule must not fire",
        test_split_logic("1_1_town", "1_1_1", "1_1_2"),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 5 — First Zone Exit (Expected Successes)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "First Zone Exit: Twilight Strand (1_1_1) -> Lioneye's Watch",
        test_split_logic("1_1_town", "1_1_1", "thetwilightstrand"),
        True, "FIRST ZONE EXIT"
    )
    assert_test(
        "First Zone Exit: Act 6 Twilight Strand (2_6_1) split -> entering 2_6_town",
        # Use same-part zone to test Rule 5 in isolation.
        # Scenario: target=2_6_1 (first zone of Act 6), current=2_6_town (Act 6 town).
        # compare(2_6_town, 2_6_1): same act (6) -> town < map -> -1 -> Rule 2 fails.
        # Rule 5: current endswith _town? Yes. target parts=['2','6','1'], parts[2]='1' -> match act '6'=='6' -> fires!
        test_split_logic("2_6_town", "2_6_1", "2_6_1"),
        True, "FIRST ZONE EXIT"
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 5 — First Zone Exit (Expected Failures / Guards)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Rule 5 must NOT fire for non-first zones (target Crossroads, entering Act 2 town)",
        test_split_logic("1_2_town", "1_2_3", "thecrossroads"),
        False
    )
    assert_test(
        "Rule 5 must NOT fire for wrong-act combination (same act, different chapter)",
        # current=1_1_town, target split is Act 2's first zone (1_2_1).
        # compare(1_1_town, 1_2_1): act 1 < act 2 -> -1 -> Rule 2 fails.
        # Rule 5: current endswith _town, target parts[2]='1', target_act='2' != current_act='1' -> no match. Correct!
        test_split_logic("1_1_town", "1_1_11_2", "thesouthernforest"),
        False
    )
    assert_test(
        "Rule 5 must NOT fire when current is not a town (no town -> no Rule 5)",
        # current=1_1_2 (Coast), target=1_1_1 (Twilight Strand). compare: 2>1 -> Rule 2 fires!
        # We need current that is NOT > target. Use current=1_1_1 same zone as target.
        # compare(1_1_1, 1_1_1) = 0 -> Rule 2 fails. No town, Rule 5 fails. No dead-end, Rule 3 fails.
        test_split_logic("1_1_1", "1_1_town", "thetwilightstrand"),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("RULE 6 — Act Completion Enter Zone (Expected Successes)")
    # ── This covers the previously-failing test. Rule 6 is in the harness ──
    # ── but NOT yet in the dev ASL. Tests here prove what's possible       ──
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Act 1 Completion: entering 1_2_1 (Southern Forest) via 'act1' alias",
        test_split_logic("1_2_1", "1_1_11_2", "act1"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 2 Completion: entering 1_3_1 (City of Sarn) via 'act2' alias",
        test_split_logic("1_3_1", "1_2_14_3", "act2"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 3 Completion: entering 1_4_1 (Aqueduct) via 'act3' alias",
        test_split_logic("1_4_1", "1_3_18_2", "act3"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 4 Completion: entering 1_5_1 (Slave Pens, first zone of Act 5) via 'act4' alias",
        # act4 now correctly targets 1_5_1 (Slave Pens = first zone of Act 5),
        # mirroring the pattern of all other act aliases (actN = first zone of act N+1).
        # Rule 6: current==target AND matched key is 'act4' (act alias) -> fires.
        test_split_logic("1_5_1", "1_4_7", "act4"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 4 guard: entering Overseer's Tower (1_5_town) fires Rule 5, NOT Rule 6, for act4",
        # target=1_5_1 (Slave Pens). Entering 1_5_town with act4 as split:
        # Rule 5: current endswith _town, target parts[2]='1', same act -> fires FIRST ZONE EXIT!
        test_split_logic("1_5_town", "1_4_7", "act4"),
        True, "FIRST ZONE EXIT"
    )
    assert_test(
        "Old act4 target 1_4_7 (Ascent): must NO LONGER fire 'act4' (Ascent is not first of Act 5)",
        # With old alias: entering Ascent would fire rule 6. With fix: act4->1_5_1, compare(1_4_7,1_5_1):
        # act 4 < act 5 -> -1 -> Rule 2 fails. Rule 6: current(1_4_7)!=target(1_5_1) -> fails. -> False
        test_split_logic("1_4_7", "1_4_6_3", "act4"),
        False
    )
    assert_test(
        "Act 5 Completion: entering 2_6_1 (Twilight Strand P2) via 'act5' alias — Rule 6",
        # With the override: act5 -> ["2_6_1"]. current==target, matched_key='act5' -> Rule 6 fires.
        # Without the override: act5 -> ["1_1_1"] -> compare(2_6_1, 1_1_1) > 0 -> Rule 2, but fires EARLY.
        test_split_logic("2_6_1", "1_5_8", "act5"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 5 guard: entering Cathedral Rooftop (1_5_8) must NOT trigger act5 (premature)",
        # With fix: target=2_6_1. compare(1_5_8, 2_6_1): act 5 < 6 -> -1 -> Rule 2 fails. No fire.
        # Without fix: target=1_1_1 -> compare(1_5_8, 1_1_1): act 5 > 1 -> +1 -> FALSE SPLIT.
        test_split_logic("1_5_8", "1_5_7", "act5"),
        False
    )
    assert_test(
        "Act 5 guard: entering Overseer's Tower (1_5_town) must NOT trigger act5 (premature)",
        # target=2_6_1. compare(1_5_town, 2_6_1): act 5 < 6 -> -1. No fire.
        test_split_logic("1_5_town", "1_5_8", "act5"),
        False
    )
    assert_test(
        "Act 6 -> Act 7: Brine King's Reef (2_6_15) -> Bridge Encampment (2_7_town) via 'act6'",
        # act6 -> 2_7_town (unique zone name, no shared list issue).
        # Rule 4: target endswith _town AND current == target -> fires!
        test_split_logic("2_7_town", "2_6_15", "act6"),
        True, "TOWN ENTRY"
    )
    assert_test(
        "Act 6 -> Act 7: entering Bridge Encampment does NOT fire 'act7' (wrong split)",
        # act7 -> 2_8_1 (Sarn Ramparts). Entering 2_7_town with act7 as split:
        # compare(2_7_town, 2_8_1): act 7 == act 8? No, '7' < '8' -> -1 -> Rule 2 fails.
        # Rule 4: target(2_8_1) doesn't endswith _town -> fails. No fire.
        test_split_logic("2_7_town", "2_6_15", "act7"),
        False
    )
    assert_test(
        "Act 7 Completion: entering 2_8_1 (Sarn Ramparts) via 'act7' alias — Rule 6",
        # act7 -> 2_8_1 (thesarnramparts, unique zone name). current==target -> Rule 6 fires.
        test_split_logic("2_8_1", "2_7_12_2", "act7"),
        True, "ACT COMPLETION"
    )
    assert_test(
        "Act 7 guard: entering Bridge Encampment (2_7_town) must NOT trigger act7 early",
        # target=2_8_1. compare(2_7_town, 2_8_1): act 7 < 8 -> -1. No fire.
        test_split_logic("2_7_town", "2_7_12_2", "act7"),
        False
    )
    assert_test(
        "Act 8 Completion: entering 2_9_1 (Blood Aqueduct) via 'act8' alias — Rule 6",
        # act8 -> 2_9_1 (thebloodaqueduct). current==target -> Rule 6 fires.
        test_split_logic("2_9_1", "2_8_13", "act8"),
        True, "ACT COMPLETION"
    )


    # ──────────────────────────────────────────────────────────
    section("RULE 6 — Act Completion (Missed Zone Fallbacks)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Act 1 missed: went to 1_2_town instead of 1_2_1 -> still splits (Rule 5)",
        test_split_logic("1_2_town", "1_2_1", "act1"),
        True   # Rule 5 fires: target=1_2_1 has parts[2]='1', entering 1_2_town
    )
    assert_test(
        "Act 6 Completion: entering 2_7_town directly (Rule 4)",
        test_split_logic("2_7_town", "2_6_15", "act6"),
        True, "TOWN ENTRY"
    )
    assert_test(
        "Act 6 missed town: went to 2_7_1 (Broken Bridge) -> Rule 2 fires",
        test_split_logic("2_7_1", "2_7_town", "act6"),
        True, "FORWARD MATH"
    )

    # ──────────────────────────────────────────────────────────
    section("Alias Resolution Tests (Human-readable names)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Alias 'brutus' resolves to Upper Prison (1_1_7_2)",
        test_split_logic("1_2_1", "1_1_7_2", "Brutus"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Alias 'merveil' resolves to Cavern of Anger (1_1_11_2)",
        test_split_logic("1_2_1", "1_1_11_2", "Merveil"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Alias 'dominus' resolves to Upper Sceptre (1_3_18_2)",
        test_split_logic("1_4_1", "1_3_18_2", "Dominus"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Alias 'weaver' resolves to Weaver Chambers (1_2_10, dead-end)",
        test_split_logic("1_2_town", "1_2_10", "weaver"),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Unresolvable alias returns False with UNRESOLVED reason",
        test_split_logic("1_1_3", "1_1_2", "xyzNothing"),
        False, "UNRESOLVED"
    )

    # ──────────────────────────────────────────────────────────
    section("Edge Cases & Specific Bugs")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Side area (1_1_2a Tidal Island) does NOT block math for base (1_1_2 Coast)",
        test_split_logic("1_1_2", "1_1_1", "1_1_2a"),
        False   # 2a == 2 numerically, not > 2, so Rule 2 fails. Dead-end Rule 3 also fails (previous!=target).
    )
    assert_test(
        "Side area equivalency: Tidal Island (1_1_2a) + Mud Flats (1_1_3) lookahead",
        test_split_logic("1_1_2", "1_1_1", "1_1_2a", future_splits=["1_1_3"]),
        False   # 1_1_3 != current (1_1_2), so lookahead doesn't fire either
    )
    assert_test(
        "Maligaro alias now maps to Chamber L1 (2_7_5_1) — 'maligarossanctum' resolves via Chamber L1 alias",
        # maligarossanctum (normalized) searches aliases. 'maligaro' is 7 chars -> alias scan hits it.
        # 'maligaro' is now an alias for thechamberofsinslevel1 / 2_7_5_1 (since 2_7_5_map was removed).
        # Rule 2: entering Den (2_7_6) > Chamber L1 (2_7_5_1) -> fires.
        test_split_logic("2_7_6", "2_7_4", "maligarossanctum"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Maligaro alias: 'maligaro' split fires on entering Chamber L2 (2_7_5_2 > 2_7_5_1)",
        # maligaro -> 2_7_5_1. Entering Chamber L2: compare(2_7_5_2, 2_7_5_1) = sub 2 > 1 -> Rule 2.
        test_split_logic("2_7_5_2", "2_7_4", "maligaro"),
        True, "FORWARD MATH"
    )

    assert_test(
        "sceptreofgod alias: maps to LOWER Sceptre (1_3_18_1), not Dominus",
        # Entering 1_3_18_1 with target 'sceptreofgod' split should fire Rule 2
        # because we just moved past it (previous = 1_3_18_1, current = 1_3_18_2)
        test_split_logic("1_3_18_2", "1_3_18_1", "sceptreofgod"),
        True, "FORWARD MATH"   # 1_3_18_2 > 1_3_18_1
    )
    assert_test(
        "Lunaris Temple L1 Act 8: ID is 2_8_7_1 (fixed, no trailing underscore)",
        # Entering 2_8_7_2 from 2_8_7_1 should trigger split for 'lunaris1' alias
        test_split_logic("2_8_7_2", "2_8_7_1", "lunaris1"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Reset zone (1_1_1): split block should NOT trigger (no previous)",
        test_split_logic("1_1_1", "", "1_1_1"),
        False   # previous is empty, target = 1_1_1, current = 1_1_1 -> Rule 2: compare=0, no match
    )
    assert_test(
        "Cross-act act alias: 'act1' in split name '- Act 1 Boss -' resolves",
        test_split_logic("1_2_1", "1_1_11_2", "- Act 1 Boss -"),
        True, "ACT COMPLETION"
    )

    # ──────────────────────────────────────────────────────────
    section("Act Timeout Scaling (Rule 3)")
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Act 1 dead-end timeout: floor = 37.5s, 38s passes",
        test_split_logic("1_1_2", "1_1_3a", "fetidpool", time_spent=38.0),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Act 1 dead-end timeout: 37.4s does NOT pass",
        test_split_logic("1_1_2", "1_1_3a", "fetidpool", time_spent=37.4),
        False
    )
    assert_test(
        "Act 5 dead-end timeout: 40-(2.5*5)=27.5s, 28s passes",
        test_split_logic("1_5_2", "1_5_6", "ossuary", time_spent=28.0),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Act 10 dead-end timeout: floor=15s (40-25=15), 16s passes",
        test_split_logic("2_10_3", "2_10_4", "desecratedchambers", time_spent=16.0),
        True, "DEAD-END EXIT"
    )
    assert_test(
        "Act 10 dead-end timeout: 15.0s exactly does NOT pass (strictly greater than)",
        test_split_logic("2_10_3", "2_10_4", "desecratedchambers", time_spent=15.0),
        False
    )

    # ──────────────────────────────────────────────────────────
    section("Act 2: Crossroads → Fell Shrine Ruins → Crypt — ID Ordering Limitation")
    # Fell Shrine Ruins is zone 1_2_15 in Act 2, but sits geographically BETWEEN
    # Crossroads (1_2_3) and Crypt (1_2_5). Because it has the highest map number
    # in Act 2, the exit-based math engine CANNOT fire it from within Act 2.
    # ──────────────────────────────────────────────────────────

    # ──────────────────────────────────────────────────────────
    section("RULE 7 — Passthrough Exit (Geographic ID Mismatch)")
    # Fell Shrine Ruins (1_2_15) is the only [PASSTHROUGH] zone.
    # The SPLIT for 'Fell Shrine' fires when you EXIT it (previousZoneId == 1_2_15),
    # NOT when you arrive. beforePreviousZoneId guards against A→B→A backtracking.
    #
    # Normal routing: Crossroads (1_2_3) → Fell Shrine (1_2_15) → Crypt L1 (1_2_5_1)
    #   • 'Crossroads' split fires on entering Fell Shrine (Rule 2: 15 > 3) — UNCHANGED
    #   • 'Fell Shrine' split fires on entering Crypt L1 (Rule 7: prev=1_2_15)
    # ──────────────────────────────────────────────────────────

    # --- 'Crossroads' split (unchanged — Rule 2 handles it)
    assert_test(
        "[PASSTHROUGH] 'Crossroads' split: entering Fell Shrine (15>3) fires Rule 2 — unchanged",
        # This already worked. Confirming it still does.
        test_split_logic("1_2_15", "1_2_3", "crossroads"),
        True, "FORWARD MATH"
    )

    # --- 'Fell Shrine' split (the fixed one — Rule 7)
    assert_test(
        "[PASSTHROUGH] 'Fell Shrine' split: fires when exiting to Crypt L1 (Rule 7)",
        # current=1_2_5_1, prev=1_2_15, beforePrev=1_2_3
        # Rule 2: compare(1_2_5_1, 1_2_15) = -1 → fails.
        # Rule 7: passhtrough? yes. prev==target? yes. backtrack? current(5_1) != beforePrev(3) → no → FIRES!
        test_split_logic("1_2_5_1", "1_2_15", "fellshrineruins",
                         before_previous_id="1_2_3"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[PASSTHROUGH] 'Fell Shrine' split: does NOT fire while still in Fell Shrine (compare=0)",
        # current=1_2_15, prev=1_2_3. Rule 2 fails (=0). Rule 7: prev(1_2_3) != target(1_2_15) → fails.
        test_split_logic("1_2_15", "1_2_3", "fellshrineruins"),
        False
    )
    assert_test(
        "[PASSTHROUGH] Anti-backtrack: Crypt→Fell Shrine→Crossroads does NOT fire (backtrack detected)",
        # Player exits Crypt back to Fell Shrine, then exits Fell Shrine back to Crossroads.
        # State on arriving at Crossroads: current=1_2_3, prev=1_2_15, beforePrev=1_2_3
        # Rule 7: passthrough? yes. prev==target(1_2_15)? yes. backtrack? current(1_2_3)==beforePrev(1_2_3) YES → BLOCKED!
        test_split_logic("1_2_3", "1_2_15", "fellshrineruins",
                         before_previous_id="1_2_3"),
        False  # Backtrack correctly blocked
    )
    assert_test(
        "[PASSTHROUGH] beforePreviousZoneId='' (start of run) does not false-block a legit exit",
        # If before_previous is empty (start of run or not yet set), current cannot equal ''
        # so backtrack check fails correctly — exit fires normally.
        test_split_logic("1_2_5_1", "1_2_15", "fellshrineruins",
                         before_previous_id=""),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[PASSTHROUGH] Normal zone Rule 7 guard: Crossroads not in passthrough_ids (no spurious exit-fire)",
        # A non-passthrough zone (Crossroads=1_2_3) does not fire Rule 7 even when prev==target.
        # Use compare=0 scenario so Rule 2 also fails: current=1_2_3, prev=1_2_3, target=1_2_3
        test_split_logic("1_2_3", "1_2_3", "thecrossroads"),
        False  # compare=0 -> Rule 2 fails. Not in passthrough_ids -> Rule 7 skipped.
    )
    assert_test(
        "[PASSTHROUGH] Guard B: Vaal Ruins(11)→Wetlands(12) is higher-ID exit — rejected",
        # Route: anything → Wetlands → VaalRuins → Wetlands. Split target = VaalRuins(11).
        # prev(1_2_11)==target(1_2_11) ✔. Guard A on Rule 2: PassthroughIDs(11) ✔ AND
        # current(1_2_12)==beforePrev(1_2_12) ✔ → Rule 2 blocked. Guard A Rule 7 also blocks.
        test_split_logic("1_2_12", "1_2_11", "1_2_11",
                         before_previous_id="1_2_12"),
        False  # correctly blocked by Rule 2 passthrough guard
    )
    assert_test(
        "[PASSTHROUGH] Guard B: Wetlands(12)→Vaal Ruins(11) is lower-ID exit — accepted",
        # Route: Riverways(7) → Wetlands(12) → Vaal Ruins(11). Split target = Wetlands(12).
        # prev(1_2_12)==target(1_2_12) ✔. backtrack(A): current(11)==beforePrev(7)? NO.
        # backtrack(B): compare(1_2_11, 1_2_12)=-1 < 0 → lower-ID exit → ACCEPT.
        test_split_logic("1_2_11", "1_2_12", "thewetlands",
                         before_previous_id="1_2_7"),
        True, "PASSTHROUGH EXIT"
    )

    # ──────────────────────────────────────────────────────────
    section("Act 2: Crossroads → Fell Shrine → Crypt — Full Journey Test")
    # End-to-end simulation of the correct behavior after the fix.
    # ──────────────────────────────────────────────────────────

    assert_test(
        "Journey step 1: In Crossroads, entering Fell Shrine — 'Crossroads' split fires (Rule 2)",
        # prev=1_2_2, current=1_2_15, target='crossroads'(1_2_3): 15>3 → FIRES
        test_split_logic("1_2_15", "1_2_2", "crossroads"),
        True, "FORWARD MATH"
    )
    assert_test(
        "Journey step 2: In Fell Shrine, next target='Fell Shrine' — does NOT fire yet (still in zone)",
        # prev=1_2_3, current=1_2_15, target='fellshrineruins'(1_2_15): compare=0, prev!=1_2_15 → No fire
        test_split_logic("1_2_15", "1_2_3", "fellshrineruins"),
        False
    )
    assert_test(
        "Journey step 3: Exiting Fell Shrine to Crypt L1 — 'Fell Shrine' split fires (Rule 7)",
        # prev=1_2_15, current=1_2_5_1, beforePrev=1_2_3, target='fellshrineruins'(1_2_15)
        test_split_logic("1_2_5_1", "1_2_15", "fellshrineruins",
                         before_previous_id="1_2_3"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "Journey step 4: Now in Crypt L1, 'Crypt L2' fires when entering Crypt L2 (Rule 3)",
        test_split_logic("1_2_town", "1_2_5_2", "thecryptlevel2"),
        True, "DEAD-END EXIT"
    )


    # ────────────────────────────────────────────────────────────
    section("Act 5: Chamber of Innocence (1_5_5) — PASSTHROUGH EXIT")
    # CoI is the geographic endpoint for Innocence. After killing the boss, the ONLY exit
    # is Torched Courts (1_5_4b), which has a LOWER map ID. Rule 7 handles the split on exit.
    # ────────────────────────────────────────────────────────────

    assert_test(
        "[CoI] Normal exit: CoI → Torched Courts — Rule 7 fires",
        # prev=1_5_5(CoI), current=1_5_4b(TC), beforePrev=1_5_4(Templar Courts)
        # Rule 2: blocked (CoI is passthrough target). Rule 7: prev==CoI ✓, !backtrack ✓, 4b<5 ✓ → FIRES
        test_split_logic("1_5_4b", "1_5_5", "chamberofinnocence",
                         before_previous_id="1_5_4"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[CoI] Direct backtrack: CoI → Templar Courts — blocked (A→B→A)",
        # current=1_5_4(Templar Courts)==beforePrev(1_5_4) → isDirectBacktrack=True → blocked
        test_split_logic("1_5_4", "1_5_5", "chamberofinnocence",
                         before_previous_id="1_5_4"),
        False
    )
    assert_test(
        "[CoI] Higher-ID exit guard: CoI → Rooftop (1_5_8 > 1_5_5) — rejected by Rule 7 guard B",
        # 1_5_8 > 1_5_5 → isHigherIdExit=True → Rule 7 blocked. (Hypothetical — not geographically possible.)
        test_split_logic("1_5_8", "1_5_5", "chamberofinnocence",
                         before_previous_id="1_5_4"),
        False
    )
    assert_test(
        "[CoI] Rule 2 guard: entering CoI (1_5_5) while targeting Torched Courts (1_5_4b) — must NOT prematurely split TC",
        # Without fix: compare(1_5_5, 1_5_4b)=+1 → Rule 2 fires (false split on entering boss room).
        # With fix: 1_5_4b in passthrough_ids → Rule 2 blocked entirely. ✓
        test_split_logic("1_5_5", "1_5_4", "torchedcourts",
                         before_previous_id="1_5_3"),
        False
    )


    # ────────────────────────────────────────────────────────────
    section("Act 5: Torched Courts (1_5_4b) — PASSTHROUGH EXIT")
    # TC is reached after CoI. Its only forward exit is Ruined Square (1_5_3b, lower id).
    # The hub classification of the destination (RS) is invisible to Rule 7.
    # ────────────────────────────────────────────────────────────

    assert_test(
        "[TC] Normal exit: TC → Ruined Square (hub destination) — Rule 7 fires",
        # prev=1_5_4b(TC), current=1_5_3b(RS=hub), beforePrev=1_5_5(CoI)
        # Rule 7: passthrough ✓, prev==target ✓, !backtrack(3b≠5 ✓), compare(3b,4b)=-1 not higher ✓ → FIRES
        test_split_logic("1_5_3b", "1_5_4b", "torchedcourts",
                         before_previous_id="1_5_5"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[TC] Higher-ID exit guard: TC → CoI (1_5_5 > 1_5_4b) — rejected by Rule 7 guard B",
        # Going back to CoI is a higher-ID exit → isHigherIdExit=True → Rule 7 blocked
        test_split_logic("1_5_5", "1_5_4b", "torchedcourts",
                         before_previous_id="1_5_3b"),
        False
    )
    assert_test(
        "[TC] Direct backtrack guard: TC→RS→TC (beforePrev match) — blocked",
        # current(1_5_3b)==beforePrev(1_5_3b) → isDirectBacktrack=True → Rule 7 blocked
        test_split_logic("1_5_3b", "1_5_4b", "torchedcourts",
                         before_previous_id="1_5_3b"),
        False
    )


    # ────────────────────────────────────────────────────────────
    section("Act 5: Ruined Square (1_5_3b) — HUB ENTRY & All Entry/Exit Paths")
    # Hub zone: 3 entries (Torched Courts, Ossuary, Reliquary), 1 exit (Cathedral Rooftop).
    # Splits ONLY on exact arrival. Portal/waypoint re-entry handled correctly.
    # ────────────────────────────────────────────────────────────

    # --- Entry paths that SHOULD fire the RS split ---
    assert_test(
        "[RS] Entry from Torched Courts (first normal entry) — Hub Rule 4 fires",
        test_split_logic("1_5_3b", "1_5_4b", "ruinedsquare",
                         before_previous_id="1_5_5"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS] Entry from Ossuary (returning after side content) — Hub Rule 4 fires",
        test_split_logic("1_5_3b", "1_5_6", "ruinedsquare",
                         before_previous_id="1_5_3b"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS] Entry from Reliquary (returning after side content) — Hub Rule 4 fires",
        test_split_logic("1_5_3b", "1_5_7", "ruinedsquare",
                         before_previous_id="1_5_3b"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS] Portal from town (waypoint return) — Hub entry from town is BLOCKED (anti-waypoint guard)",
        # previous=1_5_town (waypointed from town), current=1_5_3b → hub target, but fromTown=True → blocked.
        # This was the bug fixed in this session: town→hub was incorrectly triggering the split.
        test_split_logic("1_5_3b", "1_5_town", "ruinedsquare",
                         before_previous_id="1_5_7"),
        False  # Fixed: waypoint return to hub must NOT split
    )

    # --- Exits FROM RS that should fire ANOTHER split (RS already completed) ---
    assert_test(
        "[RS] Entering Ossuary while RS is split — Rule 2 fires (6>3b=forward)",
        # RS split is current. From RS you go to Ossuary: compare(1_5_6, 1_5_3b)=+1 → Rule 2 fires.
        # The RS split completes the moment you exit to side content.
        test_split_logic("1_5_6", "1_5_3b", "ruinedsquare",
                         before_previous_id="1_5_4b"),
        True, "FORWARD MATH"
    )
    assert_test(
        "[RS] Entering Cathedral Rooftop while RS is split — Rule 2 fires (8>3b=forward)",
        test_split_logic("1_5_8", "1_5_3b", "ruinedsquare",
                         before_previous_id="1_5_6"),
        True, "FORWARD MATH"
    )
    assert_test(
        "[RS] Cathedral Rooftop split fires when entering Rooftop from RS (Rooftop is next split)",
        # Current split = Rooftop (1_5_8). In RS, going to Rooftop: compare(1_5_8,1_5_8)=0.
        # But previous was RS. Rooftop is NOT a hub. Rule 2: compare(1_5_8,1_5_8)=0 → no fire.
        # Rooftop split fires when entering Act 6 (cross-act forward math).
        test_split_logic("1_5_8", "1_5_3b", "cathedralrooftop",
                         before_previous_id="1_5_3b"),
        False  # compare(1_5_8,1_5_8)=0. Will fire when entering Act 6.
    )

    # --- Guard tests: RS must NOT cause false splits when it is NOT the current split ---
    assert_test(
        "[RS] Entering RS while OSSUARY is current split — NO false split (3b < 6 = backward)",
        # Exiting TC into RS while current split=Ossuary. compare(1_5_3b, 1_5_6)=-1 → Rule 2 fails.
        # Hub Rule 4: target(1_5_6) not in hub_ids → no fire.
        test_split_logic("1_5_3b", "1_5_4b", "ossuary",
                         before_previous_id="1_5_5"),
        False
    )
    assert_test(
        "[RS] Lookahead: entering RS while Ossuary is current split, RS at +2 — REJECTED (RS < Ossuary)",
        # compare(1_5_3b, 1_5_6) < 0 → lookahead backward guard rejects the match.
        test_split_logic("1_5_3b", "1_5_4b", "ossuary",
                         future_splits=["reliquary", "ruinedsquare"],
                         before_previous_id="1_5_5"),
        False
    )
    assert_test(
        "[RS] Entering RS while ROOFTOP is current split — NO false split (hub mismatch + no math)",
        # compare(1_5_3b, 1_5_8)=-1 → Rule 2 fails. Hub Rule 4: target(1_5_8) not in hub_ids → no fire.
        test_split_logic("1_5_3b", "1_5_4b", "cathedralrooftop",
                         before_previous_id="1_5_5"),
        False
    )
    assert_test(
        "[RS] Entering RS while RELIQUARY is current split — NO false split (3b < 7 = backward)",
        test_split_logic("1_5_3b", "1_5_7", "reliquary",
                         before_previous_id="1_5_3b"),
        False
    )

    # --- Full Act 5 journey ---
    assert_test(
        "[Act5 Journey] CoI split fires on exit to Torched Courts (Rule 7)",
        test_split_logic("1_5_4b", "1_5_5", "chamberofinnocence",
                         before_previous_id="1_5_4"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[Act5 Journey] Torched Courts split fires on exit to Ruined Square (Rule 7)",
        test_split_logic("1_5_3b", "1_5_4b", "torchedcourts",
                         before_previous_id="1_5_5"),
        True, "PASSTHROUGH EXIT"
    )
    assert_test(
        "[Act5 Journey] Ruined Square split fires on arrival from Torched Courts (Hub Rule 4)",
        test_split_logic("1_5_3b", "1_5_4b", "ruinedsquare",
                         before_previous_id="1_5_5"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[Act5 Journey] Ruined Square split fires via portal re-entry after Reliquary — BLOCKED (from town)",
        # After fix: waypointing to town then TPing back to RS should NOT split (waypoint return guard).
        test_split_logic("1_5_3b", "1_5_town", "ruinedsquare",
                         before_previous_id="1_5_7"),
        False  # Fixed: town → hub is now blocked
    )
    assert_test(
        "[Act5 Journey] After RS split: Rooftop fires when entering Act 6 (cross-act Rule 2)",
        # Rooftop (1_5_8) is current split. You enter Act 6 Twilight Strand (2_6_1).
        # compare(2_6_1, 1_5_8): act 6 > act 5 → +1 → Rule 2 fires.
        test_split_logic("2_6_1", "1_5_8", "cathedralrooftop",
                         before_previous_id="1_5_3b"),
        True, "FORWARD MATH"
    )


    # ────────────────────────────────────────────────────────────
    section("SESSION FIXES — Kitava Act 5 Detection (Log-Line Split)")
    # Bug: kitava flag was being set but the split block checked kitavaKey == 'act5'
    # which only matches splits literally named 'act5'. Splits named 'Cathedral Rooftop'
    # resolve to key 'cathedralrooftop', not 'act5', so the split never fired.
    # Fix (dual matching): fire if target_id == '1_5_8' OR key == 'act5'.
    # ────────────────────────────────────────────────────────────

    assert_test(
        "[Kitava5] Split named 'Cathedral Rooftop' fires via id match (1_5_8) — the exact bug from session",
        # This was the live bug: split is 'Act 5 - The Cathedral Rooftop', kitava log fired,
        # but split block checked key=='act5' → 'cathedralrooftop' != 'act5' → no split.
        # Fix: check target_id == '1_5_8' first.
        test_split_logic("1_5_8", "1_5_3b", "Act 5 - The Cathedral Rooftop",
                         kitava_act5_defeated=True),
        True, "KITAVA ACT 5"
    )
    assert_test(
        "[Kitava5] Split named 'kitava' fires via id match (1_5_8)",
        test_split_logic("1_5_8", "1_5_3b", "kitava",
                         kitava_act5_defeated=True),
        True, "KITAVA ACT 5"
    )
    assert_test(
        "[Kitava5] Split named 'act5' fires via key match — original behavior preserved",
        # 'act5' resolves to 2_6_1 (not 1_5_8), so id branch fails, key branch ('act5') succeeds.
        test_split_logic("2_6_1", "1_5_8", "act5",
                         kitava_act5_defeated=True),
        True, "KITAVA ACT 5"
    )
    assert_test(
        "[Kitava5] Split named 'Act 5 Complete' with 'act5' substring fires via key match",
        test_split_logic("2_6_1", "1_5_8", "Act 5 Complete",
                         kitava_act5_defeated=True),
        True, "KITAVA ACT 5"
    )
    assert_test(
        "[Kitava5] Split named 'rooftop' fires via id match (1_5_8 alias)",
        test_split_logic("1_5_8", "1_5_3b", "rooftop",
                         kitava_act5_defeated=True),
        True, "KITAVA ACT 5"
    )
    assert_test(
        "[Kitava5] Kitava flag NOT set → no KITAVA split, falls through to normal rules",
        # No kitava flag. current=1_5_8, prev=1_5_3b, target=cathedralrooftop (1_5_8).
        # compare(1_5_8, 1_5_8)=0 → Rule 2 fails. Not dead-end, not hub, not town, not passthrough. → False.
        test_split_logic("1_5_8", "1_5_3b", "cathedralrooftop",
                         kitava_act5_defeated=False),
        False
    )
    assert_test(
        "[Kitava5] Zone entry to Feeding Trough (2_10_6) with act5 flag set but wrong split — no spurious fire",
        # kitava_act5_defeated=True but split is 'feedingtrough' (resolves to 2_10_6, key='feedingtrough').
        # Dual check: id==1_5_8? No (2_10_6). key=='act5'? No ('feedingtrough'). → No fire.
        test_split_logic("2_10_6", "2_10_5", "feedingtrough",
                         kitava_act5_defeated=True),
        False  # act5 flag must not cross-fire for a feedingtrough split
    )

    # ────────────────────────────────────────────────────────────
    section("SESSION FIXES — Kitava Act 10 Detection (Log-Line Split)")
    # Act 10 Kitava (in Feeding Trough, 2_10_6). Zone entry must NOT split;
    # only the log-line (-60% resistance penalty) should trigger the split.
    # ────────────────────────────────────────────────────────────

    assert_test(
        "[Kitava10] Zone entry to Feeding Trough (2_10_6) must NOT split when flag is NOT set",
        # The old bug: AddZone('act10', '2_10_6') caused zone-entry to split 'act10'.
        # Now act10 is log-line only. Zone entry alone → flag not set → no split.
        test_split_logic("2_10_6", "2_10_5", "act10",
                         kitava_act10_defeated=False),
        False  # Must NOT fire on zone entry
    )
    assert_test(
        "[Kitava10] Log-line fires, split named 'act10' — fires via key match",
        # kitava_act10_defeated=True (log line seen). target 'act10' → 2_10_6, key='act10'.
        # Dual match: id(2_10_6)==2_10_6 ✓ AND key=='act10' ✓. Either is sufficient.
        test_split_logic("2_10_6", "2_10_5", "act10",
                         kitava_act10_defeated=True),
        True, "KITAVA ACT 10"
    )
    assert_test(
        "[Kitava10] Log-line fires, split named 'Feeding Trough' — fires via id match (2_10_6)",
        test_split_logic("2_10_6", "2_10_5", "feedingtrough",
                         kitava_act10_defeated=True),
        True, "KITAVA ACT 10"
    )
    assert_test(
        "[Kitava10] Log-line fires, split named 'Act 10 - The Feeding Trough' — fires via id match",
        test_split_logic("2_10_6", "2_10_5", "Act 10 - The Feeding Trough",
                         kitava_act10_defeated=True),
        True, "KITAVA ACT 10"
    )
    assert_test(
        "[Kitava10] Log-line fires, split named 'kitava2' (alias) — fires via id match (2_10_6)",
        test_split_logic("2_10_6", "2_10_5", "kitava2",
                         kitava_act10_defeated=True),
        True, "KITAVA ACT 10"
    )
    assert_test(
        "[Kitava10] Act5 flag does NOT fire for act10 zone (cross-flag isolation)",
        # kitava_act5_defeated=True but current zone is 2_10_6 (act10 zone) → id != 1_5_8,
        # split name 'feedingtrough' key != 'act5' → no act5 fire. act10 flag false → no act10 fire.
        test_split_logic("2_10_6", "2_10_5", "feedingtrough",
                         kitava_act5_defeated=True, kitava_act10_defeated=False),
        False
    )

    # ────────────────────────────────────────────────────────────
    section("SESSION FIXES — Ruined Square Hub Guards (Rule 4)")
    # Guard A: player came FROM a town (waypoint return) → blocked
    # Guard B: player came FROM a higher-ID zone (backward re-entry, e.g. Rooftop→RS post-Kitava) → blocked
    # ────────────────────────────────────────────────────────────

    assert_test(
        "[RS-Town] Town → Ruined Square (waypoint return) does NOT split — Guard A",
        # previous=1_5_town, current=1_5_3b (RS hub). With fix: from_town=True → blocked.
        test_split_logic("1_5_3b", "1_5_town", "ruinedsquare"),
        False  # Must NOT fire
    )
    assert_test(
        "[RS-BackEntry] Cathedral Rooftop → RS after Kitava kill does NOT split — Guard B (the log bug)",
        # Exact scenario from log line 1275: previous=1_5_8 (Rooftop), current=1_5_3b (RS).
        # compare(1_5_8, 1_5_3b) > 0 (8 > 3b) → isBackwardEntry=True → blocked.
        test_split_logic("1_5_3b", "1_5_8", "ruinedsquare"),
        False  # Must NOT fire (backward re-entry post-Kitava)
    )
    assert_test(
        "[RS-BackEntry] Act4 Crystal Veins (1_4_3_3) → RS is cross-act: compare returns -1, NOT blocked",
        # 1_4_3_3 is act 4 < act 5 (RS). compare(1_4_3_3, 1_5_3b) = -1 → not backward → hub fires normally.
        # This is the correct first-visit from Act4 progression.
        test_split_logic("1_5_3b", "1_4_3_3", "ruinedsquare"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS-Town] Ossuary → Town → Ruined Square via waypoint does NOT split",
        # Two-step: user was in Ossuary, went to town, then waypointed to RS.
        # From harness perspective: previous=1_5_town (the step that matters).
        test_split_logic("1_5_3b", "1_5_town", "Act 5 - The Ruined Square"),
        False
    )
    assert_test(
        "[RS-Town] Ossuary → Ruined Square (direct, no town) DOES split — unaffected by fix",
        # from_town=False (previous is Ossuary 1_5_6) → hub entry fires normally.
        test_split_logic("1_5_3b", "1_5_6", "ruinedsquare"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS-Town] Reliquary → Ruined Square (direct, no town) DOES split",
        test_split_logic("1_5_3b", "1_5_7", "ruinedsquare"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS-Town] Torched Courts → Ruined Square (direct, no town) DOES split",
        test_split_logic("1_5_3b", "1_5_4b", "ruinedsquare",
                         before_previous_id="1_5_5"),
        True, "HUB ENTRY"
    )
    assert_test(
        "[RS-Town] Town ENTRY split itself is unaffected (town→town guard only applies to hubs)",
        # Entering Act 2 Forest Encampment while split = 'forestencampment'. From any non-town prev.
        # townEntry: target endswith _town, current==target, from_town check does NOT apply to towns.
        test_split_logic("1_2_town", "1_2_12", "theforestencampment"),
        True, "TOWN ENTRY"
    )
    assert_test(
        "[RS-Town] Town→Town (different act towns): Rule 2 still handles act progression",
        # Act1 town → Act2 first zone → into 1_2_town (Forest Encampment entry) while
        # split='forestencampment': compare(1_2_town, 1_2_town)=0, Rule 4: target=1_2_town,
        # from_town=True — but from_town guard only affects hub_ids, NOT town targets. Fires.
        test_split_logic("1_2_town", "1_1_town", "theforestencampment"),
        True, "TOWN ENTRY"
    )

    print(f"\n{'='*60}")
    print(f"  Results: {_passed}/{_total} Passed  |  {_failed} Failed")
    print(f"{'='*60}")



if __name__ == "__main__":
    run_tests()

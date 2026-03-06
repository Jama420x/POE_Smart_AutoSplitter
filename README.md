# POE Smart Splitter

Automatically splits your Path of Exile campaign runs in LiveSplit. It reads the game's log file and fires each split at the right moment — zone entries, boss kills, act completions — so you don't have to press anything.

---

## Setup (2 steps)

### Step 1 — Add the script to LiveSplit

1. Open LiveSplit
2. Right-click the timer → **Edit Layout**
3. Click **+** → **Control** → **Scriptable Auto Splitter**
4. Click **Browse** and select `_POESmartSpliter.asl`
5. Click **OK**

### Step 2 — Tell it where your game log is

Open `_POESmartSpliter.asl` in any text editor (Notepad works fine). Near the very top you'll see:

```
vars.poeLogPath = @""; // <-- edit this if you don't use poe_config.txt
// Example: vars.poeLogPath = @"V:\SteamLibrary\steamapps\common\Path of Exile\logs\LatestClient.txt";
```

Copy the example line, remove the `//` at the start, and replace the path with yours. Your `LatestClient.txt` is usually at:

```
C:\Program Files (x86)\Steam\steamapps\common\Path of Exile\logs\LatestClient.txt
```

If you installed Steam or the game to a different drive, it'll be the same path but starting with that drive letter instead of `C:`.

Save the file, then reload it in LiveSplit (right-click the timer → **Control** → reload the script).

**That's it.** The splitter is now running.

---

## Naming your splits

Your splits just need to contain a recognised word — capitalisation and punctuation don't matter. You don't need to name them exactly.

```
"Act 1 - Brutus Kill"    ✅   (keyword: brutus)
"Merveil"                ✅   (keyword: merveil)
"Lower Prison"           ✅   (keyword: lowerprison)
"Act 3 Done"             ✅   (keyword: act3)
```

### Act completion keywords

Use these anywhere in a split name to fire at that act boundary:

| Keyword | When it fires |
|---------|--------------|
| `act1` | Entering Act 2 (Southern Forest) |
| `act2` | Entering Act 3 (City of Sarn) |
| `act3` | Entering Act 4 (Aqueduct) |
| `act4` | Entering Act 5 (Slave Pens) |
| `act5` | Kitava Act 5 kill |
| `act6` | Entering Act 7 (Bridge Encampment) |
| `act7` | Entering Act 8 (Sarn Ramparts) |
| `act8` | Entering Act 9 (Blood Aqueduct) |
| `act9` | Entering Act 10 (Oriath Docks) |
| `act10` | Kitava Act 10 kill |

`act5` and `act10` fire the moment Kitava dies (detected via the resistance penalty in the log), not on zone entry.

---

## Splits files

Ready-made split files are in the `splits/` folder:

| File | What it covers |
|------|---------------|
| `splits/campaignAllAreas.lss` | Every zone in the campaign |
| `splits/Act5Speedrun.lss` | Act 5 speedrun |
| `splits/POE_Campaign_Acts_Only.lss` | Act completions only (10 splits) |

Load one in LiveSplit via **File → Open Splits**.

---

## Reset

The timer resets automatically when you arrive at the Twilight Strand (start of a new run).

---

## Troubleshooting

**Splits aren't firing at all**
Check that the path in `vars.poeLogPath` is correct. Open `Assets\asl_debug_log.txt` — if you see `ERREUR : Fichier log introuvable`, the path is wrong.

**A split fired at the wrong time**
Check `Assets\asl_debug_log.txt` for what zone and rule triggered it. Also make sure your split name isn't accidentally matching an unintended keyword.

**The timer won't reset**
Make sure your first split file zone is the Twilight Strand, and that the script is loaded and running (green dot in LiveSplit's layout editor).

---

## How it works (for the curious)

The script reads `LatestClient.txt` live as you play. Every time you zone, it compares the new zone ID against your current split target using a 7-rule engine:

1. **Lookahead** — if you somehow skip a split, it catches up automatically (up to 3 splits ahead)
2. **Forward math** — zone IDs are compared numerically; if you've progressed past the target, it fires
3. **Dead-end exit** — for cul-de-sac zones, fires when you leave (to town instantly, or after a timeout)
4. **Town entry** — for splits targeting a town zone explicitly
5. **First zone exit** — handles the Twilight Strand → Lioneye's Watch edge case
6. **Act completion** — handles `act1`–`act9` aliases where you arrive at exactly the target zone
7. **Passthrough exit** — for zones whose ID doesn't match their geographic position in the campaign

For full technical details, see the comments inside `_POESmartSpliter.asl`.

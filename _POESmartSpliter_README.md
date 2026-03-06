# POE Smart Splitter

Path of Exile campaign runs don't need 10 manual splits. This ASL script for [LiveSplit](https://livesplit.org/) handles them for you — it reads the game's own log file, tracks every zone transition across all 10 Acts, and fires your splits based on a mathematical engine that understands the game's zone ID system. You just name your splits in a way that makes sense to you, and the script figures out when to fire them.

It covers the full campaign (Parts 1 and 2, Acts 1–10), handles dead-end side zones, geographically out-of-order areas, multi-zone lookahead for missed splits, and exact Kitava kill detection via the resistance-penalty log line.

---

## Setup

### 1. Add the script to LiveSplit

1. Open LiveSplit → **Edit Layout** → **+** → **Control** → **Scriptable Auto Splitter**
2. Point it at `_POESmartSpliter.asl`

### 2. Set your game log path

Instead of editing the ASL file directly, you configure your path in a private file that stays off GitHub:

1. Copy `poe_config.txt.example` → `poe_config.txt` (same folder)
2. Open `poe_config.txt` and set `POE_LOG_PATH=` to wherever your `LatestClient.txt` lives, e.g.:
   ```
   POE_LOG_PATH=V:\SteamLibrary\steamapps\common\Path of Exile\logs\LatestClient.txt
   ```
3. Reload the script in LiveSplit (or restart LiveSplit)

The `LatestClient.txt` file is typically at:

| Installation | Path |
|---|---|
| Steam default | `C:\Program Files (x86)\Steam\steamapps\common\Path of Exile\logs\LatestClient.txt` |
| Custom library | `<YourLibraryDrive>:\SteamLibrary\steamapps\common\Path of Exile\logs\LatestClient.txt` |

Once loaded correctly, `Assets\asl_debug_log.txt` will show `Config loaded: <your path>` and `Stream opened on: <your path>`.

### 3. Name your splits

That's it — no further config. Read the section below for how to name them.

---

## Naming Your Splits

Split names are **case-insensitive** and **punctuation-insensitive** — only letters and digits are matched. A split name just needs to *contain* a recognised keyword anywhere in it.

```
"Lower Prison"            ✅  resolved via alias: lowerprison
"Act 1 - Brutus Kill"     ✅  resolved via alias: brutus → Upper Prison
"Merveil"                 ✅  resolved via alias: merveil → Cavern of Anger
"Act 3 Done"              ✅  resolved via alias: act3 → Aqueduct entry
"1_2_5_1"                 ✅  raw zone ID used directly as fallback
```

### Act Completion Aliases

Use these in your split name to fire at the act boundary:

| Alias | Fires when entering… |
|---|---|
| `act1` | Southern Forest (`1_2_1`) — start of Act 2 |
| `act2` | City of Sarn (`1_3_1`) — start of Act 3 |
| `act3` | Aqueduct (`1_4_1`) — start of Act 4 |
| `act4` | Slave Pens (`1_5_1`) — start of Act 5 |
| `act5` | Twilight Strand P2 (`2_6_1`) — start of Act 6, or **Kitava Act 5 death** |
| `act6` | Bridge Encampment (`2_7_town`) — start of Act 7 |
| `act7` | Sarn Ramparts (`2_8_1`) — start of Act 8 |
| `act8` | Blood Aqueduct (`2_9_1`) — start of Act 9 |
| `act9` | Oriath Docks (`2_10_town`) — start of Act 10 |
| `act10` | **Kitava Act 10 death** (resistance penalty log line) |

`act5` and `act10` fire on Kitava's death (the `-30%`/`-60%` resistance penalty message), not on a zone entry. This matches the community standard for campaign timing.

---

## How the Engine Works

The script doesn't just check "are you in zone X?" — it evaluates a chain of 7 rules on every zone transition. The first rule that matches fires the split.

### Rule 1 — Lookahead Bypass
If the current split can't fire yet but a split **up to 3 ahead** matches the zone you just entered, the engine fires the current split and queues auto-skips for the ones in between. This prevents the timer from locking up if you typo a split name or accidentally skip one.

Towns can never be used for lookahead (anti-skip guard), and the bypassed splits must be mathematically *behind* the current zone.

### Rule 2 — Forward Math
The primary rule. Zone IDs like `1_3_8_2` are compared segment by segment: Part → Act → Map → Sub-level. If your current zone ID is mathematically greater than the split's target zone ID, the split fires. Towns are always treated as "less than" any real map in the same act, so entering any zone after town will fire a town-targeted split here.

### Rule 3 — Dead-End Exit
For zones flagged as dead-ends — cul-de-sacs with no forward exit, like The Docks or Weaver's Chambers. The split fires when you *leave* that zone, either instantly if you go to town, or after a time threshold (scales from 37.5s in Act 1 down to 15s in high acts) if you exit to a regular zone.

### Rule 4 — Town / Hub Entry
Towns are mathematically neutral (Rule 2 won't fire them), so this rule catches the case where the split explicitly targets a town zone like `Forest Encampment`. It fires the moment you physically enter that exact town ID.

Ruined Square (Act 5 post-Innocence hub) works the same way — exact-match arrival only — but with an anti-waypoint guard: returning to it from the town after a boss kill doesn't trigger a split.

### Rule 5 — First Zone Exit
Edge case for Twilight Strand → Lioneye's Watch, and the equivalent transition in each act. Entering the act's town from the first zone of that act fires the split immediately.

### Rule 6 — Act Completion Enter Zone
Handles `act1`–`act9` aliases: since you enter *exactly* the target zone, Rule 2 returns 0 (neither ahead nor behind) and never fires. This rule catches that equality and fires on arrival at the exact zone. `act10` is explicitly excluded — it fires via Kitava's log line only.

### Rule 7 — Passthrough Exit
For zones whose zone ID doesn't match their geographic position. The classic example: Fell Shrine Ruins has ID `1_2_15` (the highest in Act 2) but exits to Crypt Level 1 (`1_2_5_1`), which is mathematically backward. The split fires when you *depart* the flagged zone, with two backtrack guards: one for A→B→A direct returns, and one that checks whether the exit direction is actually lower-ID (as a legitimate passthrough exit should be).

---

## Zone Flags

Each zone has two optional flags set in `AddZone(name, id, aliases, isDeadEnd, isPassthrough)`:

| Flag | Parameter | Effect |
|---|---|---|
| `isDeadEnd` | 4th param = `true` | Uses Rule 3 (timeout or town exit) |
| `isPassthrough` | 5th param = `true` | Uses Rule 7 (exit fires, with backtrack guards) |

---

## Known Limitations

**Labyrinth zones** — Zone IDs like `1_Labyrinth_boss_2` have a non-numeric map segment. The current engine strips non-digit characters from that segment, causing it to collapse to `0` and only compare sub-levels. If you enter a Labyrinth mid-campaign run, up to 2 splits can false-fire. See `KI-001` in the dev file header for details.

**Maligaro's Sanctum (`2_7_5_map`)** — Commented out of the zone database. Its `_map` suffix produces a sub-level of 0, which is less than Chamber of Sins Level 1 (sub-level 1), causing Rule 2 to fire incorrectly on entry. The `maligaro` alias instead points to Chamber of Sins Level 1 (`2_7_5_1`), which fires correctly on entry to Level 2.

**Act 10 end** — There's no zone transition after The Feeding Trough; Kitava's intro starts immediately. `act10` fires exclusively on the `-60%` resistance penalty log line.

---

## Splits Files

Pre-built split files live in the `splits/` folder:

| File | Description |
|---|---|
| `splits/campaignAllAreas.lss` | Full campaign — every zone |
| `splits/Act5Speedrun.lss` | Act 5 speedrun layout |
| `splits/POE_Campaign_Acts_Only.lss` | Act completions only (10 splits) |

---

## Reset

The timer resets automatically when zone ID `1_1_1` (Twilight Strand, Act 1 start) is detected — i.e. when you start a fresh run.

---

## Debug Log

Every zone transition is logged to `Assets\asl_debug_log.txt` in real time:
- Which zone you came from and entered (with all tags and flags)
- What the current and next split targets resolve to
- Which rule fired (or why none did)

This file is gitignored. Check it when something isn't splitting as expected.

---

## Modifying the Script

Make changes in `_POESmartSpliter_dev.asl`. After modifying:

1. Run `python test_poe_asl_logic.py` — all tests must pass
2. Copy the dev file over the production file when satisfied

### Adding a zone
```csharp
AddZone("myzonename", "1_X_Y", new string[] { "alias1", "alias2" }, isDeadEnd, isPassthrough);
```

### Adding a passthrough zone (geographic order mismatch)
Set the 5th parameter to `true`. Rule 7 and its backtrack guards apply automatically — no other changes needed.

### Files

| File | Purpose |
|---|---|
| `_POESmartSpliter.asl` | **Production** — load this in LiveSplit |
| `_POESmartSpliter_dev.asl` | Development — make changes here |
| `test_poe_asl_logic.py` | Python test harness (86+ tests) — must pass before promoting to prod |
| `poe_config.txt` | Your personal log path (gitignored — create from `.example`) |
| `poe_config.txt.example` | Template for the above |
| `splits/` | Pre-built LiveSplit split files |

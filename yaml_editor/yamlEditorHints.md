# YAML Adventure Editor Hints & Guide

The **YAML Adventure Editor** (`yaml_editor/`) is a visual authoring workbench designed to create new text adventure games from scratch or edit existing ones without writing raw YAML syntax or touching engine code.

---

## 1. How the Editor Helps Authors

* **Visual Map & Spatial Layout**:
  * Displays multi-floor layouts (`Floor 0`, `Floor 1`, etc.) as interactive 2D grids.
  * Shows room positions, exit connections (`north`, `south`, `east`, `west`, `up`, `down`, `portal`), item drops, and attached events at a glance.
  * Clicking any room opens the modular prose and fixtures editor directly.

* **Modular Room Architecture**:
  * Splits room descriptions into three clean segments:
    1. **Base Description**: Permanent introductory anchor paragraph.
    2. **Fixtures**: Interactive objects/scenery ordered by priority (e.g. `power_switch`, `containment_pod`).
       - Each fixture has independent `state` (e.g. `default`, `energized`).
       - Look prose states (setting a state to empty string `""` hides the fixture from `look` until an event reveals it).
       - Targeted `examine` prose.
    3. **Trailing Description**: Permanent closing paragraph containing exit hints.
  * **Live Engine Look Preview**: Shows the exact assembled text the player will see when typing `look`.

* **Story & Game Setup**:
  * **Facility / Game Title**: Configures `intro.title`.
  * **Narrative Briefing**: Configures `intro.text` and `intro.instructions` with real-time HUD previews.
  * **Starting Spawn Room**: Sets initial player room at `floors[0][0][0]`.
  * **Starting Inventory**: Add or remove initial player equipment.
  * **Win Conditions**: Add or remove event completion requirements for victory.
  * **Epilogue Screen**: Sets `win_screen.title` and `win_screen.text`.

* **Dialog & Script Review**:
  * Review and tweak every piece of prose across intros, items, room fixtures, and event messages in one scannable list.
  * Real-time search filters prose across all game elements.

* **Sanity Validator**:
  * Runs automated consistency checks to catch issues before testing:
    - Verifies starting room exists in the floor grid and rooms list.
    - Flags empty room descriptions.
    - Verifies all win conditions point to valid event IDs.
    - Warns about orphan references.

* **Direct YAML Source Editor & Export**:
  * Bidirectional synchronization: edit visually or edit the raw YAML directly.
  * Real-time syntax error detection.
  * One-click **Export YAML** downloads a clean, engine-ready `.yaml` file.

---

## 2. Using the Editor

1. Open `yaml_editor/index.html` in any web browser.
2. Drag and drop any adventure YAML file (e.g. `data/test_the_room.yaml`, `data/game_data.yaml`) or choose a file from disk.
3. Switch between views using the top navigation bar:
   - **Map & Roadmap**: Visual map layout, room list, item roster, and event triggers.
   - **Story & Metadata**: Title, narrative intro, spawn point, starting inventory, and win conditions.
   - **Dialog & Script**: Modular room builder, fixture states, examine texts, and item descriptions.
   - **YAML Source**: Direct text editor with syntax checking and search.
   - **Sanity Validator**: Health diagnostics report.
4. When finished, click **Export YAML** in the top right corner to download your updated adventure file.

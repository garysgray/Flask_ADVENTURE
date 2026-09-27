# YAML Adventure Schema & Integration Contract

This document defines the contract between the **Adventure Editor** (producer) and the **Python Game Engine** (consumer).

---

## Architecture Overview

```
┌───────────────────────────────────────┐
│        Adventure Editor (UI)          │
│   (yaml_editor/js/schema.js, etc.)    │
└──────────────────┬────────────────────┘
                   │
                   │ Exports / Saves YAML
                   ▼
┌───────────────────────────────────────┐
│           Adventure YAML              │
│    (Contract Definition Medium)       │
└──────────────────┬────────────────────┘
                   │
                   │ Parses via yaml.safe_load()
                   ▼
┌───────────────────────────────────────┐
│      Python Game Engine (Core)        │
│  (game/gameObjects.py, controller.py) │
└───────────────────────────────────────┘
```

---

## Schema Specification

### 1. Intro (`intro`)
Metadata displayed when the game launches.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `title` | string | **Yes** | Adventure title shown in banners |
| `text` | string | **Yes** | Narrative introductory text |
| `instructions`| string | No | Player control instructions |

```yaml
intro:
  title: "The Abandoned Citadel"
  text: "You stand before crumbling limestone gates under a gray sky."
  instructions: "Type commands like 'look', 'take torch', 'go north'."
```

---

### 2. Player (`player`)
Initial player configuration.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `starting_location` | dict (`floor`, `x`, `y`) | **Yes** | Floor index (0-5) and 2D grid coordinates (x, y). Must point to a valid room. |
| `starting_inventory`| list of strings | No | List of `item_id`s given to the player upon spawning. |

```yaml
player:
  starting_location:
    floor: 0
    x: 2
    y: 2
  starting_inventory:
    - pocket_flashlight
```

---

### 3. Items (`items`)
Dictionary mapping unique `item_id`s to item definitions.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `display_name` | string | **Yes** | Human-readable title (e.g. "Pocket Flashlight") |
| `presence` | string | No | Room overview text when item is on the ground |
| `keywords` | list | **Yes** | Parsing triggers for verb targeting |
| `aliases` | list | No | Alternate nouns accepted by parser |
| `states` | dict | **Yes** | State map (at least `default` state) containing `description`, `examine`, and `use` strings |

```yaml
items:
  brass_key:
    display_name: "Brass Key"
    presence: "An ornate brass key"
    keywords:
      - key
      - brass key
    aliases:
      - key
    states:
      default:
        description: "A heavy notched brass key with clover-shaped bow."
        examine: "A heavy notched brass key."
        use: "Try using this on a locked gate or door."
```

---

### 4. Target Aliases (`target_aliases`)
Maps canonical fixture or scenery names to alternative nouns used by players.

```yaml
target_aliases:
  heavy_gate:
    - gate
    - iron gate
    - padlock
  power_switch:
    - switch
    - lever
```

---

### 5. Rooms (`rooms`)
Array of room objects placed within the game.

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `name` | string | **Yes** | Unique identifier (e.g. `entry_hall`) |
| `display_name` | string | **Yes** | Title shown to player upon entering |
| `base_description` | string | **Yes** | Core sensory text for the room |
| `fixtures` | dict | No | Stationary interactable objects |
| `items` | list | No | `item_id`s resting on the floor |
| `exits` | list or dict | **Yes** | Available directions: list `['north']` or dict `{'north': 'courtyard'}` |
| `locked_exits` | list | No | Exits blocked until unlocked by events |
| `trailing_description`| string | No | Closing architectural / directional cues |

---

### 6. Floors (`floors`)
3D array `[floor_index][y_row][x_col]` representing grid layouts.
- **Maximum floors:** 6 floors (indices 0 through 5). Exceeding 6 triggers a `ValueError`.
- Grid tiles contain the room's unique `name` string, or `null` for empty space.
- Player's `starting_location` must resolve to an active room tile, not `null`.

---

### 7. Events (`events`)
Event-Condition-Action (ECA) system.

#### Trigger Types
- **Dual / Two-Object Use (`use_with`, `dual`, `use_item`)**:
  - `source`: item used (e.g. `brass_key`)
  - `target`: object acted upon (e.g. `heavy_gate`)
  - `action`: verb (e.g. `use`)
- **Solo Action (`solo`, `solo_action`)**:
  - `target`: object acted upon (e.g. `power_switch`)
  - `action`: verb (e.g. `pull`, `press`, `examine`)
- **Passive (`on_turn`)**:
  - Automatically evaluated after each turn when conditions are satisfied.

#### Supported Conditions
- `in_room`: player must be in specific room
- `required_items`: player inventory must contain specified items
- `events_completed`: prerequisite event IDs must already be completed
- `rooms_visited`: list of rooms player must have explored

#### Supported Mutations (`result`)
- `set_fixture_state`: updates a room fixture's active state
- `open_exit`: unblocks a locked exit direction
- `add_item`: places a new item in room or inventory
- `remove_item`: consumes an item from inventory
- `message`: narrative feedback delivered to the player

---

### 8. Win Conditions (`win_conditions`) & Win Screen (`win_screen`)
- `win_conditions`: Array of event IDs required to complete the game.
  - *Safety Rule:* An empty `win_conditions: []` list evaluates to `False` (never auto-wins).
- `win_screen`: Contains `title` and `text` displayed when all win conditions are met.

---

## Running the Integration Tests

To run the automated contract verification suite:

```bash
# Run the full integration test suite
pytest

# Or with verbose output
pytest -v
```

All 13 tests verify contract fidelity, schema compliance, movement, item lifecycle, fixture mutations, and win condition logic.

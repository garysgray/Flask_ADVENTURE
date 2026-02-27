![Game Splash](static/images/flask_splash.png)
# Flask Adventure

A browser-based text adventure game built with Flask. Started as a simple experiment and evolved into a structured, session-driven adventure engine — built from the ground up, not copied from tutorials.

---

## Project Goals

- Learn Flask deeply through real building
- Create a modular, extensible text-adventure engine
- Manage game state cleanly on the server
- Build a foundation that can evolve into a reusable engine template

---

## What Has Been Built

### Core Engine Architecture

The game is split into focused modules:

| File | Purpose |
|------|---------|
| `controller.py` | Orchestrates all game systems |
| `parser.py` | Parses raw text commands into structured input |
| `actions.py` | Executes player actions (move, pick up, drop, use, look) |
| `event_manager.py` | Manages event checking and firing |
| `event_types.py` | Event class definitions — each event type knows how to check itself |
| `persistence.py` | Save and load game state to/from database |
| `gameObjects.py` | Map, Room, Item classes and YAML loading |
| `player.py` | Player state and movement logic |

### Game Objects

- `Item` — name, states (description + use text per state), current state, solo and action keywords
- `Room` — name, states (description per state), exits, inventory, exit destinations
- `Map` — floors, rooms, events, win conditions, intro text, loaded from `game_data.yaml`

Rooms and items support a state system — descriptions and use text change dynamically as the player progresses through the game.

### Command System

Commands are parsed from plain English input:

```
go south / south
get knife / pickup knife
drop knife
look knife
read map
wind music_box
light lantern with matches
open box with key
drop locket into well
use matches with lantern
read journal
help
```

The parser converts input into a structured command dict which the action handler executes. Supports:
- Direction synonyms and move words
- Multiple pickup words
- Solo keywords — single item actions e.g. `read map`, `wind music_box`
- Action keywords — two item interactions e.g. `light lantern with matches`
- Connectors — `with`, `into`, `onto`
- Inventory-aware resolution — parser checks player inventory to determine which word is the item and which is the target
- Event recipe resolution — parser checks event definitions to determine correct item/target order when both sides are in inventory
- Already-done detection — repeating a completed event returns a contextual response instead of a generic failure
- Fallback `use [item] with [target]` always works regardless of keywords

### Item Keywords

Items define two keyword types in `game_data.yaml`:

```yaml
lantern:
  solo_keywords:   [raise, hold]       # work alone e.g. "hold lantern"
  action_keywords: [light, hang]       # require a connector e.g. "light lantern with matches"
```

- `solo_keywords` trigger single item use with no target required
- `action_keywords` only trigger when used with a connector and a target
- Item name is always a valid fallback — `use lantern` always works
- Keywords are action words only — they describe what you do, not what the item is called

### Event System

Events are defined in `game_data.yaml` and fire based on game conditions:

- `all_rooms_visited` — triggers when required rooms have been visited
- `item_used_with` — triggers when a specific item is used on a specific target in a specific room
- `all_events_completed` — triggers when a set of required events have all been completed (used for win event)

Events can:
- Unlock exits between rooms
- Add items to rooms
- Remove items from player inventory
- Change room states
- Change item states
- Display messages to the player
- Write entries to the player journal

#### Event Architecture

All event logic lives in a proper class hierarchy:

**`event_types.py`** defines a base `Event` class and one class per event type:

```python
class Event                    # base class, all events inherit from this
class AllRoomsVisitedEvent     # fires when a set of rooms have all been visited
class AllEventsCompletedEvent  # fires when a set of events have all been completed
class ItemUsedWithEvent        # fires when item + target + room all match
```

Each event class holds its own parameters and knows how to check itself via a `check()` method. Adding a new event type means adding a new class — nothing else changes.

**`gameObjects.py`** builds event objects from YAML via `make_event()` when the map loads.

**`event_manager.py`** checks events by type and fires them via a shared `_fire_event()` method that handles all result types consistently.

#### Event Result Types

Events in `game_data.yaml` support the following result keys:

| Key | What it does |
|-----|-------------|
| `open_exit` | Unlocks a directional exit on a room |
| `add_item` | Spawns an item into a room |
| `remove_item` | Removes an item from the player's inventory |
| `set_state` | Changes a room to a new state |
| `set_item_state` | Changes an item to a new state |
| `message` | Displays a message to the player and writes to journal |

### Win Conditions

Win conditions are defined in `game_data.yaml` as a list of event IDs that must all be completed:

```yaml
win_conditions:
  - light_lantern
  - unlock_vault
  - all_rooms_floor0
  - locket_into_well
  - mirror_in_gallery
```

After every action the engine checks if all win conditions are in the player's completed events. A separate `game_won` event fires via `AllEventsCompletedEvent` which writes the win message to the journal. This separates required puzzle events from optional flavour events.

### Journal System

The player has a permanent journal that cannot be dropped or lost. It records all major events as they happen.

- Intro text is pinned as the first journal entry when a new player is created
- Events write to the journal automatically when they fire
- Journal shows latest entries at the top, intro always at the bottom
- `read journal` command opens a styled panel that slides in from the right
- When a player tries to repeat a completed event they get a contextual response instead of a generic failure
- This works even when the item has been removed from inventory (e.g. locket dropped into well)
- Win event writes to journal when all win conditions are met
- Journal persists between sessions

### Intro System

- Backstory and instructions are defined in `game_data.yaml` under `intro:`
- On a new player's first visit the intro panel fades in as a centered modal
- Player dismisses it by clicking "Enter the Manor"
- The intro is pinned permanently as the last journal entry
- Never auto-shows again after dismissal — tracked via `has_seen_intro` flag saved to database

### State System

Rooms and items are no longer static — they have states that change as the player interacts with the world.

**Room states** — each room has a `default` state and optional additional states:

```yaml
vault:
  states:
    default: "A locked iron box sits apart, humming..."
    changed: "The box hangs open. The humming has stopped."
```

**Item states** — each item has a `default` state and optional additional states with both description and use text:

```yaml
lantern:
  states:
    default:
      description: "A dusty oil lantern. It still has oil in it."
      use: "You hold the lantern up. Shadows retreat from its warm glow."
    changed:
      description: "A lit oil lantern. It burns with a steady warm flame."
      use: "The lantern is already lit. It burns steadily."
```

### Action / Response Separation

`use [item] with [target]` events return a tuple of `(cmd_response, event_message)`. This means event messages and regular command responses are cleanly separated before reaching the template:

- `CMD_RESPONSE` — direct feedback from the action ("You picked up the lantern")
- `EVENT_MESSAGES` — story/puzzle events triggered by the action ("The wall opens...")

### Save / Load System

Full game state is persisted to SQLite via Flask-SQLAlchemy:

- Player position and floor
- Player inventory and item states
- Room inventories and room states
- Visited rooms (tuples) and visited room names (strings) — stored separately
- Completed events
- Unlocked exits and exit destinations
- Journal entries
- `has_seen_intro` flag

Items and rooms are always rebuilt from YAML recipes on load, with saved state restored on top. This means recipe changes are always picked up cleanly.

Each player ID gets its own controller instance so multiple players can run simultaneously. Deleting a player also clears their controller from memory so new players with the same ID start completely fresh.

### Map System

The map is defined entirely in `game_data.yaml` — no hardcoded room data in Python. Items, rooms, events, states, keywords, use responses, and intro text are all data-driven.

- Floor layout defined via `floors` array — fully dynamic
- Supports multiple floors with stair and teleport connections between them
- All exit connections defined in events — rooms start locked and open through gameplay
- Teleport exits using cardinal directions show ✦ on the mini map
- Stair exits using up/down show ⬆⬇ on the mini map
- Interactable targets highlighted in room descriptions via `<em>` tags

### UI Features

- Dark dungeon-themed CSS with medieval fonts and gold accents
- Frosted glass UI panels over atmospheric background image
- Mini map showing explored rooms, current position, and floor-aware tracking
- Floor indicator displayed alongside the mini map
- Mobile responsive layout
- Event messages displayed separately from command responses
- Interactable targets highlighted in gold in room descriptions
- Win screen displayed when all win conditions are met
- Journal panel slides in from the right in a dark parchment style
- Journal auto-opens when `read journal` command is typed
- Intro panel fades in on first visit as a centered modal
- Journal JS moved to static file `journal.js`

---

## Tech Stack

- Python 3
- Flask + Flask-SQLAlchemy
- SQLite
- PyYAML
- Jinja2 Templates
- HTML5 / CSS3 / JS (no frontend framework)

---

## Folder Structure

```
flask_adventure/
│
├── static/
│   ├── js/
│   │   └── journal.js
│   ├── css/
│   │   └── main.css
│   └── images/
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── game.html
│   └── macros.html
│
├── data/
│   └── game_data.yaml
│
├── game/
│   ├── __init__.py
│   ├── controller.py
│   ├── parser.py
│   ├── actions.py
│   ├── event_manager.py
│   ├── event_types.py
│   ├── persistence.py
│   ├── gameObjects.py
│   └── player.py
│
├── instance/
│   └── test.db
│
├── app.py
├── Procfile
└── requirements.txt
```

---

## How to Run

```bash
git clone https://github.com/garysgray/Flask_ADVENTURE.git
cd Flask_ADVENTURE
pip install -r requirements.txt
python app.py
```

Open in browser: `http://127.0.0.1:5000`

---

## Planned Improvements

- **Win screen** — replace UI with win message and play again option, journal remains accessible
- **Room images** — optional image field per room in YAML, displayed when player enters
- **NPC system** — characters with dialogue states using existing event class pattern
- **Conditional item combinations** — items that only work in certain room states
- **Polish parser** — fuzzy matching, filler word stripping, better unknown command responses
- **Better help & item hints** — richer help command, contextual hints based on item keywords
- **Item aliases** — multi-word item names, players can type natural variations
- **Refactor room targets** — remove em tag scraping from parser, use event targets from YAML only
- **Constants file** — settings, enums, magic numbers in one place
- **Command history** — press up arrow to cycle previous commands
- **Admin panel** — edit rooms, items, events without touching YAML
- **Login system** — proper accounts with admin and player roles
- **Deploy to cloud** — Railway, Render, or Heroku using existing Procfile

---

## License

MIT

---

Built by Gary Fn Gray.
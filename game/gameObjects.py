import json
import os
import yaml
from game.event_types import (
    Event, AllRoomsVisitedEvent, ItemUsedWithEvent, AllEventsCompletedEvent,
    ECAEvent, Condition, InRoomCondition, EventsCompletedCondition,
    RequiredItemsCondition, RoomsVisitedCondition
)
from pathlib import Path

from config import DATA_FILE_PATH

# =============================================================================
# FIXTURE
# =============================================================================

class Fixture:
    def __init__(self, name, states=None, examine=None, priority=100, current_state='default', display_name=None):
        self.name          = name
        self.display_name  = display_name or name.replace('_', ' ')
        self.states        = states if states is not None else {}
        self.examine       = examine if examine is not None else {}
        self.priority      = priority
        self.current_state = current_state

    @property
    def description(self):
        return self.states.get(self.current_state, '')

    def get_examine_text(self):
        if self.examine:
            if self.current_state in self.examine:
                return self.examine[self.current_state]
            if 'default' in self.examine:
                return self.examine['default']

        desc = self.description
        if desc:
            return desc

        return f"You see nothing unusual about the {self.display_name}."

    def set_state(self, state):
        self.current_state = state

# =============================================================================
# ITEM
# =============================================================================

class Item:
    def __init__(self, name, states=None, keywords=None, aliases=None, display_name=None, presence=None):
        self.name          = name
        self.display_name  = display_name or name.replace('_', ' ')
        self.presence      = presence or self.display_name
        self.states        = states if states is not None else {}
        self.keywords      = keywords if keywords is not None else [name]
        self.aliases       = aliases if aliases is not None else []
        self.current_state = 'default'

    @property
    def presence_description(self):
        return self.presence

    @property
    def description(self):
        return self.states.get(self.current_state, {}).get('description', '')

    @property
    def use_text(self):
        return self.states.get(self.current_state, {}).get('use', '')

    def set_state(self, state):
        if state in self.states:
            self.current_state = state
        else:
            print(f"[STATE ERROR] Item '{self.name}' has no state '{state}'")

# =============================================================================
# ROOM
# =============================================================================

class Room:
    def __init__(self, name, exits, inventory, exit_destinations=None, states=None,
                 display_name=None, locked_exits=None, base_description=None,
                 trailing_description=None, fixtures=None):
        self.name                 = name
        self.display_name         = display_name or name.replace('_', ' ')
        self.exits                = exits
        self.inventory            = inventory
        self.exit_destinations    = exit_destinations if exit_destinations is not None else {}
        self.locked_exits         = locked_exits if locked_exits is not None else []
        self.states               = states if states is not None else {}
        self.current_state        = 'default'
        self.base_description     = base_description or ''
        self.trailing_description = trailing_description or ''
        self.fixtures             = fixtures if fixtures is not None else {}

    @property
    def description(self):
        print("\n===== ROOM DESCRIPTION DEBUG =====")
        print(f"Room: {self.name}")
        print(f"Base: {repr(self.base_description)}")
        print(f"Fixtures: {list(self.fixtures.keys())}")
        print(f"Inventory count: {len(self.inventory)}")

        for item in self.inventory:
            print(
                f"ITEM: name={item.name!r}, "
                f"display_name={item.display_name!r}, "
                f"presence={item.presence_description!r}"
            )

        print(f"Trailing: {repr(self.trailing_description)}")
        print("==================================")

        parts = []

        if self.base_description:
            clean_base = self.base_description.strip()
            if clean_base:
                parts.append(clean_base)

        if self.fixtures:
            sorted_fixtures = sorted(
                self.fixtures.values(),
                key=lambda f: f.priority
            )

            for fixture in sorted_fixtures:
                text = fixture.description.strip()
                if text:
                    parts.append(text)

        item_descriptions = []

        for item in self.inventory:
            pres = item.presence_description.strip()

            print(
                f"ADDING ITEM TO DESCRIPTION: "
                f"{item.name!r} -> {pres!r}"
            )

            if pres:
                item_descriptions.append(pres)

        if item_descriptions:
            parts.append(
                "Items in the room are: "
                + ", ".join(item_descriptions)
                + "."
            )

        if self.trailing_description:
            clean_trailing = self.trailing_description.strip()
            if clean_trailing:
                parts.append(clean_trailing)

        result = " ".join(parts)

        print(f"FINAL ROOM DESCRIPTION: {result!r}")
        print("==================================\n")

        return result 
    
    @description.setter
    def description(self, value):
        if self.states:
            self.states[self.current_state] = value
        else:
            self.base_description = value

    def set_state(self, state):
        if state in self.states:
            self.current_state = state
        else:
            self.current_state = state

# =============================================================================
# MAP
# =============================================================================

class Map:
    def __init__(self, file_path=None):
        self.file_path = file_path
        data = self._load_data()

        self.item_recipes   = data.get('items', {})
        self.room_recipes   = data.get('rooms', [])
        self.floor_recipes  = data.get('floors', [])
        self.target_aliases = data.get('target_aliases', {})
        self.custom_verbs   = data.get('custom_verbs', {})
        self.win_conditions = data.get('win_conditions', [])
        self.intro          = data.get('intro', {})
        self.win_screen     = data.get('win_screen', {})
        self.theme          = data.get('theme', {})

        player_start_stuff = data.get('player', {}).get('starting_inventory', [])
        self.player_start_invent = [self.make_item(stuff) for stuff in player_start_stuff]

        self.event_recipes = [self.make_event(e) for e in data.get('events', [])]

        rooms = self.create_fresh_rooms_from_recipes()
        self.rebuild_from_rooms(rooms)

        self.list_of_items = [self.make_item(name) for name in self.item_recipes]

    def _load_data(self):
        if self.file_path:
            data_path = Path(self.file_path)
            if not data_path.is_absolute():
                base_dir = Path(__file__).resolve().parent
                data_path = (base_dir.parent / self.file_path).resolve()
        else:
            base_dir = Path(__file__).resolve().parent
            data_path = base_dir.parent / "data" / DATA_FILE_PATH

        with open(data_path, "r") as f:
            return yaml.safe_load(f)

    def make_item(self, item_name):
        if item_name in self.item_recipes:
            data = self.item_recipes[item_name]
            return Item(
                name         = item_name,
                states       = data.get('states', {}),
                keywords     = data.get('keywords', [item_name]),
                aliases      = data.get('aliases', []),
                display_name = data.get('display_name', item_name.replace('_', ' ')),
                presence     = data.get('presence')
            )
        return Item(name=item_name)

    def make_event(self, data):
        if 'trigger' in data or 'conditions' in data:
            trigger = data.get('trigger', {})
            cond_list = []
            for c_data in data.get('conditions', []):
                c_type = c_data.get('type')
                hint = c_data.get('on_fail_hint') or c_data.get('fail_hint', '')
                if c_type == 'in_room':
                    cond_list.append(InRoomCondition(c_data.get('room'), fail_hint=hint))
                elif c_type in ('events_completed', 'all_events_completed'):
                    cond_list.append(EventsCompletedCondition(c_data.get('events') or c_data.get('required_events'), fail_hint=hint))
                elif c_type == 'required_items':
                    cond_list.append(RequiredItemsCondition(c_data.get('required_items') or c_data.get('items'), fail_hint=hint))
                elif c_type in ('rooms_visited', 'all_rooms_visited'):
                    cond_list.append(RoomsVisitedCondition(c_data.get('required_rooms') or c_data.get('rooms')))
            return ECAEvent(
                id=data['id'],
                trigger=trigger,
                conditions=cond_list,
                result=data.get('result', {}),
                hints=data.get('hints', {})
            )
        return data

    def create_fresh_rooms_from_recipes(self):
        rooms = []
        for recipe in self.room_recipes:
            fixtures_dict = {}
            raw_fixtures = recipe.get('fixtures', {})
            if isinstance(raw_fixtures, dict):
                for fix_name, fix_data in raw_fixtures.items():
                    fixtures_dict[fix_name] = Fixture(
                        name          = fix_name,
                        states        = fix_data.get('states', {}),
                        examine       = fix_data.get('examine', {}),
                        priority      = fix_data.get('priority', 100),
                        current_state = fix_data.get('state', 'default'),
                        display_name  = fix_data.get('display_name', fix_name.replace('_', ' '))
                    )

            room = Room(
                name                 = recipe['name'],
                exits                = recipe['exits'].copy(),
                inventory            = [self.make_item(name) for name in recipe.get('items', [])],
                exit_destinations    = recipe.get('exit_destinations', {}).copy(),
                locked_exits         = recipe.get('locked_exits', []).copy(),
                states               = recipe.get('states', {}),
                display_name         = recipe.get('display_name', recipe['name'].replace('_', ' ')),
                base_description     = recipe.get('base_description', ''),
                trailing_description = recipe.get('trailing_description', ''),
                fixtures             = fixtures_dict
            )
            rooms.append(room)
        return rooms

    def rebuild_from_rooms(self, fresh_rooms):
        self.list_of_rooms = fresh_rooms
        room_by_name = {room.name: room for room in fresh_rooms}

        self.game_map = []
        for floor_layout in self.floor_recipes:
            floor = []
            for row in floor_layout:
                floor.append([
                    room_by_name.get(cell) if cell is not None else None
                    for cell in row
                ])
            self.game_map.append(floor)

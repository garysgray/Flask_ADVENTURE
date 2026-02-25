import json
from game.event_types import Event, AllRoomsVisitedEvent, ItemUsedWithEvent

class Item:
    """Represents an item in the game."""
    def __init__(self, name, states=None, keywords=None):
        self.name          = name
        self.states        = states if states is not None else {}
        self.keywords      = keywords if keywords is not None else [name]
        self.current_state = 'default'

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

class Room:
    """Represents a room in the game map."""
    def __init__(self, name, exits, inventory, exit_destinations=None, states=None):
        self.name              = name
        self.exits             = exits
        self.inventory         = inventory
        self.exit_destinations = exit_destinations if exit_destinations is not None else {}
        self.states            = states if states is not None else {}
        self.current_state     = 'default'

    @property
    def description(self):
        return self.states.get(self.current_state, '')

    def set_state(self, state):
        if state in self.states:
            self.current_state = state
        else:
            print(f"[STATE ERROR] Room '{self.name}' has no state '{state}'")

class Map:
    def __init__(self):
        data = self._load_data()
        self.item_recipes = data['items']
        self.room_recipes = data['rooms']
        self.event_recipes = [self.make_event(e) for e in data['events']]
        self.floor_recipes = data['floors']
        rooms = self.create_fresh_rooms_from_recipes()
        self.rebuild_from_rooms(rooms)
        self.list_of_items = [self.make_item(name) for name in self.item_recipes]
        self.player_start_invent = [self.make_item('watch'), self.make_item('knife')]

        self.win_conditions = data['win_conditions']

    # def make_item(self, item_name):
    #     data = self.item_recipes[item_name]
    #     return Item(item_name, data['states'])
    
    def make_item(self, item_name):
        data = self.item_recipes[item_name]
        return Item(
            name=item_name,
            states=data['states'],
            keywords=data.get('keywords', [item_name])
        )


    def create_fresh_rooms_from_recipes(self):
        rooms = []
        for recipe in self.room_recipes:
            room = Room(
                name=recipe['name'],
                exits=recipe['exits'].copy(),
                inventory=[self.make_item(name) for name in recipe['items']],
                exit_destinations=recipe['exit_destinations'].copy(),
                states=recipe.get('states', {})
            )
            rooms.append(room)
        return rooms

    def create_fresh_rooms_from_saved_data(self, rooms_data):
        rooms = []
        for room_data in rooms_data:
            room_items = [Item(name, details[0]) for item_dict in room_data['inventory'] for name, details in item_dict.items()]
            room = Room(
                name=room_data['name'],
                exits=room_data['exits'],
                description=room_data['description'],
                inventory=room_items,
                exit_destinations=room_data.get('exit_destinations', {})
            )
            rooms.append(room)
        return rooms

    def rebuild_from_rooms(self, fresh_rooms):
        self.list_of_rooms = fresh_rooms
        self.game_map = []
        for floor_layout in self.floor_recipes:
            floor = []
            for row in floor_layout:
                floor.append([fresh_rooms[i] for i in row])
            self.game_map.append(floor)

    def _load_data(self):
        import os
        import yaml
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'game_data.yaml')
        with open(path) as f:
            return yaml.safe_load(f)

        
    def make_event(self, data):
        if data['check_type'] == 'all_rooms_visited':
            return AllRoomsVisitedEvent(
                data['id'],
                data['result'],
                data['parameters']['required_rooms']
            )
        if data['check_type'] == 'item_used_with':
            return ItemUsedWithEvent(
                data['id'],
                data['result'],
                data['parameters']['item'],
                data['parameters']['target'],
                data['parameters']['room']
            )
        # all other event types stay as raw dicts for now
        return data
        
# =============================================================================
# MAP LAYOUT - as the player would experience it
# =============================================================================
#
# FLOOR 2 (attic level) - rooms[7] through rooms[10]
#
#          WEST          EAST
#   NORTH [ attic[7]  | gallery[8] ]
#   SOUTH [ study[9]  | well_room[10] ]
#
# FLOOR 1 (ground level) - rooms[4] through rooms[6]
#
#          WEST       MID        EAST
#        [ cellar[4] | chapel[5] | vault[6] ]
#
# FLOOR 0 (basement level) - rooms[0] through rooms[3]
#
#          WEST          EAST
#   NORTH [ entrance[0] | parlour[1] ]
#   SOUTH [ library[2]  | kitchen[3] ]
#
# =============================================================================
# HOW MOVEMENT WORKS
# =============================================================================
#
# On the same floor, exits like north/south/east/west move between grid cells.
# For example on floor 0:
#   standing in entrance[0] and going EAST  → parlour[1]
#   standing in entrance[0] and going SOUTH → library[2]
#
# UP and DOWN move between floors entirely, and only unlock via events:
#   entrance[0]  UP   → cellar[4]    (event: light_lantern)
#   library[2]   UP   → attic[7]     (event: all_rooms_floor0)
#   vault[6]     NORTH → attic[7]    (event: unlock_vault)
#
# =============================================================================
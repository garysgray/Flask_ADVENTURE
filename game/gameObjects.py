import json
import os
import yaml
from game.event_types import Event, AllRoomsVisitedEvent, ItemUsedWithEvent, AllEventsCompletedEvent


# =============================================================================
# ITEM
# =============================================================================

class Item:
    """
    Represents a game item. Items have states — each state has its own
    description and use_text. Current state changes when events fire.
    """
    def __init__(self, name, states=None, keywords=None):
        self.name          = name
        self.states        = states if states is not None else {}
        self.keywords      = keywords if keywords is not None else [name]
        self.current_state = 'default'

    @property
    def description(self):
        """Returns description text for the current state."""
        return self.states.get(self.current_state, {}).get('description', '')

    @property
    def use_text(self):
        """Returns use response text for the current state."""
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
    """
    Represents a room in the game map. Rooms have states — each state has
    its own description text. Current state changes when events fire.
    """
    def __init__(self, name, exits, inventory, exit_destinations=None, states=None):
        self.name              = name
        self.exits             = exits
        self.inventory         = inventory
        self.exit_destinations = exit_destinations if exit_destinations is not None else {}
        self.states            = states if states is not None else {}
        self.current_state     = 'default'

    @property
    def description(self):
        """Returns description text for the current state."""
        return self.states.get(self.current_state, '')

    def set_state(self, state):
        if state in self.states:
            self.current_state = state
        else:
            print(f"[STATE ERROR] Room '{self.name}' has no state '{state}'")


# =============================================================================
# MAP
# =============================================================================

class Map:
    """
    Loads all game data from game_data.yaml and builds the live game world.
    Holds recipes (raw YAML data) and live objects (rooms, events, items).
    Recipes are the source of truth — live objects are rebuilt from them on load,
    with saved state restored on top.
    """

    def __init__(self):
        data = self._load_data()

        # raw recipes from YAML — used to rebuild objects and look up keywords
        self.item_recipes  = data['items']
        self.room_recipes  = data['rooms']
        self.floor_recipes = data['floors']
        self.win_conditions = data['win_conditions']
        self.intro = data.get('intro', {})
        self.win_screen = data.get('win_screen', {})

        player_start_stuff = data.get('player', {})

        player_start_stuff = player_start_stuff.get('starting_inventory', [])

        self.player_start_invent = []
        for stuff in player_start_stuff:
            self.player_start_invent.append(self.make_item(stuff))

        # built event objects from YAML event definitions
        self.event_recipes = [self.make_event(e) for e in data['events']]

        # build live room and map objects
        rooms = self.create_fresh_rooms_from_recipes()
        self.rebuild_from_rooms(rooms)

        # full item list and starting inventory
        self.list_of_items       = [self.make_item(name) for name in self.item_recipes]

    # ─── Data Loading ─────────────────────────────────────────────────────────

    def _load_data(self):
        """Loads and parses game_data.yaml from the data directory."""
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'game_data.yaml')
        with open(path) as f:
            return yaml.safe_load(f)

    # ─── Factory Methods ──────────────────────────────────────────────────────

    def make_item(self, item_name):
        """Builds a fresh Item object from the item recipe."""
        data = self.item_recipes[item_name]
        return Item(
            name     = item_name,
            states   = data['states'],
            keywords = data.get('keywords', [item_name])
        )

    def make_event(self, data):
        """Builds the appropriate Event subclass from a YAML event definition."""
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
        if data['check_type'] == 'all_events_completed':
            return AllEventsCompletedEvent(
                data['id'],
                data['result'],
                data['parameters']['required_events']
            )
        # unknown event types returned as raw dict for now
        return data

    # ─── Room Building ────────────────────────────────────────────────────────

    def create_fresh_rooms_from_recipes(self):
        """Builds fresh Room objects from YAML recipes with no saved state applied."""
        rooms = []
        for recipe in self.room_recipes:
            room = Room(
                name              = recipe['name'],
                exits             = recipe['exits'].copy(),
                inventory         = [self.make_item(name) for name in recipe['items']],
                exit_destinations = recipe['exit_destinations'].copy(),
                states            = recipe.get('states', {})
            )
            rooms.append(room)
        return rooms

    # def rebuild_from_rooms(self, fresh_rooms):
    #     """
    #     Assigns the room list and builds the 3D game_map grid from floor recipes.
    #     Floor recipes are index arrays that reference rooms by position in list_of_rooms.
    #     """
    #     self.list_of_rooms = fresh_rooms
    #     self.game_map      = []
    #     for floor_layout in self.floor_recipes:
    #         floor = []
    #         for row in floor_layout:
    #             floor.append([fresh_rooms[i] for i in row])
    #         self.game_map.append(floor)

    def rebuild_from_rooms(self, fresh_rooms):
        self.list_of_rooms = fresh_rooms
        
        # build name lookup so floors can use room names instead of indices
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


# =============================================================================
# MAP LAYOUT — as the player would experience it
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
#   entrance[0]  UP    → cellar[4]   (event: light_lantern)
#   library[2]   UP    → attic[7]    (event: all_rooms_floor0)
#   vault[6]     NORTH → attic[7]    (event: unlock_vault)
#
# =============================================================================
class Item:
    """Represents an item in the game."""
    def __init__(self, name, description):
        self.name = name
        self.description = description


class Room:
    """Represents a room in the game map."""
    def __init__(self, name, exits, description, inventory, exit_destinations=None):
        self.name = name
        self.exits = exits
        self.description = description
        self.inventory = inventory
        self.exit_destinations = exit_destinations if exit_destinations is not None else {}


class Map:
    """Creates the game map, items, rooms, and events."""

    def __init__(self):
        # -------------------------------
        # Item recipes
        # -------------------------------
        self.item_recipes = {
            'baseball': "It's an official MLB baseball",
            'bat': "It's a nice wooden bat",
            'speaker': "It's a bluetooth speaker",
            'axe': "It's a trusty axe",
            'comic': "It's a classic comic book",
            'watch': "It's ticking",
            'knife': "It's sharp",
            'beer': "It looks tasty",
            'skateboard': "It's an IOU board!!!!",
            'sword': "It's well balanced",
            'phone': "It's the latest and greatest"
        }

        # -------------------------------
        # Room recipes
        # -------------------------------
        self.room_recipes = [
            {
                'name': 'red', 
                'exits': ['south', 'east'], 
                'description': "It's a reddish colored room", 
                'items': ['baseball', 'speaker'],
                'exit_destinations': {}
            },
            {
                'name': 'blue', 
                'exits': ['south', 'west'], 
                'description': "It's a blueish colored room", 
                'items': ['beer'],
                'exit_destinations': {}
            },
            {
                'name': 'yellow', 
                'exits': ['north', 'east'], 
                'description': "It's a yellowish colored room with a heavy door to the west.", 
                'items': ['axe', 'skateboard'],
                'exit_destinations': {}
            },
            {
                'name': 'green', 
                'exits': ['north', 'west'], 
                'description': "It's a greenish colored room", 
                'items': ['comic'],
                'exit_destinations': {}
            },
            {
                'name': 'black', 
                'exits': ['east'], 
                'description': "It's a dark black room", 
                'items': ['sword'],
                'exit_destinations': {}
            },
            {
                'name': 'white', 
                'exits': ['west', 'east'], 
                'description': "It's a bright white room", 
                'items': ['phone'],
                'exit_destinations': {}
            },
            {
                'name': 'purple', 
                'exits': ['west'], 
                'description': "It's a bright purple room", 
                'items': ['bat'],
                'exit_destinations': {}
            },
        ]

        # -------------------------------
        # Event recipes
        # -------------------------------
        self.event_recipes = [
            {
                'id': 'all_rooms_visited',
                'type': 'achievement',
                'check_type': 'all_rooms_visited',
                'parameters': {'required_rooms': ['red', 'blue', 'yellow', 'green']},
                'result': {
                    'open_exit': [
                        {
                            'room': 'red',
                            'direction': 'up',
                            'destination': {'floor': 1, 'x': 0, 'y': 0}
                        },
                        {
                            'room': 'black',
                            'direction': 'down',
                            'destination': {'floor': 0, 'x': 0, 'y': 0}
                        }
                    ],
                    'message': 'You hear a grinding sound from above...'
                }
            },
            {
                'id': 'key_opens_door',
                'type': 'puzzle',
                'check_type': 'item_used_with',
                'parameters': {'item': 'axe', 'target': 'door', 'room': 'yellow'},
                'result': {
                    'open_exit': [
                        {
                            'room': 'yellow',
                            'direction': 'west',
                            'destination': {'floor': 1, 'x': 2, 'y': 0}
                        },
                        {
                            'room': 'purple',
                            'direction': 'east',
                            'destination': {'floor': 0, 'x': 0, 'y': 1}
                        }
                    ],
                    'message': 'You smash the door open with the axe!'
                }
            }
        ]

        # -------------------------------
        # Build rooms and floors
        # -------------------------------
        rooms = self.create_fresh_rooms_from_recipes()

        self.floor_1 = [[rooms[0], rooms[1]],
                        [rooms[2], rooms[3]]]
        self.floor_2 = [[rooms[4], rooms[5], rooms[6]]]

        self.game_map = [self.floor_1, self.floor_2]
        self.list_of_rooms = rooms
        self.list_of_items = [self.make_item(name) for name in self.item_recipes.keys()]
        self.player_start_invent = [self.make_item('watch'), self.make_item('knife')]

    # -------------------------------
    # Helper methods
    # -------------------------------
    def make_item(self, item_name):
        """Create a fresh Item instance from the recipe."""
        return Item(item_name, self.item_recipes[item_name])

    def create_fresh_rooms_from_recipes(self):
        """Create fresh Room instances from the room recipes."""
        rooms = []
        for recipe in self.room_recipes:
            room_items = [self.make_item(name) for name in recipe['items']]
            room = Room(
                name=recipe['name'],
                exits=recipe['exits'].copy(),
                description=recipe['description'],
                inventory=room_items,
                exit_destinations=recipe['exit_destinations'].copy()
            )
            rooms.append(room)
        return rooms

    def create_fresh_rooms_from_saved_data(self, rooms_data):
        """
        Recreate rooms from saved data (used for loading game state).
        rooms_data is a list of dicts containing room info and item info.
        """
        rooms = []
        for room_data in rooms_data:
            room_items = []
            for item_dict in room_data['inventory']:
                for name, details in item_dict.items():
                    room_items.append(Item(name, details[0]))
            room = Room(
                name=room_data['name'],
                exits=room_data['exits'],
                description=room_data['description'],
                inventory=room_items,
                exit_destinations=room_data.get('exit_destinations', {})
            )
            rooms.append(room)
        return rooms

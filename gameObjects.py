import json

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
    def __init__(self):
        data = self._load_data()
        self.item_recipes = data['items']
        self.room_recipes = data['rooms']
        self.event_recipes = data['events']

        rooms = self.create_fresh_rooms_from_recipes()
        self.rebuild_from_rooms(rooms)
        self.list_of_items = [self.make_item(name) for name in self.item_recipes]
        self.player_start_invent = [self.make_item('watch'), self.make_item('knife')]

    def make_item(self, item_name):
        data = self.item_recipes[item_name]
        return Item(item_name, data['description'])

    def create_fresh_rooms_from_recipes(self):
        rooms = []
        for recipe in self.room_recipes:
            room = Room(
                name=recipe['name'],
                exits=recipe['exits'].copy(),
                description=recipe['description'],
                inventory=[self.make_item(name) for name in recipe['items']],
                exit_destinations=recipe['exit_destinations'].copy()
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
        self.floor_1 = [[fresh_rooms[0], fresh_rooms[1]],
                        [fresh_rooms[2], fresh_rooms[3]]]
        self.floor_2 = [[fresh_rooms[4], fresh_rooms[5], fresh_rooms[6]]]
        self.game_map = [self.floor_1, self.floor_2]

    def _load_data(self):
        import os
        path = os.path.join(os.path.dirname(__file__), 'game_data.json')
        with open(path) as f:
            return json.load(f)
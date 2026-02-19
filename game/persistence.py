import json
from game.gameObjects import Item

class PersistenceManager:
    def __init__(self, controller):
        self.ctrl = controller

    def load(self, db_player):
        player_location = json.loads(db_player.location)
        player_inventory_from_DB = json.loads(db_player.player_inventory)
        rooms_data = json.loads(db_player.room_inventory)

        self.ctrl.player.id = db_player.id
        self.ctrl.player.pos_x = player_location['X']
        self.ctrl.player.pos_y = player_location['Y']
        self.ctrl.player.visited_rooms = player_location.get('visited_rooms', [])
        self.ctrl.player.completed_events = player_location.get('completed_events', [])

        self.ctrl.player.inventory = []
        for item_dict in player_inventory_from_DB:
            for name, details in item_dict.items():
                self.ctrl.player.inventory.append(Item(name, details[0]))

        fresh_rooms = self.ctrl.map.create_fresh_rooms_from_saved_data(rooms_data)
        self.ctrl.map.rebuild_from_rooms(fresh_rooms)
    def save(self):
        player_data = {
            'X': self.ctrl.player.pos_x,
            'Y': self.ctrl.player.pos_y,
            'visited_rooms': self.ctrl.player.visited_rooms,
            'completed_events': self.ctrl.player.completed_events
        }

        player_inventory = [{i.name: [i.description]} for i in self.ctrl.player.inventory]

        rooms_data = []
        for room in self.ctrl.map.list_of_rooms:
            rooms_data.append({
                'name': room.name,
                'exits': room.exits,
                'description': room.description,
                'inventory': [{i.name: [i.description]} for i in room.inventory],
                'exit_destinations': room.exit_destinations
            })

        return (json.dumps(player_data), json.dumps(player_inventory), json.dumps(rooms_data))
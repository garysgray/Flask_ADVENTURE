import json
from game.gameObjects import Item

class PersistenceManager:
    def __init__(self, controller):
        self.ctrl = controller

    
    def load(self, db_player):
        player_location          = json.loads(db_player.location)
        player_inventory_from_DB = json.loads(db_player.player_inventory)
        rooms_data               = json.loads(db_player.room_inventory)

        self.ctrl.player.id               = db_player.id
        self.ctrl.player.pos_x            = player_location['X']
        self.ctrl.player.pos_y            = player_location['Y']
        self.ctrl.player.visited_rooms    = player_location.get('visited_rooms', [])
        self.ctrl.player.completed_events = player_location.get('completed_events', [])
        self.ctrl.player.journal = player_location.get('journal', [])

        # rebuild player inventory from recipes and restore state
        self.ctrl.player.inventory = []
        for item_dict in player_inventory_from_DB:
            for name, state in item_dict.items():
                item = self.ctrl.map.make_item(name)
                item.current_state = state
                self.ctrl.player.inventory.append(item)

        # update existing rooms with saved exits, inventory and state
        for saved_room in rooms_data:
            for room in self.ctrl.map.list_of_rooms:
                if room.name == saved_room['name']:
                    room.exits             = saved_room['exits']
                    room.exit_destinations = saved_room.get('exit_destinations', {})
                    room.current_state     = saved_room.get('current_state', 'default')
                    room.inventory         = []
                    for item_dict in saved_room['inventory']:
                        for name, state in item_dict.items():
                            item = self.ctrl.map.make_item(name)
                            item.current_state = state
                            room.inventory.append(item)

    def save(self):
        player_data = {
            'X': self.ctrl.player.pos_x,
            'Y': self.ctrl.player.pos_y,
            'visited_rooms':    self.ctrl.player.visited_rooms,
            'completed_events': self.ctrl.player.completed_events,
            'journal':          self.ctrl.player.journal
        }

        # only save item names, descriptions are rebuilt from recipes on load
        player_inventory = [{i.name: i.current_state} for i in self.ctrl.player.inventory]

        rooms_data = []
        for room in self.ctrl.map.list_of_rooms:
            rooms_data.append({
                'name':              room.name,
                'exits':             room.exits,
                'current_state':     room.current_state,
                'inventory':         [{i.name: i.current_state} for i in room.inventory],
                'exit_destinations': room.exit_destinations
            })

        return (json.dumps(player_data), json.dumps(player_inventory), json.dumps(rooms_data))
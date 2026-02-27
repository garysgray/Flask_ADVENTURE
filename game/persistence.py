import json
from game.gameObjects import Item


class PersistenceManager:
    """
    Handles saving and loading all game state to/from the database.

    Save strategy:
        Items and rooms are never saved as full objects — only names and current
        states are saved. On load, fresh objects are rebuilt from YAML recipes
        and saved state is restored on top. This means recipe changes (descriptions,
        keywords, use text) are always picked up cleanly without migration.

    What gets saved:
        location         — player position, visited rooms, completed events, journal
        player_inventory — item names and their current states
        room_inventory   — all rooms with their exits, states, inventories, and exit destinations
    """

    def __init__(self, controller):
        self.ctrl = controller

    # ─── Load ─────────────────────────────────────────────────────────────────

    def load(self, db_player):
        """
        Restores full game state from the database into the controller.
        Called once per session on the player's first GET request.
        """
        player_location          = json.loads(db_player.location)
        player_inventory_from_DB = json.loads(db_player.player_inventory)
        rooms_data               = json.loads(db_player.room_inventory)

        # restore player state
        self.ctrl.player.id               = db_player.id
        self.ctrl.player.pos_x            = player_location['X']
        self.ctrl.player.pos_y            = player_location['Y']
        self.ctrl.player.visited_rooms    = player_location.get('visited_rooms', [])
        self.ctrl.player.visited_room_names = player_location.get('visited_room_names', [])
        self.ctrl.player.completed_events = player_location.get('completed_events', [])
        self.ctrl.player.journal          = player_location.get('journal', [])
        self.ctrl.player.has_seen_intro   = player_location.get('has_seen_intro', False)

        # rebuild player inventory from recipes and restore saved states
        self.ctrl.player.inventory = []
        for item_dict in player_inventory_from_DB:
            for name, state in item_dict.items():
                item               = self.ctrl.map.make_item(name)
                item.current_state = state
                self.ctrl.player.inventory.append(item)

        # restore room exits, states, and inventories
        for saved_room in rooms_data:
            for room in self.ctrl.map.list_of_rooms:
                if room.name == saved_room['name']:
                    room.exits             = saved_room['exits']
                    room.exit_destinations = saved_room.get('exit_destinations', {})
                    room.current_state     = saved_room.get('current_state', 'default')
                    room.inventory         = []
                    for item_dict in saved_room['inventory']:
                        for name, state in item_dict.items():
                            item               = self.ctrl.map.make_item(name)
                            item.current_state = state
                            room.inventory.append(item)

    # ─── Save ─────────────────────────────────────────────────────────────────

    def save(self):
        """
        Serializes current game state to JSON strings for database storage.
        Returns a tuple of (location, player_inventory, room_inventory).
        """
        player_data = {
            'X':               self.ctrl.player.pos_x,
            'Y':               self.ctrl.player.pos_y,
            'visited_rooms':   self.ctrl.player.visited_rooms,
            'completed_events':self.ctrl.player.completed_events,
            'journal':         self.ctrl.player.journal,
            'has_seen_intro':  self.ctrl.player.has_seen_intro,
            'visited_room_names': self.ctrl.player.visited_room_names,
        }

        # save item name and current state only — descriptions rebuilt from recipes on load
        player_inventory = [
            {i.name: i.current_state}
            for i in self.ctrl.player.inventory
        ]

        rooms_data = [
            {
                'name':              room.name,
                'exits':             room.exits,
                'current_state':     room.current_state,
                'inventory':         [{i.name: i.current_state} for i in room.inventory],
                'exit_destinations': room.exit_destinations
            }
            for room in self.ctrl.map.list_of_rooms
        ]

        return (
            json.dumps(player_data),
            json.dumps(player_inventory),
            json.dumps(rooms_data)
        )
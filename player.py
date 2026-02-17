class Player:
    def __init__(self, game_map=None):
        self.id = None
        self.pos_x = 0
        self.pos_y = 0
        self.level = 0
        self.inventory = []
        self.directions = ['north', 'south', 'east', 'west', 'up', 'down']

        self.visited_rooms = []       # Rooms the player has visited
        self.completed_events = []    # Completed in-game events

        self.game_map = game_map

    def get_location(self):
        """Return current player coordinates."""
        return {'X': self.pos_x, 'Y': self.pos_y}

    def drop(self, room, possible_item):
        """Drop an item from inventory into the room."""
        for obj in self.inventory:
            if obj.name in possible_item:
                self.inventory.remove(obj)
                room.inventory.append(obj)
                return obj.name
        return False

    def pick_up(self, room, possible_item):
        """Pick up an item from the room into inventory."""
        for obj in room.inventory:
            if obj.name in possible_item:
                self.inventory.append(obj)
                room.inventory.remove(obj)
                return obj.name
        return False

    def look(self, room, possible_item):
        """Return description of an item in inventory or room."""
        for obj in self.inventory:
            if obj.name in possible_item:
                return obj.description
        for obj in room.inventory:
            if obj.name in possible_item:
                return obj.description
        return False

    def move(self, dir, room, level_max):
        """
        Move the player in the given direction from the current room.

        Priority:
        1. Special exits in room.exit_destinations (teleport)
        2. Regular movement on the current floor (grid-based)
        """
        # 1. Check for teleporting exit
        if dir in room.exit_destinations:
            dest = room.exit_destinations[dir]
            self.level = dest['floor']
            self.pos_x = dest['x']
            self.pos_y = dest['y']
            return True

        # 2. Regular grid movement
        current_floor = self.game_map[self.level]
        current_row = current_floor[self.pos_y]

        if dir == 'north' and self.pos_y > 0:
            self.pos_y -= 1
            return True
        elif dir == 'south' and self.pos_y + 1 < len(current_floor):
            self.pos_y += 1
            return True
        elif dir == 'east' and self.pos_x + 1 < len(current_row):
            self.pos_x += 1
            return True
        elif dir == 'west' and self.pos_x > 0:
            self.pos_x -= 1
            return True

        return False  # Invalid move

    def use(self, possible_item):
        """Use an item from inventory and return its effect text."""
        use_responses = {
            'knife': "You slash the air menacingly. The knife feels sharp.",
            'watch': "It reads 3:47pm, time is passing...",
            'beer': "You drink it. Warm and flat but hits the spot. The bottle is now empty.",
            'skateboard': "You ride it down the hall, feeling rad!",
            'baseball': "You toss it up and catch it.",
            'bat': "You swing it through the air. Whoosh!",
            'speaker': "You turn it on. Music fills the room.",
            'axe': "You swing it. It feels heavy and powerful.",
            'comic': "You flip through it. Looks interesting.",
            'sword': "You swing it. It gleams in the light.",
            'phone': "You turn it on. No signal.",
        }

        for obj in self.inventory:
            if obj.name in possible_item:
                return use_responses.get(obj.name, f"You use the {obj.name}.")
        return False

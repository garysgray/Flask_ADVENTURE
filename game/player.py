class Player:
    DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down']

    def __init__(self, game_map=None, use_responses=None):
        self.id = None
        self.pos_x = 0
        self.pos_y = 0
        self.level = 0
        self.inventory = []
        self.directions = self.DIRECTIONS
        self.visited_rooms = []
        self.completed_events = []
        self.game_map = game_map
        self.use_responses = use_responses or {}

    def get_location(self):
        return {'X': self.pos_x, 'Y': self.pos_y}

    def drop(self, room, possible_item):
        for obj in self.inventory:
            if obj.name in possible_item:
                self.inventory.remove(obj)
                room.inventory.append(obj)
                return obj.name
        return False

    def pick_up(self, room, possible_item):
        for obj in room.inventory:
            if obj.name in possible_item:
                self.inventory.append(obj)
                room.inventory.remove(obj)
                return obj.name
        return False

    def look(self, room, possible_item):
        for obj in self.inventory + room.inventory:
            if obj.name in possible_item:
                return obj.description
        return False

    def move(self, dir, room, level_max):
        if dir in room.exit_destinations:
            dest = room.exit_destinations[dir]
            self.level = dest['floor']
            self.pos_x = dest['x']
            self.pos_y = dest['y']
            return True
        floor = self.game_map[self.level]
        row = floor[self.pos_y]
        moves = {
            'north': lambda: self.pos_y > 0,
            'south': lambda: self.pos_y + 1 < len(floor),
            'east':  lambda: self.pos_x + 1 < len(row),
            'west':  lambda: self.pos_x > 0,
        }
        if dir in moves and moves[dir]():
            if dir == 'north': self.pos_y -= 1
            if dir == 'south': self.pos_y += 1
            if dir == 'east':  self.pos_x += 1
            if dir == 'west':  self.pos_x -= 1
            return True
        return False

    def use(self, possible_item):
        for obj in self.inventory:
            if obj.name in possible_item:
                return self.use_responses.get(obj.name, f"You use the {obj.name}.")
        return False
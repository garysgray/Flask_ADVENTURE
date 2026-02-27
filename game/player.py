class Player:
    """
    Holds all live player state — position, inventory, progress, and journal.
    Also handles movement, item interaction, and look logic.
    State is saved to the database after every command via PersistenceManager.
    """

    DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down']

    def __init__(self, game_map=None):
        self.id               = None
        self.pos_x            = 0
        self.pos_y            = 0
        self.level            = 0
        self.inventory        = []
        self.directions       = self.DIRECTIONS
        self.visited_rooms    = []
        self.completed_events = []
        self.journal          = []  # permanent — cannot be dropped or lost
        self.has_seen_intro   = False
        self.game_map         = game_map

        self.visited_room_names = []

    # ─── Location ─────────────────────────────────────────────────────────────

    def get_location(self):
        return {'X': self.pos_x, 'Y': self.pos_y}

    # ─── Movement ─────────────────────────────────────────────────────────────

    def move(self, dir, room, level_max):
        """
        Moves the player in the given direction.
        Checks exit_destinations first for teleport/stair exits defined by events.
        Falls back to grid movement for same-floor cardinal directions.
        Returns True if the move succeeded, False if blocked.
        """
        # teleport or stair exit defined by an event
        if dir in room.exit_destinations:
            dest       = room.exit_destinations[dir]
            self.level = dest['floor']
            self.pos_x = dest['x']
            self.pos_y = dest['y']
            return True

        # same-floor grid movement
        floor = self.game_map[self.level]
        row   = floor[self.pos_y]

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

    # ─── Inventory ────────────────────────────────────────────────────────────

    def pick_up(self, room, possible_item):
        """
        Moves a matching item from the room into player inventory.
        Returns the item name if successful, False if not found.
        """
        for obj in room.inventory:
            if obj.name in possible_item:
                self.inventory.append(obj)
                room.inventory.remove(obj)
                return obj.name
        return False

    def drop(self, room, possible_item):
        """
        Moves a matching item from player inventory into the room.
        Returns the item name if successful, False if not found.
        """
        for obj in self.inventory:
            if obj.name in possible_item:
                self.inventory.remove(obj)
                room.inventory.append(obj)
                return obj.name
        return False

    # ─── Item Interaction ─────────────────────────────────────────────────────

    def look(self, room, possible_item):
        """
        Returns the description of a matching item from inventory or room.
        Searches both so the player can look at items without picking them up.
        Returns False if not found.
        """
        for obj in self.inventory + room.inventory:
            if obj.name in possible_item:
                return obj.description
        return False

    def use(self, possible_item):
        """
        Returns the use_text of a matching item from player inventory.
        Called for solo use commands e.g. 'read map', 'wind music_box'.
        Returns False if item not found.
        """
        for obj in self.inventory:
            if obj.name in possible_item:
                return obj.use_text
        return False
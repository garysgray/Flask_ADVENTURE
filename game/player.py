class Player:
    """
    Holds all live player state — position, inventory, progress, and journal.
    Also handles movement, item interaction, and look logic.
    State is saved to the database after every command via PersistenceManager.
    """

    DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down', 'portal']

    def __init__(self, game_map=None, location=None, inventory=None):
        self.id               = None
        self.pos_x            = 0
        self.pos_y            = 0
        self.level            = 0
        if isinstance(location, dict):
            self.pos_x = location.get("x", 0)
            self.pos_y = location.get("y", 0)
            self.level = location.get("floor", location.get("z", 0))
        self.inventory        = list(inventory) if inventory is not None else []
        self.directions       = self.DIRECTIONS
        self.visited_rooms    = []
        self.completed_events = []
        self.journal          = []  # permanent — cannot be dropped or lost
        self.has_seen_intro   = False
        self.game_map         = game_map

        self.visited_room_names = []

    # ─── Location ─────────────────────────────────────────────────────────────

    def get_location(self):
        return {'X': self.pos_x, 'Y': self.pos_y, 'floor': self.level}

    # ─── Movement ─────────────────────────────────────────────────────────────

    def move(self, dir, room, level_max):
        """
        Moves the player in the given direction.
        Checks locked exits first to prevent moving through locked passages.
        Checks exit_destinations next for custom portals, stairs, or event-defined exits.
        Handles default vertical movement (up/down) between floors at the same (x, y) coordinates.
        Falls back to grid movement for same-floor cardinal directions.
        Returns True if the move succeeded, False if blocked.
        """
        if dir not in room.exits and dir not in room.exit_destinations:
            return False

        if hasattr(room, 'locked_exits') and room.locked_exits and dir in room.locked_exits:
            return False

        # teleport, portal, or stair exit defined in exit_destinations
        if dir in room.exit_destinations:
            dest       = room.exit_destinations[dir]
            self.level = dest['floor']
            self.pos_x = dest['x']
            self.pos_y = dest['y']
            return True

        # default vertical movement (up / down) between floors at same (x, y)
        if dir == 'up' and dir in room.exits:
            target_level = self.level + 1
            if target_level < len(self.game_map):
                target_floor = self.game_map[target_level]
                if self.pos_y < len(target_floor) and self.pos_x < len(target_floor[self.pos_y]):
                    if target_floor[self.pos_y][self.pos_x] is not None:
                        self.level = target_level
                        return True
            return False

        if dir == 'down' and dir in room.exits:
            target_level = self.level - 1
            if 0 <= target_level < len(self.game_map):
                target_floor = self.game_map[target_level]
                if self.pos_y < len(target_floor) and self.pos_x < len(target_floor[self.pos_y]):
                    if target_floor[self.pos_y][self.pos_x] is not None:
                        self.level = target_level
                        return True
            return False

        # same-floor grid movement
        floor = self.game_map[self.level]
        row   = floor[self.pos_y]

        moves = {
            'north': lambda: self.pos_y > 0 and floor[self.pos_y - 1][self.pos_x] is not None,
            'south': lambda: self.pos_y + 1 < len(floor) and floor[self.pos_y + 1][self.pos_x] is not None,
            'east':  lambda: self.pos_x + 1 < len(row) and floor[self.pos_y][self.pos_x + 1] is not None,
            'west':  lambda: self.pos_x > 0 and floor[self.pos_y][self.pos_x - 1] is not None,
        }

        if dir in moves and moves[dir]():
            if dir == 'north': self.pos_y -= 1
            if dir == 'south': self.pos_y += 1
            if dir == 'east':  self.pos_x += 1
            if dir == 'west':  self.pos_x -= 1
            return True

        return False

    # ─── Matching Helper ──────────────────────────────────────────────────────

    def _match_item(self, obj, target):
        """Checks if an item object matches target string, list, or alias."""
        if not target:
            return False
        if isinstance(target, str):
            t = target.strip().lower()
            return (obj.name == t or 
                    obj.name.replace('_', ' ') == t or 
                    t in getattr(obj, 'aliases', []) or 
                    t in getattr(obj, 'keywords', []))
        if isinstance(target, (list, tuple)):
            if obj.name in target:
                return True
            joined = " ".join(target).lower()
            if obj.name in joined or obj.name.replace('_', ' ') in joined:
                return True
            for a in getattr(obj, 'aliases', []):
                if a in joined:
                    return True
        return False

    # ─── Inventory ────────────────────────────────────────────────────────────

    def pick_up(self, room, possible_item):
        """
        Moves a matching item from the room into player inventory.
        Returns the item name if successful, False if not found.
        """
        for obj in room.inventory:
            if self._match_item(obj, possible_item):
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
            if self._match_item(obj, possible_item):
                self.inventory.remove(obj)
                room.inventory.append(obj)
                return obj.name
        return False

    def has_item(self, possible_item):
        """Checks if a matching item is in player inventory."""
        for obj in self.inventory:
            if (isinstance(possible_item, str) and (obj.name == possible_item or getattr(obj, 'id', None) == possible_item)) or self._match_item(obj, possible_item):
                return True
        return False

    def remove_item(self, possible_item):
        """
        Removes a matching item from player inventory.
        Returns the removed item object if successful, None if not found.
        """
        for obj in list(self.inventory):
            if (isinstance(possible_item, str) and (obj.name == possible_item or getattr(obj, 'id', None) == possible_item)) or self._match_item(obj, possible_item):
                self.inventory.remove(obj)
                return obj
        return None

    # ─── Item Interaction ─────────────────────────────────────────────────────

    def look(self, room, possible_item):
        """
        Returns the description of a matching item from inventory or room.
        Searches both so the player can look at items without picking them up.
        Returns False if not found.
        """
        for obj in self.inventory + room.inventory:
            if self._match_item(obj, possible_item):
                return obj.description
        return False

    def use(self, possible_item):
        """
        Returns the use_text of a matching item from player inventory.
        Called for solo use commands e.g. 'read map', 'wind music_box'.
        Returns False if item not found.
        """
        for obj in self.inventory:
            if self._match_item(obj, possible_item):
                return obj.use_text
        return False

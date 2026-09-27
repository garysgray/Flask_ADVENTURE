import re


class Player:
    """
    Holds all live player state — position, inventory, progress, and journal.
    Also handles movement, item interaction, and look logic.
    State is saved to the database after every command via PersistenceManager.
    """

    DIRECTIONS = ['north', 'south', 'east', 'west', 'up', 'down', 'portal']

    def __init__(self, game_map=None, location=None, inventory=None, unlocked_actions=None, locked_messages=None):
        self.id               = None
        self.pos_x            = 0
        self.pos_y            = 0
        self.level            = 0
        if isinstance(location, dict):
            self.pos_x = location.get("x", 0)
            self.pos_y = location.get("y", 0)
            self.level = location.get("floor", location.get("z", 0))
        self.inventory        = list(inventory) if inventory is not None else []
        self.unlocked_actions = set(unlocked_actions) if unlocked_actions is not None else None
        self.locked_messages  = dict(locked_messages) if locked_messages is not None else {}
        self.directions       = self.DIRECTIONS
        self.visited_rooms    = []
        self.completed_events = []
        self.journal          = []  # permanent — cannot be dropped or lost
        self.has_seen_intro   = False
        self.game_map         = game_map

        self.visited_room_names = []

    # ─── Action Unlocking & Gating ────────────────────────────────────────────

    def has_unlocked_action(self, action: str) -> bool:
        """
        Returns True if the action is currently unlocked for the player.
        If unlocked_actions is None (not specified in adventure), all actions are allowed.
        """
        if self.unlocked_actions is None:
            return True
        return action in self.unlocked_actions

    def unlock_action(self, action: str):
        """
        Unlocks a specific action for the player.
        If unlocked_actions is None (unrestricted), unlocking an action keeps everything allowed.
        """
        if self.unlocked_actions is None:
            return
        self.unlocked_actions.add(action)

    def get_locked_action_message(self, action: str) -> str:
        """
        Returns the configured locked message for an action or a genre-neutral default.
        """
        if self.locked_messages and action in self.locked_messages:
            return self.locked_messages[action]
        return f"You haven't learned how to {action.replace('_', ' ')} yet."

    # ─── Location ─────────────────────────────────────────────────────────────

    def get_location(self):
        return {'X': self.pos_x, 'Y': self.pos_y, 'floor': self.level}

    def record_current_room(self, room=None):
        """
        Records the player's current location and room name into visited lists.
        Coordinates are recorded exactly as tuple: (self.level, self.pos_y, self.pos_x).
        Guards against missing room and avoids duplicate entries.
        """
        if room is None and self.game_map:
            try:
                if 0 <= self.level < len(self.game_map):
                    floor = self.game_map[self.level]
                    if 0 <= self.pos_y < len(floor) and 0 <= self.pos_x < len(floor[self.pos_y]):
                        room = floor[self.pos_y][self.pos_x]
            except Exception:
                room = None

        if room is None or not hasattr(room, 'name'):
            return

        pos = (self.level, self.pos_y, self.pos_x)
        # Check against both tuple and list representations (from JSON persistence)
        pos_list = [self.level, self.pos_y, self.pos_x]
        if pos not in self.visited_rooms and pos_list not in self.visited_rooms:
            self.visited_rooms.append(pos)
        if room.name not in self.visited_room_names:
            self.visited_room_names.append(room.name)

    # ─── Movement ─────────────────────────────────────────────────────────────

    def move(self, dir, room, level_max):
        """
        Moves the player in the given direction.
        Checks locked exits first to prevent moving through locked passages.
        Checks exit_destinations next for custom portals, stairs, or event-defined exits.
        Handles default vertical movement (up/down) between floors at the same (x, y) coordinates.
        Falls back to grid movement for same-floor cardinal directions.
        Returns True if the move succeeded, False if blocked.
        Records the visit upon successful movement.
        """
        if dir not in room.exits and dir not in room.exit_destinations:
            return False

        if hasattr(room, 'locked_exits') and room.locked_exits and dir in room.locked_exits:
            return False

        moved = False

        # teleport, portal, or stair exit defined in exit_destinations
        if dir in room.exit_destinations:
            dest       = room.exit_destinations[dir]
            self.level = dest['floor']
            self.pos_x = dest['x']
            self.pos_y = dest['y']
            moved = True

        # default vertical movement (up / down) between floors at same (x, y)
        elif dir == 'up' and dir in room.exits:
            target_level = self.level + 1
            if target_level < len(self.game_map):
                target_floor = self.game_map[target_level]
                if self.pos_y < len(target_floor) and self.pos_x < len(target_floor[self.pos_y]):
                    if target_floor[self.pos_y][self.pos_x] is not None:
                        self.level = target_level
                        moved = True

        elif dir == 'down' and dir in room.exits:
            target_level = self.level - 1
            if 0 <= target_level < len(self.game_map):
                target_floor = self.game_map[target_level]
                if self.pos_y < len(target_floor) and self.pos_x < len(target_floor[self.pos_y]):
                    if target_floor[self.pos_y][self.pos_x] is not None:
                        self.level = target_level
                        moved = True

        # same-floor grid movement
        else:
            floor = self.game_map[self.level]
            row   = floor[self.pos_y]

            moves = {
                'north': lambda: self.pos_y > 0 and self.pos_x < len(floor[self.pos_y - 1]) and floor[self.pos_y - 1][self.pos_x] is not None,
                'south': lambda: self.pos_y + 1 < len(floor) and self.pos_x < len(floor[self.pos_y + 1]) and floor[self.pos_y + 1][self.pos_x] is not None,
                'east':  lambda: self.pos_x + 1 < len(row) and floor[self.pos_y][self.pos_x + 1] is not None,
                'west':  lambda: self.pos_x > 0 and floor[self.pos_y][self.pos_x - 1] is not None,
            }

            if dir in moves and moves[dir]():
                if dir == 'north': self.pos_y -= 1
                if dir == 'south': self.pos_y += 1
                if dir == 'east':  self.pos_x += 1
                if dir == 'west':  self.pos_x -= 1
                moved = True

        if moved:
            self.record_current_room()
            return True

        return False

    # ─── Matching Helper ──────────────────────────────────────────────────────

    def _match_item(self, obj, target):
        """
        Checks if an item object matches target string, list, or alias using
        exact matching or whole-word token matching.
        """
        if not target:
            return False

        if isinstance(target, str):
            target_str = target.strip().lower()
        elif isinstance(target, (list, tuple)):
            target_str = " ".join(str(w) for w in target).strip().lower()
        else:
            return False

        if not target_str:
            return False

        # Gather candidate names/aliases and keyword candidates separately
        name_alias_candidates = set()
        if hasattr(obj, 'name') and obj.name:
            name_alias_candidates.add(str(obj.name).lower())
            name_alias_candidates.add(str(obj.name).replace('_', ' ').lower())

        for alias in getattr(obj, 'aliases', []) or []:
            if alias:
                name_alias_candidates.add(str(alias).lower())
                name_alias_candidates.add(str(alias).replace('_', ' ').lower())

        keyword_candidates = set()
        for kw in getattr(obj, 'keywords', []) or []:
            if kw:
                keyword_candidates.add(str(kw).lower())
                keyword_candidates.add(str(kw).replace('_', ' ').lower())

        target_normalized = target_str.replace('_', ' ')

        # 1. Exact match against any name, alias, or keyword candidate
        all_candidates = name_alias_candidates | keyword_candidates
        if target_str in all_candidates or target_normalized in all_candidates:
            return True

        # 2. Whole-word phrase matching only for names and aliases (never keywords)
        target_text_spaced = f" {target_normalized} "
        for cand in name_alias_candidates:
            cand_normalized = cand.replace('_', ' ')
            if f" {cand_normalized} " in target_text_spaced:
                return True

        return False

    # ─── Inventory ────────────────────────────────────────────────────────────

    def pick_up(self, room, possible_item):
        """
        Moves a matching item from the room into player inventory.
        Returns the item name if successful, False if not found.
        """
        if not room or not hasattr(room, 'inventory') or not room.inventory:
            return False
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
        if not room or not hasattr(room, 'inventory') or room.inventory is None:
            return False
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
        room_inv = room.inventory if (room and hasattr(room, 'inventory') and room.inventory) else []
        for obj in self.inventory + room_inv:
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

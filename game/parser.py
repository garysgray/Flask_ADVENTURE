import re

class Parser:
    """
    Converts raw text input into a structured command dict.
    Passed to ActionHandler.execute() via Controller.run_the_cmd().

    Decision tree (first match wins):
        1. Empty input
        2. Single direction word         → move
        3. Move word or direction found  → move
        4. Connector word found          → use item with target
        5. 'journal' in words            → journal
        6. Solo keyword + item name      → use item
        7. Keyword commands              → pickup / drop / look / use / help / 
        8. Nothing matched               → unknown command

    OBJ types returned:
        str  — empty string, for commands with no target e.g. help
        list — word list, for move / pickup / drop / look / use [item]
        dict — {"item": str, "target": str}, for use [item] with [target]
    """

    DIRECTIONS   = {'north', 'south', 'east', 'west', 'up', 'down'}
    MOVE_WORDS   = {'go', 'move', 'walk', 'run', 'head'}
    PICKUP_WORDS = {'get', 'pickup', 'take', 'grab'}
    CONNECTORS   = {'with', 'into', 'onto'}
    STRIP_WORDS  = {'use', 'drop', 'throw', 'put', 'place', 'open', 'unlock'}

    def __init__(self, controller):
        self.ctrl = controller

    # ─── Lookup Helpers ───────────────────────────────────────────────────────
    # These build lists the parser searches to identify words in player input.

    def _get_player_item_names(self):
        """Item names currently in player inventory."""
        return [i.name for i in self.ctrl.player.inventory]

    def _get_room_targets(self):
        """Words wrapped in <em> tags in the current room description."""
        room = self.ctrl.get_room()
        if room:
            return re.findall(r'<em>(.*?)</em>', room.description)
        return []

    def _get_event_targets(self):
        """
        Target words from all ItemUsedWithEvents e.g. 'well', 'box', 'frame'.
        These are non-item targets that only exist in event definitions,
        not in item recipes or room inventory.
        """
        return [event.target for event in self.ctrl.map.event_recipes if hasattr(event, 'target')]

    def _find_any(self, words):
        """
        Scans a list of words and returns the first one that maps to something
        known in the game. Used to extract item and target names from player input.

        Search order (first match wins):
            1. Event targets    — 'well', 'box', 'frame' etc.
            2. Player inventory — items the player is carrying
            3. Room inventory   — items sitting in the current room
            4. Item recipes     — any item that exists in the game
            5. Room em tags     — words highlighted as interactable in descriptions
            6. Action keywords  — e.g. 'light' maps to lantern via action_keywords in YAML
        """
        player_items  = self._get_player_item_names()
        room_items    = [i.name for i in self.ctrl.get_room().inventory]
        room_targets  = self._get_room_targets()
        event_targets = self._get_event_targets()

        for word in words:
            if word in event_targets:   return word
        for word in words:
            if word in player_items:    return word
        for word in words:
            if word in room_items:      return word
        for word in words:
            if word in self.ctrl.map.item_recipes: return word
        for word in words:
            if word in room_targets:    return word
        for word in words:
            for name, data in self.ctrl.map.item_recipes.items():
                if word in data.get('action_keywords', []):
                    return name
        return None

    # ─── Main Parse ───────────────────────────────────────────────────────────

    def parse(self, user_input):
        words = user_input.lower().strip().split()
        if not words:
            return {"CMD": "", "OBJ": ""}

        # ── 1. Single direction word e.g. "north" ─────────────────────────────
        if len(words) == 1 and words[0] in self.DIRECTIONS:
            return {"CMD": "move", "OBJ": words}

        # ── 2. Move command e.g. "go north", "walk south" ─────────────────────
        if words[0] in self.MOVE_WORDS or any(w in self.DIRECTIONS for w in words):
            return {"CMD": "move", "OBJ": words}

        # ── 3. Connector command e.g. "light lantern with matches" ────────────
        # Splits input on the connector, finds item and target on each side.
        # Checks event recipes first to get the correct item/target order,
        # then falls back to inventory check if no event match found.
        connector = next((c for c in self.CONNECTORS if c in words), None)
        if connector:
            conn_i      = words.index(connector)
            left_words  = [w for w in words[:conn_i]   if w not in self.STRIP_WORDS]
            right_words = [w for w in words[conn_i+1:] if w not in self.STRIP_WORDS]
            left_name   = self._find_any(left_words)
            right_name  = self._find_any(right_words)

            if left_name and right_name:
                player_items = self._get_player_item_names()

                # check event recipes to resolve correct item/target order
                for event in self.ctrl.map.event_recipes:
                    if hasattr(event, 'item') and hasattr(event, 'target'):
                        if event.item == left_name and event.target == right_name:
                            return {"CMD": "use", "OBJ": {"item": left_name,  "target": right_name}}
                        if event.item == right_name and event.target == left_name:
                            return {"CMD": "use", "OBJ": {"item": right_name, "target": left_name}}

                # fallback — whichever side is in inventory is the item
                if left_name in player_items:
                    return {"CMD": "use", "OBJ": {"item": left_name,  "target": right_name}}
                if right_name in player_items:
                    return {"CMD": "use", "OBJ": {"item": right_name, "target": left_name}}
                return {"CMD": "use", "OBJ": {"item": left_name, "target": right_name}}

        # ── 4. Journal ────────────────────────────────────────────────────────
        # Checked before solo keywords so "read journal" doesn't accidentally
        # match "read" as a solo keyword defined on another item.
        if 'journal' in words:
            return {"CMD": "journal", "OBJ": words}

        # ── 5. Solo keyword + item name e.g. "read map", "wind music_box" ─────
        # Checks solo_keywords defined per item in game_data.yaml.
        # Word order doesn't matter — "map read" works the same as "read map".
        item_names = self._get_player_item_names()
        for word in words:
            remaining = [w for w in words if w != word]
            for name in item_names:
                if name in remaining:
                    keywords = self.ctrl.map.item_recipes.get(name, {}).get('solo_keywords', [])
                    if word in keywords:
                        return {"CMD": "use", "OBJ": [name]}

        # ── 6. Keyword commands ───────────────────────────────────────────────
        for word in words:
            if word in self.PICKUP_WORDS:   return {"CMD": "pickup",    "OBJ": words}
            if word == "drop":              return {"CMD": "drop",      "OBJ": words}
            if word == "look":              return {"CMD": "look",      "OBJ": words}
            if word == "use":               return {"CMD": "use",       "OBJ": words}
            if word == "help":              return {"CMD": "help",      "OBJ": ""}
            if word == "changedesc":        return {"CMD": "changedesc","OBJ": words}

        # ── 7. Nothing matched ────────────────────────────────────────────────
        return {"CMD": user_input, "OBJ": ""}


import re

class Parser:
    DIRECTIONS   = {'north', 'south', 'east', 'west', 'up', 'down'}
    MOVE_WORDS   = {'go', 'move', 'walk', 'run', 'head'}
    PICKUP_WORDS = {'get', 'pickup', 'take', 'grab'}
    CONNECTORS   = {'with', 'into', 'onto'}
    STRIP_WORDS  = {'use', 'drop', 'throw', 'put', 'place', 'open', 'unlock'}

    def __init__(self, controller):
        self.ctrl = controller

    def _get_room_targets(self):
        """Returns list of em-tagged words from current room description."""
        room = self.ctrl.get_room()
        if room:
            return re.findall(r'<em>(.*?)</em>', room.description)
        return []

    def _get_player_item_names(self):
        """Returns list of item names in player inventory."""
        return [i.name for i in self.ctrl.player.inventory]

    def _find_any(self, words):
        """
        Given a list of words, returns the first match found in:
        1. Player inventory item names
        2. Item recipe names
        3. Room em tags
        4. Item keywords
        Returns (name, source) where source is 'inventory', 'recipe', 'emtag' or 'keyword'
        """
        player_items  = self._get_player_item_names()
        room_targets  = self._get_room_targets()

        for word in words:
            if word in player_items:
                return word, 'inventory'
        for word in words:
            if word in self.ctrl.map.item_recipes:
                return word, 'recipe'
        for word in words:
            if word in room_targets:
                return word, 'emtag'
        for word in words:
            for name, data in self.ctrl.map.item_recipes.items():
                if word in data.get('keywords', []):
                    return name, 'keyword'
        return None, None

    def parse(self, user_input):
        words = user_input.lower().strip().split()
        if not words:
            return {"CMD": "", "OBJ": ""}

        # single direction word
        if len(words) == 1 and words[0] in self.DIRECTIONS:
            return {"CMD": "move", "OBJ": words}

        # move command
        if words[0] in self.MOVE_WORDS or any(w in self.DIRECTIONS for w in words):
            return {"CMD": "move", "OBJ": words}

        # connector command — split on with/into/onto
        # always resolves so inventory item = item, everything else = target
        connector = next((c for c in self.CONNECTORS if c in words), None)
        if connector:
            conn_i       = words.index(connector)
            left_words   = [w for w in words[:conn_i]  if w not in self.STRIP_WORDS]
            right_words  = [w for w in words[conn_i+1:] if w not in self.STRIP_WORDS]

            left_name,  left_src  = self._find_any(left_words)
            right_name, right_src = self._find_any(right_words)

            if left_name and right_name:
                # whichever side has the inventory item is the item being used
                player_items = self._get_player_item_names()
                if left_name in player_items:
                    return {"CMD": "use", "OBJ": {"item": left_name, "target": right_name}}
                else:
                    return {"CMD": "use", "OBJ": {"item": right_name, "target": left_name}}

        # keyword commands
        for word in words:
            if word in self.PICKUP_WORDS:
                return {"CMD": "pickup",    "OBJ": words}
            if word == "drop":
                return {"CMD": "drop",      "OBJ": words}
            if word == "look":
                return {"CMD": "look",      "OBJ": words}
            if word == "use":
                return {"CMD": "use",       "OBJ": words}
            if word == "help":
                return {"CMD": "help",      "OBJ": ""}
            if word == "changedesc":
                return {"CMD": "changedesc","OBJ": words}

        return {"CMD": user_input, "OBJ": ""}
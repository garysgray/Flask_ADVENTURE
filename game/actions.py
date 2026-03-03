class ActionHandler:
    def __init__(self, controller):
        self.ctrl = controller

    # ─── Help ─────────────────────────────────────────────────────────────────

    def help(self):
        return "Commands: north/south/east/west/up/down, get [item], drop [item], look [item], use [item] with [target], read journal"

    # ─── Movement ─────────────────────────────────────────────────────────────

    def move_player(self, dir):
        if self.ctrl.player.move(dir, self.ctrl.get_room(), len(self.ctrl.map.game_map)):
            return f"You came from the {dir}."
        else:
            if dir == "":
                return "What direction?"
            return f"You cant go {dir}."

    # ─── Inventory ────────────────────────────────────────────────────────────

    # def has_item(self, name):
    #     """Returns True if the named item is in the player's inventory."""
    #     for i in self.ctrl.player.inventory:
    #         if i.name == name:
    #             return True
    #     return False

    # def pick_up(self, possible_item):
    #     """Moves an item from the current room into player inventory."""
    #     item_name = self.ctrl.player.pick_up(self.ctrl.get_room(), possible_item)
    #     if item_name:
    #         return f"You picked up a {item_name}"
    #     else:
    #         if isinstance(possible_item, list):
    #             return f"I cant pick up {possible_item[1]}"
    #         return "Get What?"

    # def drop(self, possible_item):
    #     """Moves an item from player inventory into the current room."""
    #     item_name = self.ctrl.player.drop(self.ctrl.get_room(), possible_item)
    #     if item_name:
    #         return f"You dropped a {item_name}"
    #     else:
    #         if isinstance(possible_item, list):
    #             return f"I cant drop {possible_item[1]}"
    #         return "Drop What?"

    # # ─── Look ─────────────────────────────────────────────────────────────────

    # def look(self, possible_item):
    #     """Returns the description of an item in the room or player inventory."""
    #     item_info = self.ctrl.player.look(self.ctrl.get_room(), possible_item)
    #     if item_info:
    #         return item_info
    #     else:
    #         if isinstance(possible_item, list):
    #             return f"I dont see {possible_item[1]}"
    #         return "Look at What?"

    # # ─── Use ──────────────────────────────────────────────────────────────────

    # def use_item(self, possible_item):
    #     """
    #     Handles both single item use and item+target use.

    #     Dict input  — use [item] with [target]:
    #         1. Check if this event was already completed — return already-done message if so.
    #            Must happen before inventory check because item may have been removed (e.g. locket).
    #         2. Check player has the item.
    #         3. Check if any event fires for this item+target combination.
    #         4. Fall back to "can't use" if nothing matched.

    #     List input  — use [item]:
    #         Uses the item's current state use_text via player.use().
    #     """
    #     if isinstance(possible_item, dict):
    #         item   = possible_item['item']
    #         target = possible_item['target']

    #         # already done check must come before has_item
    #         # because item may have been removed from inventory after firing
    #         already_done = self.ctrl.check_use_with_events_already_done(item, target)
    #         if already_done:
    #             return already_done, None

    #         if not self.has_item(item):
    #             return f"You don't have {item}.", None

    #         event_result = self.ctrl.check_use_with_events(item, target)
    #         if event_result:
    #             return self.help(), event_result

    #         return f"You can't use {item} with {target}.", None

    #     # solo use — use [item]
    #     words     = [w for w in possible_item if w != 'use']
    #     item_name = words[0] if words else None
    #     if not item_name:
    #         return "Use what?", None
    #     if not self.has_item(item_name):
    #         return f"You don't have {item_name}.", None
    #     result = self.ctrl.player.use(possible_item)
    #     return (result if result else f"Nothing happens with {item_name}."), None

    # ─── Inventory ────────────────────────────────────────────────────────────

    def has_item(self, name):
        """Returns True if the named item is in the player's inventory."""
        for i in getattr(self.ctrl.player, "inventory", []):
            if getattr(i, "name", None) == name:
                return True
        return False

    def pick_up(self, possible_item):
        """Moves an item from the current room into player inventory."""
        try:
            item_name = self.ctrl.player.pick_up(self.ctrl.get_room(), possible_item)
        except Exception:
            item_name = None

        if item_name:
            return f"You picked up a {item_name}"
        else:
            # safely get the item name if it's a list
            if isinstance(possible_item, list) and len(possible_item) > 1:
                return f"I can't pick up {possible_item[1]}"
            return "Get What?"

    def drop(self, possible_item):
        """Moves an item from player inventory into the current room."""
        try:
            item_name = self.ctrl.player.drop(self.ctrl.get_room(), possible_item)
        except Exception:
            item_name = None

        if item_name:
            return f"You dropped a {item_name}"
        else:
            if isinstance(possible_item, list) and len(possible_item) > 1:
                return f"I can't drop {possible_item[1]}"
            return "Drop What?"

    # ─── Look ─────────────────────────────────────────────────────────────────

    def look(self, possible_item):
        """Returns the description of an item in the room or player inventory."""
        try:
            item_info = self.ctrl.player.look(self.ctrl.get_room(), possible_item)
        except Exception:
            item_info = None

        if item_info:
            return item_info
        else:
            if isinstance(possible_item, list) and len(possible_item) > 1:
                return f"I don't see {possible_item[1]}"
            return "Look at What?"

    # ─── Use ──────────────────────────────────────────────────────────────────

    def use_item(self, possible_item):
        """
        Handles both single item use and item+target use.
        Fully safe against empty or malformed input.
        """
        # dict input → use [item] with [target]
        if isinstance(possible_item, dict):
            item   = possible_item.get('item')
            target = possible_item.get('target')

            if not item or not target:
                return "Use what with what?", None

            already_done = self.ctrl.check_use_with_events_already_done(item, target)
            if already_done:
                return already_done, None

            if not self.has_item(item):
                return f"You don't have {item}.", None

            event_result = self.ctrl.check_use_with_events(item, target)
            if event_result:
                return self.help(), event_result

            return f"You can't use {item} with {target}.", None

        # list or string input → use [item]
        words = []
        if isinstance(possible_item, list):
            words = [w for w in possible_item if w != 'use']
        elif isinstance(possible_item, str):
            words = [possible_item] if possible_item != 'use' else []

        item_name = words[0] if words else None
        if not item_name:
            return "Use what?", None

        if not self.has_item(item_name):
            return f"You don't have {item_name}.", None

        try:
            result = self.ctrl.player.use(possible_item)
        except Exception:
            result = None

        return (result if result else f"Nothing happens with {item_name}."), None

    # ─── Journal ──────────────────────────────────────────────────────────────

    def read_journal(self):
        """
        Journal display is handled entirely in the template via the journal panel.
        The SHOW_JOURNAL flag in room_info triggers the panel to auto-open.
        This method returns an empty string so nothing appears in CMD_RESPONSE.
        """
        return ""

    # ─── Dev Tools ────────────────────────────────────────────────────────────

    def change_room_description(self, possible_item):
        """Dev command — manually override the current room's description."""
        room = self.ctrl.get_room()
        if isinstance(possible_item, list):
            words = [word for word in possible_item if word != 'changedesc']
            new_description = ' '.join(words)
        else:
            new_description = possible_item
        room.description = new_description
        return f"The {room.name} room's appearance has changed!"

    # ─── Dispatch ─────────────────────────────────────────────────────────────

    def execute(self, cmd, possible_item):
        """
        Routes a parsed command to the appropriate handler.
        Returns a tuple of (cmd_response, event_message).
        event_message is None for most commands, only set by use_item when an event fires.
        """
        dispatch = {
            'drop':       lambda: (self.drop(possible_item),            None),
            'pickup':     lambda: (self.pick_up(possible_item),         None),
            'look':       lambda: (self.look(possible_item),            None),
            'help':       lambda: (self.help(),                         None),
            'use':        lambda: self.use_item(possible_item),
            'changedesc': lambda: (self.change_room_description(possible_item), None),
            'move':       lambda: (self.move_player(next((d for d in self.ctrl.player.directions if d in possible_item), "")), None),
            'journal':    lambda: (self.read_journal(),                 None),
        }

        # single direction word typed without a move command e.g. "north"
        if cmd in self.ctrl.player.directions:
            return self.move_player(cmd), None

        handler = dispatch.get(cmd)
        if handler:
            return handler()

        return f"I don't understand: {cmd}. Try 'help' for commands.", None
class ActionHandler:
    def __init__(self, controller):
        self.ctrl = controller

    # ─── Help ─────────────────────────────────────────────────────────────────

    def help(self):
        return "Commands: north/south/east/west/up/down, get [item], drop [item], look [item], use [item] with [target], read journal"

    # ─── Movement ─────────────────────────────────────────────────────────────

    def _extract_direction(self, possible_item):
        """Extracts canonical direction string from list or string input."""
        if isinstance(possible_item, list):
            for d in self.ctrl.player.directions:
                if d in possible_item:
                    return d
        elif isinstance(possible_item, str):
            for d in self.ctrl.player.directions:
                if d == possible_item or d in possible_item.split():
                    return d
        return ""

    def move_player(self, dir):
        if self.ctrl.player.move(dir, self.ctrl.get_room(), len(self.ctrl.map.game_map)):
            return f"You came from the {dir}."
        else:
            if dir == "":
                return "What direction?"
            return f"You cant go {dir}."

    # ─── Inventory ────────────────────────────────────────────────────────────

    def has_item(self, name):
        """Returns True if the named item or alias is in the player's inventory."""
        if not name:
            return False
        clean = name.strip().lower() if isinstance(name, str) else ""
        for i in getattr(self.ctrl.player, "inventory", []):
            if i.name == clean or i.name.replace('_', ' ') == clean:
                return True
            if clean in getattr(i, "aliases", []) or clean in getattr(i, "keywords", []):
                return True
        return False

    def show_inventory(self):
        """Returns a formatted list of carried items."""
        inventory = getattr(self.ctrl.player, "inventory", [])
        if not inventory:
            return "You are not carrying anything."
        names = [getattr(i, 'display_name', i.name.replace('_', ' ')) for i in inventory]
        return f"You are carrying: {', '.join(names)}."

    def pick_up(self, possible_item):
        """Moves an item from the current room into player inventory."""
        if not possible_item:
            return "Take what?"

        target = possible_item
        if isinstance(possible_item, list):
            words = [w for w in possible_item if w not in {'take', 'get', 'pick', 'up', 'the', 'a', 'an'}]
            target = " ".join(words) if words else ""

        if not target:
            return "Take what?"

        if self.has_item(target):
            display = target.replace('_', ' ')
            return f"You are already carrying the {display}."

        try:
            item_name = self.ctrl.player.pick_up(self.ctrl.get_room(), target)
        except Exception:
            item_name = None

        if item_name:
            return f"You picked up the {item_name.replace('_', ' ')}."
        else:
            display = target.replace('_', ' ')
            if target in getattr(self.ctrl.map, 'item_recipes', {}):
                return f"I don't see any {display} here."
            return f"I don't see that here."

    def drop(self, possible_item):
        """Moves an item from player inventory into the current room."""
        if not possible_item:
            return "Drop what?"

        target = possible_item
        if isinstance(possible_item, list):
            words = [w for w in possible_item if w not in {'drop', 'put', 'down', 'the', 'a', 'an'}]
            target = " ".join(words) if words else ""

        if not target:
            return "Drop what?"

        try:
            item_name = self.ctrl.player.drop(self.ctrl.get_room(), target)
        except Exception:
            item_name = None

        if item_name:
            return f"You dropped the {item_name.replace('_', ' ')}."
        else:
            display = target.replace('_', ' ')
            for obj in self.ctrl.get_room().inventory:
                if obj.name == target or obj.name.replace('_', ' ') == target:
                    return f"You aren't carrying the {display}."
            return "You don't have that."

    # ─── Look ─────────────────────────────────────────────────────────────────

    def look(self, possible_item):
        """Returns the description of the room, or an item/fixture in the room/inventory."""
        if not possible_item or possible_item in ("", [], ["look"], ["around"]):
            room = self.ctrl.get_room()
            return room.description if room else "You look around."

        target = possible_item
        if isinstance(possible_item, list):
            words = [w for w in possible_item if w not in {'look', 'at', 'in', 'inside', 'examine', 'inspect', 'the', 'a', 'an'}]
            target = " ".join(words) if words else ""

        if not target:
            room = self.ctrl.get_room()
            return room.description if room else "You look around."

        # 1. Check player inventory and room ground items
        try:
            item_info = self.ctrl.player.look(self.ctrl.get_room(), target)
        except Exception:
            item_info = None

        if item_info:
            return item_info

        # Normalize target for fixture lookup
        target_clean = target.strip().lower()
        target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
        for canonical_target, aliases in target_aliases.items():
            if target_clean == canonical_target or target_clean in aliases or target_clean.replace('_', ' ') in aliases:
                target_clean = canonical_target
                break

        # 2. Check current room fixtures directly
        current_room = self.ctrl.get_room()
        if current_room and hasattr(current_room, 'fixtures') and current_room.fixtures:
            # Check canonical fixture name
            if target_clean in current_room.fixtures:
                return current_room.fixtures[target_clean].get_examine_text()

            # Check matching by display_name or aliases
            for fix_name, fixture in current_room.fixtures.items():
                if fix_name == target_clean or fixture.display_name.lower() == target_clean:
                    return fixture.get_examine_text()
                fix_aliases = target_aliases.get(fix_name, [])
                if target_clean in fix_aliases or target.strip().lower() in fix_aliases:
                    return fixture.get_examine_text()

        # 3. Check for ECA solo event with action in ('examine', 'look')
        eval_result = self.ctrl.evaluate_solo(target_clean, action='examine')
        if eval_result['status'] == 'success':
            return eval_result['message']
        elif eval_result['status'] in ('wrong_room', 'missing_prerequisite'):
            return eval_result['message']

        # 4. Check general target aliases fallback
        for canonical_target, aliases in target_aliases.items():
            if target_clean == canonical_target or target_clean in aliases:
                return f"You inspect the {canonical_target.replace('_', ' ')}. It is integrated into the facility."

        return "You don't see that here."

    # ─── Read ─────────────────────────────────────────────────────────────────

    def read_item(self, possible_item):
        """Handles reading readable items, inscriptions, or the journal."""
        if not possible_item:
            return "Read what?"

        if possible_item in ("journal", ["journal"]):
            return self.read_journal()

        target = possible_item
        if isinstance(possible_item, list):
            words = [w for w in possible_item if w not in {'read', 'the', 'a', 'an'}]
            target = " ".join(words) if words else ""

        if not target:
            return "Read what?"

        target_clean = target.strip().lower()
        target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
        for canonical_t, aliases in target_aliases.items():
            if target_clean == canonical_t or target_clean in aliases or target_clean.replace('_', ' ') in aliases:
                target_clean = canonical_t
                break

        # Check for ECA solo event with action='read' or action=None
        eval_result = self.ctrl.evaluate_solo(target_clean, action='read')
        if eval_result['status'] == 'success':
            return eval_result['message']
        elif eval_result['status'] in ('wrong_room', 'missing_prerequisite'):
            return eval_result['message']

        # Check current room fixtures
        current_room = self.ctrl.get_room()
        if current_room and hasattr(current_room, 'fixtures') and current_room.fixtures:
            if target_clean in current_room.fixtures:
                return current_room.fixtures[target_clean].get_examine_text()

        # Try item use_text if player has the item
        try:
            use_text = self.ctrl.player.use(target)
            if use_text:
                return use_text
        except Exception:
            pass

        # Try item description
        try:
            desc = self.ctrl.player.look(self.ctrl.get_room(), target)
            if desc:
                return desc
        except Exception:
            pass

        # Check room features
        if target_clean in target_aliases or (
            current_room and hasattr(current_room, 'description') and 
            (target_clean in current_room.description.lower() or target_clean.replace('_', ' ') in current_room.description.lower())
        ):
            return f"There is nothing written on the {target_clean.replace('_', ' ')}."

        return "You don't have that to read."

    # ─── Use ──────────────────────────────────────────────────────────────────

    def use_item(self, possible_item):
        """
        Handles both single item / room fixture use and item+target use.
        Fully safe against empty or malformed input.
        """
        # dict input with 'target' → use [item] with [target]
        if isinstance(possible_item, dict) and 'target' in possible_item:
            item   = possible_item.get('item')
            target = possible_item.get('target')

            if not item or not target:
                return "Use what with what?", None

            # Resolve canonical item name if player has it under an alias
            for inv_item in getattr(self.ctrl.player, "inventory", []):
                if (inv_item.name == item or 
                    inv_item.name.replace('_', ' ') == item or 
                    item in getattr(inv_item, 'aliases', [])):
                    item = inv_item.name
                    break

            # Resolve canonical target name if target matches target_aliases
            target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
            for canonical_t, aliases in target_aliases.items():
                if target == canonical_t or target in aliases:
                    target = canonical_t
                    break

            # If player doesn't have the parsed item, but has the parsed target in inventory, swap roles
            if not self.has_item(item) and self.has_item(target):
                item, target = target, item

            already_done = self.ctrl.check_use_with_events_already_done(item, target)
            if not already_done and self.has_item(target):
                already_done = self.ctrl.check_use_with_events_already_done(target, item)
            if already_done:
                return already_done, None

            if not self.has_item(item):
                item_display = item.replace('_', ' ')
                return f"You don't have the {item_display}.", None

            eval_result = self.ctrl.evaluate_use_with(item, target)
            if eval_result['status'] == 'success':
                return self.help(), eval_result['message']

            return eval_result['message'], None

        # Solo interaction: extract target and optional action
        action = None
        item_query = ""
        if isinstance(possible_item, dict):
            item_query = possible_item.get('item', '')
            action = possible_item.get('action')
        elif isinstance(possible_item, list):
            words = [w for w in possible_item if w not in {'use', 'the', 'a', 'an'}]
            item_query = words[0] if words else ""
        elif isinstance(possible_item, str):
            item_query = possible_item if possible_item != 'use' else ""

        if not item_query:
            return "Use what?", None

        # Resolve against carried items
        matched_item = None
        for inv_item in getattr(self.ctrl.player, "inventory", []):
            if (inv_item.name == item_query or 
                inv_item.name.replace('_', ' ') == item_query or 
                item_query in getattr(inv_item, 'aliases', []) or 
                item_query in getattr(inv_item, 'keywords', [])):
                matched_item = inv_item
                item_query = inv_item.name
                break

        # Resolve against target aliases
        target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
        for canonical_t, aliases in target_aliases.items():
            if item_query == canonical_t or item_query in aliases or item_query.replace('_', ' ') in aliases:
                item_query = canonical_t
                break

        # 1. Check if an already-done solo event exists
        already_done = self.ctrl.check_solo_events_already_done(item_query, action=action)
        if already_done:
            return already_done, None

        # 2. Check for active ECA solo event
        eval_result = self.ctrl.evaluate_solo(item_query, action=action)
        if eval_result['status'] == 'success':
            return self.help(), eval_result['message']
        elif eval_result['status'] in ('wrong_room', 'missing_prerequisite'):
            return eval_result['message'], None

        # 3. Fallback: No ECA event matched
        if matched_item:
            result = matched_item.use_text
            return (result if result else f"Nothing happens with the {matched_item.name.replace('_', ' ')}."), None

        current_room = self.ctrl.get_room()
        if current_room:
            # Check if item is in current room inventory
            for room_item in current_room.inventory:
                if (room_item.name == item_query or 
                    room_item.name.replace('_', ' ') == item_query or 
                    item_query in getattr(room_item, 'aliases', []) or 
                    item_query in getattr(room_item, 'keywords', [])):
                    return f"You need to pick up the {room_item.name.replace('_', ' ')} first.", None

            # Check if it's a valid room fixture
            is_fixture = False
            if hasattr(current_room, 'fixtures') and (item_query in current_room.fixtures):
                is_fixture = True
            elif item_query in target_aliases:
                is_fixture = True
            elif hasattr(current_room, 'description') and (
                item_query in current_room.description.lower() or 
                item_query.replace('_', ' ') in current_room.description.lower()
            ):
                is_fixture = True

            if is_fixture:
                display_name = item_query.replace('_', ' ')
                return f"Nothing happens with the {display_name}.", None

        return f"You don't have the {item_query.replace('_', ' ')}.", None

    # ─── Journal ──────────────────────────────────────────────────────────────

    def read_journal(self):
        return ""

    # ─── Dev Tools ────────────────────────────────────────────────────────────

    def change_room_description(self, possible_item):
        room = self.ctrl.get_room()
        if isinstance(possible_item, list):
            words = [word for word in possible_item if word != 'changedesc']
            new_description = ' '.join(words)
        else:
            new_description = possible_item
        room.description = new_description
        room_title = getattr(room, 'display_name', room.name.replace('_', ' '))
        return f"The {room_title} room's appearance has changed!"

    # ─── Dispatch ─────────────────────────────────────────────────────────────

    def execute(self, cmd, possible_item):
        dispatch = {
            'drop':       lambda: (self.drop(possible_item),            None),
            'pickup':     lambda: (self.pick_up(possible_item),         None),
            'look':       lambda: (self.look(possible_item),            None),
            'read':       lambda: (self.read_item(possible_item),       None),
            'inventory':  lambda: (self.show_inventory(),               None),
            'respond':    lambda: (possible_item if isinstance(possible_item, str) else " ".join(possible_item), None),
            'help':       lambda: (self.help(),                         None),
            'use':        lambda: self.use_item(possible_item),
            'changedesc': lambda: (self.change_room_description(possible_item), None),
            'move':       lambda: (self.move_player(self._extract_direction(possible_item)), None),
            'journal':    lambda: (self.read_journal(),                 None),
            'wait':       lambda: ("Time passes...",                    None),
        }

        if cmd in self.ctrl.player.directions:
            return self.move_player(cmd), None

        handler = dispatch.get(cmd)
        if handler:
            return handler()

        return f"I don't understand: {cmd}. Try 'help' for commands.", None

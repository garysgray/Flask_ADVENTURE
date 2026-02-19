class ActionHandler:
    def __init__(self, controller):
        self.ctrl = controller

    def help(self):
        return "CMD Examples: Go south, south, look book, use book, get book, drop book, help"

    def move_player(self, dir):
        if self.ctrl.player.move(dir, self.ctrl.get_room(), len(self.ctrl.map.game_map)):
            return f"You came from the {dir}."
        else:
            if dir == "":
                return "What direction?"
            return f"You cant go {dir}."

    def drop(self, possible_item):
        item_name = self.ctrl.player.drop(self.ctrl.get_room(), possible_item)
        if item_name:
            return f"You dropped a {item_name}"
        else:
            if isinstance(possible_item, list):
                return f"I cant drop {possible_item[1]}"
            return "Drop What?"

    def pick_up(self, possible_item):
        item_name = self.ctrl.player.pick_up(self.ctrl.get_room(), possible_item)
        if item_name:
            return f"You picked up a {item_name}"
        else:
            if isinstance(possible_item, list):
                return f"I cant pick up {possible_item[1]}"
            return "Get What?"

    def look(self, possible_item):
        item_info = self.ctrl.player.look(self.ctrl.get_room(), possible_item)
        if item_info:
            return item_info
        else:
            if isinstance(possible_item, list):
                return f"I dont see {possible_item[1]}"
            return "Look at What?"

    def change_room_description(self, possible_item):
        room = self.ctrl.get_room()
        if isinstance(possible_item, list):
            words = [word for word in possible_item if word != 'changedesc']
            new_description = ' '.join(words)
        else:
            new_description = possible_item
        room.description = new_description
        return f"The {room.name} room's appearance has changed!"

    def use_item(self, possible_item):
        def has_item(name):
            for i in self.ctrl.player.inventory:
                if i.name == name:
                    return True
            return False

        if isinstance(possible_item, dict):
            item = possible_item['item']
            target = possible_item['target']
            if not has_item(item):
                return f"You don't have {item} in hand."
            event_result = self.ctrl.check_use_with_events(item, target)
            if event_result:
                return event_result
            return f"You can't use {item} with {target}"
        else:
            item_name = possible_item if isinstance(possible_item, str) else possible_item[1]
            if not has_item(item_name):
                return f"You don't have {item_name} here to use."
            result = self.ctrl.player.use(possible_item)
            if result:
                return result
            if isinstance(possible_item, list):
                return f"I can't use {possible_item[1]}"
            return "Use what?"

    def execute(self, cmd, possible_item):
        if cmd in self.ctrl.player.directions:
            return self.move_player(cmd)
        elif cmd == 'drop':
            return self.drop(possible_item)
        elif cmd == 'pickup':
            return self.pick_up(possible_item)
        elif cmd == 'look':
            return self.look(possible_item)
        elif cmd == 'help':
            return self.help()
        elif cmd == 'move':
            move_dir = next((d for d in self.ctrl.player.directions if d in possible_item), "")
            return self.move_player(move_dir)
        elif cmd == 'use':
            return self.use_item(possible_item)
        elif cmd == 'changedesc':
            return self.change_room_description(possible_item)
        else:
            return f"I don't understand: {cmd}. Please try again."
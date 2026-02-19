class EventManager:
    def __init__(self, controller):
        self.ctrl = controller

    def _open_exits(self, exits_to_open):
        if not isinstance(exits_to_open, list):
            exits_to_open = [exits_to_open]
        for exit_data in exits_to_open:
            matched = False
            for room in self.ctrl.map.list_of_rooms:
                if room.name == exit_data['room']:
                    matched = True
                    if exit_data['direction'] not in room.exits:
                        room.exits.append(exit_data['direction'])
                    room.exit_destinations[exit_data['direction']] = {
                        'floor': exit_data['destination']['floor'],
                        'x': exit_data['destination']['x'],
                        'y': exit_data['destination']['y']
                    }
            if not matched:
                print(f"[EXIT ERROR] Room not found: {exit_data['room']}")
                    
    def check_events(self):
        messages = []
        current_room = self.ctrl.get_room()
        if not current_room:
            return messages

        if current_room.name not in self.ctrl.player.visited_rooms:
            self.ctrl.player.visited_rooms.append(current_room.name)

        for event in self.ctrl.map.event_recipes:
            if event['id'] in self.ctrl.player.completed_events:
                continue
            if event['check_type'] == 'all_rooms_visited':
                required_rooms = event['parameters']['required_rooms']
                if all(room in self.ctrl.player.visited_rooms for room in required_rooms):
                    result = event['result']
                    if 'open_exit' in result:
                        self._open_exits(result['open_exit'])
                    if 'message' in result:
                        messages.append(result['message'])
                    self.ctrl.player.completed_events.append(event['id'])

        return messages

    def check_use_with_events(self, item, target):
        current_room = self.ctrl.get_room()
        for event in self.ctrl.map.event_recipes:
            if event['id'] in self.ctrl.player.completed_events:
                continue
            if event['check_type'] == 'item_used_with':
                params = event['parameters']
                if (params['item'] == item and
                    params['target'] == target and
                    params['room'] == current_room.name):
                    result = event['result']
                    if 'open_exit' in result:
                        self._open_exits(result['open_exit'])
                    if 'add_item' in result:
                        item_to_add = self.ctrl.map.make_item(result['add_item']['item'])
                        for room in self.ctrl.map.list_of_rooms:
                            if room.name == result['add_item']['room']:
                                room.inventory.append(item_to_add)
                    if 'message' in result:
                        self.ctrl.player.completed_events.append(event['id'])
                        return result['message']
        return None
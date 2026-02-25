from game.event_types import Event, AllRoomsVisitedEvent, ItemUsedWithEvent

class EventManager:
    def __init__(self, controller):
        # controller gives us access to the map, player, and room state
        self.ctrl = controller

    def _open_exits(self, exits_to_open):
        """
        Opens one or more exits on rooms in the map.
        Called by events when they need to unlock new paths.
        Each exit_data looks like:
            { "room": "vault", "direction": "north", "destination": { "floor": 2, "x": 0, "y": 1 } }
        """
        if not isinstance(exits_to_open, list):
            exits_to_open = [exits_to_open]

        for exit_data in exits_to_open:
            target_room_name = exit_data['room']
            direction        = exit_data['direction']
            destination      = exit_data['destination']

            room_was_found = False
            for room in self.ctrl.map.list_of_rooms:
                if room.name == target_room_name:
                    room_was_found = True
                    if direction not in room.exits:
                        room.exits.append(direction)
                    room.exit_destinations[direction] = {
                        'floor': destination['floor'],
                        'x':     destination['x'],
                        'y':     destination['y']
                    }

            if not room_was_found:
                print(f"[EXIT ERROR] Room not found: {target_room_name}")

    def _fire_event(self, event):
        result = event.result

        if 'open_exit' in result:
            self._open_exits(result['open_exit'])

        if 'add_item' in result:
            new_item         = self.ctrl.map.make_item(result['add_item']['item'])
            destination_room = result['add_item']['room']
            for room in self.ctrl.map.list_of_rooms:
                if room.name == destination_room:
                    room.inventory.append(new_item)

        if 'remove_item' in result:
            for item_data in result['remove_item']:
                self.ctrl.player.inventory = [
                    i for i in self.ctrl.player.inventory 
                    if i.name != item_data['item']
                ]

        if 'set_state' in result:
            for state_change in result['set_state']:
                for room in self.ctrl.map.list_of_rooms:
                    if room.name == state_change['room']:
                        room.set_state(state_change['state'])

        if 'set_item_state' in result:
            for state_change in result['set_item_state']:
                item_name = state_change['item']
                new_state = state_change['state']
                # check player inventory first
                for item in self.ctrl.player.inventory:
                    if item.name == item_name:
                        item.set_state(new_state)
                # also check all rooms
                for room in self.ctrl.map.list_of_rooms:
                    for item in room.inventory:
                        if item.name == item_name:
                            item.set_state(new_state)

        # these must be OUTSIDE all the if blocks
        self.ctrl.player.completed_events.append(event.id)
        return result.get('message', None)

    def check_events(self):
        """
        Called whenever the player moves into a new room.
        Loops through all events and fires any AllRoomsVisitedEvents
        whose required rooms have all been visited.
        Returns a list of messages to display to the player.
        """
        triggered_messages = []

        current_room = self.ctrl.get_room()
        if not current_room:
            return triggered_messages

        # track that the player has now visited this room
        if current_room.name not in self.ctrl.player.visited_rooms:
            self.ctrl.player.visited_rooms.append(current_room.name)

        for event in self.ctrl.map.event_recipes:
            # this method only handles AllRoomsVisitedEvent, skip everything else
            if not isinstance(event, AllRoomsVisitedEvent):
                continue
            if event.id in self.ctrl.player.completed_events:
                continue
            # the event checks itself whether all required rooms have been visited
            if event.check(self.ctrl):
                message = self._fire_event(event)
                if message:
                    triggered_messages.append(message)

        return triggered_messages

    def check_use_with_events(self, item, target):
        """
        Called when the player uses an item on a target (e.g. 'use key on box').
        Loops through all events and fires any ItemUsedWithEvent
        whose item, target, and room all match the current situation.
        Returns the event message if triggered, or None if nothing matched.
        """
        for event in self.ctrl.map.event_recipes:
            # this method only handles ItemUsedWithEvent, skip everything else
            if not isinstance(event, ItemUsedWithEvent):
                continue
            if event.id in self.ctrl.player.completed_events:
                continue
            # the event checks itself whether item, target and room all match
            if event.check(self.ctrl, item, target):
                return self._fire_event(event)

        return None
    
    def check_win(self):
        """
        Checks if all win condition events have been completed.
        Returns True if the player has won, False otherwise.
        """
        return all(
            event_id in self.ctrl.player.completed_events
            for event_id in self.ctrl.map.win_conditions
        )
    
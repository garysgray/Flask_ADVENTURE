from game.event_types import Event, AllRoomsVisitedEvent, ItemUsedWithEvent, AllEventsCompletedEvent


class EventManager:
    """
    Checks and fires game events after every player command.

    Two event types are currently supported:
        AllRoomsVisitedEvent  — fires when the player has visited all required rooms
        ItemUsedWithEvent     — fires when item + target + room all match

    Flow per command:
        1. check_events()                     — checks AllRoomsVisitedEvents
        2. check_use_with_events()            — checks ItemUsedWithEvents (called from actions.py)
        3. check_use_with_events_already_done — returns message if event was already completed
        4. check_win()                        — checks if all win conditions are met
    """

    def __init__(self, controller):
        self.ctrl = controller

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    def _open_exits(self, exits_to_open):
        """
        Opens one or more exits on rooms in the map.
        Accepts a single exit dict or a list of them.
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
        """
        Executes all result actions for a fired event, then marks it as completed.

        Supported result keys:
            open_exit      — unlocks an exit on a room
            add_item       — spawns an item into a room
            remove_item    — removes an item from player inventory
            set_state      — changes a room to a new state
            set_item_state — changes an item to a new state
            message        — text displayed to the player

        Always writes to player journal and completed_events regardless of result keys.
        Returns the message string or None.
        """
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
                for item in self.ctrl.player.inventory:
                    if item.name == item_name:
                        item.set_state(new_state)
                for room in self.ctrl.map.list_of_rooms:
                    for item in room.inventory:
                        if item.name == item_name:
                            item.set_state(new_state)

        # always runs — must stay outside all if blocks above
        self.ctrl.player.journal.append({
            'event_id': event.id,
            'room':     self.ctrl.get_room().name,
            'message':  result.get('message', '')
        })
        self.ctrl.player.completed_events.append(event.id)

        return result.get('message', None)

    # ─── Event Checks ─────────────────────────────────────────────────────────

    def check_events(self):
        """
        Called after every command.
        Checks AllRoomsVisitedEvents and AllEventsCompletedEvents and fires
        any whose conditions have been met.
        visited_rooms tracking is handled by get_room() in controller.py.
        Returns a list of event messages to display to the player.
        """
        triggered_messages = []

        if not self.ctrl.get_room():
            return triggered_messages

        for event in self.ctrl.map.event_recipes:
            if not isinstance(event, (AllRoomsVisitedEvent, AllEventsCompletedEvent)):
                continue
            if event.id in self.ctrl.player.completed_events:
                continue
            if event.check(self.ctrl):
                message = self._fire_event(event)
                if message:
                    triggered_messages.append(message)

        return triggered_messages

    def check_use_with_events(self, item, target):
        """
        Called when the player uses an item on a target e.g. 'use key with box'.
        Fires the first ItemUsedWithEvent whose item, target, and room all match.
        Returns the event message if triggered, None if nothing matched.
        Already-completed events are skipped — handled by check_use_with_events_already_done.
        """
        for event in self.ctrl.map.event_recipes:
            if not isinstance(event, ItemUsedWithEvent):
                continue
            if event.id in self.ctrl.player.completed_events:
                continue
            if event.check(self.ctrl, item, target):
                return self._fire_event(event)
        return None

    def check_use_with_events_already_done(self, item, target):
        """
        Called before the has_item check in use_item so items removed from
        inventory (e.g. locket dropped into well) still return a meaningful response.
        Returns an already-done message if this item+target was previously completed.
        """
        for event in self.ctrl.map.event_recipes:
            if not isinstance(event, ItemUsedWithEvent):
                continue
            if event.item == item and event.target == target:
                if event.id in self.ctrl.player.completed_events:
                    return f"You already did this in the {event.room}."
        return None

    def check_win(self):
        """
        Returns True if all win condition event IDs are in completed_events.
        Win conditions are defined in game_data.yaml under win_conditions.
        """
        return all(
            event_id in self.ctrl.player.completed_events
            for event_id in self.ctrl.map.win_conditions
        )
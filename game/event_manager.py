from game.event_types import (
    Event, AllRoomsVisitedEvent, ItemUsedWithEvent, AllEventsCompletedEvent,
    ECAEvent, InRoomCondition, EventsCompletedCondition, RequiredItemsCondition, RoomsVisitedCondition
)


class EventManager:
    """
    Checks and fires game events after every player command.
    Evaluates both active interaction events and passive background observers.
    Applies world mutations (exits, items, room states, fixture states).
    """

    def __init__(self, controller_or_events):
        if isinstance(controller_or_events, list):
            self.ctrl = None
            self.events = controller_or_events
        else:
            self.ctrl = controller_or_events
            self.events = getattr(self.ctrl.map, "event_recipes", []) if self.ctrl and hasattr(self.ctrl, 'map') else []

    def evaluate_event(self, event, player=None, room=None, game_map=None):
        """
        Evaluates conditions for a specific event against player, room, and map.
        Returns (success: bool, failure_reason: Optional[str]).
        """
        if player is not None:
            for cond in getattr(event, 'conditions', []):
                passed = cond.evaluate(player, room, game_map)
                if not passed:
                    hint = getattr(cond, 'fail_hint', "Condition not met.")
                    return False, hint
            return True, None
        else:
            passed, failure_hint, _ = event.check_conditions(self.ctrl)
            return passed, (None if passed else failure_hint)

    def fire_event(self, event, player=None, room=None, game_map=None):
        """
        Fires an event and executes its mutations.
        """
        if player is not None:
            res = getattr(event, 'result', {}) or {}
            msgs = []
            if 'message' in res and res['message']:
                msgs.append(res['message'])
            if 'remove_item' in res:
                items = res['remove_item'] if isinstance(res['remove_item'], list) else [res['remove_item']]
                for it in items:
                    player.inventory = [i for i in player.inventory if getattr(i, 'name', '') != it]
            if 'remove_items' in res:
                items = res['remove_items'] if isinstance(res['remove_items'], list) else [res['remove_items']]
                for it in items:
                    player.inventory = [i for i in player.inventory if getattr(i, 'name', '') != it]
            if 'add_item' in res:
                items = res['add_item'] if isinstance(res['add_item'], list) else [res['add_item']]
                from game.gameObjects import Item
                for it in items:
                    player.inventory.append(Item(name=it) if isinstance(it, str) else it)
            if 'add_items' in res:
                items = res['add_items'] if isinstance(res['add_items'], list) else [res['add_items']]
                from game.gameObjects import Item
                for it in items:
                    player.inventory.append(Item(name=it) if isinstance(it, str) else it)
            if 'set_state' in res and room:
                for sc in res['set_state']:
                    if sc.get('room') == getattr(room, 'name', ''):
                        room.set_state(sc.get('state'))
            if 'set_fixture_state' in res and room and hasattr(room, 'fixtures'):
                fc = res['set_fixture_state']
                if not isinstance(fc, list):
                    fc = [fc]
                for sc in fc:
                    if sc.get('room') == getattr(room, 'name', '') and sc.get('fixture') in room.fixtures:
                        room.fixtures[sc.get('fixture')].set_state(sc.get('state'))
            if event.id not in player.completed_events:
                player.completed_events.append(event.id)
            return msgs
        msg = self._fire_event(event)
        return [msg] if msg else []

    # ─── Internal Helpers ─────────────────────────────────────────────────────

    def _open_exits(self, exits_to_open):
        """
        Opens one or more exits on rooms in the map.
        Accepts a single exit dict or a list of them.
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
                    if hasattr(room, 'locked_exits') and direction in room.locked_exits:
                        room.locked_exits.remove(direction)
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
            open_exit          — unlocks an exit on a room
            add_item           — spawns an item into a room or inventory
            remove_item        — removes an item from player inventory
            set_state          — changes a room to a new state
            set_fixture_state  — changes a stationary room fixture to a new state
            set_item_state     — changes an item to a new state
            message            — text displayed to the player
        """
        result = event.result

        if 'open_exit' in result:
            self._open_exits(result['open_exit'])

        # Removing/consuming items from player inventory
        items_to_remove = []
        if 'remove_items' in result:
            raw = result['remove_items']
            if isinstance(raw, list):
                items_to_remove.extend(raw)
            elif isinstance(raw, (str, dict)):
                items_to_remove.append(raw)
        if 'remove_item' in result:
            raw = result['remove_item']
            if isinstance(raw, list):
                items_to_remove.extend(raw)
            elif isinstance(raw, (str, dict)):
                items_to_remove.append(raw)

        for item_entry in items_to_remove:
            target_name = item_entry['item'] if isinstance(item_entry, dict) and 'item' in item_entry else item_entry
            if isinstance(target_name, str):
                self.ctrl.player.remove_item(target_name)

        # Adding newly created / rewarded items
        items_to_add = []
        if 'add_items' in result:
            raw = result['add_items']
            if isinstance(raw, list):
                items_to_add.extend(raw)
            elif isinstance(raw, (str, dict)):
                items_to_add.append(raw)
        if 'add_item' in result:
            raw = result['add_item']
            if isinstance(raw, list):
                items_to_add.extend(raw)
            elif isinstance(raw, (str, dict)):
                items_to_add.append(raw)

        for item_entry in items_to_add:
            if isinstance(item_entry, dict) and 'room' in item_entry and item_entry['room'] not in ('inventory', 'player'):
                item_name = item_entry.get('name') or item_entry.get('item', '')
                dest_room_name = item_entry['room']
                new_item = self.ctrl.map.make_item(item_name)
                for room in self.ctrl.map.list_of_rooms:
                    if room.name == dest_room_name:
                        room.inventory.append(new_item)
            else:
                item_name = (item_entry.get('name') or item_entry.get('item', '')) if isinstance(item_entry, dict) else item_entry
                if isinstance(item_name, str) and item_name:
                    new_item = self.ctrl.map.make_item(item_name)
                    self.ctrl.player.inventory.append(new_item)

        # Room-level state changes
        if 'set_state' in result:
            for state_change in result['set_state']:
                for room in self.ctrl.map.list_of_rooms:
                    if room.name == state_change['room']:
                        room.set_state(state_change['state'])

        # Fixture-level state changes
        if 'set_fixture_state' in result:
            fixture_changes = result['set_fixture_state']
            if not isinstance(fixture_changes, list):
                fixture_changes = [fixture_changes]
            for state_change in fixture_changes:
                room_name = state_change.get('room')
                fix_name  = state_change.get('fixture')
                new_state = state_change.get('state')
                for room in self.ctrl.map.list_of_rooms:
                    if room.name == room_name and hasattr(room, 'fixtures') and fix_name in room.fixtures:
                        room.fixtures[fix_name].set_state(new_state)

        # Item-level state changes
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

        # Journal and completed_events tracking
        current_room = self.ctrl.get_room()
        room_name = getattr(current_room, 'display_name', current_room.name.replace('_', ' ')) if current_room else ''
        self.ctrl.player.journal.append({
            'event_id': event.id,
            'room':     room_name,
            'message':  result.get('message', '')
        })
        self.ctrl.player.completed_events.append(event.id)

        return result.get('message', None)

    # ─── Event Checks ─────────────────────────────────────────────────────────

    def check_events(self):
        """
        PASSIVE TRIGGER PHASE: Evaluates background passive observers.
        """
        triggered_messages = []

        if not self.ctrl.get_room():
            return triggered_messages

        for event in self.ctrl.map.event_recipes:
            if event.id in self.ctrl.player.completed_events:
                continue

            if isinstance(event, ECAEvent):
                if event.is_passive:
                    passed, _, _ = event.check_conditions(self.ctrl)
                    if passed:
                        message = self._fire_event(event)
                        if message:
                            triggered_messages.append(message)
                continue

            if isinstance(event, (AllRoomsVisitedEvent, AllEventsCompletedEvent)):
                if event.check(self.ctrl):
                    message = self._fire_event(event)
                    if message:
                        triggered_messages.append(message)

        return triggered_messages

    def _player_has_item(self, item_name):
        return any(getattr(i, 'name', '') == item_name for i in getattr(self.ctrl.player, 'inventory', []))

    def _matches_interaction(self, event, item, target):
        player_has_target = self._player_has_item(target)

        if isinstance(event, ECAEvent):
            return event.matches_use_with(item, target, player_has_target=player_has_target)

        if isinstance(event, ItemUsedWithEvent):
            if event.matches_interaction(item, target):
                return True
            if player_has_target and event.matches_interaction(target, item):
                return True

        return False

    def evaluate_use_with(self, item, target):
        """
        ACTIVE TRIGGER PHASE: Evaluates 'use <item> with <target>'.
        """
        current_room = self.ctrl.get_room()
        current_room_name = current_room.name if current_room else ""

        candidates = []
        for event in self.ctrl.map.event_recipes:
            if event.id in self.ctrl.player.completed_events:
                continue
            if self._matches_interaction(event, item, target):
                candidates.append(event)

        if not candidates:
            return {
                'status': 'meaningless',
                'message': "Nothing happens.",
                'event': None
            }

        failed_candidates = []
        for event in candidates:
            if isinstance(event, ECAEvent):
                passed, failure_hint, failed_cond = event.check_conditions(self.ctrl)
                if passed:
                    msg = self._fire_event(event)
                    return {
                        'status': 'success',
                        'message': msg,
                        'event': event
                    }
                else:
                    failed_candidates.append((event, failure_hint, failed_cond))
            elif isinstance(event, ItemUsedWithEvent):
                room_ok = (not event.room or event.room == 'any' or event.room == current_room_name)
                prereqs_ok = event.check_prerequisites(self.ctrl)
                if room_ok and prereqs_ok:
                    msg = self._fire_event(event)
                    return {
                        'status': 'success',
                        'message': msg,
                        'event': event
                    }
                else:
                    if room_ok and not prereqs_ok:
                        hint = (event.hints.get('missing_prerequisite') if event.hints else None) or \
                               "The two pieces seem like they belong together, but something is still missing."
                        failed_candidates.append((event, hint, 'missing_prerequisite'))
                    else:
                        hint = (event.hints.get('wrong_room') if event.hints else None) or \
                               "Nice try. This seems like something that might work somewhere else."
                        failed_candidates.append((event, hint, 'wrong_room'))

        for event, hint, cond_info in failed_candidates:
            if isinstance(event, ECAEvent):
                room_conds = [c for c in event.conditions if isinstance(c, InRoomCondition)]
                room_ok = not room_conds or any(c.room == current_room_name or c.room == 'any' for c in room_conds)
                if room_ok:
                    status = 'wrong_room' if isinstance(cond_info, InRoomCondition) else 'missing_prerequisite'
                    return {
                        'status': status,
                        'message': hint,
                        'event': event
                    }
            elif isinstance(event, ItemUsedWithEvent):
                room_ok = (not event.room or event.room == 'any' or event.room == current_room_name)
                if room_ok:
                    return {
                        'status': 'missing_prerequisite',
                        'message': hint,
                        'event': event
                    }

        first_event, first_hint, first_cond_info = failed_candidates[0]
        status = 'wrong_room'
        if isinstance(first_event, ECAEvent):
            if not isinstance(first_cond_info, InRoomCondition):
                status = 'missing_prerequisite'
        elif isinstance(first_event, ItemUsedWithEvent):
            room_ok = (not first_event.room or first_event.room == 'any' or first_event.room == current_room_name)
            if room_ok:
                status = 'missing_prerequisite'

        return {
            'status': status,
            'message': first_hint,
            'event': first_event
        }

    def evaluate_solo(self, target, action=None):
        """
        ACTIVE TRIGGER PHASE: Evaluates a player's single-object interaction on `target`.
        """
        current_room = self.ctrl.get_room()
        current_room_name = current_room.name if current_room else ""

        target_clean = str(target).strip().lower().replace(' ', '_') if target else ""

        target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
        for canonical_t, aliases in target_aliases.items():
            if target_clean == canonical_t or target_clean in aliases or str(target).strip().lower() in aliases:
                target_clean = canonical_t
                break

        candidates = []
        for event in self.ctrl.map.event_recipes:
            if event.id in self.ctrl.player.completed_events:
                continue
            if isinstance(event, ECAEvent):
                if event.matches_solo(target_clean, action=action) or event.matches_solo(target, action=action):
                    candidates.append(event)

        if not candidates:
            return {
                'status': 'no_event',
                'message': None,
                'event': None
            }

        failed_candidates = []
        for event in candidates:
            passed, failure_hint, failed_cond = event.check_conditions(self.ctrl)
            if passed:
                msg = self._fire_event(event)
                return {
                    'status': 'success',
                    'message': msg,
                    'event': event
                }
            else:
                failed_candidates.append((event, failure_hint, failed_cond))

        for event, hint, cond_info in failed_candidates:
            room_conds = [c for c in event.conditions if isinstance(c, InRoomCondition)]
            room_ok = not room_conds or any(c.room == current_room_name or c.room == 'any' for c in room_conds)
            if room_ok:
                status = 'wrong_room' if isinstance(cond_info, InRoomCondition) else 'missing_prerequisite'
                return {
                    'status': status,
                    'message': hint,
                    'event': event
                }

        first_event, first_hint, first_cond_info = failed_candidates[0]
        status = 'wrong_room' if isinstance(first_cond_info, InRoomCondition) else 'missing_prerequisite'
        return {
            'status': status,
            'message': first_hint,
            'event': first_event
        }

    def check_solo_events_already_done(self, target, action=None):
        target_clean = str(target).strip().lower().replace(' ', '_') if target else ""
        target_aliases = getattr(self.ctrl.map, 'target_aliases', {})
        for canonical_t, aliases in target_aliases.items():
            if target_clean == canonical_t or target_clean in aliases or str(target).strip().lower() in aliases:
                target_clean = canonical_t
                break

        for event in self.ctrl.map.event_recipes:
            if isinstance(event, ECAEvent) and (event.matches_solo(target_clean, action=action) or event.matches_solo(target, action=action)):
                if event.id in self.ctrl.player.completed_events:
                    return "You already did this."
        return None

    def check_use_with_events(self, item, target):
        res = self.evaluate_use_with(item, target)
        if res['status'] == 'success':
            return res['message']
        return None

    def check_use_with_events_already_done(self, item, target):
        for event in self.ctrl.map.event_recipes:
            if self._matches_interaction(event, item, target):
                if event.id in self.ctrl.player.completed_events:
                    room_name = ""
                    if isinstance(event, ECAEvent):
                        for c in event.conditions:
                            if isinstance(c, InRoomCondition) and c.room:
                                room_name = c.room
                                break
                    elif isinstance(event, ItemUsedWithEvent):
                        room_name = event.room
                    if room_name and room_name != 'any':
                        return f"You already did this in the {room_name}."
                    return "You already did this."
        return None

    def check_win(self):
        return all(
            event_id in self.ctrl.player.completed_events
            for event_id in self.ctrl.map.win_conditions
        )

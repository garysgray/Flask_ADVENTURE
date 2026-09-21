class Condition:
    """
    Base interface for composable requirements.
    check() returns a tuple of (passed: bool, failure_hint: str).
    """
    type = "base"

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        return True, ""

    def evaluate(self, player, room, game_map) -> bool:
        return True


class InRoomCondition(Condition):
    """
    Requires the player to be in a specific room (or 'any').
    Returns a contextual hint when in the wrong room.
    """
    type = "in_room"

    def __init__(self, room, fail_hint=""):
        self.room = room
        self.fail_hint = fail_hint or "Nice try. This seems like something that might work somewhere else."

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        if not self.room or self.room == "any":
            return True, ""
        current_room = ctrl.get_room()
        current_room_name = getattr(current_room, "name", "") if current_room else ""
        if current_room_name != self.room:
            return False, self.fail_hint
        return True, ""

    def evaluate(self, player, room, game_map) -> bool:
        if not self.room or self.room == "any":
            return True
        return getattr(room, "name", "") == self.room


class EventsCompletedCondition(Condition):
    """
    Requires all specified prerequisite events to be completed.
    Returns a contextual hint if prerequisites are missing.
    """
    type = "events_completed"

    def __init__(self, required_events, fail_hint=""):
        self.required_events = required_events or []
        self.fail_hint = fail_hint or "The two pieces seem like they belong together, but something is still missing."

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        completed = getattr(ctrl.player, "completed_events", [])
        if not all(ev in completed for ev in self.required_events):
            return False, self.fail_hint
        return True, ""

    def evaluate(self, player, room, game_map) -> bool:
        completed = getattr(player, "completed_events", [])
        return all(ev in completed for ev in self.required_events)


class RequiredItemsCondition(Condition):
    """
    Requires the player to have specific items in their inventory.
    """
    type = "required_items"

    def __init__(self, required_items, fail_hint=""):
        self.required_items = required_items or []
        self.fail_hint = fail_hint or "You are missing required equipment."

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        if not self.required_items:
            return True, ""
        inv_names = [getattr(i, 'name', '') for i in getattr(ctrl.player, 'inventory', [])]
        if not all(req in inv_names for req in self.required_items):
            return False, self.fail_hint
        return True, ""

    def evaluate(self, player, room, game_map) -> bool:
        if not self.required_items:
            return True
        inv_names = [getattr(i, 'name', '') for i in getattr(player, 'inventory', [])]
        return all(req in inv_names for req in self.required_items)


class CustomPythonCondition(Condition):
    """
    Custom condition evaluated via a Python callable/predicate.
    """
    type = "custom_python"

    def __init__(self, predicate=None, fail_hint=""):
        self.predicate = predicate
        self.fail_hint = fail_hint or "Condition not met."

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        if callable(self.predicate):
            try:
                res = self.predicate(ctrl, context)
                if not res:
                    return False, self.fail_hint
            except Exception:
                return False, self.fail_hint
        return True, ""

    def evaluate(self, player, room, game_map) -> bool:
        if callable(self.predicate):
            try:
                return bool(self.predicate(player, room, game_map))
            except Exception:
                return False
        return True


class RoomsVisitedCondition(Condition):
    """
    Passive condition: requires all specified rooms to be in visited_room_names.
    Silent failure (empty hint) since this is checked in the background phase.
    """
    type = "rooms_visited"

    def __init__(self, required_rooms):
        self.required_rooms = required_rooms or []

    def check(self, ctrl, context=None) -> tuple[bool, str]:
        visited = getattr(ctrl.player, "visited_room_names", [])
        if not all(rm in visited for rm in self.required_rooms):
            return False, ""
        return True, ""


class ECAEvent:
    """
    Universal Event-Condition-Action Event.
    - trigger: dict specifying trigger type ('use_with' or 'on_turn') and parameters
    - conditions: list of Condition objects evaluated sequentially
    - result: dict of action mutations to apply to the world when conditions are met
    """
    def __init__(self, id, trigger: dict, conditions: list[Condition], result: dict, hints: dict = None):
        self.id = id
        self.trigger = trigger or {}
        self.conditions = conditions or []
        self.result = result or {}
        self.hints = hints or {}

    @property
    def is_passive(self) -> bool:
        return self.trigger.get("type") == "on_turn"

    def matches_solo(self, target, action=None) -> bool:
        """
        Checks if this event listens for a single-object interaction on `target`
        and optional specific `action` (e.g. 'drink', 'pull', 'open', 'read', 'turn', 'press', 'use').
        """
        trig_type = self.trigger.get("type")
        if trig_type not in ("solo", "solo_action", "interact"):
            return False

        t_target = self.trigger.get("target") or self.trigger.get("item") or ""
        t_action = self.trigger.get("action") or self.trigger.get("verb")

        clean_t_target = str(t_target).strip().lower().replace(' ', '_')
        clean_target = str(target).strip().lower().replace(' ', '_') if target else ""

        if clean_t_target != clean_target:
            return False

        if t_action:
            clean_t_action = str(t_action).strip().lower()
            if action:
                clean_action = str(action).strip().lower()
                read_examine = {'read', 'examine', 'look', 'inspect', 'look at'}
                drink_verbs = {'drink', 'sip', 'swallow', 'gulp'}
                eat_verbs = {'eat', 'chew', 'taste', 'consume'}
                open_verbs = {'open', 'unlock', 'unseal'}
                pull_verbs = {'pull', 'flip', 'switch', 'tug'}
                push_verbs = {'push', 'press'}

                is_synonym = (
                    (clean_t_action in read_examine and clean_action in read_examine) or
                    (clean_t_action in drink_verbs and clean_action in drink_verbs) or
                    (clean_t_action in eat_verbs and clean_action in eat_verbs) or
                    (clean_t_action in open_verbs and clean_action in open_verbs) or
                    (clean_t_action in pull_verbs and clean_action in pull_verbs) or
                    (clean_t_action in push_verbs and clean_action in push_verbs)
                )

                if not is_synonym and clean_action != clean_t_action and clean_action != 'use':
                    return False

        return True

    def matches_use_with(self, item, target, player_has_target=False) -> bool:
        """
        Checks if this event listens for the specified item and target.
        Supports direct match, required_items multi-tool match, and symmetric target match.
        """
        trig_type = self.trigger.get("type")
        if trig_type not in ("use_with", "dual", "two_object", "combine", "use_item", "use"):
            return False

        t_item = self.trigger.get("item") or self.trigger.get("source") or ""
        t_target = self.trigger.get("target") or ""
        req_items = self.trigger.get("required_items", [])

        # Direct match
        if t_item == item and t_target == target:
            return True

        # required_items pair match
        if req_items and item in req_items and target in req_items and item != target:
            return True

        # Symmetric match if player is carrying the target
        if player_has_target:
            if t_item == target and t_target == item:
                return True

        return False

    def check_conditions(self, ctrl, context=None) -> tuple[bool, str, Condition | None]:
        """
        Evaluates conditions sequentially.
        Returns (True, '', None) if all conditions pass, or (False, failure_hint, failed_condition) on the first failing condition.
        """
        for cond in self.conditions:
            passed, hint = cond.check(ctrl, context)
            if not passed:
                return False, hint, cond
        return True, "", None


class Event:
    """
    Base class for all legacy event types.
    Each subclass defines its own check() logic and holds its own parameters.
    When check() returns True, EventManager fires the event via _fire_event().
    """
    def __init__(self, id, result):
        self.id     = id
        self.result = result  # dict of actions to take when the event fires

    def check(self, ctrl):
        raise NotImplementedError


class AllRoomsVisitedEvent(Event):
    """
    Fires when the player has visited all rooms in the required_rooms list.
    Checked after every command in EventManager.check_events().
    """
    def __init__(self, id, result, required_rooms):
        super().__init__(id, result)
        self.required_rooms = required_rooms

    def check(self, ctrl):
        return all(r in ctrl.player.visited_room_names for r in self.required_rooms)


class ItemUsedWithEvent(Event):
    """
    Fires when the player uses a specific item on a specific target in a specific room.
    Checked in EventManager.evaluate_use_with() when a connector command is executed.
    """
    def __init__(self, id, result, item, target, room, prerequisites=None, hints=None, required_items=None):
        super().__init__(id, result)
        self.item           = item           # item the player must be using e.g. 'matches'
        self.target         = target         # target being acted on e.g. 'lantern'
        self.room           = room           # room where the interaction must happen e.g. 'entrance'
        self.prerequisites  = prerequisites or []
        self.hints          = hints or {}
        self.required_items = required_items or []

    def matches_interaction(self, item, target):
        """Checks whether this event recognizes the item and target combination."""
        if self.item == item and self.target == target:
            return True
        if self.required_items and item in self.required_items and target in self.required_items and item != target:
            return True
        return False

    def check_prerequisites(self, ctrl):
        """Checks whether all required prerequisite event IDs and required items are satisfied."""
        if not all(p in ctrl.player.completed_events for p in self.prerequisites):
            return False
        if self.required_items:
            inv_names = [getattr(i, 'name', '') for i in getattr(ctrl.player, 'inventory', [])]
            if not all(req in inv_names for req in self.required_items):
                return False
        return True

    def check(self, ctrl, item, target):
        # item, target, room, and prerequisites must all be satisfied
        return (self.matches_interaction(item, target) and
                (not self.room or self.room == 'any' or self.room == ctrl.get_room().name) and
                self.check_prerequisites(ctrl))
    
class AllEventsCompletedEvent(Event):
    """
    Fires when all required events have been completed.
    Used for the win condition journal entry.
    """
    def __init__(self, id, result, required_events):
        super().__init__(id, result)
        self.required_events = required_events

    def check(self, ctrl):
        return all(e in ctrl.player.completed_events for e in self.required_events)

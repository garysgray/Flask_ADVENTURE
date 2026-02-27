class Event:
    """
    Base class for all event types.
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
    Checked in EventManager.check_use_with_events() when a connector command is executed.
    """
    def __init__(self, id, result, item, target, room):
        super().__init__(id, result)
        self.item   = item    # item the player must be using e.g. 'matches'
        self.target = target  # target being acted on e.g. 'lantern'
        self.room   = room    # room where the interaction must happen e.g. 'entrance'

    def check(self, ctrl, item, target):
        # all three must match — item, target, and current room
        return (self.item   == item and
                self.target == target and
                self.room   == ctrl.get_room().name)
    
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
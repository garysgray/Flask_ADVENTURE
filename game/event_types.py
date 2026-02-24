class Event:
    def __init__(self, id, result):
        self.id     = id
        self.result = result

    def check(self, ctrl):
        raise NotImplementedError

class AllRoomsVisitedEvent(Event):
    def __init__(self, id, result, required_rooms):
        super().__init__(id, result)
        self.required_rooms = required_rooms

    # ALL = "for every room that is required, has the player been there? If yes to all of them, return True."
    def check(self, ctrl):
        return all(r in ctrl.player.visited_rooms for r in self.required_rooms)
    
class ItemUsedWithEvent(Event):
    def __init__(self, id, result, item, target, room):
        super().__init__(id, result)
        self.item   = item
        self.target = target
        self.room   = room

    def check(self, ctrl, item, target):
        return (self.item   == item and
                self.target == target and
                self.room   == ctrl.get_room().name)
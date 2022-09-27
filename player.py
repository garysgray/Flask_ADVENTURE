
class Player:
    def __init__(self ):
        self.id = 0
        self.pos_x = 0
        self.pos_y = 0
        self.inventory = []
        self.id = None
        self.directions = ['north','south','east','west']
        
    def get_location(self):
            loc = {'X':self.pos_x, 'Y':self.pos_y }
            return loc 

    def drop(self, room, possible_item):
        for obj in self.inventory:
            if obj.name in possible_item:
                self.inventory.remove(obj)
                room.inventory.append(obj)
                return obj.name
        else:
            return False

    def pick_up(self, room, possible_item):
        for obj in room.inventory:
            if obj.name in possible_item:
                self.inventory.append(obj)
                room.inventory.remove(obj)
                return obj.name
        else:
            return False

    def look(self, room, possible_item):
        for obj in self.inventory:
            if obj.name in possible_item:
                return obj.description
        for obj in room.inventory:
            if obj.name in possible_item:
                return obj.description
        return False

    def move(self, dir, room, level_max):
            if dir in room.exits:  
                match dir:
                    case 'north':
                        if self.pos_y > 0:
                            self.pos_y -= 1
                        else:
                            self.pos_y = 0
                    case 'east':
                        self.pos_x += 1
                    case 'south':
                        self.pos_y += 1
                    case 'west':
                        if self.pos_x > 0:
                            self.pos_x -= 1
                        else:
                            self.pos_x = 0
                    case 'up':
                        if self.level < level_max:
                            self.level += 1
                    case 'down':
                        if self.level > 0:
                            self.level -= 1
                    case _:
                        return False
                return True
            else:
                return False
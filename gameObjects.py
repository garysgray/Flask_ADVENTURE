class Item:
    def __init__(self, name, description):
        self.name = name
        self.description = description

class Room:
    def __init__(self, name, exits, description, inventory):
        self.name = name
        self.exits = exits
        self.description = description
        self.inventory = inventory

class Map:
    def __init__(self):

        baseball = Item('baseball',"its an official MLB")
        bat = Item('bat',"its a nice wooden bat")
        speaker = Item('speaker',"its bluetooth")
        axe = Item('axe',"its a trust axe")
        comic = Item('comic',"its a classic")
        watch = Item('watch',"its ticking")
        knife = Item('knife',"its sharp")
        beer = Item('beer',"its tasty")
        skateboard =Item('skateboard',"its an IOU board!!!!")
        sword = Item('sword',"its well balanced")
        phone = Item('phone',"its the latest and greatest")

        red_room = Room('red', ['south','east'], "Its a reddish in color room", [baseball, speaker])
        blue_room = Room('blue',  ['south','west'], "Its a blueish in color room,", [beer])
        yellow_room = Room('yellow', ['north', 'east'], "Its a yellowish in color room", [axe, skateboard])
        green_room = Room('green',  ['north','west' ], "Its a greenish in color room", [comic])
       
        
        self.floor_1 =[ [red_room, blue_room],
                        [yellow_room, green_room]]

        self.game_map = [self.floor_1]

        self.list_of_rooms = [red_room, blue_room, yellow_room, green_room]

        self.list_of_items = [baseball, bat, speaker, axe, comic, watch, knife, beer, skateboard, sword, phone]

        self.player_start_invent = [watch, knife]
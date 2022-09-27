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

        ball = Item('ball',"its red")
        bat = Item('bat',"its wooden")
        piano = Item('piano',"its fancy")
        axe = Item('axe',"its sharp")
        book = Item('book',"its a classic")
        watch =Item('watch',"its ticking")
        knife =Item('knife',"its sharp")

        red_room = Room('red', ['south','east'], "Its a reddish in color room", [ball, piano])
        blue_room = Room('blue',  ['south','west'], "Its a blueish in color room,", [piano])
        yellow_room = Room('yellow', ['north', 'east'], "Its a yellowish in color room", [axe])
        green_room = Room('green',  ['north','west' ], "Its a greenish in color room", [book])
        
        self.floor_1 =[ [red_room, blue_room],
                        [yellow_room, green_room]]

        self.game_map = [self.floor_1]

        self.list_of_rooms = [red_room, blue_room, yellow_room, green_room]

        self.list_of_items = [ball, bat, piano, axe, book, watch, knife]

        self.player_start_invent = [watch,knife]
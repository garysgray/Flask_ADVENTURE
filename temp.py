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
        axe = Item('axe',"its a trusty axe")
        comic = Item('comic',"its a classic")
        watch = Item('watch',"its ticking")
        knife = Item('knife',"its sharp")
        beer = Item('beer',"its looks tasty")
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
        
    def load_stuff(self, db_player):

        player_location = json.loads(db_player.location)
        player_inventory_from_DB = json.loads(db_player.player_inventory)
        rooms_inventories = json.loads(db_player.room_inventory)

        self.player.id = db_player.id

        #load player location
        self.player.pos_x = player_location['X']
        self.player.pos_y = player_location['Y']

        #loading player invent
        self.player.inventory = []
        all_items = self.map.list_of_items
        for i in player_inventory_from_DB:
            for k, v in i.items():
                for j in range(len(all_items)):
                    if all_items[j].name == k:
                        all_items[j].description = v[0]
                        self.player.inventory.append(all_items[j])

        #loading rooms inventory
        rooms = self.map.list_of_rooms
        all_items = self.map.list_of_items
        for i in range(len(rooms_inventories)):
            rooms[i].inventory = []
            items = rooms_inventories[i]
            for item in range(len(items)):
                temp = items[item]
                for k, v in temp.items():
                    for j in range(len(all_items)):
                        if all_items[j].name == k:
                            all_items[j].description = v[0]
                            rooms[i].inventory.append(all_items[j])

    def save_stuff(self):

            #player location
            player_loc_dict = {'X': self.player.pos_x, 'Y': self.player.pos_y}
            player_loc_dumped = json.dumps(player_loc_dict)

            player_inventory = []
            items = self.player.inventory
            for i in range(len(items)):
                temp_dict = {}
                temp_dict[items[i].name] = [items[i].description]
                player_inventory.append(temp_dict)
            player_inventory_dumped = json.dumps(player_inventory)

            rooms_inventories = []
            rooms = self.map.list_of_rooms
            for i in range(len(rooms)):
                items = rooms[i].inventory
                list_of_items = [] 
                for j in range(len(items)):
                    temp_dict = {}
                    temp_dict[items[j].name] = [items[j].description]
                    list_of_items.append(temp_dict)
                rooms_inventories.append(list_of_items)
            rooms_inventories_dumped = json.dumps(rooms_inventories)

            temp = (player_loc_dumped, player_inventory_dumped, rooms_inventories_dumped ) 
            return temp

    
    
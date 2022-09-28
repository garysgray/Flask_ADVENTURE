from gameObjects import Map
from player import Player
from enum import Enum
import json

class State(Enum):
    LOAD = 0
    PLAY = 1

class Controller:
    def __init__(self):
        self.State = State.LOAD
        self.map = Map()
        self.player = Player()
        self.level = 0
        self.room_info = {}

    def get_new_map(self):
        self.map = None
        self.map = Map()

    def get_room(self):
        try:
            floor = self.map.game_map[self.level]
            room = floor[self.player.pos_y][self.player.pos_x]
            return room
        except:
            return False

    def help(self):
        return "CMD Examples: Go south, south, look book, get book, drop book, read book, help "

    def move_player(self, dir):
        if self.player.move(dir, self.get_room(), len(self.map.game_map)):
            return "You came from the "+ dir +'.'
        else:
            if dir == "":
                return "What direction?"
            return "You cant go "+ dir +'.'

    def drop (self, possible_item):
        item_name = self.player.drop(self.get_room(), possible_item)
        if item_name:
            return "You dropped a " + item_name
        else:
            if type(possible_item) == list:
                return "I cant drop " + possible_item[1]
            return "Drop What?"

    def pick_up(self, possible_item):
        item_name = self.player.pick_up(self.get_room(), possible_item)
        if item_name:    
            return "You picked up a " + item_name
        else:
            if type(possible_item) == list:
                return "I cant pick up " + possible_item[1]
            return "Get What?"
            
    def look(self, possible_item):
        item_info = self.player.look(self.get_room(), possible_item)
        if item_info:
            return item_info
        else:
            if type(possible_item) == list:
                return "I dont see " + possible_item[1]
            return "Look at What?" 

    def run_the_cmd(self, input):
        cmd =""
        possible_item = ""
        move_dir = ""
    
        try:
            cmd = input["CMD"]
            possible_item = input["OBJ"]
        except:
            pass

        if cmd in self.player.directions:
            cmd_response = self.move_player(cmd)

        else:
            match cmd:
                case 'drop':   
                    cmd_response = self.drop(possible_item)  
                case 'pickup':
                    cmd_response = self.pick_up(possible_item)
                case 'look':
                    cmd_response = self.look(possible_item) 
                case 'help':
                    cmd_response = self.help()  
                case 'move':
                    for dir in self.player.directions:
                        if dir in possible_item:
                         move_dir = dir
                    cmd_response = self.move_player(move_dir)
                case _:
                    cmd_response ="I dont understand: " + cmd +", Please try again."

        room = self.get_room()
        self.room_info['CMD_RESPONSE']= cmd_response
        self.room_info['ROOM_NAME']= room.name
        self.room_info['ROOM_EXITS'] = room.exits
        self.room_info['ROOM_DESCRIPTION'] = room.description
        self.room_info['ROOM_INVENTORY'] = room.inventory
        self.room_info['SENT_CMD'] = cmd

    def parse_it(self, user_input):
        cmd_info = {}
        split_input = user_input.split()

        if len(split_input) == 1:
            cmd_info["CMD"] = split_input[-1]
            cmd_info["OBJ"] = "NO_ITEM_IN_CMD"
            return cmd_info

        elif "drop" in split_input :
                cmd_info["CMD"] = "drop"
                cmd_info["OBJ"] = split_input 
                return cmd_info

        elif "pickup" in split_input or "get" in split_input:
                cmd_info["CMD"] = "pickup"
                cmd_info["OBJ"] = split_input 
                return cmd_info

        elif "help" in split_input :
                cmd_info["CMD"] = "help"
                cmd_info["OBJ"] = " NO_ITEMS_FOR_HELP_WIP"
                return cmd_info

        elif "look" in split_input :
                cmd_info["CMD"] = "look"
                cmd_info["OBJ"] = split_input
                return cmd_info

        elif "go" in split_input or "move" in split_input:
                cmd_info["CMD"] = "move"
                cmd_info["OBJ"] = split_input
                return cmd_info

        else:
            #this is a big catch all for one word cmds that i did not like ha
            cmd_info["CMD"] = user_input
            cmd_info["OBJ"] = "NO_ITEM"
            return cmd_info


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
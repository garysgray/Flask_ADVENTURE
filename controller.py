from gameObjects import Map, Item
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
        self.player = Player(self.map.game_map)  # ✅ Pass the game map
        self.room_info = {}

    def get_new_map(self):
        self.map = Map()

    def get_room(self):
        try:
            floor = self.map.game_map[self.player.level]
            room = floor[self.player.pos_y][self.player.pos_x]

            print(f"[DEBUG] Floor: {self.player.level}, Y: {self.player.pos_y}, X: {self.player.pos_x} -> {room.name}")

            return room
        except:
            return False

    def help(self):
        return "CMD Examples: Go south, south, look book, get book, drop book, read book, help"

    def move_player(self, dir):
        if self.player.move(dir, self.get_room(), len(self.map.game_map)):
            return f"You came from the {dir}."
        else:
            if dir == "":
                return "What direction?"
            return f"You cant go {dir}."

    def drop(self, possible_item):
        item_name = self.player.drop(self.get_room(), possible_item)
        if item_name:
            return f"You dropped a {item_name}"
        else:
            if isinstance(possible_item, list):
                return f"I cant drop {possible_item[1]}"
            return "Drop What?"

    def pick_up(self, possible_item):
        item_name = self.player.pick_up(self.get_room(), possible_item)
        if item_name:    
            return f"You picked up a {item_name}"
        else:
            if isinstance(possible_item, list):
                return f"I cant pick up {possible_item[1]}"
            return "Get What?"
            
    def look(self, possible_item):
        item_info = self.player.look(self.get_room(), possible_item)
        if item_info:
            return item_info
        else:
            if isinstance(possible_item, list):
                return f"I dont see {possible_item[1]}"
            return "Look at What?" 
        
    def change_room_description(self, possible_item):
        """Change the current room's description"""
        room = self.get_room()
        if isinstance(possible_item, list):
            words = [word for word in possible_item if word != 'changedesc']
            new_description = ' '.join(words)
        else:
            new_description = possible_item
        room.description = new_description
        return f"The {room.name} room's appearance has changed!" 

    def run_the_cmd(self, input_dict):
        """Execute a parsed command and update room info."""
        cmd = input_dict.get("CMD", "")
        possible_item = input_dict.get("OBJ", "")

        if cmd in self.player.directions:
            cmd_response = self.move_player(cmd)
        elif cmd == 'drop':
            cmd_response = self.drop(possible_item)
        elif cmd == 'pickup':
            cmd_response = self.pick_up(possible_item)
        elif cmd == 'look':
            cmd_response = self.look(possible_item)
        elif cmd == 'help':
            cmd_response = self.help()
        elif cmd == 'move':
            move_dir = next((d for d in self.player.directions if d in possible_item), "")
            cmd_response = self.move_player(move_dir)
        elif cmd == 'use':
            cmd_response = self.use_item(possible_item)
        elif cmd == 'changedesc':
            cmd_response = self.change_room_description(possible_item)
        else:
            cmd_response = f"I don't understand: {cmd}. Please try again."

        event_messages = self.check_events()

        room = self.get_room()
        self.room_info = {
            'CMD_RESPONSE': cmd_response,
            'ROOM_NAME': room.name,
            'ROOM_EXITS': room.exits,
            'ROOM_DESCRIPTION': room.description,
            'ROOM_INVENTORY': room.inventory,
            'SENT_CMD': cmd,
            'EVENT_MESSAGES': event_messages
        }

    def parse_it(self, user_input):
        cmd_info = {}
        split_input = user_input.split()

        if len(split_input) == 1:
            cmd_info["CMD"] = split_input[-1]
            cmd_info["OBJ"] = "NO_ITEM_IN_CMD"
            return cmd_info
        elif "drop" in split_input:
            cmd_info["CMD"] = "drop"
            cmd_info["OBJ"] = split_input 
            return cmd_info
        elif "pickup" in split_input or "get" in split_input:
            cmd_info["CMD"] = "pickup"
            cmd_info["OBJ"] = split_input 
            return cmd_info
        elif "help" in split_input:
            cmd_info["CMD"] = "help"
            cmd_info["OBJ"] = " NO_ITEMS_FOR_HELP_WIP"
            return cmd_info
        elif "look" in split_input:
            cmd_info["CMD"] = "look"
            cmd_info["OBJ"] = split_input
            return cmd_info
        elif "go" in split_input or "move" in split_input:
            cmd_info["CMD"] = "move"
            cmd_info["OBJ"] = split_input
            return cmd_info
        elif "use" in split_input:
            cmd_info["CMD"] = "use"
            # Check if "with" is in the command
            if "with" in split_input:
                use_index = split_input.index("use")
                with_index = split_input.index("with")
                item = split_input[use_index + 1]      # word between "use" and "with"
                target = split_input[with_index + 1]   # word after "with"
                cmd_info["OBJ"] = {'item': item, 'target': target}
            else:
                cmd_info["OBJ"] = split_input
            return cmd_info
        elif "changedesc" in split_input:
            cmd_info["CMD"] = "changedesc"
            cmd_info["OBJ"] = split_input
            return cmd_info
        else:
            cmd_info["CMD"] = user_input
            cmd_info["OBJ"] = "NO_ITEM"
            return cmd_info
    
    def load_stuff_from_data_base(self, db_player):
        player_location = json.loads(db_player.location)
        player_inventory_from_DB = json.loads(db_player.player_inventory)
        rooms_data = json.loads(db_player.room_inventory)

        self.player.id = db_player.id
        self.player.pos_x = player_location['X']
        self.player.pos_y = player_location['Y']

        # Load event tracking
        self.player.visited_rooms = player_location.get('visited_rooms', [])
        self.player.completed_events = player_location.get('completed_events', [])

        # Load player inventory - CREATE FRESH ITEMS
        self.player.inventory = []
        for item_dict in player_inventory_from_DB:
            for name, details in item_dict.items():
                fresh_item = Item(name, details[0])
                self.player.inventory.append(fresh_item)

        # CREATE FRESH ROOMS from complete saved data
        fresh_rooms = self.map.create_fresh_rooms_from_saved_data(rooms_data)
        self.map.list_of_rooms = fresh_rooms
        self.map.floor_1 = [[fresh_rooms[0], fresh_rooms[1]],
                            [fresh_rooms[2], fresh_rooms[3]]]
        self.map.floor_2 = [[fresh_rooms[4], fresh_rooms[5], fresh_rooms[6]]]
        self.map.game_map = [self.map.floor_1, self.map.floor_2]

    def save_stuff_to_data_base(self):
        player_data = {
            'X': self.player.pos_x, 
            'Y': self.player.pos_y,
            'visited_rooms': self.player.visited_rooms,
            'completed_events': self.player.completed_events
        }
        player_loc_dumped = json.dumps(player_data)

        player_inventory = []
        items = self.player.inventory
        for i in range(len(items)):
            temp_dict = {items[i].name: [items[i].description]}
            player_inventory.append(temp_dict)
        player_inventory_dumped = json.dumps(player_inventory)

        rooms_data = []
        rooms = self.map.list_of_rooms
        for room in rooms:
            room_items = []
            for item in room.inventory:
                room_items.append({item.name: [item.description]})
            room_data = {
                'name': room.name,
                'exits': room.exits,
                'description': room.description,
                'inventory': room_items,
                'exit_destinations': room.exit_destinations
            }
            rooms_data.append(room_data)
        
        rooms_data_dumped = json.dumps(rooms_data)

        return (player_loc_dumped, player_inventory_dumped, rooms_data_dumped)
    
    def use_item(self, possible_item):
        """Use an item alone or with a target, only if the item is in inventory or room"""
        current_room = self.get_room()
        
        # Helper function to check if item exists
        def has_item(name):
            # Check player inventory
            for i in self.player.inventory:
                if i.name == name:
                    return True
            # # Check current room inventory
            # for i in current_room.inventory:
            #     if i.name == name:
            #         return True
            return False

        # "use key with door" - using item ON something
        if isinstance(possible_item, dict):
            item = possible_item['item']
            target = possible_item['target']
            
            if not has_item(item):
                return f"You don't have {item} in hand."
            
            # Check events for item+target combination
            event_result = self.check_use_with_events(item, target)
            if event_result:
                return event_result
            return f"You can't use {item} with {target}"
        
        # "use knife" - using item alone
        else:
            item_name = possible_item if isinstance(possible_item, str) else possible_item[1]
            if not has_item(item_name):
                return f"You don't have {item_name} here to use."
            
            result = self.player.use(possible_item)
            if result:
                return result
            
            if isinstance(possible_item, list):
                return f"I can't use {possible_item[1]}"
            return "Use what?"


    def check_events(self):
        """Check if any events should fire (e.g., achievements, global triggers)."""
        messages = []

        current_room = self.get_room()
        if not current_room:
            return messages  # safety in case get_room() fails

        # Track visited rooms
        if current_room.name not in self.player.visited_rooms:
            self.player.visited_rooms.append(current_room.name)

        for event in self.map.event_recipes:
            if event['id'] in self.player.completed_events:
                continue

            # ------------------------
            # All rooms visited events
            # ------------------------
            if event['check_type'] == 'all_rooms_visited':
                required_rooms = event['parameters']['required_rooms']
                if all(room in self.player.visited_rooms for room in required_rooms):
                    result = event['result']

                    # Handle single or multiple open_exit entries
                    if 'open_exit' in result:
                        exits_to_open = result['open_exit']

                        if not isinstance(exits_to_open, list):
                            exits_to_open = [exits_to_open]

                        for exit_data in exits_to_open:
                            for room in self.map.list_of_rooms:
                                if room.name == exit_data['room']:
                                    if exit_data['direction'] not in room.exits:
                                        room.exits.append(exit_data['direction'])
                                        room.exit_destinations[exit_data['direction']] = {
                                            'floor': exit_data['destination']['floor'],
                                            'x': exit_data['destination']['x'],
                                            'y': exit_data['destination']['y']
                                        }

                    # Handle message
                    if 'message' in result:
                        messages.append(result['message'])

                    self.player.completed_events.append(event['id'])

        return messages

    def check_use_with_events(self, item, target):
        """Check if using an item with a target triggers an event"""
        current_room = self.get_room()
        
        for event in self.map.event_recipes:
            # Skip already completed events
            if event['id'] in self.player.completed_events:
                continue
            
            if event['check_type'] == 'item_used_with':
                params = event['parameters']
                
                # Check if item, target, and room all match
                if (params['item'] == item and 
                    params['target'] == target and 
                    params['room'] == current_room.name):
                    
                    # Fire the event!
                    result = event['result']
                    
                    if 'open_exit' in result:
                        exits_to_open = result['open_exit']   # ← MUST come first

                        if not isinstance(exits_to_open, list):
                            exits_to_open = [exits_to_open]

                        for exit_data in exits_to_open:
                            for room in self.map.list_of_rooms:
                                if room.name == exit_data['room']:
                                    if exit_data['direction'] not in room.exits:
                                        room.exits.append(exit_data['direction'])
                                        room.exit_destinations[exit_data['direction']] = {
                                            'floor': exit_data['destination']['floor'],
                                            'x': exit_data['destination']['x'],
                                            'y': exit_data['destination']['y']
                                        }
                    
                    if 'add_item' in result:
                        item_to_add = self.map.make_item(result['add_item']['item'])
                        for room in self.map.list_of_rooms:
                            if room.name == result['add_item']['room']:
                                room.inventory.append(item_to_add)
                    
                    if 'message' in result:
                        self.player.completed_events.append(event['id'])
                        return result['message']
        
        return None

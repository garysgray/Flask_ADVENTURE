from game.gameObjects import Map
from game.player import Player
from game.parser import Parser
from game.actions import ActionHandler
from game.events import EventManager
from game.persistence import PersistenceManager
from enum import Enum

class State(Enum):
    LOAD = 0
    PLAY = 1

class Controller:
    def __init__(self):
        self.State = State.LOAD
        self.map = Map()
        self.player = Player(self.map.game_map, {k: v['use'] for k, v in self.map.item_recipes.items()})
        self.room_info = {}

        self.parser = Parser(self)
        self.actions = ActionHandler(self)
        self.events = EventManager(self)
        self.persistence = PersistenceManager(self)

    def get_room(self):
        try:
            floor = self.map.game_map[self.player.level]
            room = floor[self.player.pos_y][self.player.pos_x]
            pos = (self.player.level, self.player.pos_y, self.player.pos_x)
            if pos not in self.player.visited_rooms:
                self.player.visited_rooms.append(pos)
            return room
        except:
            return False


    def get_new_map(self):
        self.map = Map()

    def parse_it(self, user_input):
        return self.parser.parse(user_input)

    def run_the_cmd(self, input_dict):
        cmd = input_dict.get("CMD", "")
        possible_item = input_dict.get("OBJ", "")
        cmd_response = self.actions.execute(cmd, possible_item)
        event_messages = self.events.check_events()
        room = self.get_room()
        self.room_info = {
            'CMD_RESPONSE': cmd_response,
            'ROOM_NAME': room.name,
            'ROOM_EXITS': room.exits,
            'ROOM_DESCRIPTION': room.description,
            'ROOM_INVENTORY': room.inventory,
            'SENT_CMD': cmd,
            'EVENT_MESSAGES': event_messages,
            'ROOM_EXIT_DEST': room.exit_destinations,
        }

    def check_use_with_events(self, item, target):
        return self.events.check_use_with_events(item, target)

    def load_stuff_from_data_base(self, db_player):
        self.persistence.load(db_player)

    def save_stuff_to_data_base(self):
        return self.persistence.save()
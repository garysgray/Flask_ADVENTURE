from game.gameObjects import Map
from game.player import Player
from game.parser import Parser
from game.actions import ActionHandler
from game.event_manager import EventManager
from game.persistence import PersistenceManager
from enum import Enum


class State(Enum):
    LOAD = 0
    PLAY = 1


class Controller:
    """
    Central orchestrator for all game systems.
    One controller instance per player, stored in memory on the app object.
    """

    def __init__(self, file_path=None):
        self.State  = State.LOAD
        self.map    = Map(file_path=file_path)
        self.player = Player(self.map.game_map)
        self.player.inventory = [self.map.make_item(item.name) for item in self.map.player_start_invent]

        self.room_info = {}

        self.parser      = Parser(self)
        self.actions     = ActionHandler(self)
        self.events      = EventManager(self)
        self.persistence = PersistenceManager(self)

    # ─── Map ──────────────────────────────────────────────────────────────────

    def get_room(self):
        try:
            floor = self.map.game_map[self.player.level]
            room  = floor[self.player.pos_y][self.player.pos_x]
            pos   = (self.player.level, self.player.pos_y, self.player.pos_x)
            if pos not in self.player.visited_rooms:
                self.player.visited_rooms.append(pos)
            if room.name not in self.player.visited_room_names:
                self.player.visited_room_names.append(room.name)
            return room
        except Exception:
            return False

    def get_new_map(self):
        self.map = Map()

    # ─── Command Pipeline ─────────────────────────────────────────────────────

    def parse_it(self, user_input):
        return self.parser.parse(user_input)

    def run_the_cmd(self, input_dict):
        cmd           = input_dict.get("CMD", "")
        possible_item = input_dict.get("OBJ", "")

        cmd_response, use_event_message = self.actions.execute(cmd, possible_item)

        event_messages = self.events.check_events()
        if use_event_message:
            event_messages.append(use_event_message)

        game_won = self.events.check_win()
        room     = self.get_room()

        self.room_info = {
            'CMD_RESPONSE':     cmd_response,
            'ROOM_NAME':        getattr(room, 'display_name', room.name.replace('_', ' ')),
            'ROOM_EXITS':       room.exits,
            'ROOM_DESCRIPTION': room.description,
            'ROOM_INVENTORY':   room.inventory,
            'SENT_CMD':         cmd,
            'EVENT_MESSAGES':   event_messages,
            'ROOM_EXIT_DEST':   room.exit_destinations,
            'GAME_WON':         game_won,
            'SHOW_JOURNAL':     cmd == 'journal',
        }
        self.room_info['ROOM_DESCRIPTION'] = self.room_info['ROOM_DESCRIPTION'].replace("\n", "<br>")


    # ─── Event Passthroughs ───────────────────────────────────────────────────

    def evaluate_use_with(self, item, target):
        return self.events.evaluate_use_with(item, target)

    def evaluate_interaction(self, item, target):
        return self.events.evaluate_use_with(item, target)

    def check_use_with_events(self, item, target):
        return self.events.check_use_with_events(item, target)

    def check_use_with_events_already_done(self, item, target):
        return self.events.check_use_with_events_already_done(item, target)

    def evaluate_solo(self, target, action=None):
        return self.events.evaluate_solo(target, action)

    def check_solo_events_already_done(self, target, action=None):
        return self.events.check_solo_events_already_done(target, action)

    # ─── Persistence Passthroughs ─────────────────────────────────────────────

    def load_stuff_from_data_base(self, db_player):
        self.persistence.load(db_player)

    def save_stuff_to_data_base(self):
        return self.persistence.save()

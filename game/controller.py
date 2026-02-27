from game.gameObjects import Map
from game.player import Player
from game.parser import Parser
from game.actions import ActionHandler
from game.event_manager import EventManager
from game.persistence import PersistenceManager
from enum import Enum


class State(Enum):
    LOAD = 0  # first visit this session — needs to load from DB
    PLAY = 1  # active session — state already loaded


class Controller:
    """
    Central orchestrator for all game systems.
    One controller instance per player, stored in memory on the app object.
    On first visit (State.LOAD) saved data is loaded from the database.
    After that (State.PLAY) all state lives here in memory until the session ends.
    """

    def __init__(self):
        self.State  = State.LOAD
        self.map    = Map()
        self.player = Player(self.map.game_map)

        self.room_info = {}  # dict passed to the template each request

        # all systems receive a reference to this controller
        # so they can reach each other through self.ctrl
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
        except:
            return False

    def get_new_map(self):
        """Rebuilds the map from YAML — useful for dev reloading."""
        self.map = Map()

    # ─── Command Pipeline ─────────────────────────────────────────────────────

    def parse_it(self, user_input):
        """Parses raw text input into a structured command dict."""
        return self.parser.parse(user_input)

    def run_the_cmd(self, input_dict):
        """
        Executes a parsed command and builds room_info for the template.

        Flow:
        1. Execute the command via actions — returns (cmd_response, use_event_message)
        2. Check all passive events (e.g. all_rooms_visited)
        3. Merge any event message from use_item with passive event messages
        4. Check win conditions
        5. Build room_info dict for the template
        """
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
            'ROOM_NAME':        room.name,
            'ROOM_EXITS':       room.exits,
            'ROOM_DESCRIPTION': room.description,
            'ROOM_INVENTORY':   room.inventory,
            'SENT_CMD':         cmd,
            'EVENT_MESSAGES':   event_messages,
            'ROOM_EXIT_DEST':   room.exit_destinations,
            'GAME_WON':         game_won,
            'SHOW_JOURNAL':     cmd == 'journal',
        }

    # ─── Event Passthroughs ───────────────────────────────────────────────────
    # These keep the event manager internal — other systems call controller,
    # not event_manager directly.

    def check_use_with_events(self, item, target):
        """Fires an item+target event if one matches. Returns event message or None."""
        return self.events.check_use_with_events(item, target)

    def check_use_with_events_already_done(self, item, target):
        """Returns already-done message if this item+target event was completed before."""
        return self.events.check_use_with_events_already_done(item, target)

    # ─── Persistence Passthroughs ─────────────────────────────────────────────

    def load_stuff_from_data_base(self, db_player):
        """Loads saved player and room state from the database into this controller."""
        self.persistence.load(db_player)

    def save_stuff_to_data_base(self):
        """Serializes current game state for saving to the database."""
        return self.persistence.save()
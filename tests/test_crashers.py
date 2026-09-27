import unittest
from unittest.mock import MagicMock
from game.event_types import ItemUsedWithEvent


class TestCrashers(unittest.TestCase):
    def test_2a_item_used_with_event_null_room_guard(self):
        """
        2a: When ctrl.get_room() returns None or False (e.g. out of bounds, invalid tile, or failure),
        ItemUsedWithEvent.check() should safely return False instead of raising AttributeError on .name.
        """
        event = ItemUsedWithEvent(
            id="test_event",
            result={},
            item="key",
            target="chest",
            room="treasure_room"
        )
        ctrl = MagicMock()
        ctrl.player.completed_events = []
        ctrl.player.inventory = []

        # 1. When ctrl.get_room() is None
        ctrl.get_room.return_value = None
        result = event.check(ctrl, "key", "chest")
        self.assertFalse(result)

        # 2. When ctrl.get_room() is False (current pre-2f behavior)
        ctrl.get_room.return_value = False
        result_false = event.check(ctrl, "key", "chest")
        self.assertFalse(result_false)

    def test_2b_fixture_get_examine_text_dict_guard(self):
        """
        2b: When Fixture.examine is a string (or other non-dict type),
        Fixture.get_examine_text() should return it directly (or handle safely)
        instead of raising TypeError or crashing when doing `self.current_state in self.examine`.
        """
        from game.gameObjects import Fixture

        # 1. examine is a string (including strings containing substring 'default' which would crash with TypeError on string['default'])
        fixture_str = Fixture(name="pedestal", examine="It is a solid stone pedestal.")
        self.assertEqual(fixture_str.get_examine_text(), "It is a solid stone pedestal.")

        fixture_default_str = Fixture(name="valve", examine="The default emergency valve is rusty.")
        self.assertEqual(fixture_default_str.get_examine_text(), "The default emergency valve is rusty.")

        # 2. examine is empty/None
        fixture_none = Fixture(name="pedestal", examine=None)
        self.assertEqual(fixture_none.get_examine_text(), "You see nothing unusual about the pedestal.")

        # 3. examine is a standard dict with states
        fixture_dict = Fixture(
            name="pedestal",
            examine={"default": "A bare stone pedestal.", "active": "A glowing stone pedestal."},
            current_state="active"
        )
        self.assertEqual(fixture_dict.get_examine_text(), "A glowing stone pedestal.")

    def test_2c_make_event_never_returns_raw_dict(self):
        """
        2c: Map.make_event() should always construct a typed Event (e.g. ECAEvent)
        or raise a clear AdventureConfigError, never quietly return a raw dict that will crash
        later with AttributeError on event.id / event.conditions.
        """
        from game.gameObjects import Map
        from game.event_types import ECAEvent
        from game.loader import AdventureConfigError

        # Instantiate a bare map without full file loading
        game_map = Map.__new__(Map)
        game_map.file_path = "test.yaml"

        # 1. Standard event dict with trigger/conditions -> constructs ECAEvent
        standard_data = {
            'id': 'test_event',
            'trigger': {'type': 'on_turn'},
            'conditions': [{'type': 'in_room', 'room': 'atrium'}],
            'result': {'message': 'Hello'}
        }
        event_obj = game_map.make_event(standard_data)
        self.assertIsInstance(event_obj, ECAEvent)
        self.assertEqual(event_obj.id, 'test_event')

        # 2. Event dict missing trigger and conditions -> constructs ECAEvent, NOT raw dict
        raw_dict_data = {
            'id': 'bare_event',
            'result': {'message': 'Hello'}
        }
        res = game_map.make_event(raw_dict_data)
        self.assertNotIsInstance(res, dict)
        self.assertIsInstance(res, ECAEvent)
        self.assertEqual(res.id, 'bare_event')

    def test_2c_bare_event_never_matches_or_fires(self):
        """
        Confirms that a bare event (constructed with no trigger or conditions)
        never matches solo actions, never matches use-with actions, never matches
        on_turn passive triggers, and never fires.
        """
        from game.gameObjects import Map
        from game.event_manager import EventManager

        game_map = Map.__new__(Map)
        game_map.file_path = "test.yaml"
        bare_event = game_map.make_event({'id': 'bare_event', 'result': {'message': 'Fired!'}})

        # 1. matches_solo must be False
        self.assertFalse(bare_event.matches_solo('dummy', 'strike'))
        self.assertFalse(bare_event.matches_solo('dummy'))

        # 2. matches_use_with must be False
        self.assertFalse(bare_event.matches_use_with('key', 'gate'))
        self.assertFalse(bare_event.matches_use_with('key', 'gate', player_has_target=True))

        # 3. is_passive must be False
        self.assertFalse(bare_event.is_passive)

        # 4. In EventManager, evaluating use-with or passive checks must never fire this event
        ctrl = MagicMock()
        ctrl.map.event_recipes = [bare_event]
        ctrl.player.completed_events = []
        ctrl.player.inventory = []
        ctrl.player.journal = []
        ctrl.get_room.return_value = MagicMock(name='room', exits=[])

        em = EventManager(ctrl)

        # Passive check
        triggered = em.check_events()
        self.assertEqual(triggered, [])
        self.assertNotIn('bare_event', ctrl.player.completed_events)

        # Active use-with check
        eval_result = em.evaluate_use_with('key', 'gate')
        self.assertEqual(eval_result['status'], 'meaningless')
        self.assertNotIn('bare_event', ctrl.player.completed_events)

    def test_2c_malformed_event_recipe_raises_adventure_config_error(self):
        """
        Confirms that non-dict or missing 'id' event recipes raise AdventureConfigError
        with filename, message, details, and fix populated.
        """
        from game.gameObjects import Map
        from game.loader import AdventureConfigError

        game_map = Map.__new__(Map)
        game_map.file_path = "data/broken_adventure.yaml"

        # 1. Non-dict recipe
        with self.assertRaises(AdventureConfigError) as ctx1:
            game_map.make_event("not_a_dict_event")
        self.assertIn("Event definition must be a dictionary", str(ctx1.exception))
        self.assertEqual(ctx1.exception.filename, "data/broken_adventure.yaml")
        self.assertIsNotNone(ctx1.exception.fix)

        # 2. Dict missing 'id' key
        with self.assertRaises(AdventureConfigError) as ctx2:
            game_map.make_event({'trigger': {'type': 'on_turn'}, 'result': {}})
        self.assertIn("missing required 'id' key", str(ctx2.exception))
        self.assertEqual(ctx2.exception.filename, "data/broken_adventure.yaml")
        self.assertIsNotNone(ctx2.exception.fix)

    def test_2d_ragged_grid_north_south_bounds_check(self):
        """
        2d: Player.move() on cardinal north/south moves in a ragged floor grid
        must check column bounds (self.pos_x < len(target_row)) so moving into
        a shorter row returns False (and normal "can't go" message) instead of raising IndexError.
        """
        from game.player import Player
        from game.actions import ActionHandler

        # Room mock that permits north and south exits
        class FakeRoom:
            def __init__(self, name, exits):
                self.name = name
                self.exits = exits
                self.exit_destinations = {}
                self.locked_exits = []

        room_center = FakeRoom("center", ["north", "south", "east", "west"])
        room_north = FakeRoom("north_room", ["south"])
        room_south = FakeRoom("south_room", ["north"])

        # Ragged floor grid:
        # Row 0: length 1 -> [room_north]
        # Row 1: length 3 -> [None, None, room_center]  (pos_y=1, pos_x=2)
        # Row 2: length 2 -> [room_south, None]
        ragged_floor = [
            [room_north],
            [None, None, room_center],
            [room_south, None]
        ]
        game_map = [ragged_floor]

        # Player spawns at (pos_x=2, pos_y=1) in room_center
        player = Player(game_map=game_map, location={'floor': 0, 'x': 2, 'y': 1})

        # Mock controller to test ActionHandler move_player return message
        mock_ctrl = MagicMock()
        mock_ctrl.player = player
        mock_ctrl.map.game_map = game_map
        mock_ctrl.get_room.return_value = room_center
        action_handler = ActionHandler(mock_ctrl)

        # 1. Moving north: target row 0 has length 1, but player is at x=2.
        # Moving north should fail safely and return False without IndexError.
        move_north_result = player.move('north', room_center, len(game_map))
        self.assertFalse(move_north_result)
        self.assertEqual(player.pos_x, 2)
        self.assertEqual(player.pos_y, 1)

        msg_north = action_handler.move_player('north')
        self.assertEqual(msg_north, "You can't go north.")

        # 2. Moving south: target row 2 has length 2, but player is at x=2.
        # Moving south should fail safely and return False without IndexError.
        move_south_result = player.move('south', room_center, len(game_map))
        self.assertFalse(move_south_result)
        self.assertEqual(player.pos_x, 2)
        self.assertEqual(player.pos_y, 1)

        msg_south = action_handler.move_player('south')
        self.assertEqual(msg_south, "You can't go south.")

    def test_2e_match_item_exact_or_whole_word_matching(self):
        """
        2e: _match_item exact or whole-word matching.
        Cover:
          - "pin" must not match "spinning wheel"
          - "key" must not match "monkey"
          - "brass key" matching an item named "brass_key"
          - a single-word item matching a multi-word target that contains it as a whole word
        """
        from game.player import Player

        class DummyItem:
            def __init__(self, name, aliases=None, keywords=None):
                self.name = name
                self.aliases = aliases or []
                self.keywords = keywords or []

        player = Player()

        item_wheel = DummyItem("spinning_wheel")
        item_monkey = DummyItem("monkey")
        item_pin = DummyItem("pin")
        item_key = DummyItem("key")
        item_brass_key = DummyItem("brass_key")

        # 1. False positive cases:
        # "pin" must not match "spinning wheel" (or "spinning_wheel")
        self.assertFalse(player._match_item(item_pin, "spinning wheel"))
        self.assertFalse(player._match_item(item_pin, ["spinning", "wheel"]))
        self.assertFalse(player._match_item(item_wheel, "pin"))
        self.assertFalse(player._match_item(item_wheel, ["pin"]))

        # "key" must not match "monkey"
        self.assertFalse(player._match_item(item_key, "monkey"))
        self.assertFalse(player._match_item(item_key, ["monkey"]))
        self.assertFalse(player._match_item(item_monkey, "key"))
        self.assertFalse(player._match_item(item_monkey, ["key"]))

        # 2. Legitimate cases:
        # "brass key" matching an item named "brass_key"
        self.assertTrue(player._match_item(item_brass_key, "brass key"))
        self.assertTrue(player._match_item(item_brass_key, ["brass", "key"]))

        # A single-word item matching a multi-word target that contains it as a whole word
        # e.g. item named "key" matching target "old key" or ["old", "key"]
        self.assertTrue(player._match_item(item_key, "old key"))
        self.assertTrue(player._match_item(item_key, ["old", "key"]))

    def test_2f_get_room_and_visited_recording(self):
        """
        2f:
        - get_room() returns None on failure and no longer mutates visited state.
        - None room does not crash run_the_cmd.
        - Calling get_room() repeatedly does not change visited_rooms.
        - Moving into a room records it.
        - Starting room is recorded at game start.
        - Save/load round trip keeps visited data and visited rooms still render as visited.
        """
        import json
        from game.controller import Controller
        from game.gameObjects import Room

        # Build a minimal controller with a 2-room grid
        ctrl = Controller.__new__(Controller)
        ctrl.room_info = {}

        room_a = Room("start_room", exits=["east"], inventory=[], display_name="Start Room")
        room_b = Room("east_room", exits=["west"], inventory=[], display_name="East Room")
        grid = [[[room_a, room_b]]]

        from game.player import Player
        from game.actions import ActionHandler
        from game.event_manager import EventManager
        from game.persistence import PersistenceManager
        from game.parser import Parser

        ctrl.map = MagicMock()
        ctrl.map.game_map = grid
        ctrl.map.list_of_rooms = [room_a, room_b]
        ctrl.map.starting_location = {'floor': 0, 'x': 0, 'y': 0}
        ctrl.map.player_start_invent = []
        ctrl.map.intro = {'title': 'Test Adventure'}
        ctrl.map.win_conditions = []
        ctrl.map.win_screen = {}

        player = Player(game_map=grid, location={'floor': 0, 'x': 0, 'y': 0})
        ctrl.player = player
        ctrl.parser = Parser(ctrl)
        ctrl.actions = ActionHandler(ctrl)
        ctrl.events = EventManager(ctrl)
        ctrl.persistence = PersistenceManager(ctrl)

        # 1. Starting room is recorded
        ctrl.record_starting_room()
        self.assertIn((0, 0, 0), ctrl.player.visited_rooms)
        self.assertIn("start_room", ctrl.player.visited_room_names)

        # 2. get_room() idempotence: calling get_room repeatedly does NOT mutate visited_rooms
        initial_len = len(ctrl.player.visited_rooms)
        initial_names_len = len(ctrl.player.visited_room_names)
        r1 = ctrl.get_room()
        r2 = ctrl.get_room()
        self.assertEqual(r1, room_a)
        self.assertEqual(r2, room_a)
        self.assertEqual(len(ctrl.player.visited_rooms), initial_len)
        self.assertEqual(len(ctrl.player.visited_room_names), initial_names_len)

        # 3. get_room() returns None on failure
        ctrl.player.pos_x = 99  # Out of bounds
        out_of_bounds_room = ctrl.get_room()
        self.assertIsNone(out_of_bounds_room)
        # Calling get_room() on out of bounds does not add anything
        self.assertEqual(len(ctrl.player.visited_rooms), initial_len)

        # 4. None room does not crash run_the_cmd and handles it gracefully
        ctrl.run_the_cmd({"CMD": "look", "OBJ": ""})
        self.assertIn('ROOM_NAME', ctrl.room_info)
        self.assertIn('ROOM_DESCRIPTION', ctrl.room_info)

        # Reset player to start_room
        ctrl.player.pos_x = 0
        ctrl.player.pos_y = 0
        ctrl.player.level = 0

        # 5. Moving into a room records it
        # Move east into room_b
        cmd_resp, _ = ctrl.actions.execute("move", "east")
        self.assertIn((0, 0, 1), ctrl.player.visited_rooms)
        self.assertIn("east_room", ctrl.player.visited_room_names)

        # 6. Save/load round-trip keeps visited data and visited rooms still render
        loc_json, p_inv_json, r_inv_json = ctrl.persistence.save()
        db_mock = MagicMock()
        db_mock.id = 1
        db_mock.location = loc_json
        db_mock.player_inventory = p_inv_json
        db_mock.room_inventory = r_inv_json

        # Create fresh controller to load into
        ctrl2 = Controller.__new__(Controller)
        ctrl2.map = ctrl.map
        ctrl2.player = Player(game_map=grid, location={'floor': 0, 'x': 0, 'y': 0})
        ctrl2.parser = Parser(ctrl2)
        ctrl2.actions = ActionHandler(ctrl2)
        ctrl2.events = EventManager(ctrl2)
        ctrl2.persistence = PersistenceManager(ctrl2)

        ctrl2.persistence.load(db_mock)

        # Check visited rooms preserved
        # Note: JSON turns tuples into lists: [[0, 0, 0], [0, 0, 1]]
        # In app.py:
        # visited_rooms = []
        # for pos in ctrl.player.visited_rooms:
        #     if isinstance(pos, (list, tuple)) and len(pos) == 3:
        #         visited_rooms.append((pos[0], pos[1], pos[2]))
        # pos = (current_floor, r_idx, c_idx)
        # (pos in visited_rooms) should be True for both (0, 0, 0) and (0, 0, 1)
        visited_in_app = [
            (p[0], p[1], p[2])
            for p in ctrl2.player.visited_rooms
            if isinstance(p, (list, tuple)) and len(p) == 3
        ]
        self.assertIn((0, 0, 0), visited_in_app)
        self.assertIn((0, 0, 1), visited_in_app)
        self.assertIn("start_room", ctrl2.player.visited_room_names)
        self.assertIn("east_room", ctrl2.player.visited_room_names)

    def test_2f_broken_state_does_not_overwrite_save(self):
        """
        With a player whose saved coordinates point at an empty tile (falsy room),
        a POST command must not modify db_player.location and must not raise,
        rendering safely without corrupting the DB.
        """
        from app import app, db, User, DB_Player
        import json

        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        with app.app_context():
            db.create_all()
            # Setup test user and player
            user = User.query.filter_by(username="test_empty_tile_user").first()
            if not user:
                user = User(username="test_empty_tile_user")
                user.set_password("password")
                db.session.add(user)
                db.session.commit()

            # Location pointing to an invalid/empty tile (floor 0, y=99, x=99)
            broken_loc = json.dumps({
                "X": 99,
                "Y": 99,
                "floor": 0,
                "visited_rooms": [[0, 0, 0]],
                "completed_events": [],
                "journal": [],
                "has_seen_intro": True,
                "visited_room_names": ["start_room"],
                "unlocked_actions": None
            })

            player = DB_Player(
                user.id,
                "Broken Save",
                broken_loc,
                "[]",
                "[]",
                "look"
            )
            db.session.add(player)
            db.session.commit()
            player_id = player.id

            client = app.test_client()
            with client.session_transaction() as sess:
                sess['user_id'] = user.id
                sess['username'] = user.username

            # 1. GET to trigger initial load into controller
            get_resp = client.get(f'/game/{player_id}', follow_redirects=True)
            self.assertEqual(get_resp.status_code, 200)

            # Set a sentinel in db_player.location before the POST
            sentinel_loc = '{"SENTINEL": "PRESERVED"}'
            player = DB_Player.query.get(player_id)
            player.location = sentinel_loc
            db.session.commit()

            # 2. POST command while on empty tile
            post_resp = client.post(f'/game/{player_id}', data={'cmd': 'look'}, follow_redirects=True)
            self.assertEqual(post_resp.status_code, 200)

            # 3. Verify db_player.location was NOT overwritten by post save
            reloaded_player = DB_Player.query.get(player_id)
            self.assertEqual(reloaded_player.location, sentinel_loc)

    def test_step3_error_propagation_and_falsy_room(self):
        """
        Step 3:
        1. Unexpected errors (AttributeError) in player.pick_up, drop, look, use propagate
           instead of being swallowed.
        2. Falsy room gives normal not-found messages for pick_up, drop, look, and read.
        """
        from unittest.mock import patch, MagicMock
        from game.controller import Controller
        from game.player import Player
        from game.actions import ActionHandler
        from game.gameObjects import Room

        from game.event_manager import EventManager

        ctrl = Controller.__new__(Controller)
        ctrl.room_info = {}
        room = Room("test_room", exits=[], inventory=[], base_description="A test room.")
        grid = [[[room]]]
        ctrl.map = MagicMock()
        ctrl.map.game_map = grid
        ctrl.map.item_recipes = {}
        ctrl.map.target_aliases = {}
        ctrl.map.event_recipes = []
        ctrl.player = Player(game_map=grid, location={'floor': 0, 'x': 0, 'y': 0})
        ctrl.events = EventManager(ctrl)
        ctrl.actions = ActionHandler(ctrl)

        # ── Test 1: AttributeError propagates out of pick_up ──
        with patch.object(ctrl.player, 'pick_up', side_effect=AttributeError("boom in pick_up")):
            with self.assertRaises(AttributeError):
                ctrl.actions.pick_up("gold_key")

        # ── Test 2: AttributeError propagates out of drop ──
        with patch.object(ctrl.player, 'drop', side_effect=AttributeError("boom in drop")):
            with self.assertRaises(AttributeError):
                ctrl.actions.drop("gold_key")

        # ── Test 3: AttributeError propagates out of look ──
        with patch.object(ctrl.player, 'look', side_effect=AttributeError("boom in look")):
            with self.assertRaises(AttributeError):
                ctrl.actions.look("gold_key")

        # ── Test 4: AttributeError propagates out of read (player.use) ──
        with patch.object(ctrl.player, 'use', side_effect=AttributeError("boom in use")):
            with self.assertRaises(AttributeError):
                ctrl.actions.read_item("note")

        # ── Test 5: AttributeError propagates out of read (player.look) ──
        with patch.object(ctrl.player, 'use', return_value=False):
            with patch.object(ctrl.player, 'look', side_effect=AttributeError("boom in look")):
                with self.assertRaises(AttributeError):
                    ctrl.actions.read_item("note")

        # ── Test 6: Falsy room gives normal not-found messages ──
        with patch.object(ctrl, 'get_room', return_value=None):
            resp_pickup = ctrl.actions.pick_up("nonexistent_item")
            self.assertEqual(resp_pickup, "I don't see that here.")

            resp_drop = ctrl.actions.drop("nonexistent_item")
            self.assertEqual(resp_drop, "You don't have that.")

            resp_look = ctrl.actions.look("nonexistent_item")
            self.assertEqual(resp_look, "You don't see that here.")

            resp_read = ctrl.actions.read_item("nonexistent_item")
            self.assertEqual(resp_read, "You don't have that to read.")

    def test_4a_check_use_with_events_already_done_display_name(self):
        """
        4a. check_use_with_events_already_done must show the room's display_name
        (fall back to name with underscores replaced by spaces) instead of the raw identifier.
        """
        from game.controller import Controller
        from game.player import Player
        from game.gameObjects import Room
        from game.event_manager import EventManager
        from game.event_types import ECAEvent, InRoomCondition
        from unittest.mock import MagicMock

        ctrl = Controller.__new__(Controller)
        room_with_display = Room(
            "boiler_room_sub_level",
            display_name="Boiler Room Sub-Level",
            exits=[],
            inventory=[],
            base_description="A hot room."
        )
        room_no_display = Room(
            "secret_tunnel",
            display_name=None,
            exits=[],
            inventory=[],
            base_description="A dark tunnel."
        )
        ctrl.map = MagicMock()
        ctrl.map.list_of_rooms = [room_with_display, room_no_display]
        ctrl.map.game_map = [[[room_with_display, room_no_display]]]
        ctrl.player = Player(game_map=ctrl.map.game_map, location={'floor': 0, 'x': 0, 'y': 0})
        ctrl.events = EventManager(ctrl)

        event1 = ECAEvent(
            id="event_boiler",
            trigger={"type": "use_with", "item": "wrench", "target": "pipe"},
            conditions=[InRoomCondition("boiler_room_sub_level")],
            result={}
        )
        event2 = ECAEvent(
            id="event_tunnel",
            trigger={"type": "use_with", "item": "torch", "target": "wall"},
            conditions=[InRoomCondition("secret_tunnel")],
            result={}
        )
        ctrl.map.event_recipes = [event1, event2]

        # Mark both events as completed
        ctrl.player.completed_events = ["event_boiler", "event_tunnel"]

        msg1 = ctrl.events.check_use_with_events_already_done("wrench", "pipe")
        # Should display room's display_name: "Boiler Room Sub-Level"
        self.assertEqual(msg1, "You already did this in the Boiler Room Sub-Level.")

        msg2 = ctrl.events.check_use_with_events_already_done("torch", "wall")
        # Should fall back to name with underscores replaced by spaces: "secret tunnel"
        self.assertEqual(msg2, "You already did this in the secret tunnel.")

    def test_4b_movement_message_and_typo(self):
        """
        4b. actions.py: movement message becomes "You went {dir}." and fix the
        "You cant go" typo to "You can't go".
        """
        from game.controller import Controller
        from game.player import Player
        from game.actions import ActionHandler
        from game.gameObjects import Room
        from unittest.mock import MagicMock

        ctrl = Controller.__new__(Controller)
        room_north = Room("room_n", exits=['south'], inventory=[], base_description="North room.")
        room_start = Room("room_s", exits=['north'], inventory=[], base_description="Start room.")
        grid = [[[room_north], [room_start]]]  # y=0: north, y=1: start
        ctrl.map = MagicMock()
        ctrl.map.game_map = grid
        ctrl.player = Player(game_map=grid, location={'floor': 0, 'x': 0, 'y': 1})
        ctrl.actions = ActionHandler(ctrl)

        # Successful move north -> "You went north."
        msg_success = ctrl.actions.move_player('north')
        self.assertEqual(msg_success, "You went north.")

        # Blocked move east -> "You can't go east."
        msg_blocked = ctrl.actions.move_player('east')
        self.assertEqual(msg_blocked, "You can't go east.")

    def test_4c_successful_use_no_help_string(self):
        """
        4c. actions.py: a successful use must not return self.help() as the action result.
        Return an empty string, or a short contextual line if the item has use text.
        The event modal message must still be returned as the second tuple element.
        """
        from game.controller import Controller
        from game.player import Player
        from game.actions import ActionHandler
        from game.gameObjects import Room, Item
        from unittest.mock import MagicMock

        ctrl = Controller.__new__(Controller)
        room = Room("test_room", exits=[], inventory=[], base_description="A test room.")
        grid = [[[room]]]
        ctrl.map = MagicMock()
        ctrl.map.game_map = grid
        ctrl.map.target_aliases = {}
        ctrl.map.event_recipes = []
        ctrl.player = Player(game_map=grid, location={'floor': 0, 'x': 0, 'y': 0})
        ctrl.actions = ActionHandler(ctrl)

        item_with_use = Item("keycard", states={'default': {'description': 'A card', 'use': 'You swipe the keycard.'}})
        item_no_use = Item("wrench", states={'default': {'description': 'A wrench', 'use': ''}})
        ctrl.player.inventory = [item_with_use, item_no_use]

        # Case 1: evaluate_use_with success, item has use_text
        ctrl.check_use_with_events_already_done = MagicMock(return_value=None)
        ctrl.evaluate_use_with = MagicMock(return_value={'status': 'success', 'message': 'Door unlocked!'})

        res_action, res_modal = ctrl.actions.use_item({'item': 'keycard', 'target': 'terminal'})
        self.assertEqual(res_modal, 'Door unlocked!')
        self.assertNotEqual(res_action, ctrl.actions.help())
        self.assertEqual(res_action, "You swipe the keycard.")

        # Case 2: evaluate_use_with success, item has NO use_text -> empty string
        res_action2, res_modal2 = ctrl.actions.use_item({'item': 'wrench', 'target': 'pipe'})
        self.assertEqual(res_modal2, 'Door unlocked!')
        self.assertNotEqual(res_action2, ctrl.actions.help())
        self.assertEqual(res_action2, "")

        # Case 3: evaluate_solo success, item has use_text
        ctrl.check_solo_events_already_done = MagicMock(return_value=None)
        ctrl.evaluate_solo = MagicMock(return_value={'status': 'success', 'message': 'The radio plays music.'})

        res_action3, res_modal3 = ctrl.actions.use_item('keycard')
        self.assertEqual(res_modal3, 'The radio plays music.')
        self.assertNotEqual(res_action3, ctrl.actions.help())
        self.assertEqual(res_action3, "You swipe the keycard.")

        # Case 4: evaluate_solo success, item has NO use_text -> empty string
        res_action4, res_modal4 = ctrl.actions.use_item('wrench')
        self.assertEqual(res_modal4, 'The radio plays music.')
        self.assertNotEqual(res_action4, ctrl.actions.help())
        self.assertEqual(res_action4, "")







    def test_5a_db_model_column_types(self):
        """
        5a. app.py: DB_Player.location, DB_Player.player_inventory, and DB_Player.room_inventory
        must be db.Text (not db.String with fixed length).
        """
        import sqlalchemy.types as types
        from app import DB_Player

        loc_col = DB_Player.__table__.columns['location']
        p_inv_col = DB_Player.__table__.columns['player_inventory']
        r_inv_col = DB_Player.__table__.columns['room_inventory']

        self.assertIsInstance(loc_col.type, types.Text)
        self.assertIsNone(loc_col.type.length)
        self.assertIsInstance(p_inv_col.type, types.Text)
        self.assertIsNone(p_inv_col.type.length)
        self.assertIsInstance(r_inv_col.type, types.Text)
        self.assertIsNone(r_inv_col.type.length)

    def test_5b_inject_theme_cached_per_adventure(self):
        """
        5b. inject_theme must not call yaml.safe_load or read files on every render.
        Test that two different adventures give their own theme and that no file read
        happens on a second render. Fallback behavior if theme is missing.
        """
        import tempfile
        import unittest.mock as mock
        from pathlib import Path
        import app as app_module

        adv1_yaml = """
intro:
  title: Adventure One
theme:
  accent: "#ff0000"
player:
  starting_location:
    floor: 0
    x: 0
    y: 0
rooms:
  - name: start
    description: Start room
    exits: []
floors:
  - - [start]
"""
        adv2_yaml = """
intro:
  title: Adventure Two
theme:
  accent: "#0000ff"
player:
  starting_location:
    floor: 0
    x: 0
    y: 0
rooms:
  - name: start
    description: Start room
    exits: []
floors:
  - - [start]
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = Path(tmpdir) / "adv1.yaml"
            p2 = Path(tmpdir) / "adv2.yaml"
            p1.write_text(adv1_yaml)
            p2.write_text(adv2_yaml)

            # Switch active adventure to p1
            with mock.patch.object(app_module, 'DATA_FILE_PATH', str(p1)):
                res1 = app_module.inject_theme()
                self.assertEqual(res1['game_title'], 'Adventure One')
                self.assertEqual(res1['game_theme'].get('accent'), '#ff0000')

                # On second render, verify NO file read (open or yaml.safe_load) occurs
                with mock.patch('builtins.open', side_effect=AssertionError("builtins.open should not be called on cached render")), \
                     mock.patch('yaml.safe_load', side_effect=AssertionError("yaml.safe_load should not be called on cached render")):
                    res1_cached = app_module.inject_theme()
                    self.assertEqual(res1_cached['game_title'], 'Adventure One')
                    self.assertEqual(res1_cached['game_theme'].get('accent'), '#ff0000')

            # Switch active adventure to p2: gives its own theme
            with mock.patch.object(app_module, 'DATA_FILE_PATH', str(p2)):
                res2 = app_module.inject_theme()
                self.assertEqual(res2['game_title'], 'Adventure Two')
                self.assertEqual(res2['game_theme'].get('accent'), '#0000ff')

                # Repeat render of p2 also does not hit file read
                with mock.patch('builtins.open', side_effect=AssertionError("builtins.open should not be called on cached render")), \
                     mock.patch('yaml.safe_load', side_effect=AssertionError("yaml.safe_load should not be called on cached render")):
                    res2_cached = app_module.inject_theme()
                    self.assertEqual(res2_cached['game_title'], 'Adventure Two')
                    self.assertEqual(res2_cached['game_theme'].get('accent'), '#0000ff')

            # Test 3: Confirm fallback result from missing/broken file is NOT cached in _ADVENTURE_THEME_CACHE
            broken_path = Path(tmpdir) / "broken.yaml"
            broken_path.write_text("invalid: [broken yaml")
            initial_cache_keys = set(app_module._ADVENTURE_THEME_CACHE.keys())
            with mock.patch.object(app_module, 'DATA_FILE_PATH', str(broken_path)):
                res_broken = app_module.inject_theme()
                self.assertEqual(res_broken['game_title'], 'Text Adventure')
                self.assertEqual(res_broken['game_theme'], {})
                # Cache keys must NOT contain the broken file
                for key in app_module._ADVENTURE_THEME_CACHE.keys():
                    self.assertNotIn(str(broken_path), key[0])

            with mock.patch.object(app_module, 'DATA_FILE_PATH', "/nonexistent/path/adv.yaml"):
                res_missing = app_module.inject_theme()
                self.assertEqual(res_missing['game_title'], 'Text Adventure')
                for key in app_module._ADVENTURE_THEME_CACHE.keys():
                    self.assertNotIn("/nonexistent/path/adv.yaml", key[0])

            # Test 4: Keyed on (path, mtime) - touching/editing YAML reloads theme on next render
            import os
            import time
            new_adv1_yaml = """
intro:
  title: Adventure One Updated
theme:
  accent: "#123456"
player:
  starting_location:
    floor: 0
    x: 0
    y: 0
rooms:
  - name: start
    description: Start room
    exits: []
floors:
  - - [start]
"""
            with mock.patch.object(app_module, 'DATA_FILE_PATH', str(p1)):
                # Update file content and modify mtime
                p1.write_text(new_adv1_yaml)
                new_mtime = p1.stat().st_mtime + 5.0
                os.utime(str(p1), (new_mtime, new_mtime))

                res1_updated = app_module.inject_theme()
                self.assertEqual(res1_updated['game_title'], 'Adventure One Updated')
                self.assertEqual(res1_updated['game_theme'].get('accent'), '#123456')

            # Test fallback when theme is missing from adventure YAML
            adv_no_theme = """
intro:
  title: No Theme Adventure
player:
  starting_location:
    floor: 0
    x: 0
    y: 0
rooms:
  - name: start
    description: Start room
    exits: []
floors:
  - - [start]
"""
            p3 = Path(tmpdir) / "adv_no_theme.yaml"
            p3.write_text(adv_no_theme)
            with mock.patch.object(app_module, 'DATA_FILE_PATH', str(p3)):
                res3 = app_module.inject_theme()
                self.assertEqual(res3['game_title'], 'No Theme Adventure')
                self.assertEqual(res3['game_theme'], {})

    def test_6_room_states_description(self):
        """
        Step 6: Room.description must use the current state's text if states is defined,
        while keeping base + fixtures + items + trailing composition unchanged.
        """
        from game.gameObjects import Room, Fixture, Item

        room = Room(
            name="command_center",
            exits=[],
            inventory=[Item(name="datapad", presence="A glowing datapad rests on the floor.")],
            states={
                "default": "The command center is dark and unpowered.",
                "powered": "The command center hums with bright neon consoles."
            },
            base_description="Fallback base description.",
            trailing_description="A heavy blast door stands to the north.",
            fixtures={
                "terminal": Fixture(
                    name="terminal",
                    states={"default": "A main terminal screen flickers."},
                    priority=10
                )
            }
        )

        # 1. In 'default' state: should use states['default']
        desc_default = room.description
        self.assertIn("The command center is dark and unpowered.", desc_default)
        self.assertNotIn("Fallback base description.", desc_default)
        self.assertIn("A main terminal screen flickers.", desc_default)
        self.assertIn("Items in the room are: A glowing datapad rests on the floor.", desc_default)
        self.assertIn("A heavy blast door stands to the north.", desc_default)

        # 2. Transition state to 'powered'
        room.set_state("powered")
        desc_powered = room.description
        self.assertIn("The command center hums with bright neon consoles.", desc_powered)
        self.assertNotIn("The command center is dark and unpowered.", desc_powered)
        self.assertNotIn("Fallback base description.", desc_powered)
        self.assertIn("A main terminal screen flickers.", desc_powered)
        self.assertIn("Items in the room are: A glowing datapad rests on the floor.", desc_powered)
        self.assertIn("A heavy blast door stands to the north.", desc_powered)

        # 3. Room without states falls back to base_description
        room_no_states = Room(
            name="hallway",
            exits=[],
            inventory=[],
            base_description="A plain hallway.",
            trailing_description="Dust motes float in the air."
        )
        self.assertEqual(room_no_states.description, "A plain hallway. Dust motes float in the air.")

        # 4. Room with dict-state-without-description (or empty text) falls back to base_description
        room_dict_empty_desc = Room(
            name="storage",
            exits=[],
            inventory=[],
            states={
                "default": {"other_field": "no description key here"},
                "empty_str": {"description": ""}
            },
            base_description="Base storage room description."
        )
        self.assertEqual(room_dict_empty_desc.description, "Base storage room description.")
        room_dict_empty_desc.set_state("empty_str")
        self.assertEqual(room_dict_empty_desc.description, "Base storage room description.")

    def test_7_event_item_rewards_retain_recipe_metadata(self):
        """
        Step 7: EventManager.fire_event must award items created from the recipe via make_item
        rather than raw bare Item(name=it), retaining keywords, aliases, display_name, states, and presence.
        """
        from game.event_manager import EventManager
        from game.gameObjects import Map, Item
        from game.player import Player
        from types import SimpleNamespace

        # Create a mock map with an item recipe
        mock_map = MagicMock()
        mock_map.item_recipes = {
            "golden_key": {
                "display_name": "Golden Key",
                "keywords": ["key", "golden"],
                "aliases": ["gold key", "shiny key"],
                "presence": "A shiny golden key glints on the floor.",
                "states": {
                    "default": {
                        "description": "An intricately carved golden key.",
                        "examine": "It is crafted from pure gold.",
                        "use": "You turn the golden key."
                    }
                }
            }
        }
        # Use real Map.make_item logic bound to mock_map
        mock_map.make_item = lambda name: Map.make_item(mock_map, name)

        mock_ctrl = MagicMock()
        mock_ctrl.map = mock_map
        player = Player()
        mock_ctrl.player = player

        event_mgr = EventManager(mock_ctrl)

        event = SimpleNamespace(
            id="find_key_event",
            result={
                "message": "You discovered a golden key!",
                "add_item": "golden_key"
            }
        )

        event_mgr.fire_event(event, player=player)

        self.assertEqual(len(player.inventory), 1)
        awarded_item = player.inventory[0]

        # Must retain recipe metadata
        self.assertEqual(awarded_item.name, "golden_key")
        self.assertEqual(awarded_item.display_name, "Golden Key")
        self.assertIn("key", awarded_item.keywords)
        self.assertIn("shiny key", awarded_item.aliases)
        self.assertEqual(awarded_item.presence_description, "A shiny golden key glints on the floor.")
        self.assertIn("default", awarded_item.states)
        self.assertEqual(awarded_item.description, "An intricately carved golden key.")


if __name__ == '__main__':
    unittest.main()

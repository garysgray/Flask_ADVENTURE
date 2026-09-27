import unittest
from game.parser import Parser


class MockRoom:
    def __init__(self, inventory=None):
        self.inventory = inventory or []
        self.fixtures = {}
        self.exits = []
        self.exit_destinations = {}
        self.description = ""


class MockChar:
    def __init__(self, inventory=None):
        self.inventory = inventory or []


class MockItem:
    def __init__(self, name, display_name=None, aliases=None):
        self.name = name
        self.display_name = display_name or name.replace('_', ' ')
        self.aliases = aliases or []


class MockController:
    def __init__(self, room_items=None, player_items=None):
        self.room = MockRoom(room_items or [])
        self.character = MockChar(player_items or [])
        self.player = self.character
        self.map = type('MockMap', (), {
            'item_recipes': {
                'brass_key': {'display_name': 'brass key', 'aliases': ['brass key', 'brass', 'key']},
                'iron_key': {'display_name': 'iron key', 'aliases': ['iron key', 'iron', 'key']},
                'silver_key': {'display_name': 'silver key', 'aliases': ['silver key', 'silver', 'key']},
                'chest': {'display_name': 'wooden chest', 'aliases': ['chest', 'wooden chest']},
            },
            'target_aliases': {},
            'event_recipes': [],
            'custom_verbs': {},
        })()

    def get_room(self):
        return self.room


class TestParserDisambiguation(unittest.TestCase):

    def setUp(self):
        self.brass = MockItem('brass_key', 'brass key', ['brass key', 'brass', 'key'])
        self.iron = MockItem('iron_key', 'iron key', ['iron key', 'iron', 'key'])
        self.silver = MockItem('silver_key', 'silver key', ['silver key', 'silver', 'key'])

    def test_ambiguous_pickup_and_candidate_selection(self):
        ctrl = MockController(room_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        res1 = parser.parse("take key")
        self.assertEqual(res1["CMD"], "respond")
        self.assertIn("Which one do you mean", res1["OBJ"])
        self.assertIsNotNone(parser.pending_disambiguation)
        self.assertEqual(set(parser.pending_disambiguation["candidates"]), {"brass_key", "iron_key"})

        # Answer with full display name
        res2 = parser.parse("brass key")
        self.assertEqual(res2, {"CMD": "pickup", "OBJ": "brass_key"})
        self.assertIsNone(parser.pending_disambiguation)

        # Answer with single distinguishing token
        parser.parse("take key")
        res3 = parser.parse("iron")
        self.assertEqual(res3, {"CMD": "pickup", "OBJ": "iron_key"})
        self.assertIsNone(parser.pending_disambiguation)

        # Answer with repeated verb
        parser.parse("take key")
        res4 = parser.parse("take brass key")
        self.assertEqual(res4, {"CMD": "pickup", "OBJ": "brass_key"})
        self.assertIsNone(parser.pending_disambiguation)

    def test_ambiguous_drop_and_candidate_selection(self):
        ctrl = MockController(player_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        res1 = parser.parse("drop key")
        self.assertEqual(res1["CMD"], "respond")
        self.assertIn("Which one do you mean", res1["OBJ"])
        self.assertIsNotNone(parser.pending_disambiguation)

        res2 = parser.parse("brass key")
        self.assertEqual(res2, {"CMD": "drop", "OBJ": "brass_key"})
        self.assertIsNone(parser.pending_disambiguation)

    def test_invalid_clarification_response(self):
        ctrl = MockController(room_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        parser.parse("take key")
        self.assertIsNotNone(parser.pending_disambiguation)

        # Unrelated non-candidate input
        res = parser.parse("banana")
        self.assertIsNone(parser.pending_disambiguation)
        self.assertEqual(res, {"CMD": "banana", "OBJ": ""})

        # Subsequent command should be unaffected
        next_res = parser.parse("iron key")
        self.assertEqual(next_res, {"CMD": "look", "OBJ": "iron_key"})

    def test_unrelated_command_after_clarification(self):
        ctrl = MockController(room_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        parser.parse("take key")
        self.assertIsNotNone(parser.pending_disambiguation)

        res = parser.parse("look")
        self.assertIsNone(parser.pending_disambiguation)
        self.assertEqual(res, {"CMD": "look", "OBJ": ""})

    def test_successful_completion_clears_pending_state(self):
        ctrl = MockController(room_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        parser.parse("take key")
        parser.parse("iron")
        self.assertIsNone(parser.pending_disambiguation)

        # Standalone subsequent command
        res = parser.parse("brass key")
        self.assertEqual(res, {"CMD": "look", "OBJ": "brass_key"})

    def test_session_isolation(self):
        ctrl_a = MockController(room_items=[self.brass, self.iron])
        ctrl_b = MockController(room_items=[self.brass, self.iron])

        session_a = Parser(controller=ctrl_a)
        session_b = Parser(controller=ctrl_b)

        # Session A enters clarification
        session_a.parse("take key")
        self.assertIsNotNone(session_a.pending_disambiguation)
        self.assertIsNone(session_b.pending_disambiguation)

        # Session B issues a command
        res_b = session_b.parse("iron key")
        self.assertEqual(res_b, {"CMD": "look", "OBJ": "iron_key"})
        self.assertIsNone(session_b.pending_disambiguation)

        # Session A remains waiting and resolves independently
        res_a = session_a.parse("iron key")
        self.assertEqual(res_a, {"CMD": "pickup", "OBJ": "iron_key"})
        self.assertIsNone(session_a.pending_disambiguation)

    def test_cancel_clarification(self):
        ctrl = MockController(room_items=[self.brass, self.iron])
        parser = Parser(controller=ctrl)

        parser.parse("take key")
        self.assertIsNotNone(parser.pending_disambiguation)

        res = parser.parse("cancel")
        self.assertEqual(res, {"CMD": "respond", "OBJ": "Cancelled."})
        self.assertIsNone(parser.pending_disambiguation)

    def test_has_item_keyword_collision(self):
        """has_item() must not match an item via loose keyword collision when checking an unrelated target."""
        from game.actions import ActionHandler
        from game.player import Player

        laptop = MockItem('laptop', 'laptop', ['laptop', 'computer', 'work laptop'])
        setattr(laptop, 'keywords', ['laptop', 'computer', 'work'])

        badge = MockItem('work_badge', 'work badge', ['badge', 'work badge', 'id', 'id badge'])
        setattr(badge, 'keywords', ['badge', 'id', 'work'])

        ctrl = MockController(room_items=[badge], player_items=[laptop])
        actions = ActionHandler(ctrl)

        # Exact names and aliases should match
        self.assertTrue(actions.has_item('laptop'))
        self.assertTrue(actions.has_item('work laptop'))
        self.assertTrue(actions.has_item('computer'))

        # Items not in inventory must NOT match
        self.assertFalse(actions.has_item('work_badge'))
        self.assertFalse(actions.has_item('badge'))

        # Shared keyword 'work' must NOT match laptop in has_item
        self.assertFalse(actions.has_item('work'))

    def test_drop_badge_holding_laptop_and_work_badge(self):
        """'drop badge' while holding both laptop and work_badge must drop work_badge, not laptop."""
        from game.controller import Controller
        ctrl = Controller('data/go_to_work_new.yaml')
        ctrl.run_the_cmd(ctrl.parse_it('east'))

        ctrl.player.inventory.append(ctrl.map.make_item('laptop'))
        ctrl.player.inventory.append(ctrl.map.make_item('work_badge'))

        cmd = ctrl.parse_it('drop badge')
        ctrl.run_the_cmd(cmd)

        self.assertEqual(ctrl.room_info.get('CMD_RESPONSE'), 'You dropped the work badge.')
        self.assertTrue(any(i.name == 'laptop' for i in ctrl.player.inventory))
        self.assertFalse(any(i.name == 'work_badge' for i in ctrl.player.inventory))
        self.assertTrue(any(i.name == 'work_badge' for i in ctrl.get_room().inventory))

    def test_pickup_and_drop_badge_and_laptop_integration(self):
        """Full integration case: get laptop, get badge, drop badge, drop laptop in that order."""
        from game.controller import Controller
        ctrl = Controller('data/go_to_work_new.yaml')
        ctrl.run_the_cmd(ctrl.parse_it('east'))

        # Both items in room
        ctrl.get_room().inventory.append(ctrl.map.make_item('laptop'))
        ctrl.get_room().inventory.append(ctrl.map.make_item('work_badge'))

        # 1. Get laptop
        cmd1 = ctrl.parse_it('get laptop')
        ctrl.run_the_cmd(cmd1)
        self.assertEqual(ctrl.room_info.get('CMD_RESPONSE'), 'You picked up the laptop.')
        self.assertTrue(any(i.name == 'laptop' for i in ctrl.player.inventory))
        self.assertFalse(any(i.name == 'work_badge' for i in ctrl.player.inventory))

        # 2. Get badge
        cmd2 = ctrl.parse_it('get badge')
        ctrl.run_the_cmd(cmd2)
        self.assertEqual(ctrl.room_info.get('CMD_RESPONSE'), 'You picked up the work badge.')
        self.assertTrue(any(i.name == 'laptop' for i in ctrl.player.inventory))
        self.assertTrue(any(i.name == 'work_badge' for i in ctrl.player.inventory))

        # 3. Drop badge
        cmd3 = ctrl.parse_it('drop badge')
        ctrl.run_the_cmd(cmd3)
        self.assertEqual(ctrl.room_info.get('CMD_RESPONSE'), 'You dropped the work badge.')
        self.assertTrue(any(i.name == 'laptop' for i in ctrl.player.inventory))
        self.assertFalse(any(i.name == 'work_badge' for i in ctrl.player.inventory))
        self.assertTrue(any(i.name == 'work_badge' for i in ctrl.get_room().inventory))

        # 4. Drop laptop
        cmd4 = ctrl.parse_it('drop laptop')
        ctrl.run_the_cmd(cmd4)
        self.assertEqual(ctrl.room_info.get('CMD_RESPONSE'), 'You dropped the laptop.')
        self.assertFalse(any(i.name == 'laptop' for i in ctrl.player.inventory))
        self.assertFalse(any(i.name == 'work_badge' for i in ctrl.player.inventory))
        self.assertTrue(any(i.name == 'laptop' for i in ctrl.get_room().inventory))
        self.assertTrue(any(i.name == 'work_badge' for i in ctrl.get_room().inventory))


if __name__ == "__main__":
    unittest.main()

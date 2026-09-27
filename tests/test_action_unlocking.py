import unittest
import json
from unittest.mock import MagicMock
from game.parser import Parser
from game.player import Player
from game.actions import ActionHandler
from game.event_manager import EventManager
from game.gameObjects import Fixture
from game.persistence import PersistenceManager


class TestActionUnlocking(unittest.TestCase):

    def setUp(self):
        self.ctrl = MagicMock()
        self.ctrl.map = MagicMock()
        self.ctrl.map.custom_verbs = {"skate": ["ollie", "kickflip", "manual", "grind"]}
        self.ctrl.map.target_aliases = {
            "hubba": ["hubba ledge", "hubba"],
            "gap": ["gap"],
            "rail": ["handrail", "rail"]
        }
        self.ctrl.map.event_recipes = []

        self.hubba = Fixture(name="hubba", display_name="hubba ledge")
        self.gap = Fixture(name="gap", display_name="gap")
        self.rail = Fixture(name="rail", display_name="handrail")

        self.room = MagicMock()
        self.room.name = "skatepark"
        self.room.fixtures = {"gap": self.gap, "hubba": self.hubba, "rail": self.rail}
        self.room.inventory = []
        self.room.description = "A sunny skatepark with ledges and rails."
        self.ctrl.get_room.return_value = self.room

        self.ctrl.player = Player(
            unlocked_actions=["ollie", "manual"],
            locked_messages={"kickflip": "You need to master your ollie before trying a kickflip."}
        )
        self.ctrl.player.inventory = []

    def test_parser_phrasing_and_prepositions(self):
        parser = Parser(controller=self.ctrl)

        # Basic action with locative preposition
        res1 = parser.parse("ollie over hubba")
        self.assertEqual(res1, {"CMD": "use", "OBJ": {"item": "hubba", "action": "ollie"}})

        # Kickflip over gap
        res2 = parser.parse("kickflip over gap")
        self.assertEqual(res2, {"CMD": "use", "OBJ": {"item": "gap", "action": "kickflip"}})

        # Leading "do" filler
        res3 = parser.parse("do kickflip over gap")
        self.assertEqual(res3, {"CMD": "use", "OBJ": {"item": "gap", "action": "kickflip"}})

        # Across preposition
        res4 = parser.parse("manual across hubba")
        self.assertEqual(res4, {"CMD": "use", "OBJ": {"item": "hubba", "action": "manual"}})

    def test_locked_action_blocked_before_event(self):
        handler = ActionHandler(self.ctrl)

        # Kickflip is not in unlocked_actions
        msg, extra = handler.use_item({"item": "gap", "action": "kickflip"})
        self.assertEqual(msg, "You need to master your ollie before trying a kickflip.")
        self.assertIsNone(extra)
        # Verify event evaluation was NOT called
        self.ctrl.evaluate_solo.assert_not_called()

    def test_unlocked_action_proceeds_to_event(self):
        handler = ActionHandler(self.ctrl)
        self.ctrl.check_solo_events_already_done.return_value = None
        self.ctrl.evaluate_solo.return_value = {
            "status": "success",
            "message": "You cleanly ollie over the hubba!"
        }

        # Ollie is in unlocked_actions
        msg, extra = handler.use_item({"item": "hubba", "action": "ollie"})
        self.assertEqual(extra, "You cleanly ollie over the hubba!")
        self.ctrl.evaluate_solo.assert_called_once_with("hubba", action="ollie")

    def test_event_unlocks_action(self):
        handler = ActionHandler(self.ctrl)
        event_mgr = EventManager(self.ctrl)

        # Kickflip is initially locked
        self.assertFalse(self.ctrl.player.has_unlocked_action("kickflip"))

        # Fire event that unlocks kickflip
        event_mock = MagicMock()
        event_mock.id = "learn_kickflip"
        event_mock.result = {
            "message": "Coach teaches you the kickflip technique!",
            "unlock_action": "kickflip"
        }
        event_mgr._fire_event(event_mock)

        # Kickflip is now unlocked
        self.assertTrue(self.ctrl.player.has_unlocked_action("kickflip"))

        # Kickflip now passes gate to evaluate_solo
        self.ctrl.check_solo_events_already_done.return_value = None
        self.ctrl.evaluate_solo.return_value = {
            "status": "success",
            "message": "You nail the kickflip over the gap!"
        }
        msg, extra = handler.use_item({"item": "gap", "action": "kickflip"})
        self.assertEqual(extra, "You nail the kickflip over the gap!")

    def test_backward_compatibility_when_unlocked_actions_omitted(self):
        # When unlocked_actions is None (default), all actions are allowed
        legacy_player = Player()
        self.assertTrue(legacy_player.has_unlocked_action("anything"))
        self.assertTrue(legacy_player.has_unlocked_action("kickflip"))

    def test_unlock_action_from_none_keeps_unrestricted(self):
        # Unlocking an action from an unrestricted (None) player must keep everything allowed
        player = Player(unlocked_actions=None)
        self.assertIsNone(player.unlocked_actions)

        player.unlock_action("kickflip")
        # unlocked_actions must remain None, not become {'kickflip'}
        self.assertIsNone(player.unlocked_actions)
        self.assertTrue(player.has_unlocked_action("look"))
        self.assertTrue(player.has_unlocked_action("take"))
        self.assertTrue(player.has_unlocked_action("move"))
        self.assertTrue(player.has_unlocked_action("kickflip"))
        self.assertTrue(player.has_unlocked_action("random_verb"))

    def test_persistence_roundtrip_unlocked_actions(self):
        self.ctrl.map.list_of_rooms = []
        self.ctrl.map.make_item = MagicMock()
        pm = PersistenceManager(self.ctrl)

        # 1. Round-trip None (unrestricted)
        self.ctrl.player = Player(unlocked_actions=None)
        loc, inv, rooms = pm.save()
        loc_data = json.loads(loc)
        self.assertIn("unlocked_actions", loc_data)
        self.assertIsNone(loc_data["unlocked_actions"])

        # Restore into a player that previously had restricted actions
        db_player = MagicMock(id=1, location=loc, player_inventory=inv, room_inventory=rooms)
        self.ctrl.player = Player(unlocked_actions={"manual"})
        pm.load(db_player)
        self.assertIsNone(self.ctrl.player.unlocked_actions)
        self.assertTrue(self.ctrl.player.has_unlocked_action("anything"))

        # 2. Round-trip a populated set
        self.ctrl.player = Player(unlocked_actions={"ollie", "kickflip"})
        loc, inv, rooms = pm.save()
        loc_data = json.loads(loc)
        self.assertEqual(loc_data["unlocked_actions"], ["kickflip", "ollie"])

        self.ctrl.player = Player(unlocked_actions=None)
        db_player = MagicMock(id=2, location=loc, player_inventory=inv, room_inventory=rooms)
        pm.load(db_player)
        self.assertEqual(self.ctrl.player.unlocked_actions, {"kickflip", "ollie"})
        self.assertTrue(self.ctrl.player.has_unlocked_action("ollie"))
        self.assertTrue(self.ctrl.player.has_unlocked_action("kickflip"))
        self.assertFalse(self.ctrl.player.has_unlocked_action("manual"))

        # 3. Round-trip an empty set (explicitly locked down)
        self.ctrl.player = Player(unlocked_actions=set())
        loc, inv, rooms = pm.save()
        loc_data = json.loads(loc)
        self.assertEqual(loc_data["unlocked_actions"], [])

        self.ctrl.player = Player(unlocked_actions=None)
        db_player = MagicMock(id=3, location=loc, player_inventory=inv, room_inventory=rooms)
        pm.load(db_player)
        self.assertEqual(self.ctrl.player.unlocked_actions, set())
        self.assertFalse(self.ctrl.player.has_unlocked_action("ollie"))

        # 4. Old save without 'unlocked_actions' key must load as before without overwriting
        old_loc = json.dumps({"X": 0, "Y": 0, "floor": 0, "visited_rooms": []})
        old_db_player = MagicMock(id=4, location=old_loc, player_inventory="[]", room_inventory="[]")

        self.ctrl.player = Player(unlocked_actions=None)
        pm.load(old_db_player)
        self.assertIsNone(self.ctrl.player.unlocked_actions)

        self.ctrl.player = Player(unlocked_actions={"existing_action"})
        pm.load(old_db_player)
        self.assertEqual(self.ctrl.player.unlocked_actions, {"existing_action"})


if __name__ == '__main__':
    unittest.main()

"""
Unit tests for YAML adventure validation and AdventureConfigError handling.
Tests all error, warning, and default cases.
"""

import unittest
import tempfile
import os
import yaml
from pathlib import Path
from game.loader import load_and_validate_adventure, AdventureConfigError


class TestYAMLValidation(unittest.TestCase):
    """Verifies that AdventureConfigError is raised with clear context for fatal issues,
    while optional sections are cleanly defaulted."""

    def _write_temp_yaml(self, data):
        tf = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        if isinstance(data, str):
            tf.write(data)
        else:
            yaml.safe_dump(data, tf)
        tf.close()
        return tf.name

    def _get_minimal_valid_data(self):
        return {
            "rooms": [
                {
                    "name": "start_room",
                    "display_name": "Starting Room",
                    "base_description": "A bare room.",
                    "exits": []
                }
            ],
            "floors": [
                [["start_room"]]
            ],
            "player": {
                "starting_location": {"floor": 0, "x": 0, "y": 0}
            }
        }

    # 1. Missing file
    def test_missing_file_raises_adventure_config_error(self):
        with self.assertRaises(AdventureConfigError) as ctx:
            load_and_validate_adventure("/nonexistent/path/to/adventure.yaml")
        err_msg = str(ctx.exception)
        self.assertIn("Adventure file not found", err_msg)
        self.assertIn("Fix", err_msg)

    # 2. Malformed YAML (syntax error)
    def test_malformed_yaml_syntax(self):
        bad_yaml = "rooms:\n  - name: test\n    indentation_error: [unclosed"
        path = self._write_temp_yaml(bad_yaml)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("YAML syntax/formatting error", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 3. Non-dictionary root
    def test_non_dict_root_raises_error(self):
        path = self._write_temp_yaml("- just a list\n- not a dict")
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("Top-level YAML structure must be a dictionary", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 4. Missing / empty rooms
    def test_empty_rooms_raises_error(self):
        data = self._get_minimal_valid_data()
        data["rooms"] = []
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("No rooms defined in the adventure layout", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 5. Missing / empty floors
    def test_empty_floors_raises_error(self):
        data = self._get_minimal_valid_data()
        data["floors"] = []
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("No floors defined", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 6. More than 6 floors (> max allowed)
    def test_exceeding_max_floors_raises_error(self):
        data = self._get_minimal_valid_data()
        data["floors"] = [[["start_room"]]] * 7
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("exceeds the maximum allowed 6 floors", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 7. Floor grid references room not in catalog
    def test_floor_grid_unknown_room_raises_error(self):
        data = self._get_minimal_valid_data()
        data["floors"] = [[["start_room", "phantom_chamber"]]]
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("phantom_chamber", err_msg)
            self.assertIn("not defined in 'rooms:'", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 8. Starting location out of bounds
    def test_starting_location_out_of_bounds(self):
        data = self._get_minimal_valid_data()
        data["player"]["starting_location"] = {"floor": 0, "x": 5, "y": 5}
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("out of bounds", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 9. Starting location on empty tile
    def test_starting_location_on_empty_tile(self):
        data = self._get_minimal_valid_data()
        data["floors"] = [[["start_room", None]]]
        data["player"]["starting_location"] = {"floor": 0, "x": 1, "y": 0}
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("empty (null) or out of bounds", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 10. Broken exit destination reference (non-existent room)
    def test_exit_destination_to_non_existent_room(self):
        data = self._get_minimal_valid_data()
        data["rooms"][0]["exit_destinations"] = {"east": "non_existent_vault"}
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("points to non-existent room 'non_existent_vault'", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 11. Broken exit destination reference (invalid floor / coordinate)
    def test_exit_destination_to_invalid_coordinate(self):
        data = self._get_minimal_valid_data()
        data["rooms"][0]["exit_destinations"] = {
            "down": {"floor": 3, "x": 0, "y": 0}
        }
        path = self._write_temp_yaml(data)
        try:
            with self.assertRaises(AdventureConfigError) as ctx:
                load_and_validate_adventure(path)
            err_msg = str(ctx.exception)
            self.assertIn("points to non-existent floor 3", err_msg)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # 12. Sensible defaults: optional sections (intro, items, custom_verbs, win_conditions, etc.)
    def test_optional_sections_default_safely(self):
        data = self._get_minimal_valid_data()
        # Ensure no intro, items, custom_verbs, target_aliases, win_conditions
        for key in ["intro", "items", "custom_verbs", "target_aliases", "win_conditions", "theme", "events"]:
            data.pop(key, None)

        path = self._write_temp_yaml(data)
        try:
            sanitized = load_and_validate_adventure(path)
            self.assertIsInstance(sanitized["items"], dict)
            self.assertIsInstance(sanitized["intro"], dict)
            self.assertIsInstance(sanitized["custom_verbs"], dict)
            self.assertIsInstance(sanitized["target_aliases"], dict)
            self.assertIsInstance(sanitized["win_conditions"], list)
            self.assertEqual(len(sanitized["rooms"]), 1)
            # map_glyphs default safely
            self.assertEqual(sanitized["map_glyphs"]["player"], "👤")
            self.assertEqual(sanitized["map_glyphs"]["locked"], "🔒")
            self.assertEqual(sanitized["map_glyphs"]["stairs_up"], "⬆️")
            self.assertEqual(sanitized["map_glyphs"]["stairs_down"], "⬇️")
            self.assertEqual(sanitized["map_glyphs"]["portal"], "🌀")
            self.assertEqual(sanitized["map_glyphs"]["unexplored"], "?")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_custom_map_glyphs_normalized_and_merged(self):
        data = self._get_minimal_valid_data()
        data["map_glyphs"] = {
            "player": "@",
            "locked": "X",
            "unexplored": "·"
        }
        path = self._write_temp_yaml(data)
        try:
            sanitized = load_and_validate_adventure(path)
            self.assertEqual(sanitized["map_glyphs"]["player"], "@")
            self.assertEqual(sanitized["map_glyphs"]["locked"], "X")
            self.assertEqual(sanitized["map_glyphs"]["unexplored"], "·")
            # Unspecified keys retain defaults
            self.assertEqual(sanitized["map_glyphs"]["stairs_up"], "⬆️")
            self.assertEqual(sanitized["map_glyphs"]["stairs_down"], "⬇️")
            self.assertEqual(sanitized["map_glyphs"]["portal"], "🌀")
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()

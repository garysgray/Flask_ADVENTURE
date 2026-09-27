"""
Robust YAML Adventure Loader & Validator.

Implements the three-tiered contract:
  1. Normalize: Handles recognized alternate formats & sensible defaults (e.g. exit strings/dicts, missing optional fixtures/items/aliases).
  2. Warning: Logs actionable warnings for non-fatal inconsistencies (e.g. events referencing unplaced targets, missing win condition mappings).
  3. Fatal: Raises formatted YAMLValidationError with exact context when the engine cannot safely run (e.g. syntax errors, invalid spawn, >6 floors, missing start room).
"""

import sys
from pathlib import Path
import yaml


class AdventureConfigError(ValueError):
    """Raised when an adventure YAML file has a fatal configuration or syntax error preventing game play."""
    def __init__(self, message, filename=None, details=None, fix=None, hint=None):
        self.filename = filename
        self.details = details
        self.fix = fix or hint
        self.hint = self.fix
        formatted = format_error_banner(
            title="Adventure Configuration Error",
            message=message,
            filename=filename,
            details=details,
            fix=self.fix
        )
        super().__init__(formatted)


# Backward compatibility alias
YAMLValidationError = AdventureConfigError


DEFAULT_MAP_GLYPHS = {
    "player": "👤",
    "locked": "🔒",
    "stairs_up": "⬆️",
    "stairs_down": "⬇️",
    "portal": "🌀",
    "unexplored": "?",
}


def format_error_banner(title, message, filename=None, details=None, fix=None):
    lines = [
        "",
        "=" * 64,
        f"[ADVENTURE CONFIG ERROR] {title}",
        "-" * 64,
    ]
    if filename:
        lines.append(f"File   : {filename}")
    lines.append(f"Problem: {message}")
    if details:
        lines.append(f"Details: {details}")
    if fix:
        lines.append(f"Fix    : {fix}")
    lines.append("=" * 64)
    lines.append("")
    return "\n".join(lines)


def load_and_validate_adventure(file_path):
    """
    Loads, normalizes, and validates an adventure YAML file.
    Returns the sanitized data dictionary.
    Raises AdventureConfigError on fatal problems.
    Logs warnings to stderr for non-fatal inconsistencies.
    """
    path = Path(file_path)
    if not path.is_file():
        raise AdventureConfigError(
            message=f"Adventure file not found at: {file_path}",
            filename=str(path),
            fix="Verify that the file path is correct and the file exists in the data directory."
        )

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        problem_mark = getattr(exc, 'problem_mark', None)
        line = problem_mark.line + 1 if problem_mark else 'Unknown'
        col = problem_mark.column + 1 if problem_mark else 'Unknown'
        snippet = getattr(exc, 'problem', str(exc))
        raise AdventureConfigError(
            message=f"YAML syntax/formatting error at line {line}, column {col}",
            filename=str(path),
            details=f"{snippet}\n{getattr(exc, 'context', '') or ''}".strip(),
            fix="Check for mismatched indentation, missing colons, or invalid YAML formatting."
        ) from exc

    if not isinstance(data, dict):
        raise AdventureConfigError(
            message="Top-level YAML structure must be a dictionary/mapping.",
            filename=str(path),
            fix="Ensure the YAML file starts with key-value pairs (e.g. rooms, floors, player)."
        )

    # =========================================================================
    # 1. TIER 1: NORMALIZATION & SAFE DEFAULTS (ALLOW OPTIONAL SECTIONS)
    # =========================================================================
    data.setdefault('items', {})
    data.setdefault('rooms', [])
    data.setdefault('floors', [])
    data.setdefault('target_aliases', {})
    data.setdefault('custom_verbs', {})
    data.setdefault('win_conditions', [])
    data.setdefault('intro', {})
    data.setdefault('win_screen', {})
    data.setdefault('theme', {})
    data.setdefault('events', [])
    data.setdefault('player', {})

    if not isinstance(data['items'], dict):
        data['items'] = {}
    if not isinstance(data['rooms'], list):
        data['rooms'] = []
    if not isinstance(data['floors'], list):
        data['floors'] = []
    if not isinstance(data['target_aliases'], dict):
        data['target_aliases'] = {}
    if not isinstance(data['custom_verbs'], dict):
        data['custom_verbs'] = {}
    if not isinstance(data['win_conditions'], list):
        data['win_conditions'] = []
    if not isinstance(data['player'], dict):
        data['player'] = {}

    # Normalize map_glyphs with fallback defaults
    raw_glyphs = data.get('map_glyphs')
    normalized_glyphs = dict(DEFAULT_MAP_GLYPHS)
    if isinstance(raw_glyphs, dict):
        for k in DEFAULT_MAP_GLYPHS:
            v = raw_glyphs.get(k)
            if v is not None and str(v).strip():
                normalized_glyphs[k] = str(v).strip()
    data['map_glyphs'] = normalized_glyphs

    # Normalize rooms (exits, locked_exits, fixtures, items)
    normalized_rooms = []
    for r in data['rooms']:
        if not isinstance(r, dict) or 'name' not in r:
            continue
        
        # Exits normalization
        raw_exits = r.get('exits', [])
        if isinstance(raw_exits, list):
            clean_exits = [str(e).strip().lstrip('-').strip() for e in raw_exits if str(e).strip()]
        elif isinstance(raw_exits, dict):
            clean_exits = [str(k).strip() for k in raw_exits.keys() if str(k).strip()]
        elif isinstance(raw_exits, str):
            clean_exits = [e.strip().lstrip('-').strip() for e in raw_exits.replace(',', ' ').split() if e.strip()]
        else:
            clean_exits = []
        r['exits'] = clean_exits

        # Locked exits normalization
        raw_locked = r.get('locked_exits', [])
        if isinstance(raw_locked, list):
            clean_locked = [str(e).strip().lstrip('-').strip() for e in raw_locked if str(e).strip()]
        elif isinstance(raw_locked, str):
            clean_locked = [e.strip().lstrip('-').strip() for e in raw_locked.replace(',', ' ').split() if e.strip()]
        else:
            clean_locked = []
        r['locked_exits'] = clean_locked

        r.setdefault('fixtures', {})
        if not isinstance(r['fixtures'], dict):
            r['fixtures'] = {}

        r.setdefault('items', [])
        if not isinstance(r['items'], list):
            r['items'] = []

        normalized_rooms.append(r)
    data['rooms'] = normalized_rooms

    # =========================================================================
    # 2. TIER 3: FATAL STRUCTURAL VALIDATION (Cannot Safely Play)
    # =========================================================================
    # Check A: Room catalog presence
    if len(data['rooms']) == 0:
        raise AdventureConfigError(
            message="No rooms defined in the adventure layout.",
            filename=str(path),
            details="The 'rooms' list is empty or contains no valid room objects with a 'name'.",
            fix="Define at least one room under 'rooms:' with a unique 'name'."
        )

    # Check B: Floor limit (Between 1 and 6 floors)
    if len(data['floors']) > 6:
        raise AdventureConfigError(
            message=f"Floor layout defines {len(data['floors'])} floors, which exceeds the maximum allowed 6 floors (Floors 0 to 5).",
            filename=str(path),
            details=f"Current floors: {len(data['floors'])}; Maximum allowed: 6",
            fix="Remove extraneous floors to keep the dungeon layout between 1 and 6 floors."
        )

    if len(data['floors']) == 0:
        raise AdventureConfigError(
            message="No floors defined in the adventure layout.",
            filename=str(path),
            details="The 'floors' array is empty.",
            fix="Define at least one floor grid (Floor 0) with room coordinates."
        )

    known_room_names = {r['name'] for r in data['rooms']}

    # Check C: Floor grid integrity and room references
    for floor_idx, floor_layout in enumerate(data['floors']):
        if not isinstance(floor_layout, list):
            raise AdventureConfigError(
                message=f"Floor {floor_idx} is not a valid 2D grid list.",
                filename=str(path),
                fix="Ensure each floor in 'floors:' is a list of rows."
            )
        for row_idx, row in enumerate(floor_layout):
            if not isinstance(row, list):
                raise AdventureConfigError(
                    message=f"Floor {floor_idx}, row {row_idx} is not a list.",
                    filename=str(path),
                    fix="Ensure each row in the floor grid is a list of room names or null."
                )
            for col_idx, cell in enumerate(row):
                if cell is not None and cell != "_" and cell != "" and cell not in known_room_names:
                    raise AdventureConfigError(
                        message=f"Floor {floor_idx} grid tile at (row {row_idx}, col {col_idx}) references room '{cell}', but '{cell}' is not defined in 'rooms:'.",
                        filename=str(path),
                        details=f"Referenced room '{cell}' missing from catalog.",
                        fix=f"Add a room entry for '{cell}' under 'rooms:' or update the floor grid tile."
                    )

    # Check D: Starting location resolution
    raw_start = data['player'].get('starting_location') or data['intro'].get('starting_location')
    if isinstance(raw_start, dict):
        s_floor = int(raw_start.get('floor', 0))
        s_x = int(raw_start.get('x', 0))
        s_y = int(raw_start.get('y', 0))
    else:
        s_floor, s_x, s_y = 0, 0, 0

    if s_floor < 0 or s_floor >= len(data['floors']):
        raise AdventureConfigError(
            message=f"Starting floor {s_floor} does not exist in floor grid.",
            filename=str(path),
            details=f"Defined floors: 0 to {len(data['floors']) - 1}",
            fix="Set player.starting_location.floor to an active floor index."
        )

    floor_grid = data['floors'][s_floor]
    if not isinstance(floor_grid, list) or s_y < 0 or s_y >= len(floor_grid) or s_x < 0 or s_x >= len(floor_grid[s_y]):
        raise AdventureConfigError(
            message=f"Starting location (Floor {s_floor}, X={s_x}, Y={s_y}) is out of bounds.",
            filename=str(path),
            details="Coordinates point outside the floor grid dimensions.",
            fix="Ensure starting_location x and y fall inside the floor grid."
        )

    spawn_room_name = floor_grid[s_y][s_x]
    if not spawn_room_name or spawn_room_name == "_":
        raise AdventureConfigError(
            message=f"Starting location (Floor {s_floor}, X={s_x}, Y={s_y}) is empty (null) or out of bounds. The player must spawn in an active room.",
            filename=str(path),
            details=f"Tile at Floor {s_floor} [Y:{s_y}, X:{s_x}] contains None/null.",
            fix="Assign a room name to this grid tile or move starting_location to an existing room."
        )

    if spawn_room_name not in known_room_names:
        raise AdventureConfigError(
            message=f"Starting room '{spawn_room_name}' is placed on grid but not defined in 'rooms' catalog.",
            filename=str(path),
            details=f"Spawn room '{spawn_room_name}' is missing from rooms list.",
            fix=f"Add a definition for '{spawn_room_name}' under 'rooms:' or update the spawn coordinates."
        )

    # Check E: Exit destination references (if custom exit_destinations specified)
    for r in data['rooms']:
        raw_dest = r.get('exit_destinations')
        if isinstance(raw_dest, dict):
            for exit_dir, dest in raw_dest.items():
                if isinstance(dest, dict):
                    df = dest.get('floor')
                    dx = dest.get('x')
                    dy = dest.get('y')
                    if df is None or dx is None or dy is None:
                        raise AdventureConfigError(
                            message=f"Room '{r['name']}' exit '{exit_dir}' destination must specify 'floor', 'x', and 'y'.",
                            filename=str(path),
                            fix="Provide 'floor', 'x', and 'y' integer coordinates in exit_destinations."
                        )
                    if df < 0 or df >= len(data['floors']):
                        raise AdventureConfigError(
                            message=f"Room '{r['name']}' exit '{exit_dir}' points to non-existent floor {df}.",
                            filename=str(path),
                            fix=f"Floor index must be between 0 and {len(data['floors']) - 1}."
                        )
                    target_floor = data['floors'][df]
                    if dy < 0 or dy >= len(target_floor) or dx < 0 or dx >= len(target_floor[dy]) or not target_floor[dy][dx]:
                        raise AdventureConfigError(
                            message=f"Room '{r['name']}' exit '{exit_dir}' leads to empty tile or out-of-bounds coordinate (Floor {df}, X={dx}, Y={dy}).",
                            filename=str(path),
                            fix="Ensure the exit target coordinate contains an active room on the floor grid."
                        )
                elif isinstance(dest, str):
                    if dest not in known_room_names:
                        raise AdventureConfigError(
                            message=f"Room '{r['name']}' exit '{exit_dir}' points to non-existent room '{dest}'.",
                            filename=str(path),
                            fix=f"Add '{dest}' to 'rooms:' or correct the destination name."
                        )

    # =========================================================================
    # 3. TIER 2: WARNINGS (Non-Fatal Inconsistencies)
    # =========================================================================
    warnings = []

    # Check for starting inventory items missing from item catalog
    start_inv = data['player'].get('starting_inventory', [])
    for it in start_inv:
        if it not in data['items']:
            warnings.append(f"Starting inventory item '{it}' has no definition in 'items:' dictionary.")

    # Check for event targets that do not exist anywhere in items or fixtures
    all_fixtures = set()
    for r in data['rooms']:
        all_fixtures.update(r.get('fixtures', {}).keys())
    all_items = set(data['items'].keys())
    for r in data['rooms']:
        all_items.update(r.get('items', []))
    all_targets = all_fixtures | all_items | set(data['target_aliases'].keys())

    for ev in data.get('events', []):
        if not isinstance(ev, dict):
            continue
        ev_id = ev.get('id', 'unnamed')
        trig = ev.get('trigger', {})
        tgt = trig.get('target')
        if tgt and tgt not in all_targets:
            warnings.append(f"Event '{ev_id}' triggers on target '{tgt}', which is not placed in any room or item/alias catalog.")

        for c_data in ev.get('conditions', []):
            if isinstance(c_data, dict) and c_data.get('type') == 'in_room':
                req_room = c_data.get('room')
                if req_room and req_room not in known_room_names:
                    warnings.append(f"Event '{ev_id}' in_room condition requires room '{req_room}', which is not in 'rooms:' list.")

    # Check for win conditions pointing to non-existent events
    existing_events = {ev.get('id') for ev in data.get('events', []) if isinstance(ev, dict)}
    for win_id in data.get('win_conditions', []):
        if win_id not in existing_events:
            warnings.append(f"Win condition event '{win_id}' is not defined in 'events:' list.")

    for w in warnings:
        print(f"[YAML WARNING] {path.name}: {w}", file=sys.stderr)

    return data

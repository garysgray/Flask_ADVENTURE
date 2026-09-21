/**
 * Sanity Validator: Rules and diagnostic cards rendering
 */

function runValidation() {
  if (!window.State || !window.State.yamlData) return;
  window.State.validationResults = performGameSanityChecks(window.State.yamlData);
  updateValidationUI();
}

function filterValidationCategory(category, btn) {
  if (!window.State) return;
  window.State.valFilterCategory = category;
  document.querySelectorAll('#view-validator .filter-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderValidationCards();
}

function updateValidationUI() {
  const State = window.State;
  if (!State) return;
  const errs  = State.validationResults.filter(r => r.level === 'error');
  const warns = State.validationResults.filter(r => r.level === 'warning');
  const passes= State.validationResults.filter(r => r.level === 'pass');

  document.getElementById('val-count-all').textContent      = State.validationResults.length;
  document.getElementById('val-count-errors').textContent   = errs.length;
  document.getElementById('val-count-warnings').textContent = warns.length;
  document.getElementById('val-count-passed').textContent   = passes.length;

  const topBadge = document.getElementById('top-val-badge');
  if (topBadge) {
    if (errs.length > 0) {
      topBadge.className = 'val-top-badge val-badge-err';
      topBadge.textContent = '✕ ' + errs.length + ' ERROR' + (errs.length > 1 ? 'S' : '');
    } else if (warns.length > 0) {
      topBadge.className = 'val-top-badge val-badge-warn';
      topBadge.textContent = '⚠ ' + warns.length + ' WARNING' + (warns.length > 1 ? 'S' : '');
    } else {
      topBadge.className = 'val-top-badge val-badge-ok';
      topBadge.textContent = '✓ 0 ISSUES';
    }
  }

  const banner = document.getElementById('val-summary-banner');
  const icon   = document.getElementById('val-banner-icon');
  const title  = document.getElementById('val-banner-title');
  const desc   = document.getElementById('val-banner-desc');

  if (banner) {
    if (errs.length > 0) {
      banner.className = 'val-summary-banner val-banner-err';
      icon.textContent = '✕';
      title.textContent = errs.length + ' CRITICAL SANITY ISSUE' + (errs.length > 1 ? 'S' : '') + ' DETECTED';
      desc.textContent = 'Fix missing rooms, broken exits, or orphan references before testing.';
    } else if (warns.length > 0) {
      banner.className = 'val-summary-banner val-banner-warn';
      icon.textContent = '⚠';
      title.textContent = warns.length + ' GAME ARCHITECTURE WARNING' + (warns.length > 1 ? 'S' : '') + ' DETECTED';
      desc.textContent = 'Map and room definitions are syntactically valid with minor suggestions.';
    } else {
      banner.className = 'val-summary-banner val-banner-pass';
      icon.textContent = '✓';
      title.textContent = 'ALL SANITY CHECKS PASSING';
      desc.textContent = 'No orphan rooms, broken exits, or missing fixtures detected.';
    }
  }

  renderValidationCards();
}

function renderValidationCards() {
  const State = window.State;
  if (!State) return;
  const container = document.getElementById('validator-cards-container');
  if (!container) return;
  container.innerHTML = '';

  const filtered = State.validationResults.filter(r => {
    if (State.valFilterCategory === 'errors')   return r.level === 'error';
    if (State.valFilterCategory === 'warnings') return r.level === 'warning';
    if (State.valFilterCategory === 'passed')   return r.level === 'pass';
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div style="padding:20px; color:var(--dim); font-family:var(--mono);">No diagnostics in this filter.</div>';
    return;
  }

  filtered.forEach(r => {
    const card = document.createElement('div');
    card.className = 'val-card ' + r.level;
    card.innerHTML = `
      <div class="val-card-top">
        <span style="font-weight:bold; color:${r.level === 'error' ? 'var(--red)' : r.level === 'warning' ? 'var(--amber)' : 'var(--accent)'}">
          ${r.level === 'error' ? '✕ ERROR' : r.level === 'warning' ? '⚠ WARNING' : '✓ HEALTHY'} /// ${r.title}
        </span>
        <span style="color:var(--dim);">${r.category.toUpperCase()}</span>
      </div>
      <div style="color:var(--text); margin-top:2px;">${r.desc}</div>
      ${r.hint ? '<div style="color:var(--dim); font-size:10px; font-family:var(--mono); margin-top:4px;">💡 ' + r.hint + '</div>' : ''}
    `;
    container.appendChild(card);
  });
}

function performGameSanityChecks(d) {
  const results = [];
  if (!d) return results;

  const rooms = d.rooms || [];
  const roomNames = new Set(rooms.map(r => r.name));
  const itemsDict = d.items || {};
  const floors = d.floors || [];

  // 1. Floor Count Guardrail (Max 6 Floors)
  if (floors.length > 6) {
    results.push({
      category: 'floors',
      level: 'error',
      title: 'Exceeds Maximum Floors (Max 6)',
      desc: `Adventure defines ${floors.length} floors. The game engine allows a maximum of 6 floors (Floors 0 to 5).`,
      hint: 'Remove extra floors in the Map tab to bring the layout within the 6-floor limit.'
    });
  } else if (floors.length === 0) {
    results.push({
      category: 'floors',
      level: 'error',
      title: 'No Floors Configured',
      desc: 'Adventure has 0 floors configured.',
      hint: 'Add at least Floor 0 in the Map tab.'
    });
  } else {
    results.push({
      category: 'floors',
      level: 'pass',
      title: 'Floor Count Valid',
      desc: `Adventure has ${floors.length} floor(s), respecting the 6-floor maximum.`
    });
  }

  // 2. Starting Room / Spawn Location Resolution
  const startLoc = (d.player && d.player.starting_location) || { floor: 0, x: 0, y: 0 };
  const sFloor = startLoc.floor ?? 0;
  const sX = startLoc.x ?? 0;
  const sY = startLoc.y ?? 0;

  if (!floors[sFloor] || !Array.isArray(floors[sFloor])) {
    results.push({
      category: 'player',
      level: 'error',
      title: 'Spawn Floor Out of Range',
      desc: `Player starting floor (${sFloor}) does not exist. Total floors: ${floors.length}.`,
      hint: 'Use the Map tab to set the start room on an active floor.'
    });
  } else if (!floors[sFloor][sY] || floors[sFloor][sY][sX] === undefined) {
    results.push({
      category: 'player',
      level: 'error',
      title: 'Spawn Coordinates Out of Bounds',
      desc: `Spawn coordinates Floor ${sFloor} [X:${sX}, Y:${sY}] fall outside the floor grid.`,
      hint: 'Click "Set Start" on a valid room tile in the 5x5 grid.'
    });
  } else {
    const spawnRoom = floors[sFloor][sY][sX];
    if (!spawnRoom) {
      results.push({
        category: 'player',
        level: 'error',
        title: 'Empty Spawn Tile',
        desc: `Spawn tile Floor ${sFloor} [X:${sX}, Y:${sY}] is null/empty. The player must spawn inside an active room.`,
        hint: 'Drag a room onto this tile, or click "Set Start" on an active room card in the Map tab.'
      });
    } else if (!roomNames.has(spawnRoom)) {
      results.push({
        category: 'player',
        level: 'error',
        title: 'Invalid Spawn Room ID',
        desc: `Starting room "${spawnRoom}" is placed on the grid but not defined in the "rooms" catalog.`,
        hint: 'Create this room or place a defined room at the spawn tile.'
      });
    } else {
      results.push({
        category: 'player',
        level: 'pass',
        title: 'Player Spawn Tile Valid',
        desc: `Player spawns in "${spawnRoom}" at Floor ${sFloor} [X:${sX}, Y:${sY}].`
      });
    }
  }

  // 3. Player Starting Inventory Integrity
  const startInv = (d.player && d.player.starting_inventory) || [];
  let missingInvItems = 0;
  startInv.forEach(it => {
    if (!itemsDict[it]) {
      missingInvItems++;
      results.push({
        category: 'items',
        level: 'error',
        title: `Undefined Starting Inventory Item: "${it}"`,
        desc: `Item "${it}" is listed in player.starting_inventory but missing from the "items:" dictionary.`,
        hint: `Define "${it}" under the items dictionary with states and keywords.`
      });
    }
  });
  if (missingInvItems === 0) {
    results.push({
      category: 'items',
      level: 'pass',
      title: 'Starting Inventory Validated',
      desc: `All ${startInv.length} starting inventory item(s) are fully defined.`
    });
  }

  // 4. Room Exits Integrity
  let brokenExits = 0;
  const validDirections = new Set([
    'north', 'south', 'east', 'west',
    'up', 'down', 'in', 'out',
    'ladder', 'stairs', 'portal', 'warp',
    'n', 's', 'e', 'w', 'u', 'd',
    'ne', 'nw', 'se', 'sw',
    'northeast', 'northwest', 'southeast', 'southwest'
  ]);

  rooms.forEach(r => {
    if (!r.exits) return;

    if (Array.isArray(r.exits)) {
      // Direction list format: ["east", "south"]
      r.exits.forEach(dir => {
        const dStr = String(dir).toLowerCase().trim();
        if (!validDirections.has(dStr)) {
          brokenExits++;
          results.push({
            category: 'rooms',
            level: 'warning',
            title: `Unrecognized Exit Direction in "${r.name}"`,
            desc: `Room "${r.name}" lists direction "${dir}" which is not a recognized movement direction.`,
            hint: `Use standard directions like north, south, east, west, up, down.`
          });
        }
      });
    } else if (typeof r.exits === 'object' && r.exits !== null) {
      brokenExits++;
      results.push({
        category: 'rooms',
        level: 'warning',
        title: `Exits Should Be a List in "${r.name}"`,
        desc: `Room "${r.name}" defines exits as a key-value dictionary. The engine expects exits to be a list of direction names (e.g. ["north", "south"]).`,
        hint: `Change exits to a list of directions so event actions like open_exit function properly.`
      });
    }
  });

  if (brokenExits === 0) {
    results.push({
      category: 'rooms',
      level: 'pass',
      title: 'Room Exits Validated',
      desc: 'All room exits are configured correctly as direction lists.'
    });
  }

  // 4b. Target Aliases Format
  const targetAliases = d.target_aliases;
  if (targetAliases && typeof targetAliases === 'object' && !Array.isArray(targetAliases)) {
    let invalidAliases = 0;
    Object.entries(targetAliases).forEach(([canonical, aliases]) => {
      if (!Array.isArray(aliases)) {
        invalidAliases++;
        results.push({
          category: 'events',
          level: 'error',
          title: `Malformed Target Alias for "${canonical}"`,
          desc: `target_aliases entry for "${canonical}" is not a list. Format must be "target_id: [alias1, alias2]".`,
          hint: `Change to: ${canonical}: ["${aliases}"]`
        });
      }
    });
    if (invalidAliases === 0 && Object.keys(targetAliases).length > 0) {
      results.push({
        category: 'events',
        level: 'pass',
        title: 'Target Aliases Validated',
        desc: 'All target aliases map canonical IDs to list of alias strings.'
      });
    }
  }

  // 5. Win Conditions
  const winEvents = d.win_conditions || [];
  const eventIds = new Set((d.events || []).map(e => e.id || e.name));
  if (winEvents.length === 0) {
    results.push({
      category: 'win',
      level: 'warning',
      title: 'No Win Objectives',
      desc: 'Adventure has no win_conditions configured.',
      hint: 'Add an objective in the story tab.'
    });
  } else {
    let brokenWin = 0;
    winEvents.forEach(eid => {
      if (!eventIds.has(eid)) {
        brokenWin++;
        results.push({
          category: 'win',
          level: 'error',
          title: `Broken Win Objective: "${eid}"`,
          desc: `Win condition "${eid}" does not match any event in events:.`,
          hint: `Verify event ID "${eid}" exists in events.`
        });
      }
    });
    if (brokenWin === 0) {
      results.push({
        category: 'win',
        level: 'pass',
        title: 'Win Objectives Valid',
        desc: `All ${winEvents.length} victory condition(s) point to valid events.`
      });
    }
  }

  // 6. Modular Rooms Prose Quality
  let emptyDescCount = 0;
  rooms.forEach(r => {
    const full = window.assembleRoomDescription ? window.assembleRoomDescription(r) : '';
    if (!full || full.trim().length === 0) emptyDescCount++;
  });
  if (emptyDescCount > 0) {
    results.push({
      category: 'rooms',
      level: 'warning',
      title: 'Empty Room Descriptions',
      desc: `${emptyDescCount} room(s) have no base, fixture, or trailing prose.`,
      hint: 'Provide descriptive text in the room prose editor.'
    });
  } else {
    results.push({
      category: 'rooms',
      level: 'pass',
      title: 'Modular Room Descriptions Complete',
      desc: `All ${rooms.length} rooms have active prose.`
    });
  }

  return results;
}

window.runValidation = runValidation;
window.filterValidationCategory = filterValidationCategory;
window.updateValidationUI = updateValidationUI;
window.renderValidationCards = renderValidationCards;
window.performGameSanityChecks = performGameSanityChecks;


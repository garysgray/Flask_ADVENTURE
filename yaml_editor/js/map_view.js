/**
 * Map View: 5x5 Interactive Drag-and-Drop Floor Grid Editor, Room Palette,
 * Event flow, and Item catalog.
 */

window.activeMapFloorIndex = 0;
window.paletteSearchQuery = '';

function classifyItem(name, data) {
  const startInv = (data.player && data.player.starting_inventory) || [];
  if (startInv.includes(name)) return 'start';
  const eventItems = new Set();
  (data.events || []).forEach(ev => {
    if (ev.parameters) {
      if (ev.parameters.item)   eventItems.add(ev.parameters.item);
      if (ev.parameters.target) eventItems.add(ev.parameters.target);
    }
    if (ev.trigger) {
      if (ev.trigger.source) eventItems.add(ev.trigger.source);
      if (ev.trigger.target) eventItems.add(ev.trigger.target);
    }
    if (ev.result && ev.result.add_item) {
      const it = typeof ev.result.add_item === 'string' ? ev.result.add_item : ev.result.add_item.item;
      if (it) eventItems.add(it);
    }
  });
  if (eventItems.has(name)) return 'key';
  const itemData = data.items && data.items[name];
  if (itemData && itemData.states && itemData.states.default) {
    if ((itemData.states.default.use || '').length > 80) return 'lore';
  }
  return 'flavor';
}

function getRoomEvents(roomName, data) {
  const triggers = [], affected = [];
  (data.events || []).forEach(ev => {
    const p = ev.parameters || {};
    const cond = ev.conditions || [];
    const inRoomCond = cond.some(c => c.room === roomName);
    if (p.room === roomName || inRoomCond) {
      triggers.push(ev);
    } else if (ev.result) {
      const inStates = (ev.result.set_state || []).some(s => s.room === roomName);
      const inFixtures = (ev.result.set_fixture_state || []).some(s => s.room === roomName);
      const inExits  = (ev.result.open_exit || []).some(x => x.room === roomName);
      if (inStates || inFixtures || inExits) affected.push(ev);
    }
  });
  return { triggers, affected };
}

function buildRoomPositions(data) {
  const pos = {};
  (data.floors || []).forEach((floor, fi) => {
    floor.forEach((row, ri) => {
      row.forEach((cell, ci) => {
        if (cell && cell !== '_') pos[cell] = { floor: fi, row: ri, col: ci };
      });
    });
  });
  return pos;
}

function ensure5x5Floor(floor) {
  if (!Array.isArray(floor)) floor = [];
  while (floor.length < 5) {
    floor.push([null, null, null, null, null]);
  }
  for (let r = 0; r < 5; r++) {
    if (!Array.isArray(floor[r])) floor[r] = [];
    while (floor[r].length < 5) {
      floor[r].push(null);
    }
  }
  return floor;
}

function normalizeFloorsData(data) {
  if (!Array.isArray(data.floors) || data.floors.length === 0) {
    data.floors = [
      [
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null]
      ]
    ];
  }
  data.floors.forEach((f, idx) => {
    data.floors[idx] = ensure5x5Floor(f);
  });
}

function buildMapView(data) {
  if (!data) return;
  normalizeFloorsData(data);
  buildMapGrids(data);
  buildRoomList(data);
  buildEventFlow(data);
  buildItemList(data);
}

function buildMapGrids(data) {
  const container = document.getElementById('map-section');
  if (!container) return;
  container.innerHTML = '<div class="section-title">INTERACTIVE FLOOR MAP (5×5 GRID &bull; MAX 6 FLOORS)</div>';

  normalizeFloorsData(data);
  const floors = data.floors;
  if (window.activeMapFloorIndex >= floors.length) {
    window.activeMapFloorIndex = Math.max(0, floors.length - 1);
  }
  const currentFloorIdx = window.activeMapFloorIndex;
  const currentFloorGrid = floors[currentFloorIdx];

  const roomsByName = {};
  (data.rooms || []).forEach(r => { roomsByName[r.name] = r; });

  const startLoc = (data.player && data.player.starting_location) || { floor: 0, x: 0, y: 0 };

  const workspace = document.createElement('div');
  workspace.className = 'map-editor-workspace';

  // 1. MAIN STAGE (Floor tabs + 5x5 board)
  const stage = document.createElement('div');
  stage.className = 'map-main-stage';

  // Controls bar
  const controlsBar = document.createElement('div');
  controlsBar.className = 'floor-controls-bar';

  const tabsList = document.createElement('div');
  tabsList.className = 'floor-tabs-list';

  floors.forEach((_, fIdx) => {
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'floor-tab-btn' + (fIdx === currentFloorIdx ? ' active' : '');
    tab.textContent = `Floor ${fIdx}`;
    tab.onclick = () => {
      window.activeMapFloorIndex = fIdx;
      buildMapView(data);
    };
    tabsList.appendChild(tab);
  });

  controlsBar.appendChild(tabsList);

  // Add Floor Button (Enforce max 6 floors)
  if (floors.length < 6) {
    const addFloorBtn = document.createElement('button');
    addFloorBtn.type = 'button';
    addFloorBtn.className = 'btn btn-accent';
    addFloorBtn.style.padding = '5px 10px';
    addFloorBtn.style.fontSize = '11px';
    addFloorBtn.textContent = '+ Add Floor';
    addFloorBtn.onclick = () => {
      if (floors.length >= 6) {
        alert('Maximum floor limit reached (6 floors max: Floors 0 to 5).');
        return;
      }
      floors.push([
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null],
        [null, null, null, null, null]
      ]);
      window.activeMapFloorIndex = floors.length - 1;
      onDataModified('add_floor');
      buildMapView(data);
      if (window.State) window.State.showToast(`ADDED FLOOR ${window.activeMapFloorIndex}`);
    };
    controlsBar.appendChild(addFloorBtn);
  }

  // Delete Floor Button
  if (floors.length > 1) {
    const delFloorBtn = document.createElement('button');
    delFloorBtn.type = 'button';
    delFloorBtn.className = 'btn btn-dim';
    delFloorBtn.style.padding = '5px 10px';
    delFloorBtn.style.fontSize = '11px';
    delFloorBtn.style.color = 'var(--red)';
    delFloorBtn.textContent = 'Delete Floor';
    delFloorBtn.onclick = () => {
      const ok = confirm(`Delete Floor ${currentFloorIdx}? Placed rooms on this floor will become unplaced.`);
      if (!ok) return;
      floors.splice(currentFloorIdx, 1);
      window.activeMapFloorIndex = Math.max(0, currentFloorIdx - 1);
      onDataModified('delete_floor');
      buildMapView(data);
      if (window.State) window.State.showToast(`DELETED FLOOR ${currentFloorIdx}`);
    };
    controlsBar.appendChild(delFloorBtn);
  }

  // Limit indicator badge
  const limitBadge = document.createElement('div');
  limitBadge.className = 'floor-limit-badge';
  limitBadge.textContent = `${floors.length} / 6 FLOORS (MAX 6)`;
  controlsBar.appendChild(limitBadge);

  stage.appendChild(controlsBar);

  // 5x5 Grid Board
  const board = document.createElement('div');
  board.className = 'grid-5x5-board';

  for (let r = 0; r < 5; r++) {
    for (let c = 0; c < 5; c++) {
      const roomName = currentFloorGrid[r][c];
      const isCenter = (r === 2 && c === 2);
      const isSpawn = (currentFloorIdx === startLoc.floor && c === startLoc.x && r === startLoc.y);

      if (roomName && roomsByName[roomName]) {
        const room = roomsByName[roomName];
        const evInfo = getRoomEvents(roomName, data);
        const hasEvent = evInfo.triggers.length > 0 || evInfo.affected.length > 0;

        // Check vertical movement cues
        const exits = room.exits || [];
        const hasStairs = Array.isArray(exits)
          ? exits.some(x => ['up', 'down', 'ladder', 'stairs'].includes(String(x).toLowerCase().trim()))
          : !!(exits.up || exits.down || exits.ladder || exits.stairs);
        const hasPortal = Array.isArray(exits)
          ? exits.some(x => ['portal', 'warp'].includes(String(x).toLowerCase().trim())) || (room.exit_destinations && Object.keys(room.exit_destinations).length > 0)
          : !!(exits.portal || exits.warp || (room.exit_destinations && Object.keys(room.exit_destinations).length > 0));

        const tile = document.createElement('div');
        tile.className = 'placed-room-tile' + (isSpawn ? ' is-spawn' : '');
        tile.draggable = true;

        tile.ondragstart = (e) => {
          e.dataTransfer.setData('application/json', JSON.stringify({
            roomName: roomName,
            from: { floor: currentFloorIdx, row: r, col: c }
          }));
        };

        // Enable dropping onto placed tile to swap or replace
        tile.ondragover = (e) => {
          e.preventDefault();
          tile.classList.add('drop-hover');
        };
        tile.ondragleave = () => tile.classList.remove('drop-hover');
        tile.ondrop = (e) => {
          e.preventDefault();
          tile.classList.remove('drop-hover');
          handleDropOnCell(e, currentFloorIdx, r, c, data);
        };

        // Top line: coords & spawn flag
        const top = document.createElement('div');
        top.className = 'placed-tile-top';
        top.innerHTML = `<span>[${c}, ${r}]${isCenter ? ' &bull; CTR' : ''}</span><span style="cursor:pointer;" onclick="openRoomModal('${roomName}')">✎ PROSE</span>`;
        tile.appendChild(top);

        // Room name
        const nameEl = document.createElement('div');
        nameEl.className = 'placed-tile-name';
        nameEl.textContent = room.display_name || room.name;
        nameEl.title = `ID: ${room.name}`;
        tile.appendChild(nameEl);

        // Badges row
        const badges = document.createElement('div');
        badges.className = 'placed-tile-badges';

        if (isSpawn) {
          badges.innerHTML += '<span class="badge-tag start">📍 START</span>';
        }
        if (hasStairs) {
          badges.innerHTML += '<span class="badge-tag stairs">🪜 STAIRS</span>';
        }
        if (hasPortal) {
          badges.innerHTML += '<span class="badge-tag portal">🌀 PORTAL</span>';
        }
        if (hasEvent) {
          badges.innerHTML += '<span class="badge-tag event">⚡ EVENT</span>';
        }
        if (room.items && room.items.length > 0) {
          badges.innerHTML += `<span class="badge-tag" style="background:rgba(90,154,204,0.2);color:var(--blue)">📦 ${room.items.length}</span>`;
        }
        tile.appendChild(badges);

        // Actions toolbar
        const actions = document.createElement('div');
        actions.className = 'placed-tile-actions';

        const startBtn = document.createElement('button');
        startBtn.type = 'button';
        startBtn.className = 'placed-action-btn' + (isSpawn ? ' active-start' : '');
        startBtn.textContent = isSpawn ? '✓ Spawn' : 'Set Start';
        startBtn.onclick = (e) => {
          e.stopPropagation();
          setPlayerStartLocation(currentFloorIdx, c, r, room.name, data);
        };
        actions.appendChild(startBtn);

        const rmBtn = document.createElement('button');
        rmBtn.type = 'button';
        rmBtn.className = 'placed-action-btn btn-remove';
        rmBtn.textContent = '✕ Remove';
        rmBtn.title = 'Remove room from grid (keeps in palette)';
        rmBtn.onclick = (e) => {
          e.stopPropagation();
          currentFloorGrid[r][c] = null;
          onDataModified('remove_room_from_grid');
          buildMapView(data);
          if (window.State) window.State.showToast(`UNASSIGNED ${room.name}`);
        };
        actions.appendChild(rmBtn);

        tile.appendChild(actions);
        board.appendChild(tile);
      } else {
        // Empty Dropzone cell
        const dropzone = document.createElement('div');
        dropzone.className = 'grid-cell-dropzone' + (isCenter ? ' is-center' : '');
        dropzone.innerHTML = `
          <div class="dropzone-coord">[${c}, ${r}]${isCenter ? ' &bull; CENTER' : ''}</div>
          <div class="dropzone-hint">+ Drop Room Here</div>
          <div></div>
        `;

        dropzone.ondragover = (e) => {
          e.preventDefault();
          dropzone.classList.add('drop-hover');
        };
        dropzone.ondragleave = () => dropzone.classList.remove('drop-hover');
        dropzone.ondrop = (e) => {
          e.preventDefault();
          dropzone.classList.remove('drop-hover');
          handleDropOnCell(e, currentFloorIdx, r, c, data);
        };

        board.appendChild(dropzone);
      }
    }
  }

  stage.appendChild(board);
  workspace.appendChild(stage);

  // 2. ROOM PALETTE SIDEBAR
  const palette = buildRoomPaletteSidebar(data);
  workspace.appendChild(palette);

  container.appendChild(workspace);
}

function handleDropOnCell(e, toFloor, toRow, toCol, data) {
  let payload = null;
  const rawJson = e.dataTransfer.getData('application/json');
  if (rawJson) {
    try { payload = JSON.parse(rawJson); } catch (_) {}
  }
  const plainName = e.dataTransfer.getData('text/plain');
  const targetRoomName = payload ? payload.roomName : plainName;
  if (!targetRoomName) return;

  const currentFloorGrid = data.floors[toFloor];
  const existingAtTarget = currentFloorGrid[toRow][toCol];

  if (payload && payload.from) {
    // Moved from another cell: swap or move
    const fromGrid = data.floors[payload.from.floor];
    fromGrid[payload.from.row][payload.from.col] = existingAtTarget || null;
    currentFloorGrid[toRow][toCol] = targetRoomName;
  } else {
    // Dragged from Room Palette: place room
    currentFloorGrid[toRow][toCol] = targetRoomName;
  }

  onDataModified('place_room_on_grid');
  buildMapView(data);
  if (window.State) window.State.showToast(`PLACED ${targetRoomName} AT [${toCol}, ${toRow}]`);
}

function setPlayerStartLocation(floor, x, y, roomName, data) {
  if (!data.player) data.player = {};
  data.player.starting_location = { floor, x, y };

  const spawnStatus = document.getElementById('story-status-spawn');
  if (spawnStatus) spawnStatus.textContent = `Floor ${floor} [${x},${y}] (${roomName})`;

  onDataModified('set_spawn_tile');
  buildMapView(data);
  if (window.State) window.State.showToast(`SPAWN POINT SET TO ${roomName} AT [${x}, ${y}]`);
}

function buildRoomPaletteSidebar(data) {
  const sidebar = document.createElement('div');
  sidebar.className = 'room-palette-sidebar';

  const positions = buildRoomPositions(data);
  const rooms = data.rooms || [];

  const head = document.createElement('div');
  head.className = 'palette-head';
  head.innerHTML = `
    <span class="palette-title">ROOM PALETTE (${rooms.length})</span>
  `;

  const newRoomBtn = document.createElement('button');
  newRoomBtn.type = 'button';
  newRoomBtn.className = 'btn btn-accent';
  newRoomBtn.style.padding = '4px 8px';
  newRoomBtn.style.fontSize = '10px';
  newRoomBtn.textContent = '+ New Room';
  newRoomBtn.onclick = () => promptCreateRoom(data);
  head.appendChild(newRoomBtn);

  sidebar.appendChild(head);

  // Search filter
  const searchInp = document.createElement('input');
  searchInp.type = 'text';
  searchInp.className = 'search-input';
  searchInp.style.width = '100%';
  searchInp.style.border = '1px solid var(--border)';
  searchInp.style.borderRadius = '4px';
  searchInp.style.padding = '5px 8px';
  searchInp.style.background = 'var(--panel-alt)';
  searchInp.placeholder = 'Filter palette rooms...';
  searchInp.value = window.paletteSearchQuery || '';
  searchInp.oninput = (e) => {
    window.paletteSearchQuery = e.target.value;
    renderPaletteRoomCards(data, cardsScroll, positions);
  };
  sidebar.appendChild(searchInp);

  const cardsScroll = document.createElement('div');
  cardsScroll.className = 'palette-rooms-scroll';
  renderPaletteRoomCards(data, cardsScroll, positions);

  sidebar.appendChild(cardsScroll);
  return sidebar;
}

function renderPaletteRoomCards(data, container, positions) {
  container.innerHTML = '';
  const q = (window.paletteSearchQuery || '').trim().toLowerCase();
  const rooms = data.rooms || [];

  const filtered = rooms.filter(r => {
    if (!q) return true;
    return r.name.toLowerCase().includes(q) || (r.display_name || '').toLowerCase().includes(q);
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div style="font-family:var(--mono);font-size:11px;color:var(--dim);padding:8px;">No matching rooms found.</div>';
    return;
  }

  filtered.forEach(r => {
    const pos = positions[r.name];
    const isPlaced = !!pos;

    const card = document.createElement('div');
    card.className = 'palette-room-card';
    card.draggable = true;
    card.title = 'Drag to 5x5 grid or click to inspect prose';

    card.ondragstart = (e) => {
      e.dataTransfer.setData('text/plain', r.name);
    };
    card.onclick = () => openRoomModal(r.name);

    const top = document.createElement('div');
    top.className = 'palette-room-top';
    top.innerHTML = `
      <span class="palette-room-name">${r.display_name || r.name}</span>
      <span class="palette-room-status ${isPlaced ? 'placed' : 'unplaced'}">${isPlaced ? `F:${pos.floor} [${pos.col},${pos.row}]` : 'Unplaced'}</span>
    `;
    card.appendChild(top);

    const meta = document.createElement('div');
    meta.className = 'palette-room-meta';
    const fixCount = r.fixtures ? Object.keys(r.fixtures).length : 0;
    const itCount = r.items ? r.items.length : 0;
    const exitCount = Array.isArray(r.exits) ? r.exits.length : (r.exits ? Object.keys(r.exits).length : 0);
    meta.innerHTML = `ID: <span style="color:var(--bright)">${r.name}</span> &bull; ${fixCount} Fix &bull; ${itCount} Items &bull; ${exitCount} Exits`;
    card.appendChild(meta);

    container.appendChild(card);
  });
}

function promptCreateRoom(data) {
  const name = prompt('Enter unique internal room ID (e.g., library_hall, secret_vault):');
  if (!name || !name.trim()) return;
  const cleanId = name.trim().toLowerCase().replace(/[^a-z0-9_]/g, '_');

  if ((data.rooms || []).some(r => r.name === cleanId)) {
    alert(`Room ID "${cleanId}" already exists!`);
    return;
  }

  const displayName = prompt('Enter room display name (e.g., Grand Library Hall):', cleanId.replace(/_/g, ' '));

  const newRoom = {
    name: cleanId,
    display_name: (displayName && displayName.trim()) || cleanId,
    base_description: `You are in ${displayName || cleanId}.`,
    fixtures: {},
    items: [],
    exits: [],
    locked_exits: [],
    trailing_description: ''
  };

  if (!Array.isArray(data.rooms)) data.rooms = [];
  data.rooms.push(newRoom);

  onDataModified('create_new_room');
  buildMapView(data);
  if (window.State) window.State.showToast(`CREATED ROOM "${cleanId}"`);
  openRoomModal(cleanId);
}

function onDataModified(tag) {
  const State = window.State;
  if (!State) return;
  State.markChanged(tag);
  if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
  if (window.dumpYaml) State.rawYamlString = window.dumpYaml(State.yamlData);
  const rawTa = document.getElementById('raw-yaml-textarea');
  if (rawTa) rawTa.value = State.rawYamlString;
  if (window.runValidation) window.runValidation();
  State.triggerAutosave();
  State.updateGlobalStats();
}

function buildRoomList(data) {
  const container = document.getElementById('room-list-section');
  if (!container) return;
  container.innerHTML = '<div class="section-title">DETAILED ROOM DIRECTORY</div>';

  const positions = buildRoomPositions(data);
  const grid = document.createElement('div');
  grid.className = 'rooms-grid';

  (data.rooms || []).forEach(room => {
    const evInfo   = getRoomEvents(room.name, data);
    const hasEvent = evInfo.triggers.length > 0 || evInfo.affected.length > 0;
    const entry    = document.createElement('div');
    entry.className = 'room-entry' + (hasEvent ? ' has-event' : '');
    entry.style.cursor = 'pointer';
    entry.addEventListener('click', () => openRoomModal(room.name));

    const rSearch = [room.name, room.display_name || ''];
    if (room.items) rSearch.push(...room.items);
    if (room.fixtures) rSearch.push(...Object.keys(room.fixtures));
    evInfo.triggers.forEach(ev => rSearch.push(ev.id || ev.name || ''));
    entry.dataset.search = rSearch.join(' ').toLowerCase();

    const nameEl = document.createElement('div');
    nameEl.className = 'room-entry-name';
    nameEl.textContent = room.display_name ? `${room.display_name} (${room.name})` : room.name;
    entry.appendChild(nameEl);

    const meta = document.createElement('div');
    meta.className = 'room-entry-meta';
    const pos  = positions[room.name];
    if (pos) {
      meta.innerHTML += `<span class="rloc">F:${pos.floor} R:${pos.row} C:${pos.col}</span><br>`;
    } else {
      meta.innerHTML += `<span style="color:var(--red);">Unassigned on Floor Grid</span><br>`;
    }
    if (room.fixtures) {
      meta.innerHTML += `<span style="color:var(--accent)">Fixtures: ${Object.keys(room.fixtures).join(', ') || 'none'}</span><br>`;
    }
    if (room.items && room.items.length > 0) {
      meta.innerHTML += `<span style="color:var(--blue)">Items: ${room.items.join(', ')}</span><br>`;
    }

    entry.appendChild(meta);
    grid.appendChild(entry);
  });

  container.appendChild(grid);
}

function buildEventFlow(data) {
  const container = document.getElementById('event-flow-section');
  if (!container) return;
  container.innerHTML = '<div class="section-title">EVENT FLOW</div>';

  (data.events || []).forEach(ev => {
    const eid = ev.id || ev.name || 'event';
    const row = document.createElement('div');
    row.className = 'event-row';
    const block = document.createElement('div');
    block.className = 'event-block';

    const idEl = document.createElement('div');
    idEl.className = 'event-id';
    idEl.textContent = eid;
    block.appendChild(idEl);

    const detail = document.createElement('div');
    detail.className = 'event-detail';
    const trig = ev.trigger || {};
    detail.innerHTML = `Trigger: <span class="ev-room">${trig.action || trig.type || 'action'}</span> on <span class="ev-item">${trig.target || 'target'}</span>`;
    block.appendChild(detail);
    row.appendChild(block);

    const arrow = document.createElement('div');
    arrow.className = 'arrow';
    arrow.innerHTML = '&#8594;';
    row.appendChild(arrow);

    const res = ev.result || {};
    const eff = document.createElement('div');
    eff.className = 'effect-block';
    eff.innerHTML = '<div class="effect-label">EFFECTS</div>';

    (res.set_fixture_state || []).forEach(s => {
      eff.innerHTML += `<div class="effect-line"><span class="ek">FIXTURE</span><span class="ev g">${s.room}.${s.fixture} &rarr; ${s.state}</span></div>`;
    });
    (res.set_state || []).forEach(s => {
      eff.innerHTML += `<div class="effect-line"><span class="ek">STATE</span><span class="ev a">${s.room} &rarr; ${s.state}</span></div>`;
    });
    (res.open_exit || []).forEach(x => {
      const dest = x.destination ? ` (F:${x.destination.floor} R:${x.destination.y} C:${x.destination.x})` : '';
      eff.innerHTML += `<div class="effect-line"><span class="ek">EXIT</span><span class="ev g">${x.room} &rarr; +${x.direction}${dest}</span></div>`;
    });
    if (res.add_item) {
      const it = typeof res.add_item === 'string' ? res.add_item : res.add_item.item;
      eff.innerHTML += `<div class="effect-line"><span class="ek">ADD</span><span class="ev g">${it}</span></div>`;
    }
    row.appendChild(eff);
    container.appendChild(row);
  });
}

function buildItemList(data) {
  const container = document.getElementById('item-list-section');
  if (!container) return;
  container.innerHTML = '<div class="section-title">ITEM LIST</div>';

  const startInv = (data.player && data.player.starting_inventory) || [];
  const roomsByItem = {};
  (data.rooms || []).forEach(room => {
    (room.items || []).forEach(name => {
      if (!roomsByItem[name]) roomsByItem[name] = [];
      roomsByItem[name].push(room.name);
    });
  });

  const grid = document.createElement('div');
  grid.className = 'items-grid';

  Object.keys(data.items || {}).forEach(name => {
    const cls   = classifyItem(name, data);
    const entry = document.createElement('div');
    entry.className = 'item-entry';
    const loc  = startInv.includes(name) ? 'START INVENTORY'
               : roomsByItem[name]       ? roomsByItem[name].join(', ')
               : 'event drop';
    entry.dataset.search = (name + ' ' + cls + ' ' + loc).toLowerCase();

    const nameEl = document.createElement('div');
    nameEl.className = 'item-entry-name';
    nameEl.textContent = name;
    entry.appendChild(nameEl);

    const meta = document.createElement('div');
    meta.className = 'item-entry-meta';
    meta.innerHTML = `<span class="meta-loc">${loc}</span><br><span class="meta-role">${cls}</span>`;
    entry.appendChild(meta);
    grid.appendChild(entry);
  });
  container.appendChild(grid);
}

function onMapSearchChange(val) {
  const State = window.State;
  if (!State) return;
  State.mapSearchQuery = (val || '').trim().toLowerCase();
  const clr = document.getElementById('map-search-clear');
  if (clr) clr.style.display = State.mapSearchQuery ? 'inline' : 'none';

  const cells = document.querySelectorAll('.placed-room-tile');
  const rooms = document.querySelectorAll('.room-entry');
  const items = document.querySelectorAll('.item-entry');

  if (!State.mapSearchQuery) {
    cells.forEach(c => c.style.opacity = '1');
    rooms.forEach(r => r.classList.remove('search-dim', 'search-match'));
    items.forEach(i => i.classList.remove('search-dim', 'search-match'));
    return;
  }

  cells.forEach(c => {
    const text = c.textContent.toLowerCase();
    const match = text.includes(State.mapSearchQuery);
    c.style.opacity = match ? '1' : '0.25';
  });
  rooms.forEach(r => {
    const match = (r.dataset.search || '').includes(State.mapSearchQuery);
    r.classList.toggle('search-match', match);
    r.classList.toggle('search-dim', !match);
  });
  items.forEach(i => {
    const match = (i.dataset.search || '').includes(State.mapSearchQuery);
    i.classList.toggle('search-match', match);
    i.classList.toggle('search-dim', !match);
  });
}

function clearMapSearch() {
  const inp = document.getElementById('map-search');
  if (inp) inp.value = '';
  onMapSearchChange('');
}

window.classifyItem = classifyItem;
window.getRoomEvents = getRoomEvents;
window.buildRoomPositions = buildRoomPositions;
window.buildMapView = buildMapView;
window.onMapSearchChange = onMapSearchChange;
window.clearMapSearch = clearMapSearch;
window.setPlayerStartLocation = setPlayerStartLocation;
window.promptCreateRoom = promptCreateRoom;

/**
 * Dialog & Script View: Modular Room Card Builder, Fixture Prioritization, and Script Entries
 */

function extractDialogEntries(data) {
  const list = [];
  let id = 0;

  function add(section, pathArr, type, value, setter) {
    if (value === undefined || value === null) return;
    const strVal = String(value);
    list.push({
      id: id++,
      section,
      path: pathArr,
      type,
      value: strVal,
      setter,
      searchStr: (pathArr.join(' ') + ' ' + strVal).toLowerCase()
    });
  }

  // INTRO
  if (data.intro) {
    add('intro', ['intro', 'title'],        'text', data.intro.title,        v => { data.intro.title = v; });
    add('intro', ['intro', 'text'],         'text', data.intro.text,         v => { data.intro.text = v; });
    add('intro', ['intro', 'instructions'], 'text', data.intro.instructions, v => { data.intro.instructions = v; });
  }
  if (data.win_screen) {
    add('intro', ['win_screen', 'title'], 'text', data.win_screen.title, v => { data.win_screen.title = v; });
    add('intro', ['win_screen', 'text'],  'text', data.win_screen.text,  v => { data.win_screen.text = v; });
  }

  // ITEMS
  Object.entries(data.items || {}).forEach(([itemName, itemData]) => {
    Object.entries(itemData.states || {}).forEach(([stateName, stateData]) => {
      if (stateData.description !== undefined)
        add('items', ['items', itemName, 'states', stateName, 'description'], 'desc',
            stateData.description, v => { stateData.description = v; });
      if (stateData.use !== undefined)
        add('items', ['items', itemName, 'states', stateName, 'use'], 'use',
            stateData.use, v => { stateData.use = v; });
    });
  });

  // EVENTS
  (data.events || []).forEach(ev => {
    const eid = ev.id || ev.name || 'event';
    if (ev.result && ev.result.message !== undefined)
      add('events', ['events', eid, 'result', 'message'], 'msg',
          ev.result.message, v => { ev.result.message = v; });
  });

  return list;
}

function buildModularRoomCard(room, isInsideModal, onUpdate) {
  if (!room.fixtures || typeof room.fixtures !== 'object') room.fixtures = {};
  if (typeof room.base_description !== 'string') room.base_description = '';
  if (typeof room.trailing_description !== 'string') room.trailing_description = '';

  const card = document.createElement('div');
  card.className = 'modular-room-card';
  card.dataset.room = room.name;

  function renderCardContents() {
    card.innerHTML = '';

    const header = document.createElement('div');
    header.className = 'modular-room-header';
    header.innerHTML = `
      <div>
        <span class="modular-room-title">${room.display_name || room.name}</span>
        <span class="modular-room-id">[ID: ${room.name}]</span>
      </div>
      <div style="display:flex; gap:6px; align-items:center;">
        <span class="entry-type type-desc">MODULAR FORMAT</span>
      </div>
    `;
    card.appendChild(header);

    // 1. Base Description
    const baseGroup = document.createElement('div');
    baseGroup.className = 'modular-field-group';
    baseGroup.innerHTML = `<label class="modular-field-label">1. BASE DESCRIPTION (LOOK OPENING ANCHOR)</label>`;
    const baseTa = document.createElement('textarea');
    baseTa.className = 'modular-textarea';
    baseTa.value = room.base_description || '';
    baseTa.placeholder = 'Opening room description prose (always shown first)...';
    baseTa.addEventListener('input', () => {
      room.base_description = baseTa.value;
      updatePreview();
      onUpdate();
    });
    baseGroup.appendChild(baseTa);
    card.appendChild(baseGroup);

    // 2. Fixtures
    const fixBox = document.createElement('div');
    fixBox.className = 'fixtures-box';
    const fixHead = document.createElement('div');
    fixHead.className = 'fixtures-header';
    fixHead.innerHTML = `
      <span class="fixtures-title">2. FIXTURES (INTERACTIVE OBJECTS & PRIORITY ORDER)</span>
      <button type="button" class="btn btn-dim" style="padding:3px 8px; font-size:10px;">+ ADD FIXTURE</button>
    `;
    fixHead.querySelector('button').addEventListener('click', () => {
      const fixId = prompt('Enter new fixture ID (e.g. power_switch, console, safe):');
      if (!fixId || !fixId.trim()) return;
      const cleanId = fixId.trim().toLowerCase().replace(/\s+/g, '_');
      if (room.fixtures[cleanId]) {
        alert('Fixture "' + cleanId + '" already exists in this room.');
        return;
      }
      room.fixtures[cleanId] = {
        priority: 10,
        state: 'default',
        states: { default: 'A ' + cleanId.replace(/_/g, ' ') + ' is installed here.' },
        examine: { default: 'It appears to be in working condition.' }
      };
      renderCardContents();
      onUpdate();
    });
    fixBox.appendChild(fixHead);

    const fixList = document.createElement('div');
    const sortedFixtures = Object.entries(room.fixtures).sort(([, a], [, b]) => (a.priority || 10) - (b.priority || 10));

    if (sortedFixtures.length === 0) {
      const emptyFix = document.createElement('div');
      emptyFix.style.color = 'var(--dim)';
      emptyFix.style.fontSize = '11px';
      emptyFix.style.fontFamily = 'var(--mono)';
      emptyFix.style.padding = '8px 0';
      emptyFix.textContent = 'No fixtures configured for this room.';
      fixList.appendChild(emptyFix);
    } else {
      sortedFixtures.forEach(([fixKey, fix]) => {
        const itemCard = document.createElement('div');
        itemCard.className = 'fixture-item-card';

        const topRow = document.createElement('div');
        topRow.className = 'fixture-row-top';
        topRow.innerHTML = `
          <span style="font-family:var(--mono); font-weight:bold; color:var(--bright); font-size:12px;">${fixKey}</span>
          <label style="font-family:var(--mono); font-size:10px; color:var(--dim);">Priority:
            <input type="number" class="modular-input" style="width:55px;" value="${fix.priority !== undefined ? fix.priority : 10}" min="1" max="999">
          </label>
          <label style="font-family:var(--mono); font-size:10px; color:var(--dim);">Initial State:
            <input type="text" class="modular-input" style="width:90px;" value="${fix.state || 'default'}">
          </label>
          <button type="button" class="btn btn-danger" style="padding:2px 8px; font-size:10px; margin-left:auto;">REMOVE</button>
        `;

        const prioInp = topRow.querySelectorAll('input')[0];
        prioInp.addEventListener('change', () => {
          fix.priority = parseInt(prioInp.value, 10) || 10;
          renderCardContents();
          onUpdate();
        });

        const stateInp = topRow.querySelectorAll('input')[1];
        stateInp.addEventListener('input', () => {
          fix.state = stateInp.value.trim() || 'default';
          updatePreview();
          onUpdate();
        });

        topRow.querySelector('.btn-danger').addEventListener('click', () => {
          if (confirm('Delete fixture "' + fixKey + '"?')) {
            delete room.fixtures[fixKey];
            renderCardContents();
            onUpdate();
          }
        });
        itemCard.appendChild(topRow);

        // States
        const stContainer = document.createElement('div');
        stContainer.style.marginBottom = '8px';
        stContainer.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-family:var(--mono); font-size:10px; color:var(--dim);">LOOK STATE PROSE (Empty string "" hides fixture from look):</span>
            <button type="button" class="btn btn-dim" style="padding:2px 6px; font-size:9px;">+ Add State</button>
          </div>
        `;
        stContainer.querySelector('button').addEventListener('click', () => {
          const stName = prompt('State name (e.g. energized, broken, unlocked):');
          if (!stName || !stName.trim()) return;
          if (!fix.states) fix.states = {};
          fix.states[stName.trim()] = '';
          renderCardContents();
          onUpdate();
        });

        const stList = document.createElement('div');
        stList.className = 'fixture-state-list';
        Object.entries(fix.states || {}).forEach(([stName, stProse]) => {
          const sRow = document.createElement('div');
          sRow.className = 'fixture-sub-row';
          sRow.innerHTML = `
            <span class="state-tag">${stName}</span>
            <textarea class="modular-textarea" style="min-height:45px; flex:1;" placeholder='State prose (leave empty "" to hide until revealed)...'>${stProse || ''}</textarea>
            <button type="button" class="btn btn-dim" style="padding:3px 6px; font-size:10px;" title="Delete state">✕</button>
          `;
          const ta = sRow.querySelector('textarea');
          ta.addEventListener('input', () => {
            fix.states[stName] = ta.value;
            updatePreview();
            onUpdate();
          });
          sRow.querySelector('button').addEventListener('click', () => {
            delete fix.states[stName];
            renderCardContents();
            onUpdate();
          });
          stList.appendChild(sRow);
        });
        stContainer.appendChild(stList);
        itemCard.appendChild(stContainer);

        // Examine
        const exContainer = document.createElement('div');
        exContainer.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-family:var(--mono); font-size:10px; color:var(--dim);">EXAMINE PROSE (Optional targeted examination):</span>
            <button type="button" class="btn btn-dim" style="padding:2px 6px; font-size:9px;">+ Add Examine</button>
          </div>
        `;
        exContainer.querySelector('button').addEventListener('click', () => {
          const stName = prompt('Examine state key (e.g. default, energized):');
          if (!stName || !stName.trim()) return;
          if (!fix.examine) fix.examine = {};
          fix.examine[stName.trim()] = '';
          renderCardContents();
          onUpdate();
        });

        const exList = document.createElement('div');
        exList.className = 'fixture-examine-list';
        Object.entries(fix.examine || {}).forEach(([exKey, exProse]) => {
          const eRow = document.createElement('div');
          eRow.className = 'fixture-sub-row';
          eRow.innerHTML = `
            <span class="state-tag" style="background:var(--blue-dim); color:var(--blue);">examine:${exKey}</span>
            <textarea class="modular-textarea" style="min-height:45px; flex:1;" placeholder="Examine description...">${exProse || ''}</textarea>
            <button type="button" class="btn btn-dim" style="padding:3px 6px; font-size:10px;" title="Delete examine">✕</button>
          `;
          const ta = eRow.querySelector('textarea');
          ta.addEventListener('input', () => {
            if (!fix.examine) fix.examine = {};
            fix.examine[exKey] = ta.value;
            onUpdate();
          });
          eRow.querySelector('button').addEventListener('click', () => {
            delete fix.examine[exKey];
            renderCardContents();
            onUpdate();
          });
          exList.appendChild(eRow);
        });
        exContainer.appendChild(exList);
        itemCard.appendChild(exContainer);

        fixList.appendChild(itemCard);
      });
    }
    fixBox.appendChild(fixList);
    card.appendChild(fixBox);

    // 3. Exits & Portals (Movement Permissions & Warp Anchors)
    const exitsBox = document.createElement('div');
    exitsBox.className = 'fixtures-box';
    exitsBox.style.borderColor = 'var(--border-dim)';

    const exitsHead = document.createElement('div');
    exitsHead.className = 'fixtures-header';
    exitsHead.innerHTML = `
      <span class="fixtures-title">3. EXITS & PORTALS (PERMITTED MOVEMENT)</span>
      <div style="display:flex; gap:6px;">
        <button type="button" class="btn btn-dim btn-add-custom-exit" style="padding:2px 8px; font-size:10px;">+ CUSTOM EXIT</button>
        <button type="button" class="btn btn-dim btn-add-portal" style="padding:2px 8px; font-size:10px; color:var(--accent); border-color:var(--accent);">+ ADD PORTAL</button>
      </div>
    `;
    exitsBox.appendChild(exitsHead);

    // Normalize room.exits and room.locked_exits
    if (!Array.isArray(room.exits)) {
      if (typeof room.exits === 'object' && room.exits !== null) {
        room.exits = Object.keys(room.exits);
      } else if (typeof room.exits === 'string') {
        room.exits = [room.exits.replace(/^[-–—\s]+/, '').trim()].filter(Boolean);
      } else {
        room.exits = [];
      }
    }
    if (!Array.isArray(room.locked_exits)) {
      if (typeof room.locked_exits === 'string') {
        room.locked_exits = [room.locked_exits.replace(/^[-–—\s]+/, '').trim()].filter(Boolean);
      } else {
        room.locked_exits = [];
      }
    }
    if (!room.exit_destinations || typeof room.exit_destinations !== 'object') {
      room.exit_destinations = {};
    }

    const exitsBody = document.createElement('div');
    exitsBody.style.display = 'flex';
    exitsBody.style.flexDirection = 'column';
    exitsBody.style.gap = '10px';
    exitsBody.style.marginTop = '8px';

    // Standard Directions Row
    const standardDirs = ['north', 'south', 'east', 'west', 'up', 'down'];
    const stdRow = document.createElement('div');
    stdRow.style.display = 'flex';
    stdRow.style.flexWrap = 'wrap';
    stdRow.style.gap = '6px';
    stdRow.style.alignItems = 'center';

    const stdLabel = document.createElement('span');
    stdLabel.style.fontFamily = 'var(--mono)';
    stdLabel.style.fontSize = '10px';
    stdLabel.style.color = 'var(--dim)';
    stdLabel.style.marginRight = '6px';
    stdLabel.textContent = 'STANDARD:';
    stdRow.appendChild(stdLabel);

    standardDirs.forEach(dir => {
      const isActive = room.exits.includes(dir);
      const isLocked = room.locked_exits.includes(dir);

      const pill = document.createElement('div');
      pill.style.display = 'inline-flex';
      pill.style.alignItems = 'center';
      pill.style.gap = '4px';
      pill.style.padding = '3px 8px';
      pill.style.borderRadius = '4px';
      pill.style.fontFamily = 'var(--mono)';
      pill.style.fontSize = '11px';
      pill.style.cursor = 'pointer';
      pill.style.userSelect = 'none';
      pill.style.border = isActive ? '1px solid var(--accent)' : '1px solid var(--border-dim)';
      pill.style.background = isActive ? 'rgba(74, 240, 192, 0.12)' : 'var(--panel)';
      pill.style.color = isActive ? 'var(--accent)' : 'var(--dim)';

      const dirBtn = document.createElement('span');
      dirBtn.textContent = (isActive ? '✓ ' : '+ ') + dir.toUpperCase();
      dirBtn.title = isActive ? `Remove ${dir} exit` : `Add ${dir} exit`;
      dirBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (isActive) {
          room.exits = room.exits.filter(x => x !== dir);
          room.locked_exits = room.locked_exits.filter(x => x !== dir);
        } else {
          room.exits.push(dir);
        }
        renderCardContents();
        onUpdate();
      });
      pill.appendChild(dirBtn);

      if (isActive) {
        const lockBtn = document.createElement('span');
        lockBtn.style.cursor = 'pointer';
        lockBtn.style.fontSize = '11px';
        lockBtn.style.marginLeft = '4px';
        lockBtn.textContent = isLocked ? '🔒' : '🔓';
        lockBtn.title = isLocked ? 'Locked exit (click to unlock)' : 'Open exit (click to lock)';
        lockBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          if (isLocked) {
            room.locked_exits = room.locked_exits.filter(x => x !== dir);
          } else {
            room.locked_exits.push(dir);
          }
          renderCardContents();
          onUpdate();
        });
        pill.appendChild(lockBtn);
      }

      stdRow.appendChild(pill);
    });
    exitsBody.appendChild(stdRow);

    // Custom non-standard exits
    const customDirs = room.exits.filter(x => !standardDirs.includes(x));
    if (customDirs.length > 0) {
      const custRow = document.createElement('div');
      custRow.style.display = 'flex';
      custRow.style.flexWrap = 'wrap';
      custRow.style.gap = '6px';
      custRow.style.alignItems = 'center';

      const custLabel = document.createElement('span');
      custLabel.style.fontFamily = 'var(--mono)';
      custLabel.style.fontSize = '10px';
      custLabel.style.color = 'var(--blue)';
      custLabel.style.marginRight = '6px';
      custLabel.textContent = 'CUSTOM:';
      custRow.appendChild(custLabel);

      customDirs.forEach(dir => {
        const isLocked = room.locked_exits.includes(dir);
        const pill = document.createElement('div');
        pill.style.display = 'inline-flex';
        pill.style.alignItems = 'center';
        pill.style.gap = '4px';
        pill.style.padding = '3px 8px';
        pill.style.borderRadius = '4px';
        pill.style.fontFamily = 'var(--mono)';
        pill.style.fontSize = '11px';
        pill.style.border = '1px solid var(--blue)';
        pill.style.background = 'rgba(74, 158, 255, 0.12)';
        pill.style.color = 'var(--blue)';

        const nameSpan = document.createElement('span');
        nameSpan.textContent = dir.toUpperCase();
        pill.appendChild(nameSpan);

        const lockBtn = document.createElement('span');
        lockBtn.style.cursor = 'pointer';
        lockBtn.style.fontSize = '11px';
        lockBtn.textContent = isLocked ? '🔒' : '🔓';
        lockBtn.title = isLocked ? 'Locked exit' : 'Unlocked exit';
        lockBtn.addEventListener('click', () => {
          if (isLocked) {
            room.locked_exits = room.locked_exits.filter(x => x !== dir);
          } else {
            room.locked_exits.push(dir);
          }
          renderCardContents();
          onUpdate();
        });
        pill.appendChild(lockBtn);

        const delBtn = document.createElement('span');
        delBtn.style.cursor = 'pointer';
        delBtn.style.marginLeft = '4px';
        delBtn.style.fontSize = '10px';
        delBtn.style.color = 'var(--dim)';
        delBtn.textContent = '✕';
        delBtn.title = `Delete custom exit ${dir}`;
        delBtn.addEventListener('click', () => {
          room.exits = room.exits.filter(x => x !== dir);
          room.locked_exits = room.locked_exits.filter(x => x !== dir);
          if (room.exit_destinations && room.exit_destinations[dir]) {
            delete room.exit_destinations[dir];
          }
          renderCardContents();
          onUpdate();
        });
        pill.appendChild(delBtn);

        custRow.appendChild(pill);
      });
      exitsBody.appendChild(custRow);
    }

    // Portal / Custom Warp Destinations Section
    const portalEntries = Object.entries(room.exit_destinations || {});
    if (portalEntries.length > 0) {
      const portalBox = document.createElement('div');
      portalBox.style.background = 'rgba(0, 0, 0, 0.25)';
      portalBox.style.border = '1px solid var(--border-dim)';
      portalBox.style.borderRadius = '6px';
      portalBox.style.padding = '8px 10px';
      portalBox.style.marginTop = '4px';

      const portalTitle = document.createElement('div');
      portalTitle.style.fontFamily = 'var(--mono)';
      portalTitle.style.fontSize = '10px';
      portalTitle.style.color = 'var(--accent)';
      portalTitle.style.marginBottom = '6px';
      portalTitle.textContent = 'PORTALS & WARP DESTINATIONS (exit_destinations):';
      portalBox.appendChild(portalTitle);

      const allRooms = (window.State && window.State.yamlData && window.State.yamlData.rooms) || [];
      const positions = (window.buildRoomPositions && window.State && window.State.yamlData)
        ? window.buildRoomPositions(window.State.yamlData)
        : {};

      portalEntries.forEach(([cmd, dest]) => {
        const pRow = document.createElement('div');
        pRow.style.display = 'flex';
        pRow.style.alignItems = 'center';
        pRow.style.gap = '8px';
        pRow.style.marginBottom = '6px';
        pRow.style.fontFamily = 'var(--mono)';
        pRow.style.fontSize = '11px';

        pRow.innerHTML = `
          <span style="color:var(--accent); font-weight:bold;">🌀 ${cmd}</span>
          <span style="color:var(--dim);">&rarr;</span>
          <span style="color:var(--bright);">Floor ${dest.floor ?? 0}, X: ${dest.x ?? 0}, Y: ${dest.y ?? 0}</span>
        `;

        const roomMatch = allRooms.find(r => {
          const p = positions[r.name];
          return p && p.floor === dest.floor && p.col === dest.x && p.row === dest.y;
        });
        if (roomMatch) {
          const rTag = document.createElement('span');
          rTag.style.color = 'var(--blue)';
          rTag.textContent = `(${roomMatch.display_name || roomMatch.name})`;
          pRow.appendChild(rTag);
        }

        const delPBtn = document.createElement('button');
        delPBtn.type = 'button';
        delPBtn.className = 'btn btn-dim';
        delPBtn.style.padding = '2px 6px';
        delPBtn.style.fontSize = '9px';
        delPBtn.style.marginLeft = 'auto';
        delPBtn.textContent = '✕ Remove';
        delPBtn.addEventListener('click', () => {
          delete room.exit_destinations[cmd];
          renderCardContents();
          onUpdate();
        });
        pRow.appendChild(delPBtn);

        portalBox.appendChild(pRow);
      });
      exitsBody.appendChild(portalBox);
    }

    exitsBox.appendChild(exitsBody);

    // Event handlers for + CUSTOM EXIT and + ADD PORTAL buttons
    exitsHead.querySelector('.btn-add-custom-exit').addEventListener('click', () => {
      const customDir = prompt('Enter custom exit name (e.g. portal, ladder, tunnel, gate):');
      if (!customDir || !customDir.trim()) return;
      const cleanDir = customDir.trim().toLowerCase().replace(/\s+/g, '_');
      if (!room.exits.includes(cleanDir)) {
        room.exits.push(cleanDir);
      }
      renderCardContents();
      onUpdate();
    });

    exitsHead.querySelector('.btn-add-portal').addEventListener('click', () => {
      const cmd = prompt('Enter portal command/exit name (e.g. portal, warp, ladder, secret_door):', 'portal');
      if (!cmd || !cmd.trim()) return;
      const cleanCmd = cmd.trim().toLowerCase().replace(/\s+/g, '_');

      const allRooms = (window.State && window.State.yamlData && window.State.yamlData.rooms) || [];
      const positions = (window.buildRoomPositions && window.State && window.State.yamlData)
        ? window.buildRoomPositions(window.State.yamlData)
        : {};

      const roomOptions = allRooms
        .map(r => r.name)
        .filter(rn => rn !== room.name);

      const targetRoom = prompt(
        `Destination Room Name for "${cleanCmd}":\nAvailable: ${roomOptions.join(', ')}`,
        roomOptions[0] || ''
      );
      if (!targetRoom || !targetRoom.trim()) return;
      const cleanTarget = targetRoom.trim().toLowerCase();

      const pos = positions[cleanTarget];
      let destObj = { floor: 0, x: 0, y: 0 };
      if (pos) {
        destObj = { floor: pos.floor, x: pos.col, y: pos.row };
      } else {
        const fl = parseInt(prompt('Target Floor number (e.g. 0):', '0'), 10) || 0;
        const tx = parseInt(prompt('Target X (column 0-4):', '2'), 10) || 0;
        const ty = parseInt(prompt('Target Y (row 0-4):', '2'), 10) || 0;
        destObj = { floor: fl, x: tx, y: ty };
      }

      if (!room.exits.includes(cleanCmd)) {
        room.exits.push(cleanCmd);
      }
      if (!room.exit_destinations) room.exit_destinations = {};
      room.exit_destinations[cleanCmd] = destObj;

      renderCardContents();
      onUpdate();
    });

    card.appendChild(exitsBox);

    // 4. Trailing Description
    const trailGroup = document.createElement('div');
    trailGroup.className = 'modular-field-group';
    trailGroup.innerHTML = `<label class="modular-field-label">4. TRAILING DESCRIPTION (LOOK CLOSING ANCHOR / EXITS PROSE)</label>`;
    const trailTa = document.createElement('textarea');
    trailTa.className = 'modular-textarea';
    trailTa.value = room.trailing_description || '';
    trailTa.placeholder = 'Closing room description prose (always shown last)...';
    trailTa.addEventListener('input', () => {
      room.trailing_description = trailTa.value;
      updatePreview();
      onUpdate();
    });
    trailGroup.appendChild(trailTa);
    card.appendChild(trailGroup);

    // 5. Live Assembled Preview Box
    const prevBox = document.createElement('div');
    prevBox.className = 'preview-box';
    prevBox.innerHTML = `
      <div class="preview-label">
        <span>👁</span>
        <span>LIVE ASSEMBLED ROOM LOOK PREVIEW (ENGINE OUTPUT)</span>
      </div>
      <div class="preview-content"></div>
    `;
    card.appendChild(prevBox);

    function updatePreview() {
      const prevEl = card.querySelector('.preview-content');
      if (prevEl) {
        prevEl.textContent = assembleRoomDescription(room) || '(empty room description)';
      }
    }
    updatePreview();
  }

  renderCardContents();
  return card;
}

function renderDialogList() {
  const State = window.State;
  const container = document.getElementById('dialog-entries');
  if (!container || !State) return;
  container.innerHTML = '';
  const q = State.currentSearch.trim().toLowerCase();

  // If section is ROOMS
  if (State.currentSection === 'rooms') {
    renderModularRoomsSection(container, q);
    State.updateGlobalStats();
    return;
  }

  const labels = { intro: 'Intro & Win Screen', items: 'Items', rooms: 'Rooms (Modular Architecture)', events: 'Events' };
  let lastSection = null;

  const filtered = State.dialogEntries.filter(e => {
    const matchSection = State.currentSection === 'all' || e.section === State.currentSection;
    const matchSearch   = !q || e.searchStr.includes(q);
    return matchSection && matchSearch;
  });

  if (State.currentSection === 'all') {
    // 1. Intro
    const introEntries = filtered.filter(e => e.section === 'intro');
    if (introEntries.length > 0) {
      container.appendChild(buildSectionHeader('intro', labels.intro));
      introEntries.forEach(entry => container.appendChild(buildDialogEntryEl(entry)));
    }

    // 2. Items
    const itemEntries = filtered.filter(e => e.section === 'items');
    if (itemEntries.length > 0) {
      container.appendChild(buildSectionHeader('items', labels.items));
      itemEntries.forEach(entry => container.appendChild(buildDialogEntryEl(entry)));
    }

    // 3. Rooms
    container.appendChild(buildSectionHeader('rooms', labels.rooms));
    renderModularRoomsSection(container, q);

    // 4. Events
    const eventEntries = filtered.filter(e => e.section === 'events');
    if (eventEntries.length > 0) {
      container.appendChild(buildSectionHeader('events', labels.events));
      eventEntries.forEach(entry => container.appendChild(buildDialogEntryEl(entry)));
    }

    State.updateGlobalStats();
    return;
  }

  filtered.forEach(entry => {
    if (entry.section !== lastSection) {
      container.appendChild(buildSectionHeader(entry.section, labels[entry.section]));
      lastSection = entry.section;
    }
    container.appendChild(buildDialogEntryEl(entry));
  });

  State.updateGlobalStats();
}

function buildSectionHeader(secKey, labelText) {
  const hdr = document.createElement('div');
  hdr.className = 'section-header-dialog ' + secKey;
  hdr.textContent = labelText;
  return hdr;
}

function renderModularRoomsSection(container, searchFilter) {
  const rooms = (State.yamlData && State.yamlData.rooms) || [];
  if (rooms.length === 0) {
    const emptyMsg = document.createElement('div');
    emptyMsg.style.padding = '20px';
    emptyMsg.style.color = 'var(--dim)';
    emptyMsg.style.fontFamily = 'var(--mono)';
    emptyMsg.textContent = 'No rooms defined in this game file.';
    container.appendChild(emptyMsg);
    return;
  }

  rooms.forEach(room => {
    if (searchFilter) {
      const fullText = [
        room.name,
        room.display_name || '',
        room.base_description || '',
        room.trailing_description || '',
        JSON.stringify(room.fixtures || {})
      ].join(' ').toLowerCase();
      if (!fullText.includes(searchFilter)) return;
    }

    const roomCard = buildModularRoomCard(room, false, () => {
      State.rawYamlString = dumpYaml(State.yamlData);
      const rawTa = document.getElementById('raw-yaml-textarea');
      if (rawTa && !State.isRawYamlDirty) rawTa.value = State.rawYamlString;
      State.markChanged('room_' + room.name);
      roomCard.classList.add('changed');
    });

    container.appendChild(roomCard);
  });
}

function buildDialogEntryEl(entry) {
  const wrap = document.createElement('div');
  wrap.className = 'dialog-entry' + (State.changedIds.has(entry.id) ? ' changed' : '');
  wrap.dataset.id = entry.id;

  const hdr = document.createElement('div');
  hdr.className = 'entry-header';
  const dot = document.createElement('div');
  dot.className = 'changed-dot';
  hdr.appendChild(dot);

  const pathEl = document.createElement('div');
  pathEl.className = 'entry-path';
  entry.path.forEach((seg, i) => {
    if (i > 0) {
      const sep = document.createElement('span');
      sep.className = 'path-sep';
      sep.textContent = '›';
      pathEl.appendChild(sep);
    }
    const s = document.createElement('span');
    s.className = 'path-seg';
    if (i === 1) s.className = 'path-seg key';
    else if (['default', 'energized', 'breached', 'revealed', 'hidden', 'active'].includes(seg)) s.className = 'path-seg state';
    else if (['description', 'use', 'message', 'text', 'title', 'instructions', 'base_description', 'trailing_description'].includes(seg)) s.className = 'path-seg field';
    s.textContent = seg;
    pathEl.appendChild(s);
  });
  hdr.appendChild(pathEl);

  const badge = document.createElement('span');
  badge.className = 'entry-type type-' + entry.type;
  badge.textContent = entry.type.toUpperCase();
  hdr.appendChild(badge);
  wrap.appendChild(hdr);

  const ta = document.createElement('textarea');
  ta.className = 'dialog-textarea';
  ta.value = entry.value;
  ta.style.height = 'auto';
  setTimeout(() => { ta.style.height = Math.max(60, ta.scrollHeight) + 'px'; }, 0);

  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.max(60, ta.scrollHeight) + 'px';
    entry.setter(ta.value);
    entry.value = ta.value;
    entry.searchStr = (entry.path.join(' ') + ' ' + ta.value).toLowerCase();
    State.markChanged(entry.id);
    wrap.classList.add('changed');
  });

  wrap.appendChild(ta);
  return wrap;
}

function filterDialog(section, btn) {
  document.querySelectorAll('#view-dialog .filter-tab').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
  const State = window.State;
  if (State) State.currentSection = section;
  renderDialogList();
}

function onSearchChange(val) {
  const State = window.State;
  if (State) State.currentSearch = val;
  const clr = document.getElementById('search-clear');
  if (clr) clr.style.display = val ? 'inline' : 'none';
  renderDialogList();
}

function clearSearch() {
  const inp = document.getElementById('dialog-search');
  if (inp) inp.value = '';
  onSearchChange('');
}

function openRoomModal(roomName) {
  const State = window.State;
  const room = (State && State.yamlData && State.yamlData.rooms || []).find(r => r.name === roomName);
  if (!room) return;

  const titleEl = document.getElementById('modal-room-title');
  if (titleEl) titleEl.textContent = 'ROOM: ' + roomName.toUpperCase();

  const body = document.getElementById('modal-room-body');
  if (!body) return;
  body.innerHTML = '';

  const meta = document.createElement('div');
  meta.className = 'modal-meta-info';
  const exitsStr = Array.isArray(room.exits) ? room.exits.join(', ') : Object.keys(room.exits || {}).join(', ');
  meta.innerHTML = `
    <strong>Display Name:</strong> ${room.display_name || room.name}<br>
    <strong>Exits:</strong> ${exitsStr || 'none'}<br>
    <strong>Items Present:</strong> ${(room.items && room.items.join(', ')) || 'none'}
  `;
  body.appendChild(meta);

  const modularCard = buildModularRoomCard(room, true, () => {
    if (window.dumpYaml && State) {
      State.rawYamlString = window.dumpYaml(State.yamlData);
      State.markChanged('room_' + room.name);
    }
  });
  body.appendChild(modularCard);

  const modal = document.getElementById('room-modal');
  if (modal) modal.style.display = 'flex';
}

function closeRoomModal() {
  const modal = document.getElementById('room-modal');
  if (modal) modal.style.display = 'none';
  const State = window.State;
  if (State && State.currentMode === 'dialog') renderDialogList();
}

window.extractDialogEntries = extractDialogEntries;
window.buildModularRoomCard = buildModularRoomCard;
window.renderDialogList = renderDialogList;
window.filterDialog = filterDialog;
window.onSearchChange = onSearchChange;
window.clearSearch = clearSearch;
window.openRoomModal = openRoomModal;
window.closeRoomModal = closeRoomModal;


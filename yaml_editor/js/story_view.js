/**
 * Story & Metadata View: Title, Narrative Briefing, Starting Inventory, Spawn Tile, Win Conditions
 */

function renderStoryMetadataView() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const data = State.yamlData;
  const intro = data.intro || (data.intro = { title: '', text: '', instructions: '' });
  data.player = data.player || { starting_inventory: [] };
  data.win_screen = data.win_screen || { title: '', text: '' };
  if (!Array.isArray(data.win_conditions)) data.win_conditions = [];

  const statusTitle = document.getElementById('story-status-title');
  if (statusTitle) statusTitle.textContent = intro.title || '(Untitled Adventure)';

  const statusSpawn = document.getElementById('story-status-spawn');
  let currentStartRoom = '';
  if (Array.isArray(data.floors) && Array.isArray(data.floors[0]) && Array.isArray(data.floors[0][0])) {
    currentStartRoom = data.floors[0][0][0] || '';
  }
  if (statusSpawn) statusSpawn.textContent = `Floor 0 [0,0] (${currentStartRoom || 'void'})`;

  const statusWinCount = document.getElementById('story-status-win-count');
  if (statusWinCount) statusWinCount.textContent = `${data.win_conditions.length} Objectives`;

  const fieldTitle = document.getElementById('story-field-title');
  if (fieldTitle && document.activeElement !== fieldTitle) fieldTitle.value = intro.title || '';

  const fieldIntroText = document.getElementById('story-field-intro-text');
  if (fieldIntroText && document.activeElement !== fieldIntroText) fieldIntroText.value = intro.text || '';
  updateWordCount('story-intro-text-count', intro.text || '');

  const fieldIntroInstructions = document.getElementById('story-field-intro-instructions');
  if (fieldIntroInstructions && document.activeElement !== fieldIntroInstructions) fieldIntroInstructions.value = intro.instructions || '';
  updateWordCount('story-intro-instructions-count', intro.instructions || '');

  const fieldWinTitle = document.getElementById('story-field-win-title');
  if (fieldWinTitle && document.activeElement !== fieldWinTitle) fieldWinTitle.value = data.win_screen.title || '';

  const fieldWinText = document.getElementById('story-field-win-text');
  if (fieldWinText && document.activeElement !== fieldWinText) fieldWinText.value = data.win_screen.text || '';
  updateWordCount('story-win-text-count', data.win_screen.text || '');

  updateStoryPreviews();
  renderStoryStartRoomSelect(currentStartRoom);
  renderStoryStartingInventory();
  renderStoryWinConditions();
  updateStoryDiagnosticsUnderneath();
}

function updateWordCount(elementId, text) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const words = (text || '').trim().split(/\s+/).filter(Boolean).length;
  const chars = (text || '').length;
  el.textContent = `${words} words (${chars} chars)`;
}

function updateStoryPreviews() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const intro = State.yamlData.intro || {};
  const winScreen = State.yamlData.win_screen || {};

  const prevIntroTitle = document.getElementById('story-preview-intro-title');
  if (prevIntroTitle) prevIntroTitle.textContent = intro.title || 'ADVENTURE TITLE';

  const prevIntroText = document.getElementById('story-preview-intro-text');
  if (prevIntroText) prevIntroText.textContent = intro.text || '(No narrative briefing prose specified)';

  const prevIntroInst = document.getElementById('story-preview-intro-instructions');
  if (prevIntroInst) prevIntroInst.textContent = intro.instructions || '(No operational instructions specified)';

  const prevWinTitle = document.getElementById('story-preview-win-title');
  if (prevWinTitle) prevWinTitle.textContent = winScreen.title || 'YOU HAVE ESCAPED';

  const prevWinText = document.getElementById('story-preview-win-text');
  if (prevWinText) prevWinText.textContent = winScreen.text || '(No victory epilogue narrative specified)';
}

function updateStoryFieldSync() {
  const State = window.State;
  if (!State) return;
  if (window.dumpYaml) State.rawYamlString = window.dumpYaml(State.yamlData);
  const rawTa = document.getElementById('raw-yaml-textarea');
  if (rawTa && !State.isRawYamlDirty) rawTa.value = State.rawYamlString;
  State.isRawYamlDirty = false;

  const statusBadge = document.getElementById('yaml-sync-status');
  if (statusBadge) {
    statusBadge.textContent = 'IN SYNC';
    statusBadge.className = 'yaml-status';
  }

  State.markChanged('story_meta');
  updateStoryPreviews();
  if (window.runValidation) window.runValidation();
  updateStoryDiagnosticsUnderneath();

  const statusTitle = document.getElementById('story-status-title');
  if (statusTitle && State.yamlData.intro) statusTitle.textContent = State.yamlData.intro.title || '(Untitled Facility)';
}

function onStoryTitleChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  State.yamlData.intro = State.yamlData.intro || {};
  State.yamlData.intro.title = val;
  updateStoryFieldSync();
}

function onStoryIntroTextChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  State.yamlData.intro = State.yamlData.intro || {};
  State.yamlData.intro.text = val;
  updateWordCount('story-intro-text-count', val);
  updateStoryFieldSync();
}

function onStoryIntroInstructionsChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  State.yamlData.intro = State.yamlData.intro || {};
  State.yamlData.intro.instructions = val;
  updateWordCount('story-intro-instructions-count', val);
  updateStoryFieldSync();
}

function onStoryWinTitleChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  State.yamlData.win_screen = State.yamlData.win_screen || {};
  State.yamlData.win_screen.title = val;
  updateStoryFieldSync();
}

function onStoryWinTextChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  State.yamlData.win_screen = State.yamlData.win_screen || {};
  State.yamlData.win_screen.text = val;
  updateWordCount('story-win-text-count', val);
  updateStoryFieldSync();
}

function renderStoryStartRoomSelect(currentStartRoom) {
  const select = document.getElementById('story-field-start-room');
  if (!select) return;
  const rooms = State.yamlData.rooms || [];
  select.innerHTML = '';
  rooms.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.name;
    opt.textContent = `${r.display_name || r.name} [ID: ${r.name}]`;
    if (r.name === currentStartRoom) opt.selected = true;
    select.appendChild(opt);
  });
  updateStartRoomCard(currentStartRoom);
}

function updateStartRoomCard(roomName) {
  const card = document.getElementById('story-start-room-card');
  if (!card) return;
  const room = (State.yamlData.rooms || []).find(r => r.name === roomName);
  if (!room) {
    card.innerHTML = '<span style="color: var(--red);">⚠ Selected starting room not found!</span>';
    return;
  }
  const desc = assembleRoomDescription(room) || room.base_description || '(empty)';
  const initialItems = (room.items || []).join(', ') || 'none';
  const exits = Array.isArray(room.exits) ? room.exits.join(', ') : Object.keys(room.exits || {}).join(', ');
  card.innerHTML = `
    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
      <span style="color:var(--bright); font-weight:bold;">${room.display_name || room.name}</span>
      <span style="color:var(--accent);">ID: ${room.name}</span>
    </div>
    <div style="color:var(--text); line-height:1.4; margin-bottom:6px; font-style:italic;">"${desc}"</div>
    <div style="color:var(--dim);">Initial items: <span style="color:var(--amber);">${initialItems}</span></div>
    <div style="color:var(--dim);">Exits: <span style="color:var(--accent);">${exits || 'none'}</span></div>
  `;
}

function onStoryStartRoomChange(val) {
  const State = window.State;
  if (!State || !State.yamlData) return;
  if (!Array.isArray(State.yamlData.floors)) State.yamlData.floors = [[]];
  if (!Array.isArray(State.yamlData.floors[0])) State.yamlData.floors[0] = [];
  if (!Array.isArray(State.yamlData.floors[0][0])) State.yamlData.floors[0][0] = [];

  State.yamlData.floors[0][0][0] = val;
  if (State.yamlData.player && State.yamlData.player.starting_room) {
    State.yamlData.player.starting_room = val;
  }

  updateStartRoomCard(val);
  const statusSpawn = document.getElementById('story-status-spawn');
  if (statusSpawn) statusSpawn.textContent = `Floor 0 [0,0] (${val})`;
  if (window.buildMapView) window.buildMapView(State.yamlData);
  updateStoryFieldSync();
}

function renderStoryStartingInventory() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const container = document.getElementById('story-inv-chips');
  const countEl = document.getElementById('story-inv-count');
  const selectAdd = document.getElementById('story-select-add-inv');
  if (!container) return;

  const player = State.yamlData.player || (State.yamlData.player = { starting_inventory: [] });
  if (!Array.isArray(player.starting_inventory)) player.starting_inventory = [];

  container.innerHTML = '';
  if (countEl) countEl.textContent = `${player.starting_inventory.length} item${player.starting_inventory.length !== 1 ? 's' : ''}`;

  if (player.starting_inventory.length === 0) {
    container.innerHTML = '<span style="color:var(--dim); font-size:11px; font-family:var(--mono);">No starting items in inventory.</span>';
  } else {
    player.starting_inventory.forEach((itemKey, idx) => {
      const itemDef = (State.yamlData.items || {})[itemKey];
      const chip = document.createElement('div');
      chip.className = 'story-chip';
      const displayName = itemDef ? (itemDef.display_name || itemKey) : itemKey;
      chip.innerHTML = `
        <span>${displayName}</span>
        <span style="color:var(--dim); font-size:10px;">[${itemKey}]</span>
        <span class="story-chip-remove" title="Remove item">✕</span>
      `;
      chip.querySelector('.story-chip-remove')?.addEventListener('click', () => onRemoveStartingInventoryItem(idx));
      container.appendChild(chip);
    });
  }

  if (selectAdd) {
    selectAdd.innerHTML = '<option value="">-- Choose item to add to starting inventory --</option>';
    Object.keys(State.yamlData.items || {}).forEach(itemKey => {
      const itemDef = State.yamlData.items[itemKey] || {};
      const opt = document.createElement('option');
      opt.value = itemKey;
      opt.textContent = `${itemDef.display_name || itemKey} [${itemKey}]`;
      selectAdd.appendChild(opt);
    });
  }
}

function onAddStartingInventoryItem() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const select = document.getElementById('story-select-add-inv');
  if (!select || !select.value) return;
  const itemKey = select.value;
  State.yamlData.player = State.yamlData.player || { starting_inventory: [] };
  if (!Array.isArray(State.yamlData.player.starting_inventory)) State.yamlData.player.starting_inventory = [];
  State.yamlData.player.starting_inventory.push(itemKey);
  renderStoryStartingInventory();
  updateStoryFieldSync();
  select.value = '';
}

function onRemoveStartingInventoryItem(index) {
  const State = window.State;
  if (!State || !State.yamlData || !State.yamlData.player || !Array.isArray(State.yamlData.player.starting_inventory)) return;
  State.yamlData.player.starting_inventory.splice(index, 1);
  renderStoryStartingInventory();
  updateStoryFieldSync();
}

function renderStoryWinConditions() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const list = document.getElementById('story-win-list');
  const selectAdd = document.getElementById('story-select-add-win');
  if (!list) return;

  if (!Array.isArray(State.yamlData.win_conditions)) State.yamlData.win_conditions = [];
  const activeWins = State.yamlData.win_conditions;

  const statusWinCount = document.getElementById('story-status-win-count');
  if (statusWinCount) statusWinCount.textContent = `${activeWins.length} Objective${activeWins.length !== 1 ? 's' : ''}`;

  list.innerHTML = '';
  if (activeWins.length === 0) {
    list.innerHTML = '<div style="padding:14px; background:rgba(232,196,106,0.08); border:1px solid rgba(232,196,106,0.3); border-radius:4px; color:var(--amber); font-family:var(--mono); font-size:11px;">⚠ No win conditions configured! Add an event objective below.</div>';
  } else {
    activeWins.forEach((eventId, idx) => {
      const eventDef = (State.yamlData.events || []).find(e => (e.id === eventId || e.name === eventId));
      const itemEl = document.createElement('div');
      itemEl.className = 'story-win-item';
      let eventSummary = 'Event action';
      let eventDetails = '';
      if (eventDef) {
        const trig = eventDef.trigger || {};
        eventSummary = `Trigger: ${trig.action || trig.type || 'action'} | Target: ${trig.target || 'any'}`;
        if (eventDef.message) eventDetails = '"' + eventDef.message.substring(0, 70) + '..."';
      } else {
        eventDetails = '<span style="color:var(--red);">⚠ Error: Event ID not found!</span>';
      }

      itemEl.innerHTML = `
        <div>
          <div style="font-family:var(--mono); font-size:11px;">
            <span class="story-win-id">#${idx + 1} /// ${eventId}</span>
          </div>
          <div class="story-win-desc">${eventSummary}</div>
          ${eventDetails ? '<div style="font-size:10px; color:var(--dim); font-family:var(--mono);">' + eventDetails + '</div>' : ''}
        </div>
        <button type="button" class="story-win-btn-del">REMOVE ✕</button>
      `;
      itemEl.querySelector('.story-win-btn-del')?.addEventListener('click', () => onRemoveWinCondition(idx));
      list.appendChild(itemEl);
    });
  }

  if (selectAdd) {
    selectAdd.innerHTML = '<option value="">-- Choose event to add as victory requirement --</option>';
    (State.yamlData.events || []).forEach(e => {
      const eid = e.id || e.name;
      if (eid && !activeWins.includes(eid)) {
        const opt = document.createElement('option');
        opt.value = eid;
        opt.textContent = `${eid} (${(e.trigger && e.trigger.action) || 'event'})`;
        selectAdd.appendChild(opt);
      }
    });
  }
}

function onAddWinCondition() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const select = document.getElementById('story-select-add-win');
  if (!select || !select.value) return;
  const eventId = select.value;
  if (!Array.isArray(State.yamlData.win_conditions)) State.yamlData.win_conditions = [];
  State.yamlData.win_conditions.push(eventId);
  renderStoryWinConditions();
  updateStoryFieldSync();
  select.value = '';
}

function onRemoveWinCondition(index) {
  const State = window.State;
  if (!State || !State.yamlData || !Array.isArray(State.yamlData.win_conditions)) return;
  State.yamlData.win_conditions.splice(index, 1);
  renderStoryWinConditions();
  updateStoryFieldSync();
}

function updateStoryDiagnosticsUnderneath() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  const grid = document.getElementById('story-diag-grid');
  const badge = document.getElementById('story-diag-status-badge');
  const topPill = document.getElementById('story-status-val-pill');
  if (!grid) return;

  const checks = window.performGameSanityChecks ? window.performGameSanityChecks(State.yamlData) : [];
  const storyChecks = checks.filter(c => ['story', 'player', 'win'].includes(c.category));

  const hasErr = storyChecks.some(c => c.level === 'error');
  const hasWarn = storyChecks.some(c => c.level === 'warning');

  if (badge) {
    if (hasErr) {
      badge.className = 'story-card-badge val-badge-err';
      badge.textContent = 'CRITICAL CHECKS FAILING';
    } else if (hasWarn) {
      badge.className = 'story-card-badge val-badge-warn';
      badge.textContent = 'WARNINGS DETECTED';
    } else {
      badge.className = 'story-card-badge val-badge-ok';
      badge.textContent = 'ALL CHECKS PASSING';
    }
  }

  if (topPill) {
    if (hasErr) {
      topPill.className = 'val-badge-pill val-badge-err';
      topPill.textContent = '✕ ISSUES DETECTED';
    } else if (hasWarn) {
      topPill.className = 'val-badge-pill val-badge-warn';
      topPill.textContent = '⚠ WARNINGS DETECTED';
    } else {
      topPill.className = 'val-badge-pill val-badge-ok';
      topPill.textContent = '✓ VALIDATION PASSING';
    }
  }

  grid.innerHTML = '';
  storyChecks.forEach(c => {
    const card = document.createElement('div');
    card.className = `story-diag-item ${c.level === 'error' ? 'err' : c.level === 'warning' ? 'warn' : 'pass'}`;
    const levelIcon = c.level === 'error' ? '✕' : c.level === 'warning' ? '⚠' : '✓';
    const levelColor = c.level === 'error' ? 'var(--red)' : c.level === 'warning' ? 'var(--amber)' : 'var(--accent)';

    card.innerHTML = `
      <div class="story-diag-head">
        <span style="color:${levelColor};">${levelIcon} ${c.title}</span>
        <span style="color:var(--dim); font-size:10px;">${c.category.toUpperCase()}</span>
      </div>
      <div style="color:var(--text); line-height:1.4;">${c.desc}</div>
      ${c.hint ? '<div style="color:var(--bright); margin-top:2px; font-size:10px;">💡 ' + c.hint + '</div>' : ''}
    `;
    grid.appendChild(card);
  });
}

window.renderStoryMetadataView = renderStoryMetadataView;
window.updateStoryFieldSync = updateStoryFieldSync;
window.onStoryTitleChange = onStoryTitleChange;
window.onStoryIntroTextChange = onStoryIntroTextChange;
window.onStoryIntroInstructionsChange = onStoryIntroInstructionsChange;
window.onStoryWinTitleChange = onStoryWinTitleChange;
window.onStoryWinTextChange = onStoryWinTextChange;
window.onStoryStartRoomChange = onStoryStartRoomChange;
window.onAddStartingInventoryItem = onAddStartingInventoryItem;
window.onRemoveStartingInventoryItem = onRemoveStartingInventoryItem;
window.onAddWinCondition = onAddWinCondition;
window.onRemoveWinCondition = onRemoveWinCondition;
window.updateStoryPreviews = updateStoryPreviews;
window.updateWordCount = updateWordCount;


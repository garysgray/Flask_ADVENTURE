/**
 * Map Glyph & Icon Customization Modal
 * Allows authors to customize the 6 core map grid characters:
 * player, locked exits, stairs up, stairs down, portal, and unexplored cells.
 * Includes curated quick-pick trays for instant one-click selection.
 */

const DEFAULT_MAP_GLYPHS = {
  player: "👤",
  locked: "🔒",
  stairs_up: "⬆️",
  stairs_down: "⬇️",
  portal: "🌀",
  unexplored: "?"
};

const GLYPH_FIELDS = [
  {
    key: "player",
    label: "Player Marker",
    desc: "Current player position on map",
    defaultVal: "👤",
    tray: ["👤", "🚶", "🧙", "🤖", "@", "▲", "♞"]
  },
  {
    key: "locked",
    label: "Locked Exit",
    desc: "Locked door or passage indicator",
    defaultVal: "🔒",
    tray: ["🔒", "⛔", "🧱", "❌", "█", "#", "🚫"]
  },
  {
    key: "stairs_up",
    label: "Stairs Up",
    desc: "Upward exit / ladder indicator",
    defaultVal: "⬆️",
    tray: ["⬆️", "🪜", "▲", "⇈", "^", "/\\"]
  },
  {
    key: "stairs_down",
    label: "Stairs Down",
    desc: "Downward exit / trapdoor indicator",
    defaultVal: "⬇️",
    tray: ["⬇️", "🪜", "▼", "⇊", "v", "\\/", "🕳️"]
  },
  {
    key: "portal",
    label: "Portal",
    desc: "Warp / portal destination exit",
    defaultVal: "🌀",
    tray: ["🌀", "🔮", "✨", "🚪", "◎", "O", "✵"]
  },
  {
    key: "unexplored",
    label: "Unexplored",
    desc: "Adjacent visible room not yet visited",
    defaultVal: "?",
    tray: ["?", "·", "░", "~", "*", " "]
  }
];

function initMapGlyphsModal() {
  let modal = document.getElementById("map-glyphs-modal");
  if (modal) return modal;

  modal = document.createElement("div");
  modal.id = "map-glyphs-modal";
  modal.className = "map-glyphs-modal";
  modal.onclick = (e) => {
    if (e.target === modal) closeMapGlyphsModal();
  };

  modal.innerHTML = `
    <div class="map-glyphs-card" onclick="event.stopPropagation()">
      <div class="map-glyphs-header">
        <div class="map-glyphs-title">🗺️ MAP GLYPHS &amp; ICONS</div>
        <button class="modal-close" onclick="closeMapGlyphsModal()" title="Close">✕</button>
      </div>

      <div class="map-glyphs-intro">
        Customize the symbols rendered on the 2D game map grid. Select a symbol from each quick-pick tray or type any custom ASCII character or emoji into the input.
      </div>

      <div class="map-glyphs-body">
        <div class="map-glyphs-inputs" id="map-glyphs-inputs-container"></div>
        <div class="map-glyphs-preview-panel">
          <div class="map-glyphs-preview-title">LIVE MINI-MAP PREVIEW</div>
          <div class="map-glyphs-grid" id="map-glyphs-mini-grid"></div>
          <div class="map-glyphs-preview-legend" id="map-glyphs-mini-legend"></div>
        </div>
      </div>

      <div class="map-glyphs-footer">
        <button class="btn btn-dim" onclick="resetMapGlyphsDefaults()">Reset to Defaults</button>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-dim" onclick="closeMapGlyphsModal()">Cancel</button>
          <button class="btn btn-accent" onclick="saveMapGlyphs()">Save Map Glyphs</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  injectMapGlyphsStyles();
  return modal;
}

function injectMapGlyphsStyles() {
  if (document.getElementById("map-glyphs-styles")) return;
  const s = document.createElement("style");
  s.id = "map-glyphs-styles";
  s.textContent = `
    .map-glyphs-modal {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(2px);
      z-index: 9999;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
    }
    .map-glyphs-modal.visible {
      display: flex;
    }
    .map-glyphs-card {
      width: 100%;
      max-width: 740px;
      background: var(--panel, #121820);
      border: 1px solid var(--accent, #a83030);
      border-radius: 8px;
      box-shadow: 0 16px 48px rgba(0, 0, 0, 0.7);
      padding: 18px 20px;
      display: flex;
      flex-direction: column;
      max-height: 90vh;
      color: var(--text, #c0c8d0);
    }
    .map-glyphs-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border, #2a3544);
      margin-bottom: 12px;
    }
    .map-glyphs-title {
      font-family: var(--display, monospace);
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 1.5px;
      color: var(--accent, #a83030);
    }
    .map-glyphs-intro {
      font-size: 12px;
      color: var(--dim, #708090);
      margin-bottom: 14px;
      line-height: 1.5;
    }
    .map-glyphs-body {
      display: grid;
      grid-template-columns: 1fr 240px;
      gap: 18px;
      overflow-y: auto;
      margin-bottom: 16px;
      padding-right: 4px;
    }
    @media (max-width: 680px) {
      .map-glyphs-body { grid-template-columns: 1fr; }
    }
    .map-glyphs-row {
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding: 9px 12px;
      background: var(--panel-alt, #18202c);
      border: 1px solid var(--border-dim, #1e2836);
      border-radius: 6px;
      margin-bottom: 10px;
      transition: border-color 0.15s ease;
    }
    .map-glyphs-row:hover {
      border-color: var(--border, #2a3544);
    }
    .map-glyphs-row-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .map-glyphs-label-group {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .map-glyphs-label {
      font-size: 13px;
      font-weight: 600;
      color: var(--bright, #e8f0f8);
    }
    .map-glyphs-desc {
      font-size: 11px;
      color: var(--dim, #708090);
    }
    .map-glyphs-input {
      width: 64px;
      text-align: center;
      font-size: 16px;
      padding: 4px 6px;
      background: var(--panel, #121820);
      border: 1px solid var(--border, #2a3544);
      color: var(--bright, #fff);
      border-radius: 4px;
      font-family: var(--mono, monospace);
    }
    .map-glyphs-input:focus {
      outline: none;
      border-color: var(--accent, #a83030);
      box-shadow: 0 0 0 2px rgba(168, 48, 48, 0.25);
    }
    .map-glyphs-tray {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      padding-top: 4px;
      border-top: 1px dashed rgba(255, 255, 255, 0.07);
    }
    .map-glyphs-tray-label {
      font-size: 10px;
      font-weight: 600;
      color: var(--dim, #708090);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-right: 2px;
    }
    .map-glyphs-tray-items {
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
    }
    .mg-tray-btn {
      background: var(--panel, #121820);
      border: 1px solid var(--border-dim, #243040);
      color: var(--bright, #e0e8f0);
      font-size: 13px;
      line-height: 1;
      padding: 4px 7px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.12s ease;
      font-family: var(--mono, monospace);
      min-width: 26px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .mg-tray-btn:hover {
      background: var(--accent, #a83030);
      color: #fff;
      border-color: var(--accent, #a83030);
      transform: translateY(-1px);
    }
    .mg-tray-btn.is-active {
      border-color: var(--accent, #a83030);
      background: rgba(168, 48, 48, 0.25);
      color: #fff;
    }
    .mg-tray-btn-blank {
      font-size: 10px;
      padding: 4px 6px;
      color: var(--dim, #8898a8);
    }
    .map-glyphs-preview-panel {
      background: var(--panel-alt, #18202c);
      border: 1px solid var(--border-dim, #1e2836);
      border-radius: 6px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .map-glyphs-preview-title {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 1px;
      color: var(--dim, #708090);
      margin-bottom: 10px;
      text-align: center;
    }
    .map-glyphs-grid {
      display: grid;
      grid-template-columns: repeat(3, 64px);
      grid-template-rows: repeat(3, 64px);
      gap: 4px;
      background: #0b0f14;
      padding: 6px;
      border-radius: 4px;
      border: 1px solid var(--border, #2a3544);
      margin-bottom: 12px;
    }
    .map-glyphs-cell {
      background: #141c26;
      border: 1px solid #243040;
      border-radius: 3px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, 1fr);
      padding: 2px;
      position: relative;
    }
    .map-glyphs-cell.player-cell {
      border-color: var(--accent, #a83030);
      background: #1c1820;
    }
    .map-glyphs-cell.adjacent-cell {
      border: 1px dashed #3a4a5e;
      background: #0e141c;
    }
    .map-glyphs-cell.empty-cell {
      background: transparent;
      border: none;
    }
    .mg-slot {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      line-height: 1;
      text-align: center;
      overflow: hidden;
    }
    .mg-slot-center {
      grid-column: 2;
      grid-row: 2;
      font-size: 14px;
    }
    .map-glyphs-preview-legend {
      font-size: 11px;
      color: var(--dim, #708090);
      text-align: center;
      line-height: 1.4;
    }
    .map-glyphs-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 12px;
      border-top: 1px solid var(--border, #2a3544);
    }
  `;
  document.head.appendChild(s);
}

function getCurrentGlyphs() {
  const State = window.State;
  const current = (State && State.yamlData && State.yamlData.map_glyphs) || {};
  const result = {};
  GLYPH_FIELDS.forEach(f => {
    result[f.key] = current[f.key] !== undefined && current[f.key] !== null && String(current[f.key]).trim()
      ? String(current[f.key]).trim()
      : f.defaultVal;
  });
  return result;
}

function getFormGlyphs() {
  const result = {};
  GLYPH_FIELDS.forEach(f => {
    const input = document.getElementById(`mg-input-${f.key}`);
    const val = input ? input.value : "";
    result[f.key] = val !== "" ? val : f.defaultVal;
  });
  return result;
}

function selectQuickGlyph(key, glyphVal) {
  const input = document.getElementById(`mg-input-${key}`);
  if (input) {
    input.value = glyphVal;
    updateMapGlyphsPreview();
  }
}

function renderMapGlyphsInputs(glyphs) {
  const container = document.getElementById("map-glyphs-inputs-container");
  if (!container) return;
  container.innerHTML = "";

  GLYPH_FIELDS.forEach(f => {
    const currentVal = glyphs[f.key] !== undefined ? glyphs[f.key] : f.defaultVal;
    const row = document.createElement("div");
    row.className = "map-glyphs-row";

    const trayButtonsHtml = f.tray.map(item => {
      const isBlank = item === " ";
      const displayLabel = isBlank ? "␣ blank" : escapeHtmlAttr(item);
      const isSelected = currentVal === item;
      const extraClass = (isBlank ? " mg-tray-btn-blank" : "") + (isSelected ? " is-active" : "");
      return `<button type="button" class="mg-tray-btn${extraClass}"
                      title="${isBlank ? 'Blank space' : 'Select ' + item}"
                      onclick="selectQuickGlyph('${f.key}', '${escapeJs(item)}')">${displayLabel}</button>`;
    }).join("");

    row.innerHTML = `
      <div class="map-glyphs-row-top">
        <div class="map-glyphs-label-group">
          <span class="map-glyphs-label">${f.label}</span>
          <span class="map-glyphs-desc">${f.desc}</span>
        </div>
        <input type="text" id="mg-input-${f.key}" class="map-glyphs-input"
               value="${escapeHtmlAttr(currentVal)}"
               maxlength="8"
               oninput="updateMapGlyphsPreview()">
      </div>
      <div class="map-glyphs-tray">
        <span class="map-glyphs-tray-label">Pick:</span>
        <div class="map-glyphs-tray-items">
          ${trayButtonsHtml}
        </div>
      </div>
    `;
    container.appendChild(row);
  });
}

function escapeHtmlAttr(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeJs(str) {
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"');
}

function updateMapGlyphsPreview() {
  const glyphs = getFormGlyphs();
  const grid = document.getElementById("map-glyphs-mini-grid");
  if (!grid) return;

  // Highlight active tray buttons to reflect input value
  GLYPH_FIELDS.forEach(f => {
    const currentInputVal = glyphs[f.key];
    const inputEl = document.getElementById(`mg-input-${f.key}`);
    const rowEl = inputEl ? inputEl.closest(".map-glyphs-row") : null;
    if (rowEl) {
      const buttons = rowEl.querySelectorAll(".mg-tray-btn");
      buttons.forEach(btn => {
        const btnVal = btn.textContent === "␣ blank" ? " " : btn.textContent;
        btn.classList.toggle("is-active", btnVal === currentInputVal);
      });
    }
  });

  // Render a 3x3 sample dungeon floor:
  // [0,0]: Unexplored room
  // [0,1]: North room with Locked Exit
  // [0,2]: Empty
  // [1,0]: West room with Portal
  // [1,1]: Center room with Player Marker + locked east exit
  // [1,2]: East room with Stairs Up
  // [2,0]: Empty
  // [2,1]: South room with Stairs Down
  // [2,2]: Empty
  grid.innerHTML = `
    <!-- [0,0] Unexplored -->
    <div class="map-glyphs-cell adjacent-cell" title="Unexplored Room">
      <div class="mg-slot mg-slot-center">${escapeHtmlAttr(glyphs.unexplored)}</div>
    </div>
    <!-- [0,1] North room with locked exit -->
    <div class="map-glyphs-cell" title="North Room (Locked Exit)">
      <div class="mg-slot" style="grid-column:2; grid-row:1;">${escapeHtmlAttr(glyphs.locked)}</div>
    </div>
    <!-- [0,2] Empty -->
    <div class="map-glyphs-cell empty-cell"></div>

    <!-- [1,0] West room with portal -->
    <div class="map-glyphs-cell" title="Portal Room">
      <div class="mg-slot mg-slot-center">${escapeHtmlAttr(glyphs.portal)}</div>
    </div>
    <!-- [1,1] Center Player Room -->
    <div class="map-glyphs-cell player-cell" title="Player Room">
      <div class="mg-slot mg-slot-center">${escapeHtmlAttr(glyphs.player)}</div>
      <div class="mg-slot" style="grid-column:3; grid-row:2;">${escapeHtmlAttr(glyphs.locked)}</div>
    </div>
    <!-- [1,2] East Room with Stairs Up -->
    <div class="map-glyphs-cell" title="Stairs Up Room">
      <div class="mg-slot" style="grid-column:3; grid-row:1;">${escapeHtmlAttr(glyphs.stairs_up)}</div>
    </div>

    <!-- [2,0] Empty -->
    <div class="map-glyphs-cell empty-cell"></div>
    <!-- [2,1] South room with stairs down -->
    <div class="map-glyphs-cell" title="Stairs Down Room">
      <div class="mg-slot" style="grid-column:1; grid-row:3;">${escapeHtmlAttr(glyphs.stairs_down)}</div>
    </div>
    <!-- [2,2] Empty -->
    <div class="map-glyphs-cell empty-cell"></div>
  `;

  const legend = document.getElementById("map-glyphs-mini-legend");
  if (legend) {
    legend.textContent = `Player: ${glyphs.player} • Lock: ${glyphs.locked} • Up: ${glyphs.stairs_up} • Down: ${glyphs.stairs_down}`;
  }
}

function openMapGlyphsModal() {
  const modal = initMapGlyphsModal();
  const glyphs = getCurrentGlyphs();
  renderMapGlyphsInputs(glyphs);
  updateMapGlyphsPreview();
  modal.classList.add("visible");
}

function closeMapGlyphsModal() {
  const modal = document.getElementById("map-glyphs-modal");
  if (modal) modal.classList.remove("visible");
}

function resetMapGlyphsDefaults() {
  GLYPH_FIELDS.forEach(f => {
    const input = document.getElementById(`mg-input-${f.key}`);
    if (input) input.value = f.defaultVal;
  });
  updateMapGlyphsPreview();
}

function saveMapGlyphs() {
  const State = window.State;
  if (!State || !State.yamlData) {
    closeMapGlyphsModal();
    return;
  }

  const glyphs = getFormGlyphs();
  State.yamlData.map_glyphs = glyphs;

  if (window.dumpYaml) {
    State.rawYamlString = window.dumpYaml(State.yamlData);
  }

  State.markChanged("map_glyphs");
  State.showToast("MAP GLYPHS SAVED");
  closeMapGlyphsModal();

  if (window.renderMapView && State.currentMode === "map") {
    window.renderMapView();
  }
}

window.openMapGlyphsModal = openMapGlyphsModal;
window.closeMapGlyphsModal = closeMapGlyphsModal;
window.saveMapGlyphs = saveMapGlyphs;
window.resetMapGlyphsDefaults = resetMapGlyphsDefaults;
window.updateMapGlyphsPreview = updateMapGlyphsPreview;
window.selectQuickGlyph = selectQuickGlyph;

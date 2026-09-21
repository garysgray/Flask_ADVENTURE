/**
 * Emoji & Symbol Palette Drawer
 * Provides a categorized browser for adventure authors to pick characters, items,
 * map markers, and retro terminal glyphs.
 */

const EMOJI_PALETTE_DATA = {
  characters: {
    label: "Avatars & NPCs",
    emojis: [
      "🚶", "🏃", "🕵️", "👤", "👥", "🤖", "👾", "🧙", "🧙‍♂️", "🧙‍♀️",
      "👻", "💀", "☠️", "🐱", "🐕", "🐺", "🐉", "🐀", "🕷️", "🦇",
      "🧛", "🧟", "🧜", "🧝", "💂", "👮", "🧑‍🔬", "🧑‍🚀", "👸", "🤴"
    ]
  },
  items: {
    label: "Items & Relics",
    emojis: [
      "🔑", "🗝️", "🔦", "📜", "📖", "💾", "🧪", "🧰", "🗡️", "⚔️",
      "🛡️", "🏹", "💎", "🪙", "📦", "🧭", "🪓", "🏺", "✉️", "⚙️",
      "🔋", "🕯️", "🪞", "👑", "🔮", "📿", "💍", "🧪", "💉", "🧲"
    ]
  },
  map: {
    label: "Map & Hazards",
    emojis: [
      "🚪", "🪜", "🪟", "🔒", "🔓", "🌀", "📍", "🏢", "🏰", "🏛️",
      "🌲", "🪨", "🕸️", "💻", "🪑", "🛏️", "⚰️", "🚨", "⚠️", "🧱",
      "🔥", "💧", "⚡", "🪜", "🕳️", "🪵", "🛖", "⛺", "🛸", "⛲"
    ]
  },
  glyphs: {
    label: "Terminal & Retro Glyphs",
    emojis: [
      "▲", "▼", "◀", "▶", "◆", "◇", "◈", "○", "●", "◎",
      "█", "▓", "▒", "░", "━", "┃", "┏", "┓", "┗", "┛",
      "┣", "┫", "┳", "┻", "╋", "✦", "★", "☆", "☠", "⚑",
      "⌂", "✓", "✕", "§", "¶", "±", "∞", "≈", "≠", "≡"
    ]
  }
};

let currentEmojiCategory = "characters";
let emojiSearchQuery = "";
let lastFocusedInputElement = null;

function initEmojiPickerUI() {
  let modal = document.getElementById("emoji-picker-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "emoji-picker-modal";
    modal.className = "emoji-picker-modal";
    modal.onclick = (e) => {
      if (e.target === modal) closeEmojiPicker();
    };

    modal.innerHTML = `
      <div class="emoji-picker-card" onclick="event.stopPropagation()">
        <div class="emoji-picker-head">
          <span class="emoji-picker-title">🎨 EMOJIS &amp; ADVENTURE CHARACTERS</span>
          <button class="modal-close" onclick="closeEmojiPicker()">✕</button>
        </div>

        <div style="margin-bottom: 10px;">
          <input type="text" id="emoji-search-input" class="search-input" style="width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 6px 10px; background: var(--panel-alt);" placeholder="Search characters, items, glyphs..." oninput="onEmojiSearch(this.value)">
        </div>

        <div class="emoji-categories-tabs" id="emoji-cat-tabs"></div>

        <div class="emoji-grid-display" id="emoji-grid-cells"></div>

        <div class="emoji-preview-box">
          <div id="emoji-last-selected">Click any emoji to copy &amp; insert</div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-dim" style="padding: 4px 8px; font-size: 10px;" onclick="copyLastSelectedEmoji()">Copy Again</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  renderEmojiTabs();
  renderEmojiGrid();
}

function renderEmojiTabs() {
  const tabsContainer = document.getElementById("emoji-cat-tabs");
  if (!tabsContainer) return;
  tabsContainer.innerHTML = "";

  Object.keys(EMOJI_PALETTE_DATA).forEach(catKey => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "emoji-cat-btn" + (currentEmojiCategory === catKey ? " active" : "");
    btn.textContent = EMOJI_PALETTE_DATA[catKey].label;
    btn.onclick = () => {
      currentEmojiCategory = catKey;
      renderEmojiTabs();
      renderEmojiGrid();
    };
    tabsContainer.appendChild(btn);
  });
}

function renderEmojiGrid() {
  const grid = document.getElementById("emoji-grid-cells");
  if (!grid) return;
  grid.innerHTML = "";

  let list = EMOJI_PALETTE_DATA[currentEmojiCategory]?.emojis || [];
  if (emojiSearchQuery) {
    const q = emojiSearchQuery.toLowerCase();
    // Search across all categories when filtering
    list = [];
    Object.keys(EMOJI_PALETTE_DATA).forEach(k => {
      EMOJI_PALETTE_DATA[k].emojis.forEach(em => {
        if (!list.includes(em)) list.push(em);
      });
    });
  }

  list.forEach(emoji => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "emoji-btn-item";
    btn.textContent = emoji;
    btn.title = `Insert ${emoji}`;
    btn.onclick = () => selectEmoji(emoji);
    grid.appendChild(btn);
  });
}

let lastSelectedEmojiStr = "";

function selectEmoji(emoji) {
  lastSelectedEmojiStr = emoji;
  const prevBox = document.getElementById("emoji-last-selected");
  if (prevBox) {
    prevBox.innerHTML = `Selected: <span style="font-size:18px;">${emoji}</span> &mdash; copied to clipboard!`;
  }

  // Copy to clipboard
  try {
    navigator.clipboard.writeText(emoji).catch(() => {});
  } catch (_) {}

  // If a textarea or input was active, insert into it
  if (lastFocusedInputElement && typeof lastFocusedInputElement.focus === "function") {
    const el = lastFocusedInputElement;
    const start = el.selectionStart || 0;
    const end = el.selectionEnd || 0;
    const text = el.value || "";
    el.value = text.substring(0, start) + emoji + text.substring(end);
    el.selectionStart = el.selectionEnd = start + emoji.length;
    el.focus();
    // Trigger input event for data bindings
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  if (window.State && window.State.showToast) {
    window.State.showToast(`COPIED ${emoji} TO CLIPBOARD`);
  }
}

function copyLastSelectedEmoji() {
  if (!lastSelectedEmojiStr) return;
  try {
    navigator.clipboard.writeText(lastSelectedEmojiStr).catch(() => {});
    if (window.State && window.State.showToast) {
      window.State.showToast(`COPIED ${lastSelectedEmojiStr}`);
    }
  } catch (_) {}
}

function onEmojiSearch(val) {
  emojiSearchQuery = (val || "").trim();
  renderEmojiGrid();
}

function openEmojiPicker(targetElementId) {
  if (targetElementId) {
    lastFocusedInputElement = document.getElementById(targetElementId);
  } else if (document.activeElement && (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA")) {
    lastFocusedInputElement = document.activeElement;
  }

  initEmojiPickerUI();
  const modal = document.getElementById("emoji-picker-modal");
  if (modal) modal.classList.add("visible");
}

function closeEmojiPicker() {
  const modal = document.getElementById("emoji-picker-modal");
  if (modal) modal.classList.remove("visible");
}

// Track active inputs to facilitate one-click insertion
document.addEventListener("focusin", (e) => {
  if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) {
    if (e.target.id !== "emoji-search-input") {
      lastFocusedInputElement = e.target;
    }
  }
});

window.openEmojiPicker = openEmojiPicker;
window.closeEmojiPicker = closeEmojiPicker;

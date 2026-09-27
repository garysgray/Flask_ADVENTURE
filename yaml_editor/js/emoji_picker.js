/**
 * Global Quick-Copy Floating Panel
 * Lightweight overlay panel providing instant one-click copying of adventure emojis,
 * monsters, items, environment symbols, and retro ASCII glyphs.
 */

const EMOJI_PALETTE_DATA = {
  faces: {
    label: "Faces & NPCs",
    emojis: [
      "👤", "🚶", "🏃", "🧙", "🧙‍♂️", "🧙‍♀️", "🤖", "🧝", "🧛", "🧟",
      "🧜", "👸", "🤴", "🕵️", "👥", "💂", "👮", "🧑‍🔬", "🧑‍🚀", "🐱",
      "🐕", "🐺", "🦇", "💀", "☠️", "👻", "🧞", "🧚", "🥷", "🤡"
    ]
  },
  monsters: {
    label: "Monsters & Beasts",
    emojis: [
      "🐉", "🦇", "🐺", "🕷️", "🐀", "🐍", "🦂", "🦈", "🐙", "🦑",
      "🦁", "🐻", "🦖", "🦅", "🦉", "🐊", "🐗", "🦍", "🦟", "🪰",
      "🦠", "🧟", "🧛", "👻", "💀", "☠️", "👾", "🤖", "👹", "👺"
    ]
  },
  items: {
    label: "Items & Relics",
    emojis: [
      "🔑", "🗝️", "🔦", "📜", "📖", "💾", "🧪", "🧰", "🗡️", "⚔️",
      "🛡️", "🏹", "💎", "🪙", "📦", "🧭", "🪓", "🏺", "✉️", "⚙️",
      "🔋", "🕯️", "🪞", "👑", "🔮", "📿", "💍", "💉", "🧲", "🪵"
    ]
  },
  environment: {
    label: "Environment & Map",
    emojis: [
      "🚪", "🪜", "🪟", "🔒", "🔓", "🌀", "📍", "🏢", "🏰", "🏛️",
      "🌲", "🪨", "🕸️", "💻", "🪑", "🛏️", "⚰️", "🚨", "⚠️", "🧱",
      "🔥", "💧", "⚡", "🕳️", "🛖", "⛺", "🛸", "⛲", "🌋", "🏔️"
    ]
  },
  glyphs: {
    label: "UI & Glyphs",
    emojis: [
      "▲", "▼", "◀", "▶", "◆", "◇", "◈", "○", "●", "◎",
      "█", "▓", "▒", "░", "━", "┃", "┏", "┓", "┗", "┛",
      "┣", "┫", "┳", "┻", "╋", "✦", "★", "☆", "☠", "⚑",
      "⌂", "✓", "✕", "§", "¶", "±", "∞", "≈", "≠", "≡",
      "⇈", "⇊", "♞", "✵", "^", "v"
    ]
  }
};

let currentEmojiCategory = "faces";
let emojiSearchQuery = "";
let lastFocusedInputElement = null;

function initEmojiPickerUI() {
  let modal = document.getElementById("emoji-picker-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "emoji-picker-modal";
    modal.className = "emoji-picker-modal";

    modal.innerHTML = `
      <div class="emoji-picker-card" onclick="event.stopPropagation()">
        <div class="emoji-picker-head">
          <span class="emoji-picker-title">✨ QUICK-COPY SYMBOLS</span>
          <button class="modal-close" onclick="closeEmojiPicker()" title="Close Panel">✕</button>
        </div>

        <div style="margin-bottom: 8px;">
          <input type="text" id="emoji-search-input" class="search-input"
                 style="width: 100%; border: 1px solid var(--border); border-radius: 4px; padding: 5px 8px; font-size: 12px; background: var(--panel-alt); color: var(--bright);"
                 placeholder="Search characters, items, glyphs..." oninput="onEmojiSearch(this.value)">
        </div>

        <div class="emoji-categories-tabs" id="emoji-cat-tabs"></div>

        <div class="emoji-grid-display" id="emoji-grid-cells" style="max-height: 240px;"></div>

        <div class="emoji-preview-box" style="padding: 6px 10px; font-size: 11px;">
          <div id="emoji-last-selected">Click any symbol to copy &amp; paste anywhere</div>
          <div style="display: flex; gap: 6px;">
            <button class="btn btn-dim" style="padding: 2px 6px; font-size: 10px;" onclick="copyLastSelectedEmoji()">Copy Again</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    // Dismiss on click outside if modal is visible
    document.addEventListener("mousedown", (e) => {
      const m = document.getElementById("emoji-picker-modal");
      if (!m || !m.classList.contains("visible")) return;
      // If clicked inside the card or on the toggle button, don't close
      if (m.contains(e.target)) return;
      const toggleBtn = document.getElementById("btn-quick-copy");
      if (toggleBtn && toggleBtn.contains(e.target)) return;
      closeEmojiPicker();
    });
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
      emojiSearchQuery = "";
      const searchInp = document.getElementById("emoji-search-input");
      if (searchInp) searchInp.value = "";
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
    btn.title = `Click to copy ${emoji}`;
    btn.onclick = () => selectEmoji(emoji);
    grid.appendChild(btn);
  });
}

let lastSelectedEmojiStr = "";

function selectEmoji(emoji) {
  lastSelectedEmojiStr = emoji;
  const prevBox = document.getElementById("emoji-last-selected");
  if (prevBox) {
    prevBox.innerHTML = `Copied: <span style="font-size:16px;">${emoji}</span> to clipboard!`;
  }

  // Copy to system clipboard
  try {
    navigator.clipboard.writeText(emoji).catch(() => {});
  } catch (_) {}

  // If a text input or textarea was active, insert into it
  if (lastFocusedInputElement && typeof lastFocusedInputElement.focus === "function") {
    const el = lastFocusedInputElement;
    try {
      const start = el.selectionStart !== undefined ? el.selectionStart : el.value.length;
      const end = el.selectionEnd !== undefined ? el.selectionEnd : el.value.length;
      const text = el.value || "";
      el.value = text.substring(0, start) + emoji + text.substring(end);
      if (el.selectionStart !== undefined) {
        el.selectionStart = el.selectionEnd = start + emoji.length;
      }
      el.focus();
      el.dispatchEvent(new Event("input", { bubbles: true }));
    } catch (_) {}
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

function toggleEmojiPicker() {
  const modal = document.getElementById("emoji-picker-modal");
  if (modal && modal.classList.contains("visible")) {
    closeEmojiPicker();
  } else {
    openEmojiPicker();
  }
}

function openEmojiPicker(targetElementId) {
  if (targetElementId) {
    lastFocusedInputElement = document.getElementById(targetElementId);
  } else if (document.activeElement && (document.activeElement.tagName === "INPUT" || document.activeElement.tagName === "TEXTAREA")) {
    if (document.activeElement.id !== "emoji-search-input") {
      lastFocusedInputElement = document.activeElement;
    }
  }

  initEmojiPickerUI();
  const modal = document.getElementById("emoji-picker-modal");
  if (modal) modal.classList.add("visible");

  const searchInp = document.getElementById("emoji-search-input");
  if (searchInp) {
    setTimeout(() => searchInp.focus(), 50);
  }
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
window.toggleEmojiPicker = toggleEmojiPicker;
window.selectEmoji = selectEmoji;

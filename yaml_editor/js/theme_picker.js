/**
 * Theme & Font Customization Modal & Manager
 * Provides retro terminal themes, custom color palettes, and monospaced typography presets.
 */

const THEMES_CONFIG = {
  default: {
    id: "default",
    name: "Classic Slate",
    subtitle: "Dark slate with cyan & emerald highlights",
    vars: {
      "--bg": "#0d1117",
      "--panel": "#161b22",
      "--panel-alt": "#1c2128",
      "--border": "#30363d",
      "--border-dim": "#21262d",
      "--text": "#c9d1d9",
      "--dim": "#8b949e",
      "--bright": "#f0f6fc",
      "--accent": "#4af0c0",
      "--accent-dim": "rgba(74, 240, 192, 0.15)",
      "--accent-glow": "rgba(74, 240, 192, 0.3)",
      "--amber": "#e8c46a",
      "--amber-dim": "rgba(232, 196, 106, 0.15)",
      "--red": "#f85149",
      "--red-dim": "rgba(248, 81, 73, 0.15)",
      "--blue": "#58a6ff",
      "--blue-dim": "rgba(88, 166, 255, 0.15)"
    },
    swatch: ["#0d1117", "#161b22", "#4af0c0", "#58a6ff"]
  },
  amber: {
    id: "amber",
    name: "Amber CRT 1982",
    subtitle: "Warm retro monochrome phosphor terminal",
    vars: {
      "--bg": "#120d04",
      "--panel": "#1f1708",
      "--panel-alt": "#2b200b",
      "--border": "#4a3814",
      "--border-dim": "#33260d",
      "--text": "#e5a73b",
      "--dim": "#99732e",
      "--bright": "#ffd175",
      "--accent": "#ffb020",
      "--accent-dim": "rgba(255, 176, 32, 0.18)",
      "--accent-glow": "rgba(255, 176, 32, 0.35)",
      "--amber": "#ffca4f",
      "--amber-dim": "rgba(255, 202, 79, 0.18)",
      "--red": "#ff5c38",
      "--red-dim": "rgba(255, 92, 56, 0.18)",
      "--blue": "#e0b04c",
      "--blue-dim": "rgba(224, 176, 76, 0.18)"
    },
    swatch: ["#120d04", "#1f1708", "#ffb020", "#ffd175"]
  },
  phosphor: {
    id: "phosphor",
    name: "Green Phosphor VT100",
    subtitle: "High-contrast matrix terminal green",
    vars: {
      "--bg": "#05130b",
      "--panel": "#0c2114",
      "--panel-alt": "#12301d",
      "--border": "#1a472a",
      "--border-dim": "#102e1b",
      "--text": "#4ef080",
      "--dim": "#2ba853",
      "--bright": "#82ffa9",
      "--accent": "#33ff66",
      "--accent-dim": "rgba(51, 255, 102, 0.18)",
      "--accent-glow": "rgba(51, 255, 102, 0.35)",
      "--amber": "#d4f043",
      "--amber-dim": "rgba(212, 240, 67, 0.18)",
      "--red": "#ff4f5e",
      "--red-dim": "rgba(255, 79, 94, 0.18)",
      "--blue": "#3bf0ba",
      "--blue-dim": "rgba(59, 240, 186, 0.18)"
    },
    swatch: ["#05130b", "#0c2114", "#33ff66", "#82ffa9"]
  },
  cyberpunk: {
    id: "cyberpunk",
    name: "Cyberpunk Neon",
    subtitle: "Deep midnight purple with hot pink & electric cyan",
    vars: {
      "--bg": "#0d091a",
      "--panel": "#17102e",
      "--panel-alt": "#211742",
      "--border": "#432f7a",
      "--border-dim": "#2e1f57",
      "--text": "#d8ccf5",
      "--dim": "#9884c7",
      "--bright": "#ffffff",
      "--accent": "#00f0ff",
      "--accent-dim": "rgba(0, 240, 255, 0.18)",
      "--accent-glow": "rgba(0, 240, 255, 0.35)",
      "--amber": "#ff007f",
      "--amber-dim": "rgba(255, 0, 127, 0.18)",
      "--red": "#ff2a55",
      "--red-dim": "rgba(255, 42, 85, 0.18)",
      "--blue": "#9933ff",
      "--blue-dim": "rgba(153, 51, 255, 0.18)"
    },
    swatch: ["#0d091a", "#17102e", "#00f0ff", "#ff007f"]
  },
  solarized: {
    id: "solarized",
    name: "Solarized Dark",
    subtitle: "Calm teal & cyan palette for long writing sessions",
    vars: {
      "--bg": "#002b36",
      "--panel": "#073642",
      "--panel-alt": "#094352",
      "--border": "#586e75",
      "--border-dim": "#0b5163",
      "--text": "#93a1a1",
      "--dim": "#657b83",
      "--bright": "#fdf6e3",
      "--accent": "#2aa198",
      "--accent-dim": "rgba(42, 161, 152, 0.18)",
      "--accent-glow": "rgba(42, 161, 152, 0.35)",
      "--amber": "#b58900",
      "--amber-dim": "rgba(181, 137, 0, 0.18)",
      "--red": "#dc322f",
      "--red-dim": "rgba(220, 50, 47, 0.18)",
      "--blue": "#268bd2",
      "--blue-dim": "rgba(38, 139, 210, 0.18)"
    },
    swatch: ["#002b36", "#073642", "#2aa198", "#268bd2"]
  },
  highcontrast: {
    id: "highcontrast",
    name: "OLED Pitch Black",
    subtitle: "True #000000 black with razor sharp white and accents",
    vars: {
      "--bg": "#000000",
      "--panel": "#0d0d0d",
      "--panel-alt": "#171717",
      "--border": "#3b3b3b",
      "--border-dim": "#242424",
      "--text": "#dedede",
      "--dim": "#8f8f8f",
      "--bright": "#ffffff",
      "--accent": "#52f2c5",
      "--accent-dim": "rgba(82, 242, 197, 0.2)",
      "--accent-glow": "rgba(82, 242, 197, 0.4)",
      "--amber": "#ffdb58",
      "--amber-dim": "rgba(255, 219, 88, 0.2)",
      "--red": "#ff4d4d",
      "--red-dim": "rgba(255, 77, 77, 0.2)",
      "--blue": "#5dade2",
      "--blue-dim": "rgba(93, 173, 226, 0.2)"
    },
    swatch: ["#000000", "#171717", "#ffffff", "#52f2c5"]
  }
};

const FONTS_CONFIG = [
  {
    id: "jetbrains",
    name: "JetBrains Mono",
    family: "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace",
    desc: "Modern crisp developer font with clean punctuation"
  },
  {
    id: "fira",
    name: "Fira Code",
    family: "'Fira Code', 'JetBrains Mono', Consolas, monospace",
    desc: "Distinct coding monospace with clear distinct glyphs"
  },
  {
    id: "sharetech",
    name: "Share Tech Mono",
    family: "'Share Tech Mono', 'Courier New', monospace",
    desc: "Sci-fi interface and terminal console font"
  },
  {
    id: "vt323",
    name: "VT323 (Retro Pixel)",
    family: "'VT323', 'Courier New', monospace",
    desc: "1980s 8-bit CRT computer monitor pixel style"
  },
  {
    id: "system",
    name: "System Terminal (SF / Consolas)",
    family: "'SF Mono', Consolas, 'Courier New', monospace",
    desc: "Native operating system monospaced stack"
  }
];

const THEME_STORAGE_KEY = 'yaml_workbench_theme_id';
const FONT_STORAGE_KEY = 'yaml_workbench_font_id';

let currentThemeId = 'default';
let currentFontId = 'jetbrains';

function applyTheme(themeId, save = true) {
  const conf = THEMES_CONFIG[themeId] || THEMES_CONFIG.default;
  currentThemeId = conf.id;
  const root = document.documentElement;
  Object.entries(conf.vars).forEach(([k, v]) => {
    root.style.setProperty(k, v);
  });
  if (save) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, currentThemeId);
    } catch (e) {}
  }
  updateThemePickerUISelection();
}

function applyFont(fontId, save = true) {
  const conf = FONTS_CONFIG.find(f => f.id === fontId) || FONTS_CONFIG[0];
  currentFontId = conf.id;
  document.documentElement.style.setProperty('--mono', conf.family);
  if (save) {
    try {
      localStorage.setItem(FONT_STORAGE_KEY, currentFontId);
    } catch (e) {}
  }
  updateThemePickerUISelection();
}

function initThemeFromStorage() {
  try {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme && THEMES_CONFIG[savedTheme]) {
      applyTheme(savedTheme, false);
    }
    const savedFont = localStorage.getItem(FONT_STORAGE_KEY);
    if (savedFont && FONTS_CONFIG.some(f => f.id === savedFont)) {
      applyFont(savedFont, false);
    }
  } catch (e) {
    console.error('Error loading saved theme:', e);
  }
}

function initThemePickerModal() {
  let modal = document.getElementById('theme-picker-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'theme-picker-modal';
    modal.className = 'emoji-picker-modal';
    modal.onclick = (e) => {
      if (e.target === modal) closeThemePicker();
    };

    modal.innerHTML = `
      <div class="emoji-picker-card" style="max-width: 620px;" onclick="event.stopPropagation()">
        <div class="emoji-picker-head">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="emoji-picker-title">🎨 THEME &amp; FONT CUSTOMIZATION</span>
          </div>
          <button class="modal-close" onclick="closeThemePicker()">✕</button>
        </div>

        <div style="margin-bottom: 14px; font-family: var(--mono); font-size: 11px; color: var(--dim);">
          Personalize your workbench color scheme and monospaced console typography. Preferences are automatically saved in your browser.
        </div>

        <!-- Color Themes Header -->
        <div style="font-family: var(--mono); font-size: 11px; font-weight: 700; color: var(--accent); letter-spacing: 1px; margin-bottom: 8px;">
          COLOR PALETTES
        </div>

        <div id="theme-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; margin-bottom: 16px;"></div>

        <!-- Typography Presets Header -->
        <div style="font-family: var(--mono); font-size: 11px; font-weight: 700; color: var(--accent); letter-spacing: 1px; margin-bottom: 8px;">
          TERMINAL TYPOGRAPHY
        </div>

        <div id="font-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 8px; margin-bottom: 14px;"></div>

        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 10px; border-top: 1px solid var(--border-dim);">
          <button type="button" class="btn btn-dim" onclick="resetThemeDefaults()">Reset to Defaults</button>
          <button type="button" class="btn btn-accent" onclick="closeThemePicker()">Done</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    renderThemePickerCards();
  }
}

function renderThemePickerCards() {
  const themeGrid = document.getElementById('theme-cards-grid');
  const fontGrid = document.getElementById('font-cards-grid');
  if (!themeGrid || !fontGrid) return;

  themeGrid.innerHTML = '';
  Object.values(THEMES_CONFIG).forEach(t => {
    const card = document.createElement('div');
    card.className = 'theme-select-card';
    card.dataset.themeId = t.id;
    card.style.background = 'var(--panel-alt)';
    card.style.border = '1px solid var(--border)';
    card.style.borderRadius = '6px';
    card.style.padding = '10px 12px';
    card.style.cursor = 'pointer';
    card.style.transition = 'all 0.15s';

    const swatchDots = t.swatch.map(c =>
      `<span style="display:inline-block; width:14px; height:14px; border-radius:3px; background:${c}; border:1px solid rgba(255,255,255,0.15);"></span>`
    ).join('');

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
        <span style="font-family:var(--mono); font-size:12px; font-weight:bold; color:var(--bright);">${t.name}</span>
        <div style="display:flex; gap:4px;">${swatchDots}</div>
      </div>
      <div style="font-size:10px; color:var(--dim); line-height:1.3;">${t.subtitle}</div>
    `;

    card.onclick = () => {
      applyTheme(t.id);
      if (window.State) window.State.showToast(`THEME: ${t.name.toUpperCase()}`);
    };

    themeGrid.appendChild(card);
  });

  fontGrid.innerHTML = '';
  FONTS_CONFIG.forEach(f => {
    const card = document.createElement('div');
    card.className = 'font-select-card';
    card.dataset.fontId = f.id;
    card.style.background = 'var(--panel-alt)';
    card.style.border = '1px solid var(--border)';
    card.style.borderRadius = '6px';
    card.style.padding = '10px 12px';
    card.style.cursor = 'pointer';
    card.style.transition = 'all 0.15s';

    card.innerHTML = `
      <div style="font-family:${f.family}; font-size:13px; font-weight:bold; color:var(--bright); margin-bottom:4px;">
        ${f.name}
      </div>
      <div style="font-size:10px; color:var(--dim); line-height:1.3;">
        ${f.desc}
      </div>
    `;

    card.onclick = () => {
      applyFont(f.id);
      if (window.State) window.State.showToast(`FONT: ${f.name.toUpperCase()}`);
    };

    fontGrid.appendChild(card);
  });

  updateThemePickerUISelection();
}

function updateThemePickerUISelection() {
  document.querySelectorAll('.theme-select-card').forEach(c => {
    const isCur = c.dataset.themeId === currentThemeId;
    c.style.borderColor = isCur ? 'var(--accent)' : 'var(--border)';
    c.style.background = isCur ? 'rgba(74, 240, 192, 0.08)' : 'var(--panel-alt)';
  });
  document.querySelectorAll('.font-select-card').forEach(c => {
    const isCur = c.dataset.fontId === currentFontId;
    c.style.borderColor = isCur ? 'var(--accent)' : 'var(--border)';
    c.style.background = isCur ? 'rgba(74, 240, 192, 0.08)' : 'var(--panel-alt)';
  });
}

function openThemePicker() {
  initThemePickerModal();
  const modal = document.getElementById('theme-picker-modal');
  if (modal) {
    modal.classList.add('visible');
    updateThemePickerUISelection();
  }
}

function closeThemePicker() {
  const modal = document.getElementById('theme-picker-modal');
  if (modal) modal.classList.remove('visible');
}

function resetThemeDefaults() {
  applyTheme('default');
  applyFont('jetbrains');
  if (window.State) window.State.showToast('THEME RESET TO DEFAULTS');
}

// Auto-initialize themes from storage as soon as script evaluates
initThemeFromStorage();

window.openThemePicker = openThemePicker;
window.closeThemePicker = closeThemePicker;
window.applyTheme = applyTheme;
window.applyFont = applyFont;
window.resetThemeDefaults = resetThemeDefaults;
window.initThemeFromStorage = initThemeFromStorage;

/**
 * Main Application Orchestrator for YAML Adventure Editor
 */

function initWorkbench() {
  const State = window.State;
  if (!State) return;
  document.getElementById('upload-screen').style.display = 'none';
  document.getElementById('main-app').style.display      = 'flex';
  document.getElementById('top-file').textContent        = State.fileName;

  if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
  if (window.extractDialogEntries) State.dialogEntries  = window.extractDialogEntries(State.yamlData);
  State.changedIds.clear();
  State.isRawYamlDirty = false;

  if (!State.rawYamlString && State.yamlData && window.dumpYaml) {
    State.rawYamlString = window.dumpYaml(State.yamlData);
  }
  const rawTa = document.getElementById('raw-yaml-textarea');
  if (rawTa) rawTa.value = State.rawYamlString;

  if (window.buildMapView) window.buildMapView(State.yamlData);
  if (window.renderDialogList) window.renderDialogList();
  if (window.renderStoryMetadataView) window.renderStoryMetadataView();
  if (window.runValidation) window.runValidation();
  State.updateGlobalStats();
  if (window.updateYamlStatus) window.updateYamlStatus();
  if (window.setupYamlTextarea) window.setupYamlTextarea();
  State.triggerAutosave();
}

function switchMode(mode) {
  const State = window.State;
  if (!State) return;
  if (State.currentMode === 'yaml' && mode !== 'yaml') {
    if (State.isRawYamlDirty && window.applyYamlSource) {
      const ok = window.applyYamlSource(true);
      if (!ok) {
        const proceed = confirm('The YAML currently has syntax/indentation errors. Leave without applying to the map?');
        if (!proceed) return;
      }
    }
  }

  State.currentMode = mode;
  ['map', 'story', 'dialog', 'yaml', 'validator'].forEach(m => {
    document.getElementById('btn-mode-' + m)?.classList.toggle('active', mode === m);
    document.getElementById('view-' + m)?.classList.toggle('active-view', mode === m);
  });

  if (mode === 'yaml') {
    if (window.syncToYamlEditor) window.syncToYamlEditor();
  } else if (mode === 'dialog') {
    if (window.renderDialogList) window.renderDialogList();
  } else if (mode === 'story') {
    if (window.renderStoryMetadataView) window.renderStoryMetadataView();
  } else if (mode === 'validator') {
    if (window.runValidation) window.runValidation();
  }
}

function resetToUpload() {
  const State = window.State;
  document.getElementById('upload-screen').style.display = 'flex';
  document.getElementById('main-app').style.display      = 'none';
  if (State) {
    State.yamlData = null;
    State.rawYamlString = '';
    State.dialogEntries = [];
    State.changedIds.clear();
    State.isRawYamlDirty = false;
    State.checkAutosave();
  }
  const fileInp = document.getElementById('file-input');
  if (fileInp) fileInp.value = '';
}

function createNewAdventure() {
  const State = window.State;
  if (!State) return;
  if (State.yamlData && State.changedIds.size > 0) {
    const confirmDiscard = confirm('You have unsaved edits in your current adventure. Discard them and create a fresh adventure?');
    if (!confirmDiscard) return;
  }
  if (!window.createBarebonesAdventure) return;
  State.fileName = 'barebones.yaml';
  State.yamlData = window.createBarebonesAdventure();
  State.rawYamlString = window.dumpYaml ? window.dumpYaml(State.yamlData) : '';
  State.dialogEntries = [];
  initWorkbench();
  State.markChanged('new_adventure');
  State.showToast('NEW ADVENTURE CREATED (barebones.yaml)');
}

function promptRenameFile() {
  const State = window.State;
  if (!State) return;
  const current = State.fileName || 'barebones.yaml';
  const newName = prompt('Enter file name for this adventure (must end with .yaml):', current);
  if (newName && newName.trim()) {
    let clean = newName.trim();
    if (!clean.endsWith('.yaml') && !clean.endsWith('.yml')) clean += '.yaml';
    State.fileName = clean;
    const topFile = document.getElementById('top-file');
    if (topFile) topFile.textContent = clean;
    State.markChanged('filename');
    State.showToast('RENAMED TO ' + clean);
  }
}

function exportYaml() {
  const State = window.State;
  if (!State) return;
  if (State.isRawYamlDirty && window.applyYamlSource) {
    const ok = window.applyYamlSource(true);
    if (!ok) {
      alert('Fix YAML syntax errors before exporting.');
      return;
    }
  }

  // Pre-flight validation check
  if (window.performGameSanityChecks && State.yamlData) {
    const results = window.performGameSanityChecks(State.yamlData);
    const criticals = results.filter(r => r.level === 'error');
    if (criticals.length > 0) {
      const msg = `⚠️ PRE-FLIGHT VALIDATION WARNING\n\nFound ${criticals.length} critical issue(s) that may cause runtime errors in the game:\n\n` +
        criticals.slice(0, 4).map(c => `• ${c.title}: ${c.desc}`).join('\n') +
        (criticals.length > 4 ? `\n• ...and ${criticals.length - 4} more issues.` : '') +
        `\n\nDo you want to export anyway?`;
      const proceed = confirm(msg);
      if (!proceed) {
        if (window.switchMode) window.switchMode('validator');
        return;
      }
    }
  }

  const out = window.dumpYaml ? window.dumpYaml(State.yamlData) : State.rawYamlString;
  const blob = new Blob([out], { type: 'text/yaml;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = State.fileName || 'game_data.yaml';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  State.changedIds.clear();
  State.updateGlobalStats();
  State.showToast('YAML EXPORTED');
}

function loadFile(file) {
  const State = window.State;
  const upErr = document.getElementById('up-error');
  if (upErr) upErr.textContent = '';
  if (State) State.fileName = file.name;
  const reader = new FileReader();
  reader.onload = ev => {
    try {
      if (State) {
        State.rawYamlString = ev.target.result;
        State.yamlData      = window.jsyaml.load(State.rawYamlString);
        if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
      }
      initWorkbench();
    } catch (err) {
      if (upErr) upErr.textContent = 'YAML parse error: ' + err.message;
    }
  };
  reader.readAsText(file);
}

async function loadLiveGameData() {
  const State = window.State;
  const upErr = document.getElementById('up-error');
  if (upErr) upErr.textContent = '';
  try {
    const res = await fetch('/data/game_data.yaml');
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    const text = await res.text();
    if (State) {
      State.rawYamlString = text;
      State.yamlData = window.jsyaml.load(text);
      State.fileName = 'game_data.yaml';
      if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
    }
    initWorkbench();
    if (State) State.showToast('LOADED LIVE GAME DATA');
  } catch (err) {
    if (upErr) upErr.textContent = 'Could not fetch /data/game_data.yaml (' + err.message + ').';
  }
}

async function loadLiveTestRoom() {
  const State = window.State;
  const upErr = document.getElementById('up-error');
  if (upErr) upErr.textContent = '';
  try {
    const res = await fetch('/data/test_the_room.yaml');
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    const text = await res.text();
    if (State) {
      State.rawYamlString = text;
      State.yamlData = window.jsyaml.load(text);
      State.fileName = 'test_the_room.yaml';
      if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
    }
    initWorkbench();
    if (State) State.showToast('LOADED TEST_THE_ROOM.YAML');
  } catch (err) {
    if (upErr) upErr.textContent = 'Could not fetch /data/test_the_room.yaml (' + err.message + ').';
  }
}

function restoreAutosave() {
  const State = window.State;
  if (!State) return;
  const saved     = localStorage.getItem(State.AUTOSAVE_KEY);
  const savedName = localStorage.getItem(State.AUTOSAVE_NAME_KEY) || 'game_data.yaml';
  if (!saved) return;
  try {
    State.yamlData      = window.jsyaml.load(saved);
    State.fileName      = savedName;
    State.rawYamlString = saved;
    if (window.cleanModularRoomsForExport) window.cleanModularRoomsForExport(State.yamlData);
    initWorkbench();
    document.getElementById('upload-restore-banner')?.classList.remove('visible');
    document.getElementById('app-restore-banner')?.classList.remove('visible');
    State.showToast('AUTOSAVED DRAFT RESTORED');
  } catch (err) {
    alert('Could not restore draft: ' + err.message);
  }
}

function setupUploadListeners() {
  const upZone  = document.getElementById('up-zone');
  const fileInp = document.getElementById('file-input');
  if (!upZone || !fileInp) return;

  upZone.addEventListener('click', () => fileInp.click());
  upZone.addEventListener('dragover', e => { e.preventDefault(); upZone.classList.add('drag-over'); });
  upZone.addEventListener('dragleave', () => upZone.classList.remove('drag-over'));
  upZone.addEventListener('drop', e => {
    e.preventDefault();
    upZone.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]);
  });
  fileInp.addEventListener('change', e => { if (e.target.files[0]) loadFile(e.target.files[0]); });
}

// Attach globals for inline HTML event handlers and external callers
window.initWorkbench = initWorkbench;
window.loadFile = loadFile;
window.setupUploadListeners = setupUploadListeners;
window.restoreAutosave = restoreAutosave;
window.discardAutosave = () => window.State && window.State.discardAutosave();
window.loadLiveGameData = loadLiveGameData;
window.loadLiveTestRoom = loadLiveTestRoom;
window.resetToUpload = resetToUpload;
window.createNewAdventure = createNewAdventure;
window.promptRenameFile = promptRenameFile;
window.switchMode = switchMode;
window.exportYaml = exportYaml;

window.addEventListener('beforeunload', (e) => {
  const State = window.State;
  if (State && (State.changedIds.size > 0 || State.isRawYamlDirty)) {
    e.preventDefault();
    e.returnValue = '';
    return '';
  }
});

window.addEventListener('DOMContentLoaded', () => {
  setupUploadListeners();
  if (window.State) window.State.checkAutosave();
});


/**
 * YAML View: Direct raw YAML editor, search, and parse validation
 */

function syncToYamlEditor() {
  const State = window.State;
  if (!State || !State.yamlData) return;
  if (window.dumpYaml) State.rawYamlString = window.dumpYaml(State.yamlData);
  const ta = document.getElementById('raw-yaml-textarea');
  if (ta) ta.value = State.rawYamlString;
  State.isRawYamlDirty = false;
  updateYamlStatus();
  clearYamlError();
}

function setupYamlTextarea() {
  const ta = document.getElementById('raw-yaml-textarea');
  if (!ta) return;
  ta.addEventListener('input', () => {
    const State = window.State;
    if (State) State.isRawYamlDirty = true;
    updateYamlStatus();
    liveValidateYamlSyntax(ta.value);
  });
}

function updateYamlStatus() {
  const State = window.State;
  const badge = document.getElementById('yaml-sync-status');
  if (!badge || !State) return;
  if (State.isRawYamlDirty) {
    badge.textContent = 'MODIFIED (UNSAVED)';
    badge.className = 'yaml-status dirty';
  } else {
    badge.textContent = 'IN SYNC';
    badge.className = 'yaml-status';
  }
}

function liveValidateYamlSyntax(text) {
  try {
    window.jsyaml.load(text);
    clearYamlError();
    return true;
  } catch (e) {
    showYamlError('YAML Syntax Error: ' + e.message);
    return false;
  }
}

function showYamlError(msg) {
  const box = document.getElementById('yaml-error-box');
  if (box) { box.textContent = msg; box.classList.add('visible'); }
}

function clearYamlError() {
  const box = document.getElementById('yaml-error-box');
  if (box) { box.textContent = ''; box.classList.remove('visible'); }
}

function applyYamlSource(silent) {
  const State = window.State;
  const ta = document.getElementById('raw-yaml-textarea');
  if (!ta || !State) return false;
  try {
    const parsed = window.jsyaml.load(ta.value);
    if (!parsed || typeof parsed !== 'object') throw new Error('Root YAML must be an object.');
    State.yamlData = parsed;
    State.rawYamlString = ta.value;
    if (window.extractDialogEntries) State.dialogEntries = window.extractDialogEntries(State.yamlData);
    State.isRawYamlDirty = false;
    clearYamlError();
    updateYamlStatus();

    if (window.buildMapView) window.buildMapView(State.yamlData);
    if (window.renderDialogList) window.renderDialogList();
    if (window.renderStoryMetadataView) window.renderStoryMetadataView();
    if (window.runValidation) window.runValidation();
    State.updateGlobalStats();
    State.triggerAutosave();

    if (!silent) State.showToast('YAML APPLIED & MAP REFRESHED');
    return true;
  } catch (err) {
    showYamlError('Cannot Apply YAML: ' + err.message);
    return false;
  }
}

function findNextYamlMatch() {
  const State = window.State;
  const inp = document.getElementById('yaml-search-input');
  const ta  = document.getElementById('raw-yaml-textarea');
  const countEl = document.getElementById('yaml-find-count');
  if (!inp || !ta || !State) return;
  const q = inp.value;
  if (!q) return;

  const text = ta.value.toLowerCase();
  const qLower = q.toLowerCase();
  const total = text.split(qLower).length - 1;
  if (countEl) countEl.textContent = total > 0 ? total + ' matches' : 'No matches';
  if (total === 0) return;

  let idx = text.indexOf(qLower, State.yamlSearchLastIndex);
  if (idx === -1) {
    idx = text.indexOf(qLower, 0);
  }
  if (idx !== -1) {
    ta.focus();
    ta.setSelectionRange(idx, idx + q.length);
    State.yamlSearchLastIndex = idx + q.length;
  }
}

window.syncToYamlEditor = syncToYamlEditor;
window.setupYamlTextarea = setupYamlTextarea;
window.updateYamlStatus = updateYamlStatus;
window.liveValidateYamlSyntax = liveValidateYamlSyntax;
window.showYamlError = showYamlError;
window.clearYamlError = clearYamlError;
window.applyYamlSource = applyYamlSource;
window.findNextYamlMatch = findNextYamlMatch;


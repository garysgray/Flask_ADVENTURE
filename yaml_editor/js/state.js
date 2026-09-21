/**
 * State Management & Autosave for YAML Adventure Editor
 */

const State = {
  yamlData: null,
  rawYamlString: '',
  fileName: 'game_data.yaml',
  dialogEntries: [],
  changedIds: new Set(),
  isRawYamlDirty: false,
  currentMode: 'map',
  currentSection: 'all',
  currentSearch: '',
  mapSearchQuery: '',
  yamlSearchLastIndex: 0,
  validationResults: [],
  valFilterCategory: 'all',

  AUTOSAVE_KEY: 'yaml_workbench_autosave_yaml',
  AUTOSAVE_TIME_KEY: 'yaml_workbench_autosave_time',
  AUTOSAVE_NAME_KEY: 'yaml_workbench_autosave_filename',

  markChanged(id) {
    this.changedIds.add(id);
    this.updateGlobalStats();
    this.triggerAutosave();
  },

  showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 2200);
  },

  updateGlobalStats() {
    const unsavedEl = document.getElementById('unsaved-count');
    const count = this.changedIds.size + (this.isRawYamlDirty ? 1 : 0);
    if (unsavedEl) {
      unsavedEl.textContent = count + ' UNSAVED EDIT' + (count !== 1 ? 'S' : '');
      unsavedEl.classList.toggle('visible', count > 0);
    }

    const statCh = document.getElementById('stat-changed');
    if (statCh) statCh.textContent = count;

    const statEnt = document.getElementById('stat-entries');
    if (statEnt) statEnt.textContent = this.dialogEntries.length;

    let totalWords = 0;
    this.dialogEntries.forEach(e => {
      totalWords += (e.value || '').trim().split(/\s+/).filter(Boolean).length;
    });
    const statWords = document.getElementById('stat-words');
    if (statWords) statWords.textContent = totalWords.toLocaleString();

    if (this.yamlData) {
      const statR = document.getElementById('stat-rooms');
      if (statR) statR.textContent = (this.yamlData.rooms || []).length;
      const statI = document.getElementById('stat-items');
      if (statI) statI.textContent = Object.keys(this.yamlData.items || {}).length;
      const statE = document.getElementById('stat-events');
      if (statE) statE.textContent = (this.yamlData.events || []).length;
    }
  },

  triggerAutosave() {
    try {
      let out = this.rawYamlString;
      if (!this.isRawYamlDirty && this.yamlData && window.jsyaml) {
        out = window.jsyaml.dump(this.yamlData, { lineWidth: 120, quotingType: '"', forceQuotes: false, noRefs: true });
      }
      if (out) {
        localStorage.setItem(this.AUTOSAVE_KEY, out);
        localStorage.setItem(this.AUTOSAVE_TIME_KEY, new Date().toLocaleTimeString());
        localStorage.setItem(this.AUTOSAVE_NAME_KEY, this.fileName);
      }
    } catch (e) {
      console.error('Autosave error:', e);
    }
  },

  checkAutosave() {
    const saved = localStorage.getItem(this.AUTOSAVE_KEY);
    const time  = localStorage.getItem(this.AUTOSAVE_TIME_KEY);
    if (saved && saved.trim().length > 0) {
      const timeStr = time ? ' (' + time + ')' : '';
      const msg = 'Found autosaved work' + timeStr + '. You can restore your recent unsaved edits.';
      const upText = document.getElementById('upload-restore-text');
      if (upText) upText.textContent = msg;
      const upBanner = document.getElementById('upload-restore-banner');
      if (upBanner) upBanner.classList.add('visible');
      const appText = document.getElementById('app-restore-text');
      if (appText) appText.textContent = msg;
    }
  },

  discardAutosave() {
    localStorage.removeItem(this.AUTOSAVE_KEY);
    localStorage.removeItem(this.AUTOSAVE_TIME_KEY);
    localStorage.removeItem(this.AUTOSAVE_NAME_KEY);
    document.getElementById('upload-restore-banner')?.classList.remove('visible');
    document.getElementById('app-restore-banner')?.classList.remove('visible');
    this.showToast('AUTOSAVE DISCARDED');
  }
};

window.State = State;


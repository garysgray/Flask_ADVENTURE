// ─── Focus Management ────────────────────────────────────────────────────────
// Restores keyboard focus to the command input when an interruption closes.

function restoreGameplayFocus() {
    var cmd = document.getElementById('cmd');
    if (cmd) {
        cmd.focus();
    }
}

// ─── Journal ──────────────────────────────────────────────────────────────────
// Opens and closes the journal panel that slides in from the right.
// Panel HTML is only rendered when the player has journal entries.

function openJournal() {
    document.getElementById('journal-overlay').style.display = 'block';
    var panel = document.getElementById('journal-panel');
    panel.style.display = 'block';
    panel.style.right = '0';
}

function closeJournal() {
    var panel = document.getElementById('journal-panel');
    panel.style.right = '-420px';
    panel.style.display = 'none';
    document.getElementById('journal-overlay').style.display = 'none';
    restoreGameplayFocus();
}

// ─── Intro ────────────────────────────────────────────────────────────────────
// Dismisses the intro modal and tells the server the player has seen it.
// PLAYER_ID is set inline in game.html before this script loads.
// After dismissal the intro never auto-shows again.

function closeIntro() {
    document.getElementById('intro-overlay').style.display = 'none';
    document.getElementById('intro-panel').style.display = 'none';
    fetch('/seen_intro/' + PLAYER_ID, {method: 'POST'});
    restoreGameplayFocus();
}

// ─── Event Modal ─────────────────────────────────────────────────────────────
// Dismisses the event popup modal and refocuses the command input.

function closeEventModal() {
    var overlay = document.getElementById('event-overlay');
    var panel = document.getElementById('event-panel');
    if (overlay) overlay.style.display = 'none';
    if (panel) panel.style.display = 'none';
    restoreGameplayFocus();
}

document.addEventListener('DOMContentLoaded', function() {
    var eventPanel = document.getElementById('event-panel');
    var closeBtn = document.getElementById('event-close-btn');
    if (eventPanel && closeBtn) {
        closeBtn.focus();
    }
});

document.addEventListener('keydown', function(e) {
    var eventPanel = document.getElementById('event-panel');
    if (eventPanel && eventPanel.style.display !== 'none') {
        if (e.key === 'Escape' || e.key === 'Enter') {
            e.preventDefault();
            closeEventModal();
        }
    }
});

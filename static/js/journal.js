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
}

// ─── Intro ────────────────────────────────────────────────────────────────────
// Dismisses the intro modal and tells the server the player has seen it.
// PLAYER_ID is set inline in game.html before this script loads.
// After dismissal the intro never auto-shows again.

function closeIntro() {
    document.getElementById('intro-overlay').style.display = 'none';
    document.getElementById('intro-panel').style.display = 'none';
    fetch('/seen_intro/' + PLAYER_ID, {method: 'POST'});
}
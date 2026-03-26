from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from game import Controller, State
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
#app.config['SECRET_KEY'] = 'change-this-secret-in-production'


db = SQLAlchemy(app)


# =============================================================================
# DATABASE MODELS
# =============================================================================

class User(db.Model):
    """
    A registered user account. One user can have many saved games (DB_Players).
    First visit auto-creates the account — no separate registration page.
    """
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(30), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    date_create   = db.Column(db.DateTime, default=datetime.utcnow)
    players       = db.relationship('DB_Player', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DB_Player(db.Model):
    """
    Persists a single saved game. Tied to a User via user_id.
    Each user can have multiple independent saved games.

    All game state is serialized to JSON strings:
        location         — player position, visited rooms, completed events, journal
        player_inventory — items the player is carrying and their current states
        room_inventory   — all room inventories, exits, and states across the whole map
    """
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    save_name        = db.Column(db.String(30), nullable=False)
    location         = db.Column(db.String(30))
    player_inventory = db.Column(db.String(500))
    room_inventory   = db.Column(db.String(3000))
    cmd_info         = db.Column(db.String(30))
    date_create      = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, save_name, location, player_inventory, room_inventory, cmd):
        self.user_id          = user_id
        self.save_name        = save_name
        self.location         = location
        self.player_inventory = player_inventory
        self.room_inventory   = room_inventory
        self.cmd_info         = cmd

    def __repr__(self):
        return f'<DB_Player {self.id}>'


# =============================================================================
# HELPERS
# =============================================================================

def login_required(f):
    """Redirect to login page if no user is in the session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def owns_player(player_id):
    """
    Returns the DB_Player only if it belongs to the currently logged-in user.
    Prevents users from accessing or modifying each other's saves.
    """
    db_player = DB_Player.query.get_or_404(player_id)
    if db_player.user_id != session.get('user_id'):
        return None
    return db_player


def get_controller(player_id):
    """
    Returns the in-memory Controller for the given player ID.
    Controllers are stored on the app object, one per active save.
    A fresh controller is created if none exists (e.g. after server restart).
    State is set to LOAD so the game route knows to load from the database.
    """
    if not hasattr(app, 'controllers'):
        app.controllers = {}
    if player_id not in app.controllers:
        app.controllers[player_id] = Controller()
    return app.controllers[player_id]


# =============================================================================
# LOGIN / LOGOUT
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Single login page — handles both new and returning users.

    POST: Look up the username. If not found, create the account automatically.
          Then check the password. Wrong password returns an error.
    GET:  Render the login form.
    """
    if 'user_id' in session:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form['u_name'].strip()
        password = request.form['u_pass']
        user = User.query.filter_by(username=username).first()
        if not user:
            # first time this username is used — create the account
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        if user.check_password(password):
            session['user_id']  = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            error = 'WRONG PASSWORD'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Clears the session and returns to the login page."""
    session.clear()
    return redirect(url_for('login'))


# =============================================================================
# PORTAL
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """
    Game portal — shows the logged-in user's saved games only.

    POST: Creates a new save with fresh starting state and saves to DB.
          A temporary controller generates the initial save data.
    GET:  Renders the save list filtered to the current user.
    """
    if request.method == 'POST':
        save_name = request.form['save_name'].strip() or 'New Save'

        # spin up a temporary controller just to generate starting save data
        temp_ctrl = Controller()
        temp_ctrl.player.inventory = temp_ctrl.map.player_start_invent
        temp_ctrl.player.journal.append({
            'event_id': 'intro',
            'room':     'Delictum Facility',
            'message':  temp_ctrl.map.intro.get('text', '') + '\n\n' + temp_ctrl.map.intro.get('instructions', '')
        })
        loc, inv, rooms = temp_ctrl.save_stuff_to_data_base()
        new_player = DB_Player(session['user_id'], save_name, loc, inv, rooms, "NONE")
        try:
            db.session.add(new_player)
            db.session.commit()
        except Exception as e:
            return f'Error creating save: {e}'
        return redirect('/')

    players = DB_Player.query.filter_by(user_id=session['user_id']).order_by(DB_Player.date_create).all()
    return render_template('index.html', players=players, username=session.get('username'))


# =============================================================================
# GAME ROUTES
# =============================================================================

@app.route('/seen_intro/<int:id>', methods=['POST'])
@login_required
def seen_intro(id):
    """
    Called by JS when the player dismisses the intro panel.
    Sets has_seen_intro so the modal never shows again for this save.
    """
    db_player = owns_player(id)
    if not db_player:
        return redirect(url_for('index'))
    ctrl = get_controller(id)
    ctrl.player.has_seen_intro = True
    loc, inv, rooms            = ctrl.save_stuff_to_data_base()
    db_player.location         = loc
    db_player.player_inventory = inv
    db_player.room_inventory   = rooms
    db.session.commit()
    return '', 204


@app.route('/game/<int:id>', methods=['GET', 'POST'])
@login_required
def game(id):
    """
    Main game route.

    POST: Player typed a command.
        - Parse and run the command via the controller
        - Save updated state to the database
        - Redirect back to GET (prevents form resubmission on refresh)

    GET: Player is viewing the game page.
        - On first visit (State.LOAD), load saved data from DB and auto-run help
        - Build the map layout and visited rooms list for the template
        - Render the game page
    """
    db_player = owns_player(id)
    if not db_player:
        return redirect(url_for('index'))
    ctrl = get_controller(id)

    if request.method == 'POST':
        cmd = request.form['cmd'].lower()
        db_player.cmd_info = cmd
        db.session.commit()

        cmd_info = ctrl.parse_it(cmd)
        ctrl.run_the_cmd(cmd_info)

        loc, inv, rooms            = ctrl.save_stuff_to_data_base()
        db_player.location         = loc
        db_player.player_inventory = inv
        db_player.room_inventory   = rooms
        db.session.commit()

        return redirect(url_for('game', id=db_player.id))

    # GET — first visit this session: load saved state and show help
    if ctrl.State == State.LOAD:
        ctrl.load_stuff_from_data_base(db_player)
        ctrl.State = State.PLAY
        cmd_info = ctrl.parse_it("help")
        ctrl.run_the_cmd(cmd_info)
        db_player.cmd_info = "help"
        db.session.commit()

    # build map grid with positions so template can highlight current room
    # and show which rooms have been visited
    map_layout    = getattr(ctrl.map, 'game_map', [])
    current_floor = ctrl.player.level
    player_pos    = (current_floor, ctrl.player.pos_y, ctrl.player.pos_x)

    visited_rooms = []
    for pos in ctrl.player.visited_rooms:
        if isinstance(pos, (list, tuple)) and len(pos) == 3:
            visited_rooms.append((pos[0], pos[1], pos[2]))

    map_with_indices = []
    for r_idx, row in enumerate(map_layout[current_floor]):
        row_with_indices = []
        for c_idx, cell in enumerate(row):
            row_with_indices.append({
                'pos':  (current_floor, r_idx, c_idx),
                'cell': cell
            })
        map_with_indices.append(row_with_indices)

    return render_template(
        'game.html',
        cmd           = db_player.cmd_info,
        db_player     = db_player,
        debug1        = ctrl.room_info,
        player_inv    = ctrl.player.inventory,
        map_layout    = map_with_indices,
        player_pos    = player_pos,
        visited_rooms = visited_rooms,
        journal       = list(reversed(ctrl.player.journal)),
        show_intro    = not ctrl.player.has_seen_intro,
        intro         = ctrl.map.intro,
        win_screen    = ctrl.map.win_screen,
    )


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    """
    Deletes a save from the database and removes its controller from memory.
    Clearing the controller ensures a new save with the same ID starts fresh.
    Only the owning user can delete their own saves.
    """
    db_player = owns_player(id)
    if not db_player:
        return redirect(url_for('index'))
    try:
        db.session.delete(db_player)
        db.session.commit()
        if hasattr(app, 'controllers') and id in app.controllers:
            del app.controllers[id]
    except Exception as e:
        return f'Error deleting save: {e}'
    return redirect('/')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

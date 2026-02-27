from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from game import Controller, State

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'change-this-secret-in-production'
db = SQLAlchemy(app)


# =============================================================================
# DATABASE MODEL
# =============================================================================

class DB_Player(db.Model):
    """
    Persists player state between sessions.
    The live game runs in memory via Controller. When the browser closes or
    refreshes, this is what gets loaded back in on the next visit.

    All game state is serialized to JSON strings:
        location         — player position, visited rooms, completed events, journal
        player_inventory — items the player is carrying and their current states
        room_inventory   — all room inventories, exits, and states across the whole map
    """
    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(30),   nullable=False)
    location         = db.Column(db.String(30))
    player_inventory = db.Column(db.String(500))
    room_inventory   = db.Column(db.String(3000))
    cmd_info         = db.Column(db.String(30))
    date_create      = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, location, player_inventory, room_inventory, cmd):
        self.username         = username
        self.location         = location
        self.player_inventory = player_inventory
        self.room_inventory   = room_inventory
        self.cmd_info         = cmd

    def __repr__(self):
        return f'<DB_Player {self.id}>'


# =============================================================================
# CONTROLLER MANAGEMENT
# =============================================================================

def get_controller(player_id):
    """
    Returns the in-memory Controller for the given player ID.
    Controllers are stored on the app object, one per player.
    A fresh controller is created if none exists (e.g. after server restart).
    State is set to LOAD so the game route knows to load from the database.
    """
    if not hasattr(app, 'controllers'):
        app.controllers = {}
    if player_id not in app.controllers:
        app.controllers[player_id] = Controller()
    return app.controllers[player_id]


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Home page — player list and new player creation.

    POST: Creates a new player with fresh starting state and saves to DB.
    GET:  Renders the player list.
    """
    if request.method == 'POST':
        username = request.form['username']

        # spin up a temporary controller just to generate starting save data
        temp_ctrl = Controller()
        temp_ctrl.player.inventory = temp_ctrl.map.player_start_invent

        temp_ctrl.player.journal.append({
            'event_id': 'intro',
            'room':    'Ashwood Manor',
            'message':  temp_ctrl.map.intro.get('text', '') + '\n\n' + temp_ctrl.map.intro.get('instructions', '')
        })

        loc, inv, rooms = temp_ctrl.save_stuff_to_data_base()

        new_player = DB_Player(username, loc, inv, rooms, "NONE")
        try:
            db.session.add(new_player)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f'Error creating player: {e}'

    players = DB_Player.query.order_by(DB_Player.date_create).all()
    return render_template('index.html', players=players)

@app.route('/seen_intro/<int:id>', methods=['POST'])
def seen_intro(id):
    ctrl = get_controller(id)
    ctrl.player.has_seen_intro = True
    loc, inv, rooms = ctrl.save_stuff_to_data_base()
    db_player = DB_Player.query.get_or_404(id)
    db_player.location         = loc
    db_player.player_inventory = inv
    db_player.room_inventory   = rooms
    db.session.commit()
    return '', 204

@app.route('/game/<int:id>', methods=['GET', 'POST'])
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
    ctrl      = get_controller(id)
    db_player = DB_Player.query.get_or_404(id)

    if request.method == 'POST':
        cmd = request.form['cmd'].lower()
        db_player.cmd_info = cmd
        db.session.commit()

        cmd_info = ctrl.parse_it(cmd)
        ctrl.run_the_cmd(cmd_info)

        loc, inv, rooms        = ctrl.save_stuff_to_data_base()
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
        cmd          = db_player.cmd_info,
        db_player    = db_player,
        debug1       = ctrl.room_info,
        player_inv   = ctrl.player.inventory,
        map_layout   = map_with_indices,
        player_pos   = player_pos,
        visited_rooms= visited_rooms,
        journal       = list(reversed(ctrl.player.journal)),
        show_intro   = not ctrl.player.has_seen_intro,
        intro        = ctrl.map.intro,
    )


@app.route('/delete/<int:id>')
def delete(id):
    """
    Deletes a player from the database and removes their controller from memory.
    Clearing the controller ensures a new player with the same ID starts fresh.
    """
    db_player = DB_Player.query.get_or_404(id)
    try:
        db.session.delete(db_player)
        db.session.commit()
        if hasattr(app, 'controllers') and id in app.controllers:
            del app.controllers[id]
        return redirect('/')
    except Exception as e:
        return f'Error deleting player: {e}'


if __name__ == "__main__":
    app.run(debug=True)
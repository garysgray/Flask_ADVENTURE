from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from game import Controller, State

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'change-this-secret-in-production'
db = SQLAlchemy(app)


# -------------------------------
# Database model
# -------------------------------
class DB_Player(db.Model):
    """
    Stores the saved state of a player between sessions.
    The game itself runs in memory via the Controller, but when the player
    closes the browser or refreshes, this is what gets loaded back in.
    """
    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(30), nullable=False)
    location         = db.Column(db.String(30))       # serialized player position
    player_inventory = db.Column(db.String(500))      # serialized player inventory
    room_inventory   = db.Column(db.String(3000))     # serialized state of all room inventories
    cmd_info         = db.Column(db.String(30))       # last command the player typed
    date_create      = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, location, player_inventory, room_inventory, cmd):
        self.username         = username
        self.location         = location
        self.player_inventory = player_inventory
        self.room_inventory   = room_inventory
        self.cmd_info         = cmd

    def __repr__(self):
        return f'<DB_Player {self.id}>'


# -------------------------------
# Controller management
# -------------------------------
def get_controller(player_id):
    """
    Controllers live in memory on the app object, one per player id.
    If a controller doesn't exist yet for this player (e.g. first request
    after server restart), a fresh one is created. The controller holds
    all live game state: map, player, parser, events etc.
    """
    if not hasattr(app, 'controllers'):
        app.controllers = {}
    if player_id not in app.controllers:
        app.controllers[player_id] = Controller()
    return app.controllers[player_id]


# -------------------------------
# Routes
# -------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Home page. Shows a list of all saved players.
    POST: creates a new player, saves their starting state to the database,
    then redirects back to the player list.
    GET: just renders the player list.
    """
    if request.method == 'POST':
        username = request.form['username']

        # spin up a temporary controller just to generate the starting save data
        temp_ctrl = Controller()
        temp_ctrl.player.inventory = temp_ctrl.map.player_start_invent
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


@app.route('/game/<int:id>', methods=['GET', 'POST'])
def game(id):
    """
    Main game route.

    POST: player typed a command.
        - parse and run the command via the controller
        - save updated state back to the database
        - redirect back to GET (prevents form resubmission on refresh)

    GET: player is viewing the game page.
        - if the controller is in LOAD state (first visit this session),
          load saved data from the database and auto-run 'help'
        - build the map layout and visited rooms for the template
        - render the game page
    """
    ctrl      = get_controller(id)
    db_player = DB_Player.query.get_or_404(id)

    if request.method == 'POST':
        cmd = request.form['cmd'].lower()
        db_player.cmd_info = cmd
        db.session.commit()

        cmd_info = ctrl.parse_it(cmd)
        ctrl.run_the_cmd(cmd_info)

        # save the updated game state back to the database after every command
        loc, inv, rooms = ctrl.save_stuff_to_data_base()
        db_player.location         = loc
        db_player.player_inventory = inv
        db_player.room_inventory   = rooms
        db.session.commit()

        return redirect(url_for('game', id=db_player.id))

    # GET request
    if ctrl.State == State.LOAD:
        # first visit this session — load saved data and auto-run help
        # after this, State is set to PLAY and this block never runs again
        ctrl.load_stuff_from_data_base(db_player)
        ctrl.State = State.PLAY
        cmd_info = ctrl.parse_it("help")
        ctrl.run_the_cmd(cmd_info)
        db_player.cmd_info = "help"
        db.session.commit()

    # build the current floor map with grid positions attached
    # so the template knows where the player is and which rooms are visited
    map_layout    = getattr(ctrl.map, 'game_map', [])
    current_floor = ctrl.player.level
    player_pos    = (current_floor, ctrl.player.pos_y, ctrl.player.pos_x)

    # normalize visited rooms to tuples so the template can compare them to player_pos
    visited_rooms = []
    for pos in ctrl.player.visited_rooms:
        if isinstance(pos, (list, tuple)) and len(pos) == 3:
            visited_rooms.append((pos[0], pos[1], pos[2]))

    # attach grid position to each cell so the template can highlight
    # the current room and visited rooms on the map
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
        cmd=db_player.cmd_info,
        db_player=db_player,
        debug1=ctrl.room_info,
        player_inv=ctrl.player.inventory,
        map_layout=map_with_indices,
        player_pos=player_pos,
        visited_rooms=visited_rooms,
    )


@app.route('/delete/<int:id>')
def delete(id):
    """Deletes a player and their saved data from the database."""
    db_player = DB_Player.query.get_or_404(id)
    try:
        db.session.delete(db_player)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f'Error deleting player: {e}'


if __name__ == "__main__":
    app.run(debug=True)
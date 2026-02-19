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
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(30))
    player_inventory = db.Column(db.String(500))
    room_inventory = db.Column(db.String(3000))
    cmd_info = db.Column(db.String(30))
    date_create = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, location, player_inventory, room_inventory, cmd):
        self.username = username
        self.location = location
        self.player_inventory = player_inventory
        self.room_inventory = room_inventory
        self.cmd_info = cmd

    def __repr__(self):
        return f'<DB_Player {self.id}>'

# -------------------------------
# Controller management
# -------------------------------
def get_controller(player_id):
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
    if request.method == 'POST':
        username = request.form['username']
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
    ctrl = get_controller(id)
    db_player = DB_Player.query.get_or_404(id)

    if request.method == 'POST':
        cmd = request.form['cmd'].lower()
        db_player.cmd_info = cmd
        db.session.commit()

        cmd_info = ctrl.parse_it(cmd)
        ctrl.run_the_cmd(cmd_info)

        loc, inv, rooms = ctrl.save_stuff_to_data_base()
        db_player.location = loc
        db_player.player_inventory = inv
        db_player.room_inventory = rooms
        db.session.commit()

        return redirect(url_for('game', id=db_player.id))

    # GET request
    if ctrl.State == State.LOAD:
        ctrl.load_stuff_from_data_base(db_player)
        ctrl.State = State.PLAY
        cmd_info = ctrl.parse_it("help")
        ctrl.run_the_cmd(cmd_info)
        db_player.cmd_info = "help"
        db.session.commit()

    # Safe map variable
    map_layout = getattr(ctrl.map, 'game_map', [])
    current_floor = ctrl.player.level
    player_pos = (current_floor, ctrl.player.pos_y, ctrl.player.pos_x)

    visited_rooms = []
    for pos in ctrl.player.visited_rooms:
        if isinstance(pos, (list, tuple)) and len(pos) == 3:
            visited_rooms.append((pos[0], pos[1], pos[2]))

    map_with_indices = []
    for r_idx, row in enumerate(map_layout[current_floor]):
        row_with_indices = []
        for c_idx, cell in enumerate(row):
            row_with_indices.append({
                'pos': (current_floor, r_idx, c_idx),
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
        visited_rooms=visited_rooms
    )

@app.route('/delete/<int:id>')
def delete(id):
    db_player = DB_Player.query.get_or_404(id)
    try:
        db.session.delete(db_player)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f'Error deleting player: {e}'

if __name__ == "__main__":
    app.run(debug=True)

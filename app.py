from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from controller import Controller, State
import time


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)

my_ctrl= Controller()
        
class DB_Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(30), nullable=True)
    player_inventory = db.Column(db.String(500), nullable=True)
    room_inventory = db.Column(db.String(3000), nullable=True)
    cmd_info = db.Column(db.String(30), nullable=True)
    date_create = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, username, location, player_inventory, room_inventory, cmd):
        self.username = username
        self.location = location
        self.player_inventory = player_inventory
        self.room_inventory = room_inventory
        self.cmd_info = cmd
    
    def __repr__(self):
        return '<DB_Player %r>' % self.id

@app.route('/', methods=['GET', 'POST'])
def index():

    #fix cleaner way of doing this
    my_ctrl.State = State.LOAD
    my_ctrl.player.pos_x = 0
    my_ctrl.player.pos_y = 0
    my_ctrl.player.inventory = my_ctrl.map.player_start_invent
    my_ctrl.get_new_map()

    if request.method == 'POST':

        username = request.form['username']
        if username != "":

            player_loc_dumped, player_inventory_dumped, rooms_inventories_dumped = my_ctrl.save_stuff()
                
            new_db_player = DB_Player(username, player_loc_dumped, player_inventory_dumped, rooms_inventories_dumped, "NONE" )
            try:
                db.session.add(new_db_player)
                db.session.commit()
                return redirect('/')
            except:
                return 'issues here mannn. like.. wow man!'
        return redirect('/')
    else:
        players = DB_Player.query.order_by(DB_Player.date_create).all()
        return render_template('index.html', players=players)

@app.route('/game/<int:id>', methods=['GET','POST'])
def game(id):

    time.sleep(.5)

    try:
        db_player = DB_Player.query.get_or_404(id)
    except:
        return 'issues getting player thru id'

    match my_ctrl.State:
        case State.LOAD:   
            my_ctrl.load_stuff(db_player)
            cmd = "help"
            my_ctrl.State = State.PLAY 
        case State.PLAY:
            my_ctrl.load_stuff(db_player)
            cmd = db_player.cmd_info

    time.sleep(.5)

    cmd_info = my_ctrl.parse_it(cmd)
    my_ctrl.run_the_cmd(cmd_info)

    time.sleep(.5)
    
    #SAVING STUFF TO DB
    player_loc_dumped, player_inventory_dumped, rooms_inventories_dumped = my_ctrl.save_stuff()
    db_player.location = player_loc_dumped
    db_player.player_inventory = player_inventory_dumped
    db_player.room_inventory = rooms_inventories_dumped

    try:
        db.session.commit()  
    except:
        return 'issues saving after running cmd'

    if request.method == 'POST':

        cmd = request.form['cmd']
        db_player.cmd_info = cmd
   
        try:
            db.session.commit()
            return redirect(url_for('game',id=db_player.id))
        except:
            return 'issues saving cmd and redirecting'

    else:
        debug1 = my_ctrl.room_info
        return render_template('game.html', cmd=cmd , db_player=db_player, debug1= debug1, player_inv= my_ctrl.player.inventory)

           
if __name__ == ("__main__"):
    app.run(debug=True)

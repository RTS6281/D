from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import random
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# تخزين بيانات اللعبة
games = {}
players = {}
cities = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    player_id = request.sid
    if player_id in players:
        game_id = players[player_id]['game_id']
        if game_id in games:
            # إعلام اللاعبين الآخرين بترك اللاعب
            emit('playerLeft', {
                'playerId': player_id,
                'playerName': players[player_id]['player_name']
            }, room=game_id)
            
            # إزالة اللاعب من اللعبة
            del games[game_id]['players'][player_id]
            del players[player_id]
            
            # إذا لم يعد هناك لاعبين، إزالة اللعبة
            if not games[game_id]['players']:
                del games[game_id]

@socketio.on('createGame')
def handle_create_game(data):
    player_id = request.sid
    game_id = str(random.randint(100000, 999999))
    
    # إنشاء لعبة جديدة
    games[game_id] = {
        'players': {},
        'cities': {},
        'resources': {},
        'units': {},
        'battles': {}
    }
    
    # إضافة اللاعب إلى اللعبة
    games[game_id]['players'][player_id] = {
        'country': '',
        'resources': {
            'gold': 1500,
            'oil': 800,
            'equip': 3500,
            'steel': 500
        }
    }
    
    players[player_id] = {
        'game_id': game_id,
        'player_name': '',
        'player_country': ''
    }
    
    # إرسال تأكيد إنشاء اللعبة
    emit('gameCreated', {'gameId': game_id}, room=player_id)

@socketio.on('joinGame')
def handle_join_game(data):
    player_id = request.sid
    game_id = data['game_id']
    
    if game_id not in games:
        emit('gameError', {'message': 'Game not found'}, room=player_id)
        return
    
    # إضافة اللاعب إلى اللعبة
    games[game_id]['players'][player_id] = {
        'country': '',
        'resources': {
            'gold': 1500,
            'oil': 800,
            'equip': 3500,
            'steel': 500
        }
    }
    
    players[player_id] = {
        'game_id': game_id,
        'player_name': '',
        'player_country': ''
    }
    
    # إعلام اللاعبين الآخرين بانضمام لاعب جديد
    emit('playerJoined', {
        'playerId': player_id,
        'playerName': players[player_id]['player_name']
    }, room=game_id)
    
    # إرسال تأكيد الانضمام إلى اللعبة
    emit('gameJoined', {'gameId': game_id}, room=player_id)

@socketio.on('playerReady')
def handle_player_ready(data):
    player_id = request.sid
    game_id = data['game_id']
    
    if player_id not in players or game_id not in games:
        return
    
    # تحديث معلومات اللاعب
    players[player_id]['player_name'] = data['player_name']
    players[player_id]['player_country'] = data['player_country']
    games[game_id]['players'][player_id]['country'] = data['player_country']
    
    # إعلام اللاعبين الآخرين
    emit('playerReady', {
        'playerId': player_id,
        'playerName': data['player_name'],
        'playerCountry': data['player_country']
    }, room=game_id)

@socketio.on('moveUnit')
def handle_move_unit(data):
    player_id = request.sid
    game_id = data['game_id']
    
    if player_id not in players or game_id not in games:
        return
    
    # إرسال حركة الوحدة إلى جميع اللاعبين
    emit('unitMoved', {
        'playerId': player_id,
        'unitId': data['unit_id'],
        'targetX': data['target_x'],
        'targetY': data['target_y']
    }, room=game_id)

@socketio.on('startBattle')
def handle_start_battle(data):
    game_id = data['game_id']
    city_id = data['city_id']
    
    if game_id not in games:
        return
    
    # بدء المعركة
    games[game_id]['battles'][city_id] = {
        'attacker_id': data['attacker_id'],
        'attacker_power': data['attacker_power'],
        'defender_power': data['defender_power'],
        'start_time': time.time()
    }
    
    # إعلام جميع اللاعبين ببدء المعركة
    emit('battleStarted', {
        'cityId': city_id,
        'attackerId': data['attacker_id']
    }, room=game_id)

@socketio.on('endBattle')
def handle_end_battle(data):
    game_id = data['game_id']
    city_id = data['city_id']
    
    if game_id not in games or city_id not in games[game_id]['battles']:
        return
    
    # إنهاء المعركة
    battle = games[game_id]['battles'][city_id]
    winner_id = data['winner_id']
    
    # إعلام جميع اللاعبين بنهاية المعركة
    emit('battleEnded', {
        'cityId': city_id,
        'winnerId': winner_id
    }, room=game_id)
    
    # إذا كان هناك فائز، تحديث ملكية المدينة
    if winner_id:
        emit('cityCaptured', {
            'cityId': city_id,
            'playerId': winner_id
        }, room=game_id)
    
    # إزالة المعركة من السجلات
    del games[game_id]['battles'][city_id]

@socketio.on('sendMessage')
def handle_send_message(data):
    game_id = data['game_id']
    recipient = data['recipient']
    
    if game_id not in games:
        return
    
    # إرسال الرسالة إلى اللاعب المستهدف
    for player_id, player_data in games[game_id]['players'].items():
        if player_data['country'] == recipient:
            emit('messageReceived', {
                'type': data['type'],
                'content': f"{data['sender_name']}: {data['content']}"
            }, room=player_id)
            break

@socketio.on('updateResources')
def handle_update_resources(data):
    player_id = request.sid
    game_id = data['game_id']
    
    if player_id not in players or game_id not in games:
        return
    
    # تحديث موارد اللاعب
    games[game_id]['players'][player_id]['resources'] = data['resources']
    
    # إرسال التحديث إلى اللاعب
    emit('resourcesUpdated', {
        'playerId': player_id,
        'resources': data['resources']
    }, room=player_id)

@socketio.on('gameOver')
def handle_game_over(data):
    game_id = data['game_id']
    
    if game_id not in games:
        return
    
    # إعلام جميع اللاعبين بنهاية اللعبة
    emit('gameOver', {
        'winnerId': data['winner_id']
    }, room=game_id)
    
    # إزالة اللعبة
    for player_id in list(games[game_id]['players'].keys()):
        if player_id in players:
            del players[player_id]
    del games[game_id]

if __name__ == '__main__':
    socketio.run(app, debug=True)
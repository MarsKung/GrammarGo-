import random
import uuid
from flask import request, session
from flask_socketio import emit, join_room, leave_room
from . import socketio
from .game_logic import games, create_new_game_state, get_random_question, CHANCE_CARDS, DESTINY_CARDS
from .llm_client import validate_grammar

def broadcast_game_state(room_id):
    """廣播指定房間的、可被 JSON 序列化的遊戲狀態。"""
    if room_id in games:
        game_state = games[room_id]
        # 建立一個可傳送的狀態複本
        state_to_send = {
            'players': game_state['players'],
            'player_order': game_state['player_order'],
            'turn_index': game_state['turn_index'],
            'board_size': game_state['board_size'],
            'status': game_state['status'],
            'winner': game_state['winner'],
            'used_sentences': list(game_state['used_sentences']),
            'player_sids': game_state['player_sids']
        }
        socketio.emit('update_game_state', state_to_send, to=room_id)

@socketio.on('connect')
def handle_connect():
    """處理新的客戶端連線。"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """處理客戶端離線。"""
    sid = request.sid
    room_id = session.get('room_id')
    player_id = session.get('player_id')
    print(f"Client disconnected: {sid}, was in room {room_id}")

    if room_id and player_id and room_id in games:
        game_state = games[room_id]
        # 從 sid -> player_id 的映射中移除
        if sid in game_state['player_sids']:
            del game_state['player_sids'][sid]
        
        player = game_state['players'].get(player_id)
        if player:
            player['is_connected'] = False  # 標記為離線
            leave_room(room_id)
            socketio.emit('message', {'text': f"玩家 {player['name']} 已離線。"}, to=room_id)
            broadcast_game_state(room_id)

@socketio.on('reconnect_request')
def handle_reconnect():
    """處理 F5 刷新後的重新連線請求。"""
    room_id = session.get('room_id')
    player_id = session.get('player_id')
    sid = request.sid

    if not (room_id and player_id and room_id in games):
        emit('reconnect_failed')
        return

    game_state = games[room_id]
    player = game_state['players'].get(player_id)
    
    if player:
        join_room(room_id)
        player['sid'] = sid  # 更新為新的 sid
        player['is_connected'] = True
        game_state['player_sids'][sid] = player_id  # 更新 sid -> player_id 的映射
        
        socketio.emit('message', {'text': f"玩家 {player['name']} 已重新連線！"}, to=room_id)
        broadcast_game_state(room_id)
    else:
        emit('reconnect_failed')

@socketio.on('join_game')
def handle_join_game(data):
    """處理新玩家加入指定房間。"""
    room_id = data.get('room_id')
    player_name = data.get('name', '匿名玩家')
    sid = request.sid
    
    if not room_id: return

    if room_id not in games:
        games[room_id] = create_new_game_state()
    
    game_state = games[room_id]

    if len(game_state['players']) >= 4:
        emit('error', {'message': '這個房間已經滿了！'})
        return
        
    player_id = str(uuid.uuid4())
    session['player_id'] = player_id
    session['room_id'] = room_id

    join_room(room_id)
    
    game_state['players'][player_id] = {
        'id': player_id, 'name': player_name, 'position': 0,
        'color': f'hsl({hash(player_id) % 360}, 80%, 60%)',
        'sid': sid, 'is_connected': True
    }
    game_state['player_order'].append(player_id)
    game_state['player_sids'][sid] = player_id

    socketio.emit('message', {'text': f'歡迎玩家 {player_name} 加入房間 {room_id}！'}, to=room_id)

    if len(game_state['players']) >= 2 and game_state['status'] == 'waiting':
        game_state['status'] = 'playing'
        game_state['used_sentences'].clear()
        socketio.emit('message', {'text': '遊戲開始！'}, to=room_id)
    
    broadcast_game_state(room_id)

@socketio.on('roll_dice')
def handle_roll_dice(data):
    room_id = data.get('room_id')
    sid = request.sid
    if not (room_id and room_id in games): return
    
    game_state = games[room_id]
    player_id = game_state['player_sids'].get(sid)

    if not player_id or game_state['status'] != 'playing' or player_id != game_state['player_order'][game_state['turn_index']]:
        return

    roll = random.randint(1, 6)
    player = game_state['players'][player_id]
    player['last_roll_origin'] = player['position']
    player['position'] += roll
    socketio.emit('message', {'text': f"{player['name']} 擲出了 {roll} 點，準備移動..."}, to=room_id)

    if player['position'] >= game_state['board_size']:
        player['position'] = game_state['board_size']
        game_state['status'] = 'finished'
        game_state['winner'] = player['name']
        broadcast_game_state(room_id)
        return

    new_pos = player['position']
    if new_pos > 0 and new_pos % 5 == 0:
        emit('show_chance_destiny')
    else:
        question = get_random_question()
        emit('show_question', question)

@socketio.on('chose_chance_destiny')
def handle_chance_destiny_choice(data):
    room_id = data.get('room_id')
    sid = request.sid
    if not (room_id and room_id in games): return
    
    game_state = games[room_id]
    player_id = game_state['player_sids'].get(sid)
    if not player_id: return
    
    player = game_state['players'][player_id]
    choice = data.get('choice')
    card = None

    if choice == 'chance':
        card = random.choice(CHANCE_CARDS)
        socketio.emit('message', {'text': f" ✨ {player['name']} 抽到機會卡：『{card['text']}』"}, to=room_id)
    elif choice == 'destiny':
        card = random.choice(DESTINY_CARDS)
        socketio.emit('message', {'text': f" 💣 {player['name']} 抽到命運卡：『{card['text']}』"}, to=room_id)

    if card:
        card_type = card.get('type')
        if card_type == 'move_relative': player['position'] += card['value']
        elif card_type == 'move_absolute': player['position'] = card['value']
        elif card_type == 'swap_position_leader':
            leader, max_pos = None, -1
            for p_id in game_state['player_order']:
                if p_id != player_id and game_state['players'][p_id]['position'] > max_pos:
                    max_pos, leader = game_state['players'][p_id]['position'], game_state['players'][p_id]
            if leader:
                player['position'], leader['position'] = leader['position'], player['position']
                socketio.emit('message', {'text': f"🌀 天翻地覆！{player['name']} 和 {leader['name']} 交換了位置！"}, to=room_id)
            else:
                socketio.emit('message', {'text': f"🤔 {player['name']} 環顧四周，發現自己就是領先者，什麼也沒發生。"}, to=room_id)
        player['position'] = max(0, min(game_state['board_size'], player['position']))

    if len(game_state['player_order']) > 0:
        game_state['turn_index'] = (game_state['turn_index'] + 1) % len(game_state['player_order'])
    broadcast_game_state(room_id)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    room_id = data.get('room_id')
    sid = request.sid
    if not (room_id and room_id in games): return

    game_state = games[room_id]
    player_id = game_state['player_sids'].get(sid)
    if not player_id: return

    answer, rule = data.get('answer', ''), data.get('rule', '')
    if not rule:
        emit('show_result', {'correct': False, 'explanation': '錯誤：提交答案時遺失了問題規則。'})
        return

    normalized_sentence = answer.strip().lower()
    if normalized_sentence in game_state['used_sentences']:
        emit('show_result', {'correct': False, 'explanation': '這個句子已經被用過了，請換一個更有創意的句子！'})
        return

    player = game_state['players'][player_id]
    result_dict = validate_grammar(answer, rule)

    if result_dict.get('correct'):
        game_state['used_sentences'].add(normalized_sentence)
        emit('show_result', {'correct': True, 'explanation': result_dict['explanation']})
    else:
        emit('show_result', {'correct': False, 'explanation': result_dict.get('explanation', '發生未知錯誤')})
        player['position'] = player.get('last_roll_origin', player['position'])

    if len(game_state['player_order']) > 0:
        game_state['turn_index'] = (game_state['turn_index'] + 1) % len(game_state['player_order'])
    broadcast_game_state(room_id)
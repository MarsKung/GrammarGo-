# /GrammarGo_Pro/project/__init__.py
import string
import random
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO
from config import Config

socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    socketio.init_app(app)

    # --- 新增的路由邏輯 ---
    @app.route('/')
    def lobby():
        """顯示大廳頁面"""
        return render_template('index.html')

    @app.route('/create_room')
    def create_room():
        """建立一個新房間並跳轉"""
        room_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        # 這裡只是跳轉，房間狀態在玩家加入時才會真正建立
        return redirect(url_for('game_room', room_id=room_id))

    @app.route('/game/<room_id>')
    def game_room(room_id):
        """顯示特定房間的遊戲頁面"""
        return render_template('index.html', room_id=room_id)

    from . import events
    return app

app = create_app()
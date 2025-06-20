# /GrammarGo_Pro/project/__init__.py (最終路由修正版)

import string
import random
from flask import Flask, render_template, redirect, url_for
from flask_socketio import SocketIO
# from flask_session import Session # 我們不再使用它，可以移除
from config import Config

socketio = SocketIO()

def create_app(config_class=Config):
    """
    應用程式工廠函式
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Session(app) # 我們不再使用它，可以移除

    socketio.init_app(app)

    # --- 定義所有需要的路由 ---

    @app.route('/')
    def lobby():
        """處理首頁/大廳的請求"""
        return render_template('index.html')

    @app.route('/create_room')
    def create_room():
        """處理建立房間的請求，會生成一個隨機ID並跳轉"""
        room_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return redirect(url_for('game_room', room_id=room_id))

    @app.route('/game/<room_id>')
    def game_room(room_id):
        """處理進入特定遊戲房間的請求"""
        return render_template('index.html', room_id=room_id)

    # 在函式結尾匯入事件，避免循環依賴
    from . import events
    
    return app

# 建立 app 實例供 app.py 匯入
app = create_app()
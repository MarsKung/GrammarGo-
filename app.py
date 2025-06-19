from project import app, socketio

if __name__ == '__main__':
    # 使用 socketio.run 來啟動伺服器，以便同時支援 Flask 和 Socket.IO
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0')
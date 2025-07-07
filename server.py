import os
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    print("جارٍ التشغيل على http://127.0.0.1:5000")
    socketio.run(app, host='0.0.0.0', port=5000)

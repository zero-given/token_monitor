from flask import Flask, jsonify, g
from flask_socketio import SocketIO
from flask_cors import CORS
import sqlite3
import logging
from pair_monitor import PairMonitor
from datetime import datetime

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocketIOHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            socketio.emit('server_log', {
                'level': record.levelname.lower(),
                'message': msg,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception:
            self.handleError(record)

# Add SocketIO handler to logger
socket_handler = SocketIOHandler()
socket_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(socket_handler)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('pairs.db')
        g.db.row_factory = sqlite3.Row
    return g.db

@app.before_first_request
def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS pairs (
            address TEXT PRIMARY KEY,
            token0_address TEXT,
            token0_name TEXT,
            token0_symbol TEXT,
            token1_address TEXT,
            token1_name TEXT,
            token1_symbol TEXT,
            timestamp DATETIME,
            security_info TEXT
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/pairs')
def get_pairs():
    try:
        db = get_db()
        pairs = db.execute('SELECT * FROM pairs ORDER BY timestamp DESC').fetchall()
        return jsonify([dict(pair) for pair in pairs])
    except Exception as e:
        logger.error(f"Error fetching pairs: {str(e)}")
        return jsonify({"error": str(e)}), 500

def on_new_pair(pair_info):
    try:
        logger.info(f"New pair detected: {pair_info['token0']['symbol']}/{pair_info['token1']['symbol']}")
        socketio.emit('new_pair', pair_info)
    except Exception as e:
        logger.error(f"Error handling new pair: {str(e)}")

def on_pair_updated(pair_info):
    try:
        logger.info(f"Pair updated: {pair_info['token0']['symbol']}/{pair_info['token1']['symbol']}")
        socketio.emit('pair_updated', pair_info)
    except Exception as e:
        logger.error(f"Error handling pair update: {str(e)}")

if __name__ == '__main__':
    monitor = PairMonitor(on_new_pair=on_new_pair, on_pair_updated=on_pair_updated)
    monitor.start()
    socketio.run(app, debug=True, port=5000) 
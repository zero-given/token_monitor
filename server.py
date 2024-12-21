from flask import Flask, jsonify, g
from flask_socketio import SocketIO
from flask_cors import CORS
import sqlite3
import logging
from pair_monitor_enhanced import PairMonitor
from datetime import datetime
import asyncio
import json
import threading
import os

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
        # Use the same database as pair_monitor_enhanced
        # Get today's date for the session directory
        today = datetime.now()
        session_dir = os.path.join('monitoring_sessions', today.strftime('%b%d').lower())
        
        # Find the latest session
        if os.path.exists(session_dir):
            sessions = [d for d in os.listdir(session_dir) if d.startswith('session')]
            if sessions:
                latest_session = max(sessions, key=lambda x: int(x.replace('session', '')))
                db_path = os.path.join(session_dir, latest_session, 'pairs.db')
                if os.path.exists(db_path):
                    g.db = sqlite3.connect(db_path, check_same_thread=False)
                    g.db.row_factory = sqlite3.Row
                    return g.db
        
        # Fallback to default database if session database not found
        g.db = sqlite3.connect('pairs.db', check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT UNIQUE,
            block_number INTEGER,
            transaction_hash TEXT,
            pair_name TEXT,
            pair_symbol TEXT,
            pair_eth_balance TEXT,
            
            token0_address TEXT,
            token0_name TEXT,
            token0_symbol TEXT,
            token0_decimals INTEGER,
            token0_total_supply TEXT,
            token0_eth_balance TEXT,
            token0_verified INTEGER,
            token0_security_info TEXT,
            
            token1_address TEXT,
            token1_name TEXT,
            token1_symbol TEXT,
            token1_decimals INTEGER,
            token1_total_supply TEXT,
            token1_eth_balance TEXT,
            token1_verified INTEGER,
            token1_security_info TEXT,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            security_info TEXT
        )
    ''')
    db.commit()

def init_app(app):
    with app.app_context():
        init_db()

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

@app.route('/pairs')
def get_pairs():
    try:
        db = get_db()
        # Try the new schema with security info
        try:
            pairs = db.execute('''
                SELECT 
                    p.id,
                    p.pair_address,
                    p.block_number,
                    p.transaction_hash,
                    p.pair_name,
                    p.pair_symbol,
                    
                    p.token0_address,
                    p.token0_name,
                    p.token0_symbol,
                    p.token0_decimals,
                    p.token0_total_supply,
                    p.token0_eth_balance,
                    p.token0_verified,
                    
                    p.token1_address,
                    p.token1_name,
                    p.token1_symbol,
                    p.token1_decimals,
                    p.token1_total_supply,
                    p.token1_eth_balance,
                    p.token1_verified,
                    
                    p.created_at,
                    
                    -- Token0 Security Info
                    t0s.hp_is_honeypot as token0_is_honeypot,
                    t0s.hp_honeypot_reason as token0_honeypot_reason,
                    t0s.hp_buy_tax as token0_buy_tax,
                    t0s.hp_sell_tax as token0_sell_tax,
                    t0s.hp_is_open_source as token0_is_open_source,
                    t0s.gp_holder_count as token0_holder_count,
                    t0s.gp_is_mintable as token0_is_mintable,
                    t0s.gp_owner_address as token0_owner_address,
                    t0s.gp_creator_address as token0_creator_address,
                    
                    -- Token1 Security Info
                    t1s.hp_is_honeypot as token1_is_honeypot,
                    t1s.hp_honeypot_reason as token1_honeypot_reason,
                    t1s.hp_buy_tax as token1_buy_tax,
                    t1s.hp_sell_tax as token1_sell_tax,
                    t1s.hp_is_open_source as token1_is_open_source,
                    t1s.gp_holder_count as token1_holder_count,
                    t1s.gp_is_mintable as token1_is_mintable,
                    t1s.gp_owner_address as token1_owner_address,
                    t1s.gp_creator_address as token1_creator_address,
                    
                    -- Raw Security Data
                    t0s.hp_raw_data as token0_hp_raw_data,
                    t0s.gp_raw_data as token0_gp_raw_data,
                    t1s.hp_raw_data as token1_hp_raw_data,
                    t1s.gp_raw_data as token1_gp_raw_data
                    
                FROM pairs p
                LEFT JOIN security_checks t0s ON p.token0_address = t0s.token_address
                LEFT JOIN security_checks t1s ON p.token1_address = t1s.token_address
                ORDER BY p.created_at DESC
            ''').fetchall()
        except sqlite3.OperationalError as e:
            logger.error(f"Database query error: {str(e)}")
            # If that fails, try without security info
            pairs = db.execute('SELECT * FROM pairs ORDER BY created_at DESC').fetchall()
        
        # Convert to list of dicts and process security info
        result = []
        for pair in pairs:
            pair_dict = dict(pair)
            
            # Add timestamp for compatibility
            if 'created_at' in pair_dict:
                pair_dict['timestamp'] = pair_dict['created_at']
            
            # Process token0 security info
            token0_security = {
                'is_honeypot': pair_dict.get('token0_is_honeypot'),
                'honeypot_reason': pair_dict.get('token0_honeypot_reason'),
                'buy_tax': pair_dict.get('token0_buy_tax'),
                'sell_tax': pair_dict.get('token0_sell_tax'),
                'is_open_source': pair_dict.get('token0_is_open_source'),
                'holder_count': pair_dict.get('token0_holder_count'),
                'is_mintable': pair_dict.get('token0_is_mintable'),
                'owner_address': pair_dict.get('token0_owner_address'),
                'creator_address': pair_dict.get('token0_creator_address'),
            }
            
            # Process token1 security info
            token1_security = {
                'is_honeypot': pair_dict.get('token1_is_honeypot'),
                'honeypot_reason': pair_dict.get('token1_honeypot_reason'),
                'buy_tax': pair_dict.get('token1_buy_tax'),
                'sell_tax': pair_dict.get('token1_sell_tax'),
                'is_open_source': pair_dict.get('token1_is_open_source'),
                'holder_count': pair_dict.get('token1_holder_count'),
                'is_mintable': pair_dict.get('token1_is_mintable'),
                'owner_address': pair_dict.get('token1_owner_address'),
                'creator_address': pair_dict.get('token1_creator_address'),
            }
            
            # Add raw security data if available
            if pair_dict.get('token0_hp_raw_data'):
                try:
                    token0_security['honeypot_details'] = json.loads(pair_dict['token0_hp_raw_data'])
                except:
                    pass
            if pair_dict.get('token0_gp_raw_data'):
                try:
                    token0_security['goplus_details'] = json.loads(pair_dict['token0_gp_raw_data'])
                except:
                    pass
                    
            if pair_dict.get('token1_hp_raw_data'):
                try:
                    token1_security['honeypot_details'] = json.loads(pair_dict['token1_hp_raw_data'])
                except:
                    pass
            if pair_dict.get('token1_gp_raw_data'):
                try:
                    token1_security['goplus_details'] = json.loads(pair_dict['token1_gp_raw_data'])
                except:
                    pass
            
            # Add security info to result
            pair_dict['token0_security_info'] = token0_security
            pair_dict['token1_security_info'] = token1_security
            
            # Remove raw data fields from final output
            for key in list(pair_dict.keys()):
                if key.endswith('_raw_data') or key.startswith('token0_is_') or key.startswith('token1_is_') or \
                   key.startswith('token0_hp_') or key.startswith('token1_hp_') or \
                   key.startswith('token0_gp_') or key.startswith('token1_gp_'):
                    del pair_dict[key]
            
            result.append(pair_dict)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error fetching pairs: {str(e)}")
        return jsonify({"error": str(e)}), 500

def convert_to_json_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.hex()
    return str(obj)

def get_background_db():
    # Use the same database path logic as get_db
    # Get today's date for the session directory
    today = datetime.now()
    session_dir = os.path.join('monitoring_sessions', today.strftime('%b%d').lower())
    
    # Find the latest session
    if os.path.exists(session_dir):
        sessions = [d for d in os.listdir(session_dir) if d.startswith('session')]
        if sessions:
            latest_session = max(sessions, key=lambda x: int(x.replace('session', '')))
            db_path = os.path.join(session_dir, latest_session, 'pairs.db')
            if os.path.exists(db_path):
                return sqlite3.connect(db_path, check_same_thread=False)
    
    # Fallback to default database if session database not found
    return sqlite3.connect('pairs.db', check_same_thread=False)

def on_new_pair(pair_info):
    try:
        logger.info(f"New pair detected: {pair_info['token0']['symbol']}/{pair_info['token1']['symbol']}")
        logger.info(f"Full pair info: {json.dumps(pair_info, indent=2, default=str)}")  # Debug log
        
        db = get_background_db()
        try:
            # Extract security info
            token0_security = json.dumps(pair_info.get('token0', {}).get('security_info', {}))
            token1_security = json.dumps(pair_info.get('token1', {}).get('security_info', {}))
            
            # Debug logs for security info
            logger.info(f"Token0 security info: {token0_security}")
            logger.info(f"Token1 security info: {token1_security}")
            
            db.execute('''
                INSERT OR REPLACE INTO pairs (
                    address,
                    block_number,
                    transaction_hash,
                    pair_name,
                    pair_symbol,
                    pair_eth_balance,
                    
                    token0_address,
                    token0_name,
                    token0_symbol,
                    token0_decimals,
                    token0_total_supply,
                    token0_eth_balance,
                    token0_verified,
                    token0_security_info,
                    
                    token1_address,
                    token1_name,
                    token1_symbol,
                    token1_decimals,
                    token1_total_supply,
                    token1_eth_balance,
                    token1_verified,
                    token1_security_info,
                    
                    created_at,
                    security_info
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ''', (
                pair_info['address'],
                pair_info.get('block_number'),
                pair_info.get('transaction_hash'),
                pair_info.get('name', 'Uniswap V2'),
                pair_info.get('symbol', 'UNI-V2'),
                pair_info.get('eth_balance', '0.0000 ETH'),
                
                pair_info['token0']['address'],
                pair_info['token0']['name'],
                pair_info['token0']['symbol'],
                pair_info['token0'].get('decimals', 18),
                str(pair_info['token0'].get('total_supply', '0')),
                pair_info['token0'].get('eth_balance', '0.0000 ETH'),
                1 if pair_info['token0'].get('verified', False) else 0,
                token0_security,
                
                pair_info['token1']['address'],
                pair_info['token1']['name'],
                pair_info['token1']['symbol'],
                pair_info['token1'].get('decimals', 18),
                str(pair_info['token1'].get('total_supply', '0')),
                pair_info['token1'].get('eth_balance', '0.0000 ETH'),
                1 if pair_info['token1'].get('verified', False) else 0,
                token1_security,
                
                json.dumps(pair_info.get('security_info', {}))
            ))
            db.commit()
            logger.info(f"Successfully saved new pair to database: {pair_info['address']}")
        finally:
            db.close()
        
        serialized_pair = json.loads(json.dumps(pair_info, default=convert_to_json_serializable))
        socketio.emit('new_pair', serialized_pair)
        logger.info(f"Successfully emitted new pair: {pair_info['address']}")
    except Exception as e:
        logger.error(f"Error handling new pair: {str(e)}")
        logger.error(f"Error details: {str(e.__class__.__name__)}: {str(e)}")  # More detailed error
        raise

def on_pair_updated(pair_info):
    try:
        logger.info(f"Pair updated: {pair_info['token0']['symbol']}/{pair_info['token1']['symbol']}")
        
        db = get_background_db()
        try:
            db.execute('''
                UPDATE pairs SET 
                    token0_name = ?, token0_symbol = ?,
                    token1_name = ?, token1_symbol = ?,
                    security_info = ?
                WHERE address = ?
            ''', (
                pair_info['token0']['name'], pair_info['token0']['symbol'],
                pair_info['token1']['name'], pair_info['token1']['symbol'],
                json.dumps(pair_info.get('security_info', {})),
                pair_info['address']
            ))
            db.commit()
            logger.info(f"Successfully updated pair in database: {pair_info['address']}")
        finally:
            db.close()
        
        serialized_pair = json.loads(json.dumps(pair_info, default=convert_to_json_serializable))
        socketio.emit('pair_updated', serialized_pair)
        logger.info(f"Successfully emitted pair update: {pair_info['address']}")
    except Exception as e:
        logger.error(f"Error handling pair update: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        logger.info("Initializing application...")
        
        # Initialize the database
        logger.info("Setting up database...")
        init_app(app)
        logger.info("Database setup complete")
        
        logger.info("Initializing PairMonitor...")
        monitor = PairMonitor(
            on_new_pair=on_new_pair,
            on_pair_updated=on_pair_updated
        )
        logger.info("PairMonitor initialized")
        
        async def start_monitor():
            logger.info("Starting monitor...")
            await monitor.start()
        
        # Create event loop
        logger.info("Setting up event loop...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start monitor in background thread
        def run_async_monitor():
            loop.run_until_complete(start_monitor())
            
        monitor_thread = threading.Thread(target=run_async_monitor)
        monitor_thread.daemon = True  # This ensures the thread exits when the main program exits
        logger.info("Starting monitor thread...")
        monitor_thread.start()
        
        try:
            # Run Flask server without debug mode
            logger.info("Starting Flask server...")
            socketio.run(app, debug=False, port=5001, use_reloader=False, allow_unsafe_werkzeug=True)
        except OSError as e:
            if e.errno == 10048:  # Port already in use
                logger.error("Port 5001 is already in use. Please make sure no other instance is running.")
                raise SystemExit(1)
            raise e
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            # Clean up
            logger.info("Cleaning up...")
            if loop.is_running():
                loop.stop()
            loop.close()
            logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Fatal error during startup: {str(e)}")
        raise 
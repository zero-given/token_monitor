from web3 import Web3
from dotenv import load_dotenv
import os
import json
import time
import aiohttp
import asyncio
import sqlite3
from datetime import datetime
from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import logging
import shutil  # For directory operations
import requests

# Initialize Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variables
load_dotenv()

# Global variables for database
SESSIONS_ROOT = "monitoring_sessions"
current_session = None
db_path = None

def get_session_path():
    """Create and get path for current monitoring session"""
    global current_session, db_path
    
    # Create base directory if it doesn't exist
    if not os.path.exists(SESSIONS_ROOT):
        os.makedirs(SESSIONS_ROOT)
    
    # Create dated folder
    date_str = datetime.now().strftime("%b%d").lower()
    date_folder = os.path.join(SESSIONS_ROOT, date_str)
    if not os.path.exists(date_folder):
        os.makedirs(date_folder)
    
    # Find next session number
    session_num = 1
    while os.path.exists(os.path.join(date_folder, f"session{session_num}")):
        session_num += 1
    
    # Create session folder
    current_session = os.path.join(date_folder, f"session{session_num}")
    os.makedirs(current_session)
    
    # Set database path
    db_path = os.path.join(current_session, "pairs.db")
    
    return db_path

def init_database():
    """Initialize SQLite database with session management"""
    try:
        # Get session-specific database path
        db_file = get_session_path()
        
        # Create session info file
        session_info = {
            "start_time": datetime.now().isoformat(),
            "database": db_file,
            "infura_network": os.getenv('INFURA_NETWORK'),
            "factory_address": UNISWAP_V2_FACTORY
        }
        
        with open(os.path.join(current_session, "session_info.json"), "w") as f:
            json.dump(session_info, f, indent=2)
        
        log_message(f"Session started in: {current_session}", "INFO")
        
        # Initialize database
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        
        # Create pairs table
        c.execute('''
            CREATE TABLE IF NOT EXISTS pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                block_number INTEGER,
                transaction_hash TEXT,
                pair_address TEXT UNIQUE,
                pair_name TEXT,
                pair_symbol TEXT,
                token0_address TEXT,
                token0_name TEXT,
                token0_symbol TEXT,
                token0_decimals INTEGER,
                token0_total_supply TEXT,
                token0_eth_balance TEXT,
                token0_verified BOOLEAN,
                token1_address TEXT,
                token1_name TEXT,
                token1_symbol TEXT,
                token1_decimals INTEGER,
                token1_total_supply TEXT,
                token1_eth_balance TEXT,
                token1_verified BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create security_checks table
        c.execute('''
            CREATE TABLE IF NOT EXISTS security_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_address TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Honeypot API Data
                hp_is_honeypot BOOLEAN,
                hp_honeypot_reason TEXT,
                hp_buy_tax REAL,
                hp_sell_tax REAL,
                hp_transfer_tax REAL,
                hp_max_buy_amount TEXT,
                hp_max_sell_amount TEXT,
                hp_buy_gas REAL,
                hp_sell_gas REAL,
                hp_is_open_source BOOLEAN,
                hp_is_proxy BOOLEAN,
                hp_is_blacklisted BOOLEAN,
                hp_is_whitelisted BOOLEAN,
                hp_is_anti_whale BOOLEAN,
                hp_is_trading_cooldown BOOLEAN,
                hp_is_personal_slippage_modifiable BOOLEAN,
                hp_has_hidden_owner BOOLEAN,
                hp_can_take_ownership BOOLEAN,
                hp_has_mint_function BOOLEAN,
                hp_simulation_success BOOLEAN,
                hp_simulation_error TEXT,
                hp_raw_data TEXT,  -- Store complete JSON response
                
                -- GoPlus API Data
                gp_buy_tax REAL,
                gp_sell_tax REAL,
                gp_is_mintable BOOLEAN,
                gp_is_proxy BOOLEAN,
                gp_is_open_source BOOLEAN,
                gp_can_take_back_ownership BOOLEAN,
                gp_owner_address TEXT,
                gp_creator_address TEXT,
                gp_holder_count INTEGER,
                gp_total_supply TEXT,
                gp_token_name TEXT,
                gp_token_symbol TEXT,
                gp_lp_holder_count INTEGER,
                gp_lp_total_supply TEXT,
                gp_is_in_dex BOOLEAN,
                gp_is_anti_whale BOOLEAN,
                gp_is_blacklisted BOOLEAN,
                gp_is_whitelisted BOOLEAN,
                gp_is_trading_cooldown BOOLEAN,
                gp_trust_list TEXT,
                gp_dex TEXT,
                gp_potential_risks TEXT,
                gp_raw_data TEXT,  -- Store complete JSON response
                
                api_errors TEXT,
                UNIQUE(token_address, checked_at)
            )
        ''')
        
        # Create session_stats table
        c.execute('''
            CREATE TABLE IF NOT EXISTS session_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pairs_found INTEGER DEFAULT 0,
                honeypots_found INTEGER DEFAULT 0,
                high_risk_pairs INTEGER DEFAULT 0,
                api_errors INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        log_message("✅ Database initialized successfully", "SUCCESS")
        return True
    except sqlite3.Error as e:
        log_message(f"❌ Database error: {str(e)}", "ERROR")
        return False
    except Exception as e:
        log_message(f"❌ Error initializing database: {str(e)}", "ERROR")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def update_session_stats(stats_update):
    """Update session statistics"""
    global db_path
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Get current stats
        c.execute('SELECT * FROM session_stats ORDER BY id DESC LIMIT 1')
        current_stats = c.fetchone()
        
        if current_stats:
            # Update existing stats
            new_stats = {
                'pairs_found': current_stats[2] + stats_update.get('pairs_found', 0),
                'honeypots_found': current_stats[3] + stats_update.get('honeypots_found', 0),
                'high_risk_pairs': current_stats[4] + stats_update.get('high_risk_pairs', 0),
                'api_errors': current_stats[5] + stats_update.get('api_errors', 0)
            }
        else:
            # Insert new stats
            new_stats = {
                'pairs_found': stats_update.get('pairs_found', 0),
                'honeypots_found': stats_update.get('honeypots_found', 0),
                'high_risk_pairs': stats_update.get('high_risk_pairs', 0),
                'api_errors': stats_update.get('api_errors', 0)
            }
        
        c.execute('''
            INSERT INTO session_stats 
            (pairs_found, honeypots_found, high_risk_pairs, api_errors)
            VALUES (?, ?, ?, ?)
        ''', (
            new_stats['pairs_found'],
            new_stats['honeypots_found'],
            new_stats['high_risk_pairs'],
            new_stats['api_errors']
        ))
        
        conn.commit()
        log_message(f"Updated session stats", "SUCCESS")
    except Exception as e:
        log_message(f"Error updating session stats: {str(e)}", "ERROR")
    finally:
        if 'conn' in locals():
            conn.close()

# Uniswap V2 Factory address
UNISWAP_V2_FACTORY = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'

# Initialize Web3
infura_url = f"https://{os.getenv('INFURA_NETWORK')}.infura.io/v3/{os.getenv('INFURA_API_KEY')}"
w3 = Web3(Web3.HTTPProvider(infura_url))

# Factory ABI - only including what we need
FACTORY_ABI = '''[
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},
    {"indexed":true,"internalType":"address","name":"token1","type":"address"},
    {"indexed":false,"internalType":"address","name":"pair","type":"address"},
    {"indexed":false,"internalType":"uint256","name":null,"type":"uint256"}],
    "name":"PairCreated","type":"event"}
]'''

# ERC20 ABI - only including what we need
ERC20_ABI = '''[
    {"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},
    {"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}
]'''

logger = logging.getLogger(__name__)

class PairMonitor:
    def __init__(self, on_new_pair=None, on_pair_updated=None):
        self.on_new_pair = on_new_pair
        self.on_pair_updated = on_pair_updated
        self.known_pairs = {}
        logger.info("PairMonitor initialized")

    async def start(self):
        try:
            logger.info("Starting PairMonitor")
            self._setup_web3()
            self._setup_factory()
            await self._start_monitoring()
        except Exception as e:
            logger.error(f"Error starting PairMonitor: {str(e)}")
            raise

    def _setup_web3(self):
        try:
            logger.info(f"Connecting to Ethereum network via Infura")
            self.w3 = Web3(Web3.HTTPProvider(infura_url))
            if not self.w3.is_connected():
                raise ConnectionError("Failed to connect to Ethereum network")
            logger.info("Successfully connected to Ethereum network")
        except Exception as e:
            logger.error(f"Failed to connect to Ethereum network: {str(e)}")
            raise

    def _setup_factory(self):
        try:
            logger.info("Setting up Uniswap V2 Factory contract")
            self.factory_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(UNISWAP_V2_FACTORY),
                abi=json.loads(FACTORY_ABI)
            )
            logger.info("Successfully set up Uniswap V2 Factory contract")
        except Exception as e:
            logger.error(f"Failed to set up factory contract: {str(e)}")
            raise

    async def _start_monitoring(self):
        try:
            logger.info("Starting pair monitoring")
            await self.monitor_pairs()
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
            raise

    async def monitor_pairs(self):
        """Monitor for new pairs and check existing ones"""
        while True:
            try:
                logger.info("ℹ️ Starting periodic rescan of existing pairs")
                for pair_address in list(self.known_pairs.keys()):
                    logger.info(f"ℹ️ Checking pair {pair_address}")
                    await self.check_pair_security(pair_address)
                logger.info("✅ Completed periodic rescan")
            except Exception as e:
                logger.error(f"❌ Error: {str(e)}")
            await asyncio.sleep(180)  # Sleep for 3 minutes

    async def check_pair_security(self, pair_address: str):
        """Check security details for a trading pair"""
        try:
            # Check token0
            token0_address = self.known_pairs[pair_address]["token0"]["address"]
            logger.info(f"ℹ️ Checking Honeypot API for {token0_address}")
            honeypot_result = await check_honeypot(token0_address)
            
            if not honeypot_result:
                logger.warning("⚠️ Invalid response format, retrying...")
                honeypot_result = await check_honeypot(token0_address)
            
            logger.info("✅ Honeypot check completed successfully")
            
            logger.info(f"ℹ️ Checking GoPlus API for {token0_address}")
            goplus_result = await check_goplus(token0_address)
            
            if not goplus_result:
                logger.warning("⚠️ Invalid response format, retrying...")
                goplus_result = await check_goplus(token0_address)
            
            logger.info("✅ GoPlus check completed successfully")

            # Check token1
            token1_address = self.known_pairs[pair_address]["token1"]["address"]
            logger.info(f"ℹ️ Checking Honeypot API for {token1_address}")
            honeypot_result1 = await check_honeypot(token1_address)
            
            if not honeypot_result1:
                logger.warning("⚠️ Invalid response format, retrying...")
                honeypot_result1 = await check_honeypot(token1_address)
            
            logger.info("✅ Honeypot check completed successfully")
            
            logger.info(f"ℹ️ Checking GoPlus API for {token1_address}")
            goplus_result1 = await check_goplus(token1_address)
            
            if not goplus_result1:
                logger.warning("⚠️ Invalid response format, retrying...")
                goplus_result1 = await check_goplus(token1_address)
            
            logger.info("✅ GoPlus check completed successfully")

            # Update security info
            self.known_pairs[pair_address]["securityChecks"] = {
                "token0": {
                    "honeypot": honeypot_result,
                    "goplus": goplus_result
                },
                "token1": {
                    "honeypot": honeypot_result1,
                    "goplus": goplus_result1
                }
            }
            
            logger.info(f"✅ Updated security info for pair {token0_address}/{token1_address}")
            
            if self.on_pair_updated:
                self.on_pair_updated(self.known_pairs[pair_address])
                
        except Exception as e:
            logger.error(f"❌ Error checking pair security: {str(e)}")

    async def handle_new_pair(self, pair_address: str):
        """Handle new pair creation"""
        try:
            logger.info(f"ℹ️ Fetching token info for {pair_address}")
            
            # Get pair contract
            pair_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(pair_address),
                abi=PAIR_ABI
            )
            
            # Get token addresses
            token0_address = await pair_contract.functions.token0().call()
            token1_address = await pair_contract.functions.token1().call()
            
            # Get token contracts
            token0_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token0_address),
                abi=TOKEN_ABI
            )
            token1_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(token1_address),
                abi=TOKEN_ABI
            )
            
            # Get token details
            try:
                token0_name = await token0_contract.functions.name().call()
                token0_symbol = await token0_contract.functions.symbol().call()
                token0_decimals = await token0_contract.functions.decimals().call()
                try:
                    token0_supply = await token0_contract.functions.totalSupply().call()
                except Exception as e:
                    logger.warning(f"⚠️ Error reading total supply: {str(e)}")
                    token0_supply = None
            except Exception as e:
                logger.error(f"❌ Error reading token0 info: {str(e)}")
                token0_name = "Unknown"
                token0_symbol = "???"
                token0_decimals = 18
                token0_supply = None
                
            try:
                token1_name = await token1_contract.functions.name().call()
                token1_symbol = await token1_contract.functions.symbol().call()
                token1_decimals = await token1_contract.functions.decimals().call()
                try:
                    token1_supply = await token1_contract.functions.totalSupply().call()
                except Exception as e:
                    logger.warning(f"⚠️ Error reading total supply: {str(e)}")
                    token1_supply = None
            except Exception as e:
                logger.error(f"❌ Error reading token1 info: {str(e)}")
                token1_name = "Unknown"
                token1_symbol = "???"
                token1_decimals = 18
                token1_supply = None

            # Store pair info
            pair_info = {
                "address": pair_address,
                "token0": {
                    "address": token0_address,
                    "name": token0_name,
                    "symbol": token0_symbol,
                    "decimals": token0_decimals,
                    "totalSupply": token0_supply
                },
                "token1": {
                    "address": token1_address,
                    "name": token1_name,
                    "symbol": token1_symbol,
                    "decimals": token1_decimals,
                    "totalSupply": token1_supply
                },
                "timestamp": datetime.now().isoformat()
            }
            
            self.known_pairs[pair_address] = pair_info
            
            # Check security
            await self.check_pair_security(pair_address)
            
            if self.on_new_pair:
                self.on_new_pair(pair_info)
                
            logger.info(f"✅ Successfully processed new pair {pair_address}")
            
        except Exception as e:
            logger.error(f"❌ Error handling new pair: {str(e)}")

    def _check_pair(self, pair_address):
        try:
            logger.info(f"Checking pair {pair_address}")
            # ... existing pair check code ...
            if self.on_pair_updated:
                self.on_pair_updated(pair_info)
            logger.info(f"Successfully checked pair {pair_address}")
        except Exception as e:
            logger.error(f"Error checking pair {pair_address}: {str(e)}")

    def _check_security(self, token_address):
        try:
            logger.info(f"Checking security for token {token_address}")
            # ... existing security check code ...
            logger.info(f"Completed security check for token {token_address}")
            return security_info
        except Exception as e:
            logger.error(f"Error checking security for token {token_address}: {str(e)}")
            return None

    def _handle_new_pair(self, pair_address):
        try:
            logger.info(f"Processing new pair {pair_address}")
            # ... existing new pair handling code ...
            if self.on_new_pair:
                self.on_new_pair(pair_info)
            logger.info(f"Successfully processed new pair {pair_address}")
        except Exception as e:
            logger.error(f"Error processing new pair {pair_address}: {str(e)}")

async def check_honeypot(token_address: str) -> dict:
    """Check token using Honeypot API"""
    url = "https://api.honeypot.is/v2/IsHoneypot"
    params = {"address": token_address}
    max_retries = 3
    
    timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout
    
    for attempt in range(max_retries):
        try:
            log_message(f"Checking Honeypot API for {token_address} (attempt {attempt + 1}/{max_retries})", "INFO")
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'honeypotResult' not in data:
                            if attempt == max_retries - 1:
                                return {'error': 'No honeypot result in response'}
                            log_message("Invalid response format, retrying...", "WARNING")
                            continue
                        log_message("Honeypot check completed successfully", "SUCCESS")
                        return data
                    if attempt == max_retries - 1:
                        return {'error': f'API error: {response.status}'}
                    log_message(f"API error {response.status}, retrying...", "WARNING")
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                return {'error': 'All requests timed out'}
            log_message("Request timed out, retrying...", "WARNING")
        except Exception as e:
            if attempt == max_retries - 1:
                return {'error': str(e)}
            log_message(f"Error: {str(e)}, retrying...", "WARNING")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
    
    return {'error': 'Max retries reached'}

async def check_goplus(token_address: str) -> dict:
    """Check token using GoPlus API"""
    base_url = "https://api.gopluslabs.io/api/v1/token_security/1"
    params = {"contract_addresses": token_address}
    max_retries = 3
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    for attempt in range(max_retries):
        try:
            log_message(f"Checking GoPlus API for {token_address} (attempt {attempt + 1}/{max_retries})", "INFO")
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and 'result' in data:
                            log_message("GoPlus check completed successfully", "SUCCESS")
                            return data
                        if attempt == max_retries - 1:
                            return {'error': 'Invalid response format'}
                        log_message("Invalid response format, retrying...", "WARNING")
                        continue
                    if attempt == max_retries - 1:
                        return {'error': f'API error: {response.status}'}
                    log_message(f"API error {response.status}, retrying...", "WARNING")
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                return {'error': 'All requests timed out'}
            log_message("Request timed out, retrying...", "WARNING")
        except Exception as e:
            if attempt == max_retries - 1:
                return {'error': str(e)}
            log_message(f"Error: {str(e)}, retrying...", "WARNING")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(1)
    
    return {'error': 'Max retries reached'}

def print_security_info(token_address: str, honeypot_data: dict, goplus_data: dict):
    """Print complete security analysis information"""
    print("\n" + "="*80)
    print(f"🔍 COMPLETE SECURITY ANALYSIS FOR {token_address}")
    print("="*80)
    
    # Honeypot Analysis
    print("\n🍯 HONEYPOT API ANALYSIS:")
    print("-"*50)
    if 'error' not in honeypot_data:
        # Extract all relevant data
        hp_result = honeypot_data.get('honeypotResult', {})
        simulation = honeypot_data.get('simulationResult', {})
        contract = honeypot_data.get('contractCode', {})
        
        # Basic Status
        is_honeypot = hp_result.get('isHoneypot', 'Unknown')
        status = "🔴 YES" if is_honeypot else "🟢 NO" if is_honeypot is False else "⚪ Unknown"
        print(f"Is Honeypot: {status}")
        
        if hp_result.get('honeypotReason'):
            print(f"❗ Honeypot Reason: {hp_result.get('honeypotReason')}")
        
        # Simulation Results
        print("\n📊 Simulation Results:")
        print(f"Buy Tax: {simulation.get('buyTax', 'Unknown')}% {'🚨 HIGH' if isinstance(simulation.get('buyTax'), (int, float)) and simulation.get('buyTax') > 10 else ''}")
        print(f"Sell Tax: {simulation.get('sellTax', 'Unknown')}% {'🚨 HIGH' if isinstance(simulation.get('sellTax'), (int, float)) and simulation.get('sellTax') > 10 else ''}")
        print(f"Transfer Tax: {simulation.get('transferTax', 'Unknown')}% {'🚨 HIGH' if isinstance(simulation.get('transferTax'), (int, float)) and simulation.get('transferTax') > 10 else ''}")
        print(f"Buy Gas: {simulation.get('buyGas', 'Unknown')}")
        print(f"Sell Gas: {simulation.get('sellGas', 'Unknown')}")
        print(f"Max Buy Amount: {simulation.get('maxBuyAmount', 'Unknown')}")
        print(f"Max Sell Amount: {simulation.get('maxSellAmount', 'Unknown')}")
        
        # Contract Analysis
        print("\n📝 Contract Analysis:")
        print(f"Is Open Source: {'✅' if contract.get('isOpenSource') else '❌'}")
        print(f"Is Proxy: {'⚠️' if contract.get('isProxy') else '✅'}")
        print(f"Is Blacklisted: {'🚨' if contract.get('isBlacklisted') else '✅'}")
        print(f"Is Whitelisted: {'✅' if contract.get('isWhitelisted') else '❌'}")
        print(f"Has Anti-Whale: {'⚠️' if contract.get('isAntiWhale') else '✅'}")
        print(f"Has Trading Cooldown: {'⚠️' if contract.get('isTradingCooldown') else '✅'}")
        print(f"Personal Slippage Modifiable: {'✅' if contract.get('isPersonalSlippageModifiable') else '⚠️'}")
        print(f"Has Hidden Owner: {'🚨' if contract.get('hasHiddenOwner') else '✅'}")
        print(f"Can Take Ownership: {'🚨' if contract.get('canTakeOwnership') else '✅'}")
        print(f"Has Mint Function: {'⚠️' if contract.get('hasMintFunction') else '✅'}")
        
        # Simulation Status
        if not simulation.get('simulationSuccess'):
            print(f"\n❌ Simulation Failed: {simulation.get('simulationError', 'Unknown error')}")
            
        # Store raw data for debugging
        print("\n🔍 Raw Honeypot Data (for debugging):")
        print(json.dumps(honeypot_data, indent=2))
    else:
        print(f"❌ Honeypot API Error: {honeypot_data['error']}")
    
    # GoPlus Analysis
    print("\n🔐 GOPLUS SECURITY ANALYSIS:")
    print("-"*50)
    if 'error' not in goplus_data and 'result' in goplus_data:
        token_data = goplus_data['result'].get(token_address.lower(), {})
        if token_data:
            # Basic Token Info
            print("\n📊 Token Information:")
            print(f"Name: {token_data.get('token_name', 'Unknown')}")
            print(f"Symbol: {token_data.get('token_symbol', 'Unknown')}")
            print(f"Total Supply: {token_data.get('total_supply', 'Unknown')}")
            
            # Tax Information
            print("\n💰 Tax Information:")
            buy_tax = token_data.get('buy_tax', 'Unknown')
            sell_tax = token_data.get('sell_tax', 'Unknown')
            print(f"Buy Tax: {buy_tax}% {'🚨 HIGH' if isinstance(buy_tax, (int, float)) and float(buy_tax) > 10 else ''}")
            print(f"Sell Tax: {sell_tax}% {'🚨 HIGH' if isinstance(sell_tax, (int, float)) and float(sell_tax) > 10 else ''}")
            
            # Contract Properties
            print("\n📝 Contract Properties:")
            print(f"Is Mintable: {'⚠️' if token_data.get('is_mintable') == '1' else '✅'}")
            print(f"Is Open Source: {'✅' if token_data.get('is_open_source') == '1' else '❌'}")
            print(f"Is Proxy: {'⚠️' if token_data.get('is_proxy') == '1' else '✅'}")
            print(f"Can Take Back Ownership: {'🚨' if token_data.get('can_take_back_ownership') == '1' else '✅'}")
            print(f"Is Anti-Whale: {'⚠️' if token_data.get('is_anti_whale') == '1' else '✅'}")
            print(f"Is Blacklisted: {'🚨' if token_data.get('is_blacklisted') == '1' else '✅'}")
            print(f"Is Whitelisted: {'✅' if token_data.get('is_whitelisted') == '1' else '❌'}")
            print(f"Has Trading Cooldown: {'⚠️' if token_data.get('trading_cooldown') == '1' else '✅'}")
            
            # Holder Information
            print("\n👥 Holder Information:")
            holder_count = token_data.get('holder_count', 'Unknown')
            print(f"Token Holders: {holder_count} {'⚠️ LOW' if isinstance(holder_count, (int, str)) and str(holder_count).isdigit() and int(holder_count) < 50 else ''}")
            print(f"LP Holders: {token_data.get('lp_holder_count', 'Unknown')}")
            print(f"LP Total Supply: {token_data.get('lp_total_supply', 'Unknown')}")
            
            # Addresses
            print("\n📍 Important Addresses:")
            print(f"Owner Address: {token_data.get('owner_address', 'Unknown')}")
            print(f"Creator Address: {token_data.get('creator_address', 'Unknown')}")
            
            # DEX Information
            print("\n💱 DEX Information:")
            print(f"Listed on DEX: {'✅' if token_data.get('is_in_dex') == '1' else '❌'}")
            if token_data.get('dex'):
                print(f"DEX Platforms: {token_data.get('dex')}")
            
            # Trust List
            if token_data.get('trust_list'):
                print("\n✅ Trust List:")
                print(token_data.get('trust_list'))
            
            # Potential Risks
            risks = token_data.get('other_potential_risks', '')
            if risks:
                print("\n⚠️ Potential Risks:")
                for risk in risks.split(','):
                    if risk.strip():
                        print(f"❗ {risk.strip()}")
            
            # Store raw data for debugging
            print("\n🔍 Raw GoPlus Data (for debugging):")
            print(json.dumps(goplus_data, indent=2))
        else:
            print("❌ No data available from GoPlus for this token")
    else:
        print(f"❌ GoPlus API Error: {goplus_data.get('error', 'Unknown error')}")
    
    print("="*80 + "\n")

def get_timestamp():
    """Get current timestamp in readable format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_message(message: str, level: str = "INFO"):
    """Print a timestamped log message"""
    timestamp = get_timestamp()
    prefix = {
        "INFO": "ℹ️",
        "ERROR": "❌",
        "WARNING": "⚠️",
        "SUCCESS": "✅"
    }.get(level, "ℹ️")
    print(f"[{timestamp}] {prefix} {message}")

def save_pair_to_db(event, token0_info, token1_info, pair_info):
    """Save pair information to database"""
    global db_path
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO pairs (
                block_number, transaction_hash, pair_address, pair_name, pair_symbol,
                token0_address, token0_name, token0_symbol, token0_decimals, token0_total_supply,
                token0_eth_balance, token0_verified,
                token1_address, token1_name, token1_symbol, token1_decimals, token1_total_supply,
                token1_eth_balance, token1_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['blockNumber'],
            event['transactionHash'].hex(),
            event['args']['pair'],
            pair_info['name'],
            pair_info['symbol'],
            token0_info['contract_address'],
            token0_info['name'],
            token0_info['symbol'],
            token0_info['decimals'],
            token0_info['total_supply'],
            token0_info['eth_balance'],
            token0_info['verified'],
            token1_info['contract_address'],
            token1_info['name'],
            token1_info['symbol'],
            token1_info['decimals'],
            token1_info['total_supply'],
            token1_info['eth_balance'],
            token1_info['verified']
        ))
        conn.commit()
        log_message(f"Saved pair data to database", "SUCCESS")
        
        # Update session stats
        update_session_stats({'pairs_found': 1})
        
    except sqlite3.IntegrityError:
        log_message("Pair already exists in database", "WARNING")
    except Exception as e:
        log_message(f"Error saving pair data: {str(e)}", "ERROR")
    finally:
        conn.close()

def save_security_check(token_address: str, honeypot_data: dict, goplus_data: dict):
    """Save complete security check results to database"""
    global db_path
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Extract Honeypot data
        hp_result = honeypot_data.get('honeypotResult', {})
        simulation = honeypot_data.get('simulationResult', {})
        contract = honeypot_data.get('contractCode', {})
        
        # Extract GoPlus data
        gp_token_data = {}
        if 'error' not in goplus_data and 'result' in goplus_data:
            gp_token_data = goplus_data['result'].get(token_address.lower(), {})
        
        # Combine errors if any
        errors = []
        if 'error' in honeypot_data:
            errors.append(f"Honeypot: {honeypot_data['error']}")
        if 'error' in goplus_data:
            errors.append(f"GoPlus: {goplus_data['error']}")
        
        # Convert raw data to JSON strings
        hp_raw_data = json.dumps(honeypot_data)
        gp_raw_data = json.dumps(goplus_data)
        
        # Convert numeric values
        def safe_float(value):
            try:
                return float(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            try:
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                return None
        
        def safe_bool(value):
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() == 'true' or value == '1'
            return bool(value) if value is not None else None
        
        # Create the SQL query
        query = '''
            INSERT INTO security_checks (
                token_address, checked_at,
                hp_is_honeypot, hp_honeypot_reason,
                hp_buy_tax, hp_sell_tax, hp_transfer_tax,
                hp_max_buy_amount, hp_max_sell_amount,
                hp_buy_gas, hp_sell_gas,
                hp_is_open_source, hp_is_proxy, hp_is_blacklisted,
                hp_is_whitelisted, hp_is_anti_whale, hp_is_trading_cooldown,
                hp_is_personal_slippage_modifiable, hp_has_hidden_owner,
                hp_can_take_ownership, hp_has_mint_function,
                hp_simulation_success, hp_simulation_error,
                hp_raw_data,
                gp_buy_tax, gp_sell_tax,
                gp_is_mintable, gp_is_proxy, gp_is_open_source,
                gp_can_take_back_ownership,
                gp_owner_address, gp_creator_address,
                gp_holder_count, gp_total_supply,
                gp_token_name, gp_token_symbol,
                gp_lp_holder_count, gp_lp_total_supply,
                gp_is_in_dex, gp_is_anti_whale,
                gp_is_blacklisted, gp_is_whitelisted,
                gp_is_trading_cooldown,
                gp_trust_list, gp_dex,
                gp_potential_risks, gp_raw_data,
                api_errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # Create values tuple with proper type conversion
        values = (
            token_address,
            datetime.now().isoformat(),
            
            # Honeypot API Data
            safe_bool(hp_result.get('isHoneypot')),
            str(hp_result.get('honeypotReason', '')),
            safe_float(simulation.get('buyTax')),
            safe_float(simulation.get('sellTax')),
            safe_float(simulation.get('transferTax')),
            str(simulation.get('maxBuyAmount', '')),
            str(simulation.get('maxSellAmount', '')),
            safe_float(simulation.get('buyGas')),
            safe_float(simulation.get('sellGas')),
            safe_bool(contract.get('isOpenSource')),
            safe_bool(contract.get('isProxy')),
            safe_bool(contract.get('isBlacklisted')),
            safe_bool(contract.get('isWhitelisted')),
            safe_bool(contract.get('isAntiWhale')),
            safe_bool(contract.get('isTradingCooldown')),
            safe_bool(contract.get('isPersonalSlippageModifiable')),
            safe_bool(contract.get('hasHiddenOwner')),
            safe_bool(contract.get('canTakeOwnership')),
            safe_bool(contract.get('hasMintFunction')),
            safe_bool(simulation.get('simulationSuccess')),
            str(simulation.get('simulationError', '')),
            hp_raw_data,
            
            # GoPlus API Data
            safe_float(gp_token_data.get('buy_tax')),
            safe_float(gp_token_data.get('sell_tax')),
            safe_bool(gp_token_data.get('is_mintable')),
            safe_bool(gp_token_data.get('is_proxy')),
            safe_bool(gp_token_data.get('is_open_source')),
            safe_bool(gp_token_data.get('can_take_back_ownership')),
            str(gp_token_data.get('owner_address', '')),
            str(gp_token_data.get('creator_address', '')),
            safe_int(gp_token_data.get('holder_count')),
            str(gp_token_data.get('total_supply', '')),
            str(gp_token_data.get('token_name', '')),
            str(gp_token_data.get('token_symbol', '')),
            safe_int(gp_token_data.get('lp_holder_count')),
            str(gp_token_data.get('lp_total_supply', '')),
            safe_bool(gp_token_data.get('is_in_dex')),
            safe_bool(gp_token_data.get('is_anti_whale')),
            safe_bool(gp_token_data.get('is_blacklisted')),
            safe_bool(gp_token_data.get('is_whitelisted')),
            safe_bool(gp_token_data.get('trading_cooldown')),
            str(gp_token_data.get('trust_list', '')),
            json.dumps(gp_token_data.get('dex', [])),
            str(gp_token_data.get('other_potential_risks', '')),
            gp_raw_data,
            
            ', '.join(errors) if errors else None
        )
        
        # Execute the query
        c.execute(query, values)
        conn.commit()
        log_message(f"Saved security check data for {token_address}", "SUCCESS")
        
        # Update session stats
        update_session_stats({
            'honeypots_found': 1 if hp_result.get('isHoneypot') else 0,
            'high_risk_pairs': 1 if any([
                hp_result.get('isHoneypot'),
                contract.get('isBlacklisted'),
                contract.get('hasHiddenOwner'),
                contract.get('canTakeOwnership'),
                gp_token_data.get('is_blacklisted') == '1'
            ]) else 0,
            'api_errors': 1 if errors else 0
        })
        
    except sqlite3.IntegrityError:
        log_message(f"Security check already exists for token {token_address}", "WARNING")
    except Exception as e:
        log_message(f"Error saving security check: {str(e)}", "ERROR")
    finally:
        conn.close()

def handle_event(event):
    """Handle new pair creation event"""
    token0_address = event['args']['token0']
    token1_address = event['args']['token1']
    pair_address = event['args']['pair']

    # Get token information
    token0_info = get_token_info(token0_address)
    token1_info = get_token_info(token1_address)
    pair_info = get_token_info(pair_address)
    
    # Save to database
    save_pair_to_db(event, token0_info, token1_info, pair_info)

    # Print formatted output
    print("\n" + "="*50)
    print("🔔 NEW PAIR DETECTED")
    print("="*50)
    
    print(f"\n📊 BLOCK INFO:")
    print(f"Block Number: {event['blockNumber']}")
    print(f"Transaction Hash: {event['transactionHash'].hex()}")
    
    print(f"\n🔄 PAIR CONTRACT:")
    print(f"Address: {pair_address}")
    print(f"Name: {pair_info['name']}")
    print(f"Symbol: {pair_info['symbol']}")
    print(f"ETH Balance: {pair_info['eth_balance']}")
    
    print(f"\n💎 TOKEN 0:")
    print(f"Address: {token0_info['contract_address']}")
    print(f"Name: {token0_info['name']}")
    print(f"Symbol: {token0_info['symbol']}")
    print(f"Decimals: {token0_info['decimals']}")
    print(f"Total Supply: {token0_info['total_supply']}")
    print(f"ETH Balance: {token0_info['eth_balance']}")
    print(f"Contract Verified: {'✅ Yes' if token0_info['verified'] else '❌ No'}")
    
    print(f"\n💎 TOKEN 1:")
    print(f"Address: {token1_info['contract_address']}")
    print(f"Name: {token1_info['name']}")
    print(f"Symbol: {token1_info['symbol']}")
    print(f"Decimals: {token1_info['decimals']}")
    print(f"Total Supply: {token1_info['total_supply']}")
    print(f"ETH Balance: {token1_info['eth_balance']}")
    print(f"Contract Verified: {'✅ Yes' if token1_info['verified'] else '❌ No'}")
    
    print(f"\n🔍 LINKS:")
    print(f"Pair: https://etherscan.io/address/{pair_address}")
    print(f"Token 0: https://etherscan.io/address/{token0_address}")
    print(f"Token 1: https://etherscan.io/address/{token1_address}")
    print("="*50 + "\n")

def convert_to_json_serializable(obj):
    """Convert Web3 types to JSON serializable format"""
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(v) for v in obj]
    elif hasattr(obj, 'hex'):
        return obj.hex()
    elif hasattr(obj, '__dict__'):
        return convert_to_json_serializable(obj.__dict__)
    else:
        return obj

async def handle_event_with_security(event):
    """Enhanced event handler with security checks"""
    token0_address = event['args']['token0']
    token1_address = event['args']['token1']
    
    try:
        # First print basic pair info
        handle_event(event)
        
        # Then check security for both tokens
        print("\n🔍 SECURITY ANALYSIS")
        print("="*50)
        
        print("\nAnalyzing Token 0...")
        hp_data0 = await check_honeypot(token0_address)
        gp_data0 = await check_goplus(token0_address)
        print_security_info(token0_address, hp_data0, gp_data0)
        save_security_check(token0_address, hp_data0, gp_data0)
        
        print("\nAnalyzing Token 1...")
        hp_data1 = await check_honeypot(token1_address)
        gp_data1 = await check_goplus(token1_address)
        print_security_info(token1_address, hp_data1, gp_data1)
        save_security_check(token1_address, hp_data1, gp_data1)
        
        # Broadcast to WebSocket clients
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Convert event to JSON serializable format
                json_event = convert_to_json_serializable(event)
                await session.post(
                    'http://localhost:5000/broadcast',
                    json={
                        'event': json_event,
                        'token0_security': {
                            'honeypot': hp_data0,
                            'goplus': gp_data0
                        },
                        'token1_security': {
                            'honeypot': hp_data1,
                            'goplus': gp_data1
                        }
                    }
                )
        except Exception as e:
            print(f"Failed to broadcast to frontend: {str(e)}")
        
    except Exception as e:
        print(f"❌ Error during security check: {str(e)}")

async def main_async():
    """Main async function with graceful shutdown"""
    print("\n" + "="*50)
    print("🚀 UNISWAP V2 PAIR MONITOR")
    print("="*50)
    
    log_message(f"Network: {os.getenv('INFURA_NETWORK').upper()}")
    log_message(f"Factory: {UNISWAP_V2_FACTORY}")
    
    # Create session directory and initialize database
    if not os.path.exists(SESSIONS_ROOT):
        os.makedirs(SESSIONS_ROOT)
    
    # Initialize database
    if not init_database():
        log_message("Failed to initialize database. Exiting...", "ERROR")
        return 1
    
    try:
        # Create contract instance
        factory_contract = w3.eth.contract(
            address=UNISWAP_V2_FACTORY,
            abi=json.loads(FACTORY_ABI)
        )

        # Get event signature hash
        pair_created_topic = '0x' + w3.keccak(text="PairCreated(address,address,address,uint256)").hex()

        # First scan for recent pairs
        await get_recent_pairs_async(pair_created_topic)
        
        print("\n" + "="*50)
        log_message("MONITORING FOR NEW PAIRS", "INFO")
        print("="*50)
        print("\nPress Ctrl+C to stop monitoring.")
        
        # Create event filter for new pairs
        event_filter = w3.eth.filter({
            'address': UNISWAP_V2_FACTORY,
            'topics': [pair_created_topic]
        })
        
        # Start periodic rescan task
        rescan_task = asyncio.create_task(periodic_rescan())
        
        while True:
            try:
                events = w3.eth.get_filter_changes(event_filter.filter_id)
                for event_log in events:
                    # Parse the event
                    event = factory_contract.events.PairCreated().process_log(event_log)
                    await handle_event_with_security(event)
                await asyncio.sleep(1)
            except Exception as e:
                log_message(f"Error: {e}", "ERROR")
                await asyncio.sleep(1)
                continue
    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        log_message("SHUTTING DOWN", "INFO")
        print("="*50)
        return 0
    except Exception as e:
        log_message(f"Fatal error: {str(e)}", "ERROR")
        return 1
    finally:
        # Clean up any remaining connections
        if 'rescan_task' in locals():
            rescan_task.cancel()
        await cleanup()
    return 0

async def periodic_rescan():
    """Periodically rescan existing pairs for updated security info"""
    while True:
        try:
            # Wait for 3 minutes
            await asyncio.sleep(180)
            
            log_message("Starting periodic rescan of existing pairs", "INFO")
            
            # Get pairs from database
            db = sqlite3.connect(db_path)
            cursor = db.cursor()
            cursor.execute('SELECT token0_address, token1_address FROM pairs ORDER BY created_at DESC LIMIT 100')
            pairs = cursor.fetchall()
            db.close()
            
            # Rescan each pair
            for token0_address, token1_address in pairs:
                try:
                    # Check security for both tokens
                    hp_data0 = await check_honeypot(token0_address)
                    gp_data0 = await check_goplus(token0_address)
                    save_security_check(token0_address, hp_data0, gp_data0)
                    
                    hp_data1 = await check_honeypot(token1_address)
                    gp_data1 = await check_goplus(token1_address)
                    save_security_check(token1_address, hp_data1, gp_data1)
                    
                    log_message(f"Updated security info for pair {token0_address}/{token1_address}", "SUCCESS")
                except Exception as e:
                    log_message(f"Failed to update security info for pair: {str(e)}", "ERROR")
                
                # Small delay between pairs to avoid rate limiting
                await asyncio.sleep(1)
            
            log_message("Completed periodic rescan", "SUCCESS")
            
        except Exception as e:
            log_message(f"Error during periodic rescan: {str(e)}", "ERROR")
            await asyncio.sleep(60)  # Wait a minute before retrying

async def cleanup():
    """Clean up resources"""
    try:
        # Close any remaining aiohttp sessions
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        log_message(f"Error during cleanup: {str(e)}", "ERROR")

async def get_recent_pairs_async(pair_created_topic):
    """Async version of get_recent_pairs"""
    log_message("Starting scan for recent pairs", "INFO")
    
    try:
        current_block = w3.eth.block_number
        log_message(f"Current block: {current_block}", "INFO")
        
        from_block = current_block - 100
        log_message(f"Scanning blocks {from_block} to {current_block} (last 100 blocks)", "INFO")
        
        factory_contract = w3.eth.contract(
            address=UNISWAP_V2_FACTORY,
            abi=json.loads(FACTORY_ABI)
        )
        
        try:
            event_filter = {
                'address': UNISWAP_V2_FACTORY,
                'fromBlock': hex(from_block),
                'toBlock': hex(current_block),
                'topics': [pair_created_topic]
            }
            
            logs = w3.eth.get_logs(event_filter)
            events = [factory_contract.events.PairCreated().process_log(log) for log in logs]
            
            if events:
                log_message(f"Found {len(events)} pairs in the last 100 blocks!", "SUCCESS")
                log_message("Processing most recent pair...", "INFO")
                await handle_event_with_security(events[-1])
            else:
                from_block = current_block - 500
                log_message("No recent pairs found, extending search...", "WARNING")
                log_message(f"Scanning blocks {from_block} to {current_block}", "INFO")
                
                event_filter['fromBlock'] = hex(from_block)
                logs = w3.eth.get_logs(event_filter)
                events = [factory_contract.events.PairCreated().process_log(log) for log in logs]
                
                if events:
                    log_message(f"Found {len(events)} pairs in the last 500 blocks!", "SUCCESS")
                    log_message("Processing most recent pair...", "INFO")
                    await handle_event_with_security(events[-1])
                else:
                    log_message("No pairs found in extended search", "WARNING")
        except Exception as e:
            log_message(f"Error fetching logs: {str(e)}", "ERROR")
    except Exception as e:
        log_message(f"Error during recent pairs scan: {str(e)}", "ERROR")

def get_token_info(token_address):
    """Get token information"""
    try:
        # Create contract instance
        contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Get basic info
        try:
            name = contract.functions.name().call()
        except:
            name = "Unknown"
            
        try:
            symbol = contract.functions.symbol().call()
        except:
            symbol = "Unknown"
            
        try:
            decimals = contract.functions.decimals().call()
        except:
            decimals = 18
            
        try:
            total_supply = contract.functions.totalSupply().call()
            total_supply = str(total_supply / (10 ** decimals))
        except Exception as e:
            total_supply = "Unknown"
            log_message(f"Error reading total supply: {str(e)}", "WARNING")
        
        # Get ETH balance
        eth_balance = w3.eth.get_balance(token_address)
        eth_balance = w3.from_wei(eth_balance, 'ether')
        
        # Check if contract is verified on Etherscan
        etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        verified = False
        if etherscan_api_key:
            url = f"https://api.etherscan.io/api?module=contract&action=getabi&address={token_address}&apikey={etherscan_api_key}"
            try:
                response = requests.get(url)
                data = response.json()
                verified = data['status'] == '1' and data['message'] == 'OK'
            except:
                verified = False
        
        return {
            'contract_address': token_address,
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'total_supply': total_supply,
            'eth_balance': f"{eth_balance:.4f} ETH",
            'verified': verified
        }
        
    except Exception as e:
        log_message(f"Error getting token info: {str(e)}", "ERROR")
        return {
            'contract_address': token_address,
            'name': "Unknown",
            'symbol': "Unknown",
            'decimals': 18,
            'total_supply': "Unknown",
            'eth_balance': "0.0000 ETH",
            'verified': False
        }

@app.route('/pairs', methods=['GET'])
def get_pairs():
    """Get all pairs from database"""
    global db_path
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            SELECT * FROM pairs 
            ORDER BY created_at DESC 
            LIMIT 100
        ''')
        pairs = c.fetchall()
        
        # Convert to list of dictionaries
        pairs_list = []
        for pair in pairs:
            pair_dict = {
                'address': pair[3],
                'blockNumber': pair[1],
                'transactionHash': pair[2],
                'timestamp': pair[16],
                'token0': {
                    'address': pair[6],
                    'name': pair[7],
                    'symbol': pair[8],
                    'decimals': pair[9],
                    'totalSupply': pair[10],
                    'ethBalance': pair[11],
                    'isVerified': bool(pair[12])
                },
                'token1': {
                    'address': pair[13],
                    'name': pair[14],
                    'symbol': pair[15],
                    'decimals': pair[16],
                    'totalSupply': pair[17],
                    'ethBalance': pair[18],
                    'isVerified': bool(pair[19])
                }
            }
            
            # Get security checks
            c.execute('SELECT * FROM security_checks WHERE token_address = ? ORDER BY checked_at DESC LIMIT 1', (pair_dict['token0']['address'],))
            security0 = c.fetchone()
            c.execute('SELECT * FROM security_checks WHERE token_address = ? ORDER BY checked_at DESC LIMIT 1', (pair_dict['token1']['address'],))
            security1 = c.fetchone()
            
            if security0:
                pair_dict['securityChecks'] = {
                    'token0': {
                        'isHoneypot': bool(security0[3]),
                        'honeypotReason': security0[4],
                        'buyTax': security0[5],
                        'sellTax': security0[6],
                        'transferTax': security0[7],
                        'isOpenSource': bool(security0[11]),
                        'isProxy': bool(security0[12]),
                        'isBlacklisted': bool(security0[13]),
                        'isWhitelisted': bool(security0[14]),
                        'isAntiWhale': bool(security0[15]),
                        'isTradingCooldown': bool(security0[16]),
                        'hasHiddenOwner': bool(security0[18]),
                        'canTakeOwnership': bool(security0[19]),
                        'hasMintFunction': bool(security0[20]),
                        'holderCount': security0[31],
                        'ownerAddress': security0[30],
                        'creatorAddress': security0[31],
                        'potentialRisks': security0[44].split(',') if security0[44] else [],
                        'apiErrors': security0[45].split(',') if security0[45] else [],
                        'checkedAt': security0[2]
                    }
                }
            
            if security1:
                if 'securityChecks' not in pair_dict:
                    pair_dict['securityChecks'] = {}
                pair_dict['securityChecks']['token1'] = {
                    'isHoneypot': bool(security1[3]),
                    'honeypotReason': security1[4],
                    'buyTax': security1[5],
                    'sellTax': security1[6],
                    'transferTax': security1[7],
                    'isOpenSource': bool(security1[11]),
                    'isProxy': bool(security1[12]),
                    'isBlacklisted': bool(security1[13]),
                    'isWhitelisted': bool(security1[14]),
                    'isAntiWhale': bool(security1[15]),
                    'isTradingCooldown': bool(security1[16]),
                    'hasHiddenOwner': bool(security1[18]),
                    'canTakeOwnership': bool(security1[19]),
                    'hasMintFunction': bool(security1[20]),
                    'holderCount': security1[31],
                    'ownerAddress': security1[30],
                    'creatorAddress': security1[31],
                    'potentialRisks': security1[44].split(',') if security1[44] else [],
                    'apiErrors': security1[45].split(',') if security1[45] else [],
                    'checkedAt': security1[2]
                }
            
            pairs_list.append(pair_dict)
        
        return jsonify(pairs_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

async def broadcast_to_frontend(event_data):
    """Broadcast event data to frontend via WebSocket"""
    try:
        socketio.emit('new_pair', event_data)
    except Exception as e:
        print(f"Failed to broadcast to frontend: {str(e)}")

if __name__ == "__main__":
    if not os.getenv('INFURA_API_KEY') or os.getenv('INFURA_API_KEY') == 'your_infura_api_key_here':
        log_message("Please set your Infura API key in the .env file", "ERROR")
        exit(1)
    
    try:
        # Start the Flask server in a separate thread
        import threading
        server_thread = threading.Thread(target=lambda: socketio.run(app, port=5000))
        server_thread.daemon = True
        server_thread.start()
        
        # Run the main async loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exit_code = loop.run_until_complete(main_async())
        loop.run_until_complete(cleanup())
        loop.close()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n" + "="*50)
        log_message("SHUTTING DOWN", "INFO")
        print("="*50)
        exit(0)
    except Exception as e:
        log_message(f"Fatal error: {str(e)}", "ERROR")
        exit(1) 
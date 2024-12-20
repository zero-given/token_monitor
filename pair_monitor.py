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

# Initialize Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load environment variables
load_dotenv()

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
        # ... existing initialization ...
        self.on_new_pair = on_new_pair
        self.on_pair_updated = on_pair_updated
        logger.info("PairMonitor initialized")

    def start(self):
        try:
            logger.info("Starting PairMonitor")
            self._setup_web3()
            self._setup_factory()
            self._start_monitoring()
        except Exception as e:
            logger.error(f"Error starting PairMonitor: {str(e)}")
            raise

    def _setup_web3(self):
        try:
            logger.info(f"Connecting to Ethereum network via Infura")
            # ... existing web3 setup ...
            logger.info("Successfully connected to Ethereum network")
        except Exception as e:
            logger.error(f"Failed to connect to Ethereum network: {str(e)}")
            raise

    def _setup_factory(self):
        try:
            logger.info("Setting up Uniswap V2 Factory contract")
            # ... existing factory setup ...
            logger.info("Successfully set up Uniswap V2 Factory contract")
        except Exception as e:
            logger.error(f"Failed to set up factory contract: {str(e)}")
            raise

    def _start_monitoring(self):
        try:
            logger.info("Starting pair monitoring thread")
            # ... existing monitoring setup ...
        except Exception as e:
            logger.error(f"Failed to start monitoring: {str(e)}")
            raise

    def monitor_pairs(self):
        """Monitor for new pairs and check existing ones"""
        while True:
            try:
                logger.info("ℹ️ Starting periodic rescan of existing pairs")
                for pair_address in self.known_pairs:
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
            logger.info(f"ℹ️ Checking Honeypot API for {token0_address} (attemmpt 1/3)")
            honeypot_result = await check_honeypot(token0_address)
            
            if not honeypot_result:
                logger.warning("⚠️ Invalid response format, retrying...")
                honeypot_result = await check_honeypot(token0_address)
            
            logger.info("✅ Honeypot check completed successfully")
            
            logger.info(f"ℹ️ Checking GoPlus API for {token0_address} (attemptt 1/3)")
            goplus_result = await check_goplus(token0_address)
            
            if not goplus_result:
                logger.warning("⚠️ Invalid response format, retrying...")
                goplus_result = await check_goplus(token0_address)
            
            logger.info("✅ GoPlus check completed successfully")

            # Check token1
            token1_address = self.known_pairs[pair_address]["token1"]["address"]
            logger.info(f"ℹ️ Checking Honeypot API for {token1_address} (attemmpt 1/3)")
            honeypot_result1 = await check_honeypot(token1_address)
            
            if not honeypot_result1:
                logger.warning("⚠️ Invalid response format, retrying...")
                honeypot_result1 = await check_honeypot(token1_address)
            
            logger.info("✅ Honeypot check completed successfully")
            
            logger.info(f"ℹ️ Checking GoPlus API for {token1_address} (attemptt 1/3)")
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
    """Print security analysis information"""
    print("\n=== Security Analysis ===")
    
    # Honeypot Analysis
    print("\nHoneypot Analysis:")
    if 'error' not in honeypot_data:
        hp_result = honeypot_data.get('honeypotResult', {})
        simulation = honeypot_data.get('simulationResult', {})
        is_honeypot = hp_result.get('isHoneypot', 'Unknown')
        
        # Color-coded honeypot status
        status = "🔴 YES" if is_honeypot else "🟢 NO" if is_honeypot is False else "⚪ Unknown"
        print(f"Is Honeypot: {status}")
        
        if hp_result.get('isHoneypot'):
            print(f"❗ Honeypot Reason: {hp_result.get('honeypotReason', 'Unknown')}")
        
        # Format taxes
        buy_tax = simulation.get('buyTax', 'Unknown')
        sell_tax = simulation.get('sellTax', 'Unknown')
        transfer_tax = simulation.get('transferTax', 'Unknown')
        
        print(f"Buy Tax: {buy_tax}% {'🚨 HIGH' if isinstance(buy_tax, (int, float)) and buy_tax > 10 else ''}")
        print(f"Sell Tax: {sell_tax}% {'🚨 HIGH' if isinstance(sell_tax, (int, float)) and sell_tax > 10 else ''}")
        print(f"Transfer Tax: {transfer_tax}% {'🚨 HIGH' if isinstance(transfer_tax, (int, float)) and transfer_tax > 10 else ''}")
        
        # Add contract info
        contract = honeypot_data.get('contractCode', {})
        print(f"Is Open Source: {'✅' if contract.get('isOpenSource') else '❌'}")
        print(f"Is Proxy: {'⚠️' if contract.get('isProxy') else '✅'}")
        print(f"Can Take Ownership: {'🚨' if contract.get('canTakeOwnership') else '✅'}")
    else:
        print(f"❌ Honeypot API Error: {honeypot_data['error']}")
    
    # GoPlus Analysis
    print("\nGoPlus Security Analysis:")
    if 'error' not in goplus_data:
        if 'result' in goplus_data and token_address.lower() in goplus_data['result']:
            token_data = goplus_data['result'][token_address.lower()]
            
            # Format taxes
            buy_tax = token_data.get('buy_tax', 'Unknown')
            sell_tax = token_data.get('sell_tax', 'Unknown')
            
            print(f"Buy Tax: {buy_tax}% {'🚨 HIGH' if isinstance(buy_tax, (int, float)) and float(buy_tax) > 10 else ''}")
            print(f"Sell Tax: {sell_tax}% {'🚨 HIGH' if isinstance(sell_tax, (int, float)) and float(sell_tax) > 10 else ''}")
            
            # Contract properties
            print(f"Is Mintable: {'⚠️' if token_data.get('is_mintable') == '1' else '✅'}")
            print(f"Is Open Source: {'✅' if token_data.get('is_open_source') == '1' else '❌'}")
            print(f"Is Proxy: {'⚠️' if token_data.get('is_proxy') == '1' else '✅'}")
            print(f"Can Take Back Ownership: {'🚨' if token_data.get('can_take_back_ownership') == '1' else '✅'}")
            
            # Addresses
            print(f"\nOwner Address: {token_data.get('owner_address', 'Unknown')}")
            print(f"Creator Address: {token_data.get('creator_address', 'Unknown')}")
            
            # Holder info
            holder_count = token_data.get('holder_count', 'Unknown')
            print(f"Holder Count: {holder_count} {'⚠️ LOW' if isinstance(holder_count, (int, str)) and str(holder_count).isdigit() and int(holder_count) < 50 else ''}")
            
            # Print potential risks
            risks = token_data.get('other_potential_risks', '')
            if risks:
                print("\n⚠️ Potential Risks:")
                for risk in risks.split(','):
                    if risk.strip():
                        print(f"❗ {risk.strip()}")
        else:
            print("❌ No data available from GoPlus")
    else:
        print(f"❌ GoPlus API Error: {goplus_data['error']}")
    
    print("=====================")

def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect('pairs.db')
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
                is_honeypot BOOLEAN,
                honeypot_reason TEXT,
                buy_tax REAL,
                sell_tax REAL,
                transfer_tax REAL,
                is_open_source BOOLEAN,
                is_proxy BOOLEAN,
                can_take_ownership BOOLEAN,
                holder_count INTEGER,
                owner_address TEXT,
                creator_address TEXT,
                potential_risks TEXT,
                api_errors TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(token_address, checked_at)
            )
        ''')
        
        conn.commit()
        print("✅ Database initialized successfully")
        return True
    except sqlite3.Error as e:
        print(f"❌ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

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
    conn = sqlite3.connect('pairs.db')
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
    except sqlite3.IntegrityError:
        print("Pair already exists in database")
    finally:
        conn.close()

def save_security_check(token_address: str, honeypot_data: dict, goplus_data: dict):
    """Save security check results to database"""
    conn = sqlite3.connect('pairs.db')
    c = conn.cursor()
    
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
    
    try:
        c.execute('''
            INSERT INTO security_checks (
                token_address, is_honeypot, honeypot_reason,
                buy_tax, sell_tax, transfer_tax,
                is_open_source, is_proxy, can_take_ownership,
                holder_count, owner_address, creator_address,
                potential_risks, api_errors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token_address,
            hp_result.get('isHoneypot'),
            hp_result.get('honeypotReason'),
            simulation.get('buyTax'),
            simulation.get('sellTax'),
            simulation.get('transferTax'),
            contract.get('isOpenSource'),
            contract.get('isProxy'),
            contract.get('canTakeOwnership'),
            gp_token_data.get('holder_count'),
            gp_token_data.get('owner_address'),
            gp_token_data.get('creator_address'),
            gp_token_data.get('other_potential_risks'),
            ', '.join(errors) if errors else None
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Security check already exists for this token")
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
            db = sqlite3.connect('pairs.db')
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
    """Get detailed token information"""
    log_message(f"Fetching token info for {token_address}", "INFO")
    try:
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        
        # Basic info
        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
        except Exception as e:
            log_message(f"Error reading basic token info: {str(e)}", "ERROR")
            return {
                'name': "Unknown",
                'symbol': "Unknown",
                'decimals': 18,
                'total_supply': "Unknown",
                'eth_balance': "0 ETH",
                'contract_address': token_address,
                'verified': False,
                'error': str(e)
            }
        
        # Get total supply if available
        try:
            total_supply = token_contract.functions.totalSupply().call() / (10 ** decimals)
            total_supply = f"{total_supply:,.2f}"
        except Exception as e:
            log_message(f"Error reading total supply: {str(e)}", "WARNING")
            total_supply = "Unknown"
        
        # Get ETH balance of token contract
        try:
            eth_balance = w3.eth.get_balance(token_address)
            eth_balance = w3.from_wei(eth_balance, 'ether')
        except Exception as e:
            log_message(f"Error reading ETH balance: {str(e)}", "WARNING")
            eth_balance = 0
        
        return {
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'total_supply': total_supply,
            'eth_balance': f"{eth_balance:.4f} ETH",
            'contract_address': token_address,
            'verified': True  # If we can read name/symbol, it's likely verified
        }
    except Exception as e:
        log_message(f"Failed to get token info: {str(e)}", "ERROR")
        return {
            'name': "Unknown",
            'symbol': "Unknown",
            'decimals': 18,
            'total_supply': "Unknown",
            'eth_balance': "0 ETH",
            'contract_address': token_address,
            'verified': False,
            'error': str(e)
        }

@app.route('/pairs', methods=['GET'])
def get_pairs():
    """Get all pairs from database"""
    try:
        conn = sqlite3.connect('pairs.db')
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
                        'isHoneypot': bool(security0[2]),
                        'honeypotReason': security0[3],
                        'buyTax': security0[4],
                        'sellTax': security0[5],
                        'transferTax': security0[6],
                        'isOpenSource': bool(security0[7]),
                        'isProxy': bool(security0[8]),
                        'canTakeOwnership': bool(security0[9]),
                        'holderCount': security0[10],
                        'ownerAddress': security0[11],
                        'creatorAddress': security0[12],
                        'potentialRisks': security0[13].split(',') if security0[13] else [],
                        'apiErrors': security0[14].split(',') if security0[14] else [],
                        'checkedAt': security0[15]
                    }
                }
            
            if security1:
                if 'securityChecks' not in pair_dict:
                    pair_dict['securityChecks'] = {}
                pair_dict['securityChecks']['token1'] = {
                    'isHoneypot': bool(security1[2]),
                    'honeypotReason': security1[3],
                    'buyTax': security1[4],
                    'sellTax': security1[5],
                    'transferTax': security1[6],
                    'isOpenSource': bool(security1[7]),
                    'isProxy': bool(security1[8]),
                    'canTakeOwnership': bool(security1[9]),
                    'holderCount': security1[10],
                    'ownerAddress': security1[11],
                    'creatorAddress': security1[12],
                    'potentialRisks': security1[13].split(',') if security1[13] else [],
                    'apiErrors': security1[14].split(',') if security1[14] else [],
                    'checkedAt': security1[15]
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
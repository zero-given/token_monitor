import asyncio
import time
import aiohttp
from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound, ContractLogicError
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta 
import sqlite3
import json
import logging
import os
import sys
import threading
import traceback
import requests
from SPXfucked import TokenTracker
from tabulate import tabulate
from colorama import Fore, Style, init

init(autoreset=True)  # Initialize colorama
def initialize_database_structure(folder_name: str):
    """Initialize all required database structures with single record per token"""
    print(f"Initializing database structure in {folder_name}")
    
    # Create SCAN_RECORDS database
    scan_records_path = os.path.join(folder_name, 'SCAN_RECORDS.db')
    print(f"Creating/verifying SCAN_RECORDS database at: {scan_records_path}")
    
    with sqlite3.connect(scan_records_path) as db:
        cursor = db.cursor()
        
        # First, check if the table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scan_records'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Creating new scan_records table with all columns...")
            cursor.execute('DROP TABLE IF EXISTS scan_records')
            cursor.execute('''
            CREATE TABLE scan_records (
                token_address TEXT PRIMARY KEY,
                scan_timestamp TEXT NOT NULL,
                token_name TEXT,
                token_symbol TEXT,
                token_decimals INTEGER,
                token_total_supply TEXT,
                token_pair_address TEXT,
                token_age_hours REAL,
                hp_simulation_success BOOLEAN,
                hp_buy_tax REAL,
                hp_sell_tax REAL,
                hp_transfer_tax REAL,
                hp_liquidity_amount REAL,
                hp_pair_reserves0 TEXT,
                hp_pair_reserves1 TEXT,
                hp_buy_gas_used INTEGER,
                hp_sell_gas_used INTEGER,
                hp_creation_time TEXT,
                hp_holder_count INTEGER,
                hp_is_honeypot BOOLEAN,
                hp_honeypot_reason TEXT,
                hp_is_open_source BOOLEAN,
                hp_is_proxy BOOLEAN,
                hp_is_mintable BOOLEAN,
                hp_can_be_minted BOOLEAN,
                hp_owner_address TEXT,
                hp_creator_address TEXT,
                hp_deployer_address TEXT,
                hp_has_proxy_calls BOOLEAN,
                hp_pair_liquidity REAL,
                hp_pair_liquidity_token0 REAL,
                hp_pair_liquidity_token1 REAL,
                hp_pair_token0_symbol TEXT,
                hp_pair_token1_symbol TEXT,
                hp_flags TEXT,
                gp_is_open_source INTEGER,
                gp_is_proxy INTEGER,
                gp_is_mintable INTEGER,
                gp_owner_address TEXT,
                gp_creator_address TEXT,
                gp_can_take_back_ownership INTEGER,
                gp_owner_change_balance INTEGER,
                gp_hidden_owner INTEGER,
                gp_selfdestruct INTEGER,
                gp_external_call INTEGER,
                gp_buy_tax REAL,
                gp_sell_tax REAL,
                gp_is_anti_whale INTEGER,
                gp_anti_whale_modifiable INTEGER,
                gp_cannot_buy INTEGER,
                gp_cannot_sell_all INTEGER,
                gp_slippage_modifiable INTEGER,
                gp_personal_slippage_modifiable INTEGER,
                gp_trading_cooldown INTEGER,
                gp_is_blacklisted INTEGER,
                gp_is_whitelisted INTEGER,
                gp_is_in_dex INTEGER,
                gp_transfer_pausable INTEGER,
                gp_can_be_minted INTEGER,
                gp_total_supply TEXT,
                gp_holder_count INTEGER,
                gp_owner_percent REAL,
                gp_owner_balance TEXT,
                gp_creator_percent REAL,
                gp_creator_balance TEXT,
                gp_lp_holder_count INTEGER,
                gp_lp_total_supply TEXT,
                gp_is_true_token INTEGER,
                gp_is_airdrop_scam INTEGER,
                gp_trust_list TEXT,
                gp_other_potential_risks TEXT,
                gp_note TEXT,
                gp_honeypot_with_same_creator INTEGER,
                gp_fake_token INTEGER,
                gp_holders TEXT,
                gp_lp_holders TEXT,
                gp_dex_info TEXT,
                total_scans INTEGER DEFAULT 1,
                honeypot_failures INTEGER DEFAULT 0,
                last_error TEXT,
                status TEXT DEFAULT 'new',
                liq10 REAL,
                liq20 REAL,
                liq30 REAL,
                liq40 REAL,
                liq50 REAL,
                liq60 REAL,
                liq70 REAL,
                liq80 REAL,
                liq90 REAL,
                liq100 REAL,
                liq110 REAL,
                liq120 REAL,
                liq130 REAL,
                liq140 REAL,
                liq150 REAL,
                liq160 REAL,
                liq170 REAL,
                liq180 REAL,
                liq190 REAL,
                liq200 REAL
            )''')
            
            # Create an index on token_age_hours for faster ordering
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_token_age 
            ON scan_records(token_age_hours DESC)
            ''')

            # Create or verify indexes
            print("Creating/verifying indexes...")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_records(scan_timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_age ON scan_records(token_age_hours DESC)')
            
            db.commit()
            print("SCAN_RECORDS table and indexes verified/updated successfully")

            # Now create xHoneypot_removed table as table 2
            print("Creating xHoneypot_removed table...")
            cursor.execute('DROP TABLE IF EXISTS xHoneypot_removed')
            cursor.execute('''
            CREATE TABLE xHoneypot_removed (
                token_address TEXT PRIMARY KEY,
                removal_timestamp TEXT NOT NULL,
                original_scan_timestamp TEXT,
                token_name TEXT,
                token_symbol TEXT,
                token_decimals INTEGER,
                token_total_supply TEXT,
                token_pair_address TEXT,
                token_age_hours REAL,
                hp_simulation_success BOOLEAN,
                hp_buy_tax REAL,
                hp_sell_tax REAL,
                hp_transfer_tax REAL,
                hp_liquidity_amount REAL,
                hp_pair_reserves0 TEXT,
                hp_pair_reserves1 TEXT,
                hp_buy_gas_used INTEGER,
                hp_sell_gas_used INTEGER,
                hp_creation_time TEXT,
                hp_holder_count INTEGER,
                hp_is_honeypot BOOLEAN,
                hp_honeypot_reason TEXT,
                total_scans INTEGER,
                honeypot_failures INTEGER,
                last_error TEXT,
                removal_reason TEXT
            )''')
            
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_removal_timestamp 
            ON xHoneypot_removed(removal_timestamp DESC)
            ''')
            
            db.commit()
            print("xHoneypot_removed table and indexes created successfully")
        else:
            # If table exists, check if token_age_hours column exists
            cursor.execute("PRAGMA table_info(scan_records)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'token_age_hours' not in columns:
                print("Adding token_age_hours column to existing table...")
                try:
                    cursor.execute('ALTER TABLE scan_records ADD COLUMN token_age_hours REAL')
                    print("Successfully added token_age_hours column")
                except Exception as e:
                    print(f"Error adding column: {str(e)}")
        
        # Create RESCAN database
        rescan_path = os.path.join(folder_name, 'rescan.db')
        print(f"Creating/verifying RESCAN database at: {rescan_path}")
        
        with sqlite3.connect(rescan_path) as db:
            cursor = db.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rescan (
                    id INTEGER PRIMARY KEY,
                    address TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    resid TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    honeypot_failures INTEGER NOT NULL DEFAULT 0
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON rescan(timestamp)')
            db.commit()
            print("RESCAN table and indexes created successfully")


def get_folder_name() -> str:
    """Get the session folder name based on current date"""
    current_date = datetime.now().strftime("%B %d")
    session_number = 1
    
    while True:
        folder_name = f"{current_date} - Sesh {session_number}"
        if os.path.exists(folder_name):
            session_number += 1
        else:
            return folder_name
        

def format_table_output(goplus_data: dict) -> None:
    """Format GoPlus data into nice tables similar to go.py output"""
    if not isinstance(goplus_data, dict) or 'result' not in goplus_data:
        print("Invalid GoPlus data format")
        return
        
    # Get the first (and only) token data from result
    token_address = list(goplus_data['result'].keys())[0]
    token_data = goplus_data['result'][token_address]
    
    print("\nGoPlus Security Analysis:")
    print("=" * 50)

    # Contract Info
    contract_info = [
        ('is_open_source', 'Yes' if str(token_data.get('is_open_source', '0')) == '1' else 'No'),
        ('is_proxy', 'Yes' if str(token_data.get('is_proxy', '0')) == '1' else 'No'),
        ('is_mintable', 'Yes' if str(token_data.get('is_mintable', '0')) == '1' else 'No'),
        ('can_take_back_ownership', token_data.get('can_take_back_ownership', '0')),
        ('owner_change_balance', token_data.get('owner_change_balance', '0')),
        ('hidden_owner', token_data.get('hidden_owner', '0'))
    ]
    
    # Token Info
    token_info = [
        ('token_name', token_data.get('token_name', 'Unknown')),
        ('token_symbol', token_data.get('token_symbol', 'Unknown')),
        ('total_supply', token_data.get('total_supply', '0')),
        ('holder_count', token_data.get('holder_count', '0')),
        ('lp_holder_count', token_data.get('lp_holder_count', '0')),
        ('lp_total_supply', token_data.get('lp_total_supply', '0'))
    ]
    
    # Owner Info
    owner_info = [
        ('owner_address', token_data.get('owner_address', '')),
        ('creator_address', token_data.get('creator_address', '')),
        ('owner_balance', token_data.get('owner_balance', '0')),
        ('owner_percent', token_data.get('owner_percent', '0')),
        ('creator_percent', token_data.get('creator_percent', '0')),
        ('creator_balance', token_data.get('creator_balance', '0'))
    ]
    
    # Trading Info
    trading_info = [
        ('buy_tax', token_data.get('buy_tax', '0')),
        ('sell_tax', token_data.get('sell_tax', '0')),
        ('cannot_buy', token_data.get('cannot_buy', '0')),
        ('cannot_sell_all', token_data.get('cannot_sell_all', '0')),
        ('slippage_modifiable', token_data.get('slippage_modifiable', '0')),
        ('personal_slippage_modifiable', token_data.get('personal_slippage_modifiable', '0'))
    ]

    # Print contract and token info side by side
    contract_table = tabulate(contract_info, headers=['Contract Info', 'Value'], tablefmt="grid")
    token_table = tabulate(token_info, headers=['Token Info', 'Value'], tablefmt="grid")
    
    # Print tables side by side
    contract_lines = contract_table.split('\n')
    token_lines = token_table.split('\n')
    max_contract_width = max(len(line) for line in contract_lines)
    
    for c_line, t_line in zip(contract_lines, token_lines):
        print(f"{c_line:<{max_contract_width}} {t_line}")
    
    print("\n")
    
    # Print owner and trading info side by side
    owner_table = tabulate(owner_info, headers=['Owner Info', 'Value'], tablefmt="grid")
    trading_table = tabulate(trading_info, headers=['Trading Info', 'Value'], tablefmt="grid")
    
    owner_lines = owner_table.split('\n')
    trading_lines = trading_table.split('\n')
    max_owner_width = max(len(line) for line in owner_lines)
    
    for o_line, t_line in zip(owner_lines, trading_lines):
        print(f"{o_line:<{max_owner_width}} {t_line}")
    
    # Print holder info with proper validation
    print("\nHolder Information:")
    holders = token_data.get('holders', [])
    if holders and isinstance(holders, list):
        print("\nTop Holders:")
        holder_rows = []
        for holder in holders[:10]:  # Show top 10 holders
            if isinstance(holder, dict):  # Make sure holder is a dictionary
                holder_rows.append([
                    holder.get('address', 'Unknown'),
                    holder.get('balance', 'Unknown'),
                    f"{float(holder.get('percent', 0)) * 100:.2f}%",
                    'Yes' if holder.get('is_locked') else 'No',
                    'Yes' if holder.get('is_contract') else 'No',
                    holder.get('tag', '')
                ])
        if holder_rows:
            print(tabulate(holder_rows, 
                         headers=['Address', 'Balance', 'Percent', 'Locked', 'Contract', 'Tag'],
                         tablefmt="grid"))
    
    # Print LP holder info with proper validation
    lp_holders = token_data.get('lp_holders', [])
    if lp_holders and isinstance(lp_holders, list):
        print("\nLP Holders:")
        lp_rows = []
        for holder in lp_holders:
            if isinstance(holder, dict):  # Make sure holder is a dictionary
                lp_rows.append([
                    holder.get('address', 'Unknown'),
                    holder.get('balance', 'Unknown'),
                    f"{float(holder.get('percent', 0)) * 100:.2f}%",
                    'Yes' if holder.get('is_locked') else 'No',
                    'Yes' if holder.get('is_contract') else 'No',
                    holder.get('tag', '')
                ])
        if lp_rows:
            print(tabulate(lp_rows,
                         headers=['Address', 'Balance', 'Percent', 'Locked', 'Contract', 'Tag'],
                         tablefmt="grid"))
    
    # Print DEX info with validation
    dex_info = token_data.get('dex', [])
    if dex_info:
        print("\nDEX Info:")
        print(json.dumps(dex_info, indent=2))


def prepare_goplus_values(self, goplus_data: dict, token_address: str) -> tuple:
    """Helper function to properly extract and validate GoPlus values"""
    # First, get the token data accounting for case sensitivity
    token_data = None
    if 'result' in goplus_data:
        token_data = (goplus_data['result'].get(token_address.lower()) or 
                     goplus_data['result'].get(token_address) or {})

    def safe_int_bool(value):
        """Safely convert string to int boolean (0 or 1)"""
        if isinstance(value, bool):
            return 1 if value else 0
        try:
            return 1 if str(value).strip() == '1' else 0
        except:
            return 0
    
    def safe_float(value, default=0.0):
        """Safely convert string to float, handling percentage signs"""
        if value is None:
            return default
        try:
            if isinstance(value, (int, float)):
                return float(value)
            # Remove percentage sign and any whitespace
            cleaned = str(value).replace('%', '').strip()
            if cleaned:
                return float(cleaned)
            return default
        except:
            return default

    def safe_str(value, default=''):
        """Safely convert value to string"""
        return str(value or default)
    
    def safe_int(value, default=0):
        """Safely convert value to integer"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point
                cleaned = ''.join(c for c in value if c.isdigit() or c == '.')
                if cleaned:
                    return int(float(cleaned))
            return int(float(str(value)))
        except:
            return default

    # Extract values with proper error handling
    return (
        safe_int_bool(token_data.get('is_open_source')),
        safe_int_bool(token_data.get('is_proxy')),
        safe_int_bool(token_data.get('is_mintable')),
        safe_str(token_data.get('owner_address')),
        safe_str(token_data.get('creator_address')),
        safe_int_bool(token_data.get('can_take_back_ownership')),
        safe_int_bool(token_data.get('owner_change_balance')),
        safe_int_bool(token_data.get('hidden_owner')),
        safe_int_bool(token_data.get('selfdestruct')),
        safe_int_bool(token_data.get('external_call')),
        safe_float(token_data.get('buy_tax')),
        safe_float(token_data.get('sell_tax')),
        safe_int_bool(token_data.get('is_anti_whale')),
        safe_int_bool(token_data.get('anti_whale_modifiable')),
        safe_int_bool(token_data.get('cannot_buy')),
        safe_int_bool(token_data.get('cannot_sell_all')),
        safe_int_bool(token_data.get('slippage_modifiable')),
        safe_int_bool(token_data.get('personal_slippage_modifiable')),
        safe_int_bool(token_data.get('trading_cooldown')),
        safe_int_bool(token_data.get('is_blacklisted')),
        safe_int_bool(token_data.get('is_whitelisted')),
        safe_int_bool(token_data.get('is_in_dex')),
        safe_int_bool(token_data.get('transfer_pausable')),
        safe_int_bool(token_data.get('can_be_minted')),
        safe_str(token_data.get('total_supply', '0')),
        safe_int(token_data.get('holder_count')),
        safe_float(token_data.get('owner_percent')),
        safe_str(token_data.get('owner_balance', '0')),
        safe_float(token_data.get('creator_percent')),
        safe_str(token_data.get('creator_balance', '0')),
        safe_int(token_data.get('lp_holder_count')),
        safe_str(token_data.get('lp_total_supply', '0')),
        safe_int_bool(token_data.get('is_true_token')),
        safe_int_bool(token_data.get('is_airdrop_scam')),
        json.dumps(token_data.get('trust_list', {})),
        json.dumps(token_data.get('other_potential_risks', [])),
        safe_str(token_data.get('note')),
        safe_int_bool(token_data.get('honeypot_with_same_creator')),
        safe_int_bool(token_data.get('fake_token')),
        json.dumps(token_data.get('holders', [])),
        json.dumps(token_data.get('lp_holders', [])),
        json.dumps(token_data.get('dex', []))
    )



class TokenChecker:
    def __init__(self, tracker: TokenTracker, folder_name: str):
        self.tracker = tracker
        self.folder_name = folder_name
        self.web3 = Web3(HTTPProvider(self.tracker.config.node_rpc))
        self.logger = tracker.logger
        self.ensure_database_ready()

    def ensure_database_ready(self):
        """Ensure database and tables exist before operations"""
        db_path = os.path.join(self.folder_name, 'SCAN_RECORDS.db')
        try:
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_records (
                    token_address TEXT PRIMARY KEY,
                    scan_timestamp TEXT NOT NULL,
                    token_name TEXT,
                    token_symbol TEXT,
                    token_decimals INTEGER,
                    token_total_supply TEXT,
                    token_pair_address TEXT,
                    token_age_hours REAL,
                    hp_simulation_success BOOLEAN,
                    hp_buy_tax REAL,
                    hp_sell_tax REAL,
                    hp_transfer_tax REAL,
                    hp_liquidity_amount REAL,
                    hp_pair_reserves0 TEXT,
                    hp_pair_reserves1 TEXT,
                    hp_buy_gas_used INTEGER,
                    hp_sell_gas_used INTEGER,
                    hp_creation_time TEXT,
                    hp_holder_count INTEGER,
                    hp_is_honeypot BOOLEAN,
                    hp_honeypot_reason TEXT,
                    hp_is_open_source BOOLEAN,
                    hp_is_proxy BOOLEAN,
                    hp_is_mintable BOOLEAN,
                    hp_can_be_minted BOOLEAN,
                    hp_owner_address TEXT,
                    hp_creator_address TEXT,
                    hp_deployer_address TEXT,
                    hp_has_proxy_calls BOOLEAN,
                    hp_pair_liquidity REAL,
                    hp_pair_liquidity_token0 REAL,
                    hp_pair_liquidity_token1 REAL,
                    hp_pair_token0_symbol TEXT,
                    hp_pair_token1_symbol TEXT,
                    hp_flags TEXT,
                    gp_is_open_source INTEGER,
                    gp_is_proxy INTEGER,
                    gp_is_mintable INTEGER,
                    gp_owner_address TEXT,
                    gp_creator_address TEXT,
                    gp_can_take_back_ownership INTEGER,
                    gp_owner_change_balance INTEGER,
                    gp_hidden_owner INTEGER,
                    gp_selfdestruct INTEGER,
                    gp_external_call INTEGER,
                    gp_buy_tax REAL,
                    gp_sell_tax REAL,
                    gp_is_anti_whale INTEGER,
                    gp_anti_whale_modifiable INTEGER,
                    gp_cannot_buy INTEGER,
                    gp_cannot_sell_all INTEGER,
                    gp_slippage_modifiable INTEGER,
                    gp_personal_slippage_modifiable INTEGER,
                    gp_trading_cooldown INTEGER,
                    gp_is_blacklisted INTEGER,
                    gp_is_whitelisted INTEGER,
                    gp_is_in_dex INTEGER,
                    gp_transfer_pausable INTEGER,
                    gp_can_be_minted INTEGER,
                    gp_total_supply TEXT,
                    gp_holder_count INTEGER,
                    gp_owner_percent REAL,
                    gp_owner_balance TEXT,
                    gp_creator_percent REAL,
                    gp_creator_balance TEXT,
                    gp_lp_holder_count INTEGER,
                    gp_lp_total_supply TEXT,
                    gp_is_true_token INTEGER,
                    gp_is_airdrop_scam INTEGER,
                    gp_trust_list TEXT,
                    gp_other_potential_risks TEXT,
                    gp_note TEXT,
                    gp_honeypot_with_same_creator INTEGER,
                    gp_fake_token INTEGER,
                    gp_holders TEXT,
                    gp_lp_holders TEXT,
                    gp_dex_info TEXT,
                    total_scans INTEGER DEFAULT 1,
                    honeypot_failures INTEGER DEFAULT 0,
                    last_error TEXT,
                    status TEXT DEFAULT 'new',
                    liq10 REAL,
                    liq20 REAL,
                    liq30 REAL,
                    liq40 REAL,
                    liq50 REAL,
                    liq60 REAL,
                    liq70 REAL,
                    liq80 REAL,
                    liq90 REAL,
                    liq100 REAL,
                    liq110 REAL,
                    liq120 REAL,
                    liq130 REAL,
                    liq140 REAL,
                    liq150 REAL,
                    liq160 REAL,
                    liq170 REAL,
                    liq180 REAL,
                    liq190 REAL,
                    liq200 REAL
                )''')
                db.commit()
                print(f"Verified scan_records table exists in {self.folder_name}")
        except sqlite3.Error as e:
            print(f"Database error during table verification: {str(e)}")
            raise

    async def check_honeypot(self, address: str) -> Dict:
        """Check token using Honeypot API with improved error handling"""
        try:
            url = "https://api.honeypot.is/v2/IsHoneypot"
            params = {"address": address}
            print("\nFetching Honeypot API data...")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Honeypot API response received for {address}")
                        # Process and validate the response
                        if isinstance(data, dict):
                            # Check for essential keys
                            if 'token' not in data:
                                print(f"Warning: No token data in response for {address}")
                            if 'simulationResult' not in data:
                                print(f"Warning: No simulation data in response for {address}")
                            if 'honeypotResult' not in data:
                                print(f"Warning: No honeypot result in response for {address}")
                                # Default to considering it a honeypot if no result
                                data['honeypotResult'] = {'isHoneypot': True}
                            return data
                        else:
                            print(f"Error: Invalid response format from Honeypot API")
                            return {}
                    print(f"Honeypot API error status: {response.status} for {address}")
                    try:
                        error_text = await response.text()
                        print(f"Error response: {error_text}")
                    except:
                        pass
                    return {}
        except Exception as e:
            print(f"Honeypot API error for {address}: {str(e)}")
            return {}

    async def check_goplus(self, address: str) -> Dict:
        """Check token using GoPlus API with improved error handling and retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                base_url = "https://api.gopluslabs.io/api/v1/token_security/1"
                params = {"contract_addresses": address}
                
                print(f"\nGoPlus API Request Details (Attempt {attempt + 1}/{max_retries}):")
                print(f"URL: {base_url}")
                print(f"Parameters: {params}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(base_url, params=params) as response:
                        print(f"Response Status: {response.status}")
                        response_text = await response.text()
                        print(f"Raw Response: {response_text}")
                        
                        try:
                            data = json.loads(response_text)
                            
                            # Check if we have valid data
                            if data.get('code') == 1 and data.get('result'):
                                token_data = data['result'].get(address.lower()) or data['result'].get(address)
                                
                                if token_data:
                                    # Process token data into standardized format with proper validation
                                    processed_data = {k: token_data.get(k) for k in token_data}
                                    return {
                                        'result': {
                                            address: processed_data
                                        }
                                    }
                        
                        except json.JSONDecodeError as e:
                            print(f"Error decoding response: {str(e)}")
                        
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                
            except Exception as e:
                print(f"Error during GoPlus API call: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        # If all retries failed, return empty result
        return {
            'result': {
                address: {}
            }
        }
    




    async def process_new_pair(self, token_address: str, pair_address: str):
        """Process and update token data with improved debugging"""
        db_path = None
        try:
            print("\n" + "="*50)
            print(f"DEBUG: Starting process_new_pair for token {token_address}")
            print(f"DEBUG: Pair address: {pair_address}")
            print("="*50)
            
            # Fetch Honeypot data
            honeypot_data = await self.check_honeypot(token_address) or {}
            print("\nDEBUG: Honeypot API Response:")
            print(json.dumps(honeypot_data, indent=2))
            
            await asyncio.sleep(1)  # Rate limiting
            
            # Fetch GoPlus data
            print("\nDEBUG: Fetching GoPlus data...")
            goplus_data = await self.check_goplus(token_address)
            print("\nDEBUG: GoPlus API Response:")
            print(json.dumps(goplus_data, indent=2))
            
            # Calculate token age
            token_age_hours = None
            creation_time_str = honeypot_data.get('pair', {}).get('createdAtTimestamp')
            if creation_time_str:
                try:
                    if str(creation_time_str).isdigit():
                        creation_time = datetime.fromtimestamp(int(creation_time_str))
                        token_age_hours = float((datetime.now() - creation_time).total_seconds() / 3600)
                        print(f"DEBUG: Calculated token age: {token_age_hours:.2f} hours from timestamp {creation_time_str}")
                    else:
                        creation_time = datetime.strptime(creation_time_str, '%Y-%m-%d %H:%M:%S')
                        token_age_hours = float((datetime.now() - creation_time).total_seconds() / 3600)
                        print(f"DEBUG: Calculated token age: {token_age_hours:.2f} hours from datetime string")
                    
                    if token_age_hours is not None:
                        print(f"DEBUG: Token age to be stored: {token_age_hours}")
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse creation time: {creation_time_str} - Error: {str(e)}")
                    token_age_hours = None
            else:
                print("Warning: No creation timestamp found in Honeypot API response")
            
            # Extract all data components
            print("\nDEBUG: Extracting data components...")
            
            token_info = honeypot_data.get('token', {})
            simulation = honeypot_data.get('simulationResult', {})
            contract = honeypot_data.get('contractCode', {})
            pair_info = honeypot_data.get('pair', {})
            pair_details = pair_info.get('pair', {})
            honeypot_result = honeypot_data.get('honeypotResult', {})
            
            # Get current scan count
            db_path = os.path.join(self.folder_name, 'SCAN_RECORDS.db')
            with sqlite3.connect(db_path) as db:
                cursor = db.cursor()
                cursor.execute('SELECT total_scans, honeypot_failures FROM scan_records WHERE token_address = ?', 
                            (token_address,))
                result = cursor.fetchone()
                total_scans = (result[0] + 1) if result else 1
                honeypot_failures = result[1] if result else 0

                print("\nDEBUG: Preparing values for database insertion...")
                
                # Prepare Honeypot values
                honeypot_values = [
                    token_address,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    token_info.get('name', 'Unknown'),
                    token_info.get('symbol', 'Unknown'),
                    token_info.get('decimals', 18),
                    token_info.get('totalSupply', '0'),
                    pair_address,
                    token_age_hours,  # Add token age here
                    bool(honeypot_data.get('simulationSuccess', False)),
                    float(simulation.get('buyTax', 0)),
                    float(simulation.get('sellTax', 0)),
                    float(simulation.get('transferTax', 0)),
                    float(pair_info.get('liquidity', 0)),
                    str(pair_info.get('reserves0', '')),
                    str(pair_info.get('reserves1', '')),
                    int(simulation.get('buyGas', 0)),
                    int(simulation.get('sellGas', 0)),
                    pair_info.get('createdAtTimestamp', ''),
                    int(token_info.get('totalHolders', 0)),
                    bool(honeypot_result.get('isHoneypot', True)),
                    honeypot_result.get('honeypotReason', ''),
                    bool(contract.get('openSource', False)),
                    bool(contract.get('isProxy', False)),
                    bool(contract.get('isMintable', False)),
                    bool(contract.get('canBeMinted', False)),
                    token_info.get('owner', ''),
                    token_info.get('creator', ''),
                    token_info.get('deployer', ''),
                    bool(contract.get('hasProxyCalls', False)),
                    float(pair_info.get('liquidity', 0)),
                    float(pair_info.get('liquidityToken0', 0)),
                    float(pair_info.get('liquidityToken1', 0)),
                    pair_details.get('token0Symbol', ''),
                    pair_details.get('token1Symbol', ''),
                    json.dumps(honeypot_data.get('flags', []))
                ]

                print(f"DEBUG: Token age in values list: {honeypot_values[7]}")

                # Use the prepare_goplus_values helper function to get GoPlus values
                goplus_values = list(prepare_goplus_values(self, goplus_data, token_address))

                # Get existing liquidity values first
                cursor.execute("""
                    SELECT liq10, liq20, liq30, liq40, liq50, liq60, liq70, liq80, liq90, liq100,
                           liq110, liq120, liq130, liq140, liq150, liq160, liq170, liq180, liq190, liq200 
                    FROM scan_records 
                    WHERE token_address = ?""", (token_address,))
                
                previous_values = cursor.fetchone() or [None] * 20

                # Prepare liquidity tracking values
                liquidity_values = []
                current_liquidity = float(pair_info.get('liquidity', 0))
                multiplier = getattr(self.tracker.config, 'liquidity_multiplier', 1)  # Access as class attribute

                # Debug liquidity calculation
                print(f"\nDEBUG: Liquidity Tracking Calculation:")
                print(f"Total Scans: {total_scans}")
                print(f"Current Liquidity: {current_liquidity}")
                print(f"Multiplier: {multiplier}")

                # Calculate which liquidity field should be updated (if any)
                update_field = None
                if total_scans % multiplier == 0:  # Only update on multiples of multiplier
                    update_field = total_scans  # This will be the field number to update (e.g., 10, 20, 30, etc.)

                for i, field_num in enumerate(range(10, 201, 10)):
                    if update_field and field_num == update_field:
                        # Update this field with current liquidity
                        liquidity_values.append(current_liquidity)
                        print(f"DEBUG: Setting liq{field_num} to {current_liquidity} (scan #{total_scans})")
                    else:
                        # Keep previous value if it exists
                        liquidity_values.append(previous_values[i] if previous_values else None)

                # Debug output
                print("\nDEBUG: Final Liquidity Values:")
                for i, val in enumerate(liquidity_values):
                    field_num = (i + 1) * 10
                    if val is not None:
                        print(f"liq{field_num}: {val}")
                
                # Add liquidity values to values list
                values = honeypot_values + goplus_values + [total_scans, honeypot_failures, '', 'active'] + liquidity_values

                # Debug output before database operation
                print("\nDEBUG: Database Operation Details:")
                print(f"Number of columns: {len(values)}")
                print(f"Number of values: {len(values)}")
                print("\nFirst few columns and their values:")
                for i in range(min(5, len(values))):
                    print(f"{i}: {values[i]}")
                
                # Single INSERT OR REPLACE operation
                columns = [
                    "token_address", "scan_timestamp", "token_name", "token_symbol",
                    "token_decimals", "token_total_supply", "token_pair_address",
                    "token_age_hours",
                    "hp_simulation_success", "hp_buy_tax", "hp_sell_tax", "hp_transfer_tax",
                    "hp_liquidity_amount", "hp_pair_reserves0", "hp_pair_reserves1",
                    "hp_buy_gas_used", "hp_sell_gas_used", "hp_creation_time",
                    "hp_holder_count", "hp_is_honeypot", "hp_honeypot_reason",
                    "hp_is_open_source", "hp_is_proxy", "hp_is_mintable", "hp_can_be_minted",
                    "hp_owner_address", "hp_creator_address", "hp_deployer_address",
                    "hp_has_proxy_calls", "hp_pair_liquidity", "hp_pair_liquidity_token0",
                    "hp_pair_liquidity_token1", "hp_pair_token0_symbol", "hp_pair_token1_symbol",
                    "hp_flags",
                    # GoPlus columns
                    "gp_is_open_source", "gp_is_proxy", "gp_is_mintable",
                    "gp_owner_address", "gp_creator_address", "gp_can_take_back_ownership",
                    "gp_owner_change_balance", "gp_hidden_owner", "gp_selfdestruct",
                    "gp_external_call", "gp_buy_tax", "gp_sell_tax", "gp_is_anti_whale",
                    "gp_anti_whale_modifiable", "gp_cannot_buy", "gp_cannot_sell_all",
                    "gp_slippage_modifiable", "gp_personal_slippage_modifiable",
                    "gp_trading_cooldown", "gp_is_blacklisted", "gp_is_whitelisted",
                    "gp_is_in_dex", "gp_transfer_pausable", "gp_can_be_minted",
                    "gp_total_supply", "gp_holder_count", "gp_owner_percent",
                    "gp_owner_balance", "gp_creator_percent", "gp_creator_balance",
                    "gp_lp_holder_count", "gp_lp_total_supply", "gp_is_true_token",
                    "gp_is_airdrop_scam", "gp_trust_list", "gp_other_potential_risks",
                    "gp_note", "gp_honeypot_with_same_creator", "gp_fake_token",
                    "gp_holders", "gp_lp_holders", "gp_dex_info",
                    # Metadata columns
                    "total_scans", "honeypot_failures", "last_error", "status",
                    "liq10", "liq20", "liq30", "liq40", "liq50", "liq60", "liq70", "liq80", "liq90", "liq100",
                    "liq110", "liq120", "liq130", "liq140", "liq150", "liq160", "liq170", "liq180", "liq190", "liq200"
                ]
                placeholders = ", ".join(["?" for _ in range(len(columns))])
                sql = f"""
                    INSERT OR REPLACE INTO scan_records ({", ".join(columns)})
                    VALUES ({placeholders})
                """
                
                print("\nDEBUG: Executing SQL:")
                print(sql)
                
                try:
                    cursor.execute(sql, values)
                    print("DEBUG: SQL execution successful")
                    
                    # Verify the insertion immediately
                    cursor.execute("""
                        SELECT token_address, token_name, total_scans, hp_liquidity_amount
                        FROM scan_records 
                        WHERE token_address = ?
                    """, (token_address,))
                    
                    result = cursor.fetchone()
                    if result:
                        print("\nDEBUG: Record verification:")
                        print(f"Token Address: {result[0]}")
                        print(f"Token Name: {result[1]}")
                        print(f"Total Scans: {result[2]}")
                        print(f"Liquidity: {result[3]}")
                    else:
                        print("DEBUG: WARNING - Record not found after insertion!")
                    
                    db.commit()
                    print("DEBUG: Database committed successfully")
                    
                except sqlite3.Error as e:
                    print(f"DEBUG: Database error: {str(e)}")
                    raise
                except Exception as e:
                    print(f"DEBUG: Unexpected error: {str(e)}")
                    raise
                
        except Exception as e:
            print(f"\nERROR: Error processing token {token_address}")
            print(f"Error details: {str(e)}")
            print("\nFull traceback:")
            import traceback
            print(traceback.format_exc())
            
            if db_path:
                try:
                    with sqlite3.connect(db_path) as error_db:
                        error_cursor = error_db.cursor()
                        error_cursor.execute('''
                            UPDATE scan_records 
                            SET honeypot_failures = honeypot_failures + 1,
                                last_error = ?
                            WHERE token_address = ?
                        ''', (str(e), token_address))

                        # Check if token should be moved to xHoneypot_removed
                        error_cursor.execute('''
                            SELECT 
                                token_address,
                                scan_timestamp,
                                token_name,
                                token_symbol,
                                token_decimals,
                                token_total_supply,
                                token_pair_address,
                                token_age_hours,
                                hp_simulation_success,
                                hp_buy_tax,
                                hp_sell_tax,
                                hp_transfer_tax,
                                hp_liquidity_amount,
                                hp_pair_reserves0,
                                hp_pair_reserves1,
                                hp_buy_gas_used,
                                hp_sell_gas_used,
                                hp_creation_time,
                                hp_holder_count,
                                hp_is_honeypot,
                                hp_honeypot_reason,
                                total_scans,
                                honeypot_failures,
                                last_error
                            FROM scan_records 
                            WHERE token_address = ? 
                            AND honeypot_failures >= ?
                            AND hp_is_honeypot = 1
                        ''', (token_address, self.tracker.config.scanning['honeypot_failure_limit']))
                        
                        failed_token = error_cursor.fetchone()
                        if failed_token:
                            print(f"\nMoving token {token_address} to xHoneypot_removed table")
                            # Insert into xHoneypot_removed
                            error_cursor.execute('''
                                INSERT INTO xHoneypot_removed (
                                    token_address,
                                    removal_timestamp,
                                    original_scan_timestamp,
                                    token_name,
                                    token_symbol,
                                    token_decimals,
                                    token_total_supply,
                                    token_pair_address,
                                    token_age_hours,
                                    hp_simulation_success,
                                    hp_buy_tax,
                                    hp_sell_tax,
                                    hp_transfer_tax,
                                    hp_liquidity_amount,
                                    hp_pair_reserves0,
                                    hp_pair_reserves1,
                                    hp_buy_gas_used,
                                    hp_sell_gas_used,
                                    hp_creation_time,
                                    hp_holder_count,
                                    hp_is_honeypot,
                                    hp_honeypot_reason,
                                    total_scans,
                                    honeypot_failures,
                                    last_error,
                                    removal_reason
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                failed_token[0],  # token_address
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # removal_timestamp
                                failed_token[1],  # original_scan_timestamp
                                failed_token[2],  # token_name
                                failed_token[3],  # token_symbol
                                failed_token[4],  # token_decimals
                                failed_token[5],  # token_total_supply
                                failed_token[6],  # token_pair_address
                                failed_token[7],  # token_age_hours
                                failed_token[8],  # hp_simulation_success
                                failed_token[9],  # hp_buy_tax
                                failed_token[10], # hp_sell_tax
                                failed_token[11], # hp_transfer_tax
                                failed_token[12], # hp_liquidity_amount
                                failed_token[13], # hp_pair_reserves0
                                failed_token[14], # hp_pair_reserves1
                                failed_token[15], # hp_buy_gas_used
                                failed_token[16], # hp_sell_gas_used
                                failed_token[17], # hp_creation_time
                                failed_token[18], # hp_holder_count
                                failed_token[19], # hp_is_honeypot
                                failed_token[20], # hp_honeypot_reason
                                failed_token[21], # total_scans
                                failed_token[22], # honeypot_failures
                                failed_token[23], # last_error
                                f"Exceeded honeypot failure limit ({self.tracker.config.scanning['honeypot_failure_limit']})"
                            ))

                            # Delete from scan_records
                            error_cursor.execute('DELETE FROM scan_records WHERE token_address = ?', (token_address,))
                            print(f"Token {token_address} moved to xHoneypot_removed table")

                        error_db.commit()
                        print(f"DEBUG: Updated honeypot_failures and last_error for token {token_address}")
                except sqlite3.Error as e:
                    print(f"ERROR: Failed to update error status in database: {str(e)}")
                except Exception as e:
                    print(f"ERROR: Unexpected error updating error status: {str(e)}")
                raise

        finally:
            print("\nDEBUG: process_new_pair completion status:")
            print(f"Token: {token_address}")
            print(f"Pair: {pair_address}")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50)

    async def process_token(self, token_address: str, pair_address: str = None):
        """Process a token by checking its honeypot status and other data"""
        try:
            # Always process the token to get fresh data
            await self.process_new_pair(token_address, pair_address)
        except Exception as e:
            print(f"Error processing token {token_address}: {str(e)}")
            import traceback
            print(traceback.format_exc())
    




class TokenTrackerMain:
    def __init__(self, config_path: str, folder_name: str):  # Add folder_name parameter
        """Initialize the TokenTrackerMain with configuration and setup."""
        self.folder_name = folder_name  # Use passed folder_name instead of creating new one
        
        # Load config first
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}")
            raise
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file: {config_path}")
            raise

        # Initialize tracker and other components
        self.tracker = TokenTracker(config_path)
        self.checker = TokenChecker(self.tracker, self.folder_name)
        self.running = True
        self.event_filter = None
        self.setup_event_filter()





        # Spinner setup
        self.spinner_chars = ['|', '/', '-', '\\']
        self.spinner_idx = 0

        # Set default values if scanning config is missing
        if 'scanning' not in self.config:
            self.config['scanning'] = {
                "rescan_interval": 500,
                "max_rescan_count": 1000,
                "remove_after_max_scans": True,
                "honeypot_failure_limit": 5
            }
        
        # Initialize latest pair
        self.initialize_latest_pair()

    def initialize_latest_folder(self) -> str:
        """Initialize and get the current session folder."""
        current_date = datetime.now().strftime("%B %d")
        session_number = 1
        
        while True:
            folder_name = f"{current_date} - Sesh {session_number}"
            if os.path.exists(folder_name):
                session_number += 1
            else:
                os.makedirs(folder_name)
                return folder_name

    def initialize_latest_pair(self):
            """Scan and add the latest token pair before starting main loop"""
            try:
                print("Scanning latest listed token...")
                
                # First verify the table exists
                db_path = os.path.join(self.folder_name, 'rescan.db')
                with sqlite3.connect(db_path) as db:
                    cursor = db.cursor()
                    # Check if table exists
                    cursor.execute('''
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='rescan'
                    ''')
                    if not cursor.fetchone():
                        print("Creating rescan table...")
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS rescan (
                                id INTEGER PRIMARY KEY,
                                address TEXT NOT NULL,
                                pair TEXT NOT NULL,
                                count INTEGER NOT NULL DEFAULT 0,
                                resid TEXT NOT NULL,
                                timestamp TEXT NOT NULL,
                                honeypot_failures INTEGER NOT NULL DEFAULT 0
                            )
                        ''')
                        db.commit()
                
                pair_length = self.tracker.factory_contract.functions.allPairsLength().call()
                latest_pair_address = None
                token_to_scan = None
                
                for i in range(pair_length - 1, -1, -1):
                    latest_pair_address = self.tracker.factory_contract.functions.allPairs(i).call()
                    pair_contract = self.tracker.web3.eth.contract(
                        address=latest_pair_address,
                        abi=self.tracker.liquidity_pool_abi
                    )
                    
                    token0_address = pair_contract.functions.token0().call()
                    token1_address = pair_contract.functions.token1().call()
                    
                    if token0_address == self.tracker.weth_address:
                        token_to_scan = token1_address
                        break
                    elif token1_address == self.tracker.weth_address:
                        token_to_scan = token0_address
                        break

                if token_to_scan:
                    print(f"Latest pair address: {latest_pair_address}")
                    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Add to rescan database
                    with sqlite3.connect(db_path) as db:
                        cursor = db.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO rescan (address, pair, count, resid, timestamp, honeypot_failures) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (token_to_scan, latest_pair_address, 0, "r1", current_timestamp, 0))
                        db.commit()
                    
                    # Process the token immediately using asyncio.run
                    async def process_token():
                        await self.checker.process_token(token_to_scan, latest_pair_address)
                    
                    asyncio.run(process_token())
                    
                    print(f"\n{token_to_scan} added to database for monitoring")
                else:
                    print("No suitable latest pair found")

            except Exception as e:
                print(f"Error initializing latest pair: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
    def get_next_spinner(self):
        """Get next spinner character and rotate index"""
        char = self.spinner_chars[self.spinner_idx]
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_chars)
        return char

    def setup_event_filter(self):
        """Setup event filter for new pairs"""
        try:
            print("Setting up Uniswap event filter...")
            self.event_filter = self.tracker.factory_contract.events.PairCreated.create_filter(from_block='latest')
            print("Event filter setup successfully")
        except Exception as e:
            print(f"Error setting up event filter: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise




    async def main_loop(self):
        """Main event loop with simplified monitoring output"""
        print("\n=== Initializing Main Loop ===")
        last_check_time = datetime.now()
        last_rescan_time = datetime.now()
        check_interval = 1  # seconds between new pair checks
        rescan_interval = 60  # seconds between rescans
        status_update_interval = 60  # seconds between full status updates
        last_status_update = datetime.now()
        
        if not self.event_filter:
            print("Error: Event filter not initialized")
            return
        
        print("\nMonitoring for new pairs and managing rescans...")
        print(f"Configuration:")
        print(f"- Check interval: {check_interval} seconds")
        print(f"- Rescan interval: {rescan_interval} seconds")
        print(f"- Status update interval: {status_update_interval} seconds")
        print(f"- Max rescans: {self.config['scanning']['max_rescan_count']}")
        print(f"- Honeypot failure limit: {self.config['scanning']['honeypot_failure_limit']}")
        print("\nStarting monitoring...")
        
        try:
            while self.running:
                current_time = datetime.now()
                
                # Check for new pairs
                if (current_time - last_check_time).total_seconds() >= check_interval:
                    try:
                        events = self.event_filter.get_new_entries()
                        
                        if events:
                            print(f"\nFound {len(events)} new pair(s)")
                            for event in events:
                                try:
                                    token0 = event['args']['token0']
                                    token1 = event['args']['token1']
                                    pair = event['args']['pair']
                                    
                                    print("\nNew pair detected:")
                                    print(f"Token0: {token0}")
                                    print(f"Token1: {token1}")
                                    print(f"Pair: {pair}")
                                    
                                    if token0 == self.tracker.weth_address:
                                        print(f"\nProcessing new WETH pair with token: {token1}")
                                        await self.checker.process_token(token1, pair)
                                    elif token1 == self.tracker.weth_address:
                                        print(f"\nProcessing new WETH pair with token: {token0}")
                                        await self.checker.process_token(token0, pair)
                                except Exception as e:
                                    print(f"Error processing event: {str(e)}")
                                    print("Full error details:")
                                    import traceback
                                    print(traceback.format_exc())
                                    continue
                        else:
                            # Update single line status with spinning cursor
                            spinner = self.get_next_spinner()
                            status_time = current_time.strftime('%H:%M:%S')
                            print(f"\r[{status_time}] Monitoring pairs... {spinner}", end='', flush=True)
                        
                        last_check_time = current_time
                    except Exception as e:
                        print(f"\nError in main loop iteration: {str(e)}")
                        print("Full error details:")
                        import traceback
                        print(traceback.format_exc())
                
                # Process rescans on interval
                if (current_time - last_rescan_time).total_seconds() >= rescan_interval:
                    print("\n") # Clear line before rescan output
                    await self.process_rescan_tokens()
                    last_rescan_time = current_time
                    print("\nResuming monitoring...")
                
                # Small sleep to prevent CPU overuse
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            print("\n=== Main Loop Cancelled ===")
            print("Shutting down gracefully...")
        except Exception as e:
            print("\n=== Main Loop Fatal Error ===")
            print(f"Unexpected error: {str(e)}")
            print("Full error details:")
            import traceback
            print(traceback.format_exc())
        finally:
            self.running = False
            print("\n=== Main Loop Stopped ===")
            print(f"Final time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")








    async def process_rescan_tokens(self):
        """Process tokens that need rescanning with updated logic for single records"""
        print("\n=== Starting Rescan Process ===")
        scan_records_path = os.path.join(self.folder_name, 'SCAN_RECORDS.db')
        
        try:
            print("Opening SCAN_RECORDS database...")
            with sqlite3.connect(scan_records_path) as db:
                db.execute("PRAGMA datetime_precision = 'seconds'")
                cursor = db.cursor()
                
                # Get current time minus 1 minute
                one_minute_ago = (datetime.now() - timedelta(minutes=1)).strftime('%Y-%m-%d %H:%M:%S')
                
                print("\nExecuting query to find tokens needing rescan...")
                cursor.execute('''
                    SELECT 
                        token_address,
                        token_pair_address,
                        scan_timestamp,
                        total_scans,
                        honeypot_failures
                    FROM scan_records
                    WHERE 
                        honeypot_failures < ?
                        AND total_scans < ?
                        AND scan_timestamp <= ?
                    ORDER BY token_age_hours DESC
                ''', (
                    self.config["scanning"]["honeypot_failure_limit"],
                    self.config["scanning"]["max_rescan_count"],
                    one_minute_ago
                ))
                
                tokens = cursor.fetchall()
                
                if tokens:
                    print(f"\nFound {len(tokens)} tokens to rescan")
                    print("\nToken Details:")
                    for token in tokens:
                        minutes_since_scan = (datetime.now() - datetime.strptime(token[2], '%Y-%m-%d %H:%M:%S')).total_seconds() / 60
                        print(f"Address: {token[0]}")
                        print(f"Pair: {token[1]}")
                        print(f"Last Scan: {token[2]} ({minutes_since_scan:.1f} minutes ago)")
                        print(f"Total Scans: {token[3]}")
                        print(f"Failures: {token[4]}")
                        print("-" * 50)
                    
                    for token_data in tokens:
                        token_address, pair_address = token_data[0], token_data[1]
                        try:
                            print(f"\nProcessing rescan for token: {token_address}")
                            print(f"Current timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Process the token with updated record
                            await self.checker.process_token(token_address, pair_address)
                            
                            # Verify the update
                            cursor.execute('''
                                SELECT total_scans, scan_timestamp 
                                FROM scan_records 
                                WHERE token_address = ?
                            ''', (token_address,))
                            scan_info = cursor.fetchone()
                            print(f"Scan completed - Total scans now: {scan_info[0]}")
                            print(f"Last scan timestamp: {scan_info[1]}")
                            
                            await asyncio.sleep(1)  # Rate limiting between rescans
                            
                        except Exception as e:
                            print(f"Error rescanning {token_address}: {str(e)}")
                            try:
                                cursor.execute('''
                                    UPDATE scan_records 
                                    SET honeypot_failures = honeypot_failures + 1,
                                        last_error = ?
                                    WHERE token_address = ?
                                ''', (str(e), token_address))

                                # Check if token should be moved to xHoneypot_removed
                                cursor.execute('''
                                    SELECT 
                                        token_address,
                                        scan_timestamp,
                                        token_name,
                                        token_symbol,
                                        token_decimals,
                                        token_total_supply,
                                        token_pair_address,
                                        token_age_hours,
                                        hp_simulation_success,
                                        hp_buy_tax,
                                        hp_sell_tax,
                                        hp_transfer_tax,
                                        hp_liquidity_amount,
                                        hp_pair_reserves0,
                                        hp_pair_reserves1,
                                        hp_buy_gas_used,
                                        hp_sell_gas_used,
                                        hp_creation_time,
                                        hp_holder_count,
                                        hp_is_honeypot,
                                        hp_honeypot_reason,
                                        total_scans,
                                        honeypot_failures,
                                        last_error
                                    FROM scan_records 
                                    WHERE token_address = ? 
                                    AND honeypot_failures >= ?
                                    AND hp_is_honeypot = 1
                                ''', (token_address, self.config["scanning"]["honeypot_failure_limit"]))
                                
                                failed_token = cursor.fetchone()
                                if failed_token:
                                    print(f"\nMoving token {token_address} to xHoneypot_removed table")
                                    # Insert into xHoneypot_removed
                                    cursor.execute('''
                                        INSERT INTO xHoneypot_removed (
                                            token_address,
                                            removal_timestamp,
                                            original_scan_timestamp,
                                            token_name,
                                            token_symbol,
                                            token_decimals,
                                            token_total_supply,
                                            token_pair_address,
                                            token_age_hours,
                                            hp_simulation_success,
                                            hp_buy_tax,
                                            hp_sell_tax,
                                            hp_transfer_tax,
                                            hp_liquidity_amount,
                                            hp_pair_reserves0,
                                            hp_pair_reserves1,
                                            hp_buy_gas_used,
                                            hp_sell_gas_used,
                                            hp_creation_time,
                                            hp_holder_count,
                                            hp_is_honeypot,
                                            hp_honeypot_reason,
                                            total_scans,
                                            honeypot_failures,
                                            last_error,
                                            removal_reason
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        failed_token[0],  # token_address
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # removal_timestamp
                                        failed_token[1],  # original_scan_timestamp
                                        failed_token[2],  # token_name
                                        failed_token[3],  # token_symbol
                                        failed_token[4],  # token_decimals
                                        failed_token[5],  # token_total_supply
                                        failed_token[6],  # token_pair_address
                                        failed_token[7],  # token_age_hours
                                        failed_token[8],  # hp_simulation_success
                                        failed_token[9],  # hp_buy_tax
                                        failed_token[10], # hp_sell_tax
                                        failed_token[11], # hp_transfer_tax
                                        failed_token[12], # hp_liquidity_amount
                                        failed_token[13], # hp_pair_reserves0
                                        failed_token[14], # hp_pair_reserves1
                                        failed_token[15], # hp_buy_gas_used
                                        failed_token[16], # hp_sell_gas_used
                                        failed_token[17], # hp_creation_time
                                        failed_token[18], # hp_holder_count
                                        failed_token[19], # hp_is_honeypot
                                        failed_token[20], # hp_honeypot_reason
                                        failed_token[21], # total_scans
                                        failed_token[22], # honeypot_failures
                                        failed_token[23], # last_error
                                        f"Exceeded honeypot failure limit ({self.config['scanning']['honeypot_failure_limit']})"
                                    ))

                                    # Delete from scan_records
                                    cursor.execute('DELETE FROM scan_records WHERE token_address = ?', (token_address,))
                                    print(f"Token {token_address} moved to xHoneypot_removed table")

                                db.commit()
                            except sqlite3.Error as e:
                                print(f"Failed to update error status: {str(e)}")
                            except Exception as e:
                                print(f"Failed to update error status: {str(e)}")
                else:
                    print("\nNo tokens found that need rescanning")
                    print("Criteria:")
                    print(f"- Failures < {self.config['scanning']['honeypot_failure_limit']}")
                    print(f"- Total scans < {self.config['scanning']['max_rescan_count']}")
                    print("- Last scan > 1 minute ago")
            
            print("\n=== Rescan Process Complete ===")
        
        except sqlite3.Error as e:
            print(f"\nDatabase error during rescan: {str(e)}")
            import traceback
            print(traceback.format_exc())
        except Exception as e:
            print(f"\nUnexpected error during rescan process: {str(e)}")
            import traceback
            print(traceback.format_exc())


    def stop(self):
        """Gracefully stop the main loop"""
        self.running = False

if __name__ == "__main__":
    try:
        print("Bot Started (ETH Token Snipe Bot)")
        
        # Get the session folder name
        folder_name = get_folder_name()
        
        # Create the folder
        os.makedirs(folder_name, exist_ok=True)
        
        # Initialize database structure
        initialize_database_structure(folder_name)
        
        # Start the main tracker
        tracker = TokenTrackerMain("config.json", folder_name)
        asyncio.run(tracker.main_loop())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
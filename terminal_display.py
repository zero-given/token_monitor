from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from datetime import datetime
import subprocess
import platform
import os
import json

console = Console()

def open_new_terminal():
    """Open a new terminal window based on the operating system"""
    system = platform.system().lower()
    current_dir = os.getcwd()
    
    if system == "windows":
        subprocess.Popen(f"start cmd /K cd /D {current_dir}", shell=True)
    elif system == "linux":
        subprocess.Popen(["x-terminal-emulator", "-e", f"cd {current_dir} && bash"])
    elif system == "darwin":  # macOS
        subprocess.Popen(["open", "-a", "Terminal", current_dir])

def create_pair_table(event, token0_info, token1_info, pair_info):
    """Create a formatted table for pair information"""
    table = Table(title="🔔 NEW PAIR DETECTED", show_header=True, header_style="bold magenta")
    
    # Block Info Section
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Information", style="green")
    
    table.add_row("Block Number", str(event['blockNumber']))
    table.add_row("Transaction Hash", event['transactionHash'].hex())
    table.add_row("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Pair Contract Section
    table.add_section()
    table.add_row("Pair Address", pair_info['contract_address'])
    table.add_row("Pair Name", pair_info['name'])
    table.add_row("Pair Symbol", pair_info['symbol'])
    table.add_row("Pair ETH Balance", pair_info['eth_balance'])
    
    # Token 0 Section
    table.add_section()
    table.add_row("Token 0 Address", token0_info['contract_address'])
    table.add_row("Token 0 Name", token0_info['name'])
    table.add_row("Token 0 Symbol", token0_info['symbol'])
    table.add_row("Token 0 Decimals", str(token0_info['decimals']))
    table.add_row("Token 0 Total Supply", str(token0_info['total_supply']))
    table.add_row("Token 0 ETH Balance", token0_info['eth_balance'])
    
    # Token 1 Section
    table.add_section()
    table.add_row("Token 1 Address", token1_info['contract_address'])
    table.add_row("Token 1 Name", token1_info['name'])
    table.add_row("Token 1 Symbol", token1_info['symbol'])
    table.add_row("Token 1 Decimals", str(token1_info['decimals']))
    table.add_row("Token 1 Total Supply", str(token1_info['total_supply']))
    table.add_row("Token 1 ETH Balance", token1_info['eth_balance'])
    
    return table

def create_security_table(token_address, honeypot_data, goplus_data):
    """Create a formatted table for security information"""
    # Create main table
    table = Table(title=f"🔍 SECURITY ANALYSIS FOR {token_address}", show_header=True, header_style="bold magenta", 
                 title_style="bold magenta", border_style="magenta")
    
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Result", style="green")
    table.add_column("Risk Level", style="yellow")
    
    # Honeypot Analysis Section
    table.add_row("HONEYPOT ANALYSIS", "", "", style="bold cyan")
    hp_result = honeypot_data.get('honeypotResult', {})
    simulation = honeypot_data.get('simulationResult', {})
    
    is_honeypot = hp_result.get('isHoneypot', False)
    table.add_row(
        "Honeypot Status",
        "❌ YES" if is_honeypot else "✅ NO",
        "🔴 HIGH RISK" if is_honeypot else "🟢 SAFE"
    )
    
    if hp_result.get('honeypotReason'):
        table.add_row("Honeypot Reason", hp_result['honeypotReason'], "🔴 HIGH RISK")
    
    # Tax Information
    buy_tax = simulation.get('buyTax', 0)
    sell_tax = simulation.get('sellTax', 0)
    table.add_row(
        "Buy Tax",
        f"{buy_tax}%",
        "🔴 HIGH" if buy_tax > 10 else "🟡 MEDIUM" if buy_tax > 5 else "🟢 LOW"
    )
    table.add_row(
        "Sell Tax",
        f"{sell_tax}%",
        "🔴 HIGH" if sell_tax > 10 else "🟡 MEDIUM" if sell_tax > 5 else "🟢 LOW"
    )
    
    # GoPlus Analysis Section
    table.add_row("GOPLUS ANALYSIS", "", "", style="bold cyan")
    if 'error' not in goplus_data and 'result' in goplus_data:
        gp_data = goplus_data['result'].get(token_address.lower(), {})
        
        # Basic Token Info
        table.add_row("Token Name", str(gp_data.get('token_name', 'Unknown')), "ℹ️")
        table.add_row("Token Symbol", str(gp_data.get('token_symbol', 'Unknown')), "ℹ️")
        table.add_row("Total Supply", str(gp_data.get('total_supply', 'Unknown')), "ℹ️")
        
        # Holder Information
        holder_count = int(gp_data.get('holder_count', 0))
        table.add_row(
            "Token Holders",
            str(holder_count),
            "🔴 LOW" if holder_count < 50 else "🟡 MEDIUM" if holder_count < 100 else "🟢 HIGH"
        )
        table.add_row("LP Holders", str(gp_data.get('lp_holder_count', 'Unknown')), "ℹ️")
        table.add_row("LP Total Supply", str(gp_data.get('lp_total_supply', 'Unknown')), "ℹ️")
        
        # Tax Information from GoPlus
        gp_buy_tax = gp_data.get('buy_tax', 'Unknown')
        gp_sell_tax = gp_data.get('sell_tax', 'Unknown')
        table.add_row(
            "GoPlus Buy Tax",
            f"{gp_buy_tax}%",
            "🔴 HIGH" if isinstance(gp_buy_tax, (int, float)) and float(gp_buy_tax) > 10 else "🟡 MEDIUM" if isinstance(gp_buy_tax, (int, float)) and float(gp_buy_tax) > 5 else "🟢 LOW"
        )
        table.add_row(
            "GoPlus Sell Tax",
            f"{gp_sell_tax}%",
            "🔴 HIGH" if isinstance(gp_sell_tax, (int, float)) and float(gp_sell_tax) > 10 else "🟡 MEDIUM" if isinstance(gp_sell_tax, (int, float)) and float(gp_sell_tax) > 5 else "🟢 LOW"
        )
        
        # Contract Security Checks
        table.add_row(
            "Is Mintable",
            "⚠️ Yes" if gp_data.get('is_mintable') == '1' else "✅ No",
            "🔴 HIGH RISK" if gp_data.get('is_mintable') == '1' else "🟢 SAFE"
        )
        table.add_row(
            "Is Open Source",
            "✅ Yes" if gp_data.get('is_open_source') == '1' else "❌ No",
            "🟢 SAFE" if gp_data.get('is_open_source') == '1' else "🔴 CAUTION"
        )
        table.add_row(
            "Is Proxy",
            "⚠️ Yes" if gp_data.get('is_proxy') == '1' else "✅ No",
            "🟡 CAUTION" if gp_data.get('is_proxy') == '1' else "🟢 SAFE"
        )
        table.add_row(
            "Can Take Back Ownership",
            "🚨 Yes" if gp_data.get('can_take_back_ownership') == '1' else "✅ No",
            "🔴 HIGH RISK" if gp_data.get('can_take_back_ownership') == '1' else "🟢 SAFE"
        )
        table.add_row(
            "Is Anti-Whale",
            "⚠️ Yes" if gp_data.get('is_anti_whale') == '1' else "✅ No",
            "🟡 MEDIUM" if gp_data.get('is_anti_whale') == '1' else "🟢 SAFE"
        )
        table.add_row(
            "Is Blacklisted",
            "🚨 Yes" if gp_data.get('is_blacklisted') == '1' else "✅ No",
            "🔴 HIGH RISK" if gp_data.get('is_blacklisted') == '1' else "🟢 SAFE"
        )
        table.add_row(
            "Is Whitelisted",
            "✅ Yes" if gp_data.get('is_whitelisted') == '1' else "❌ No",
            "🟢 SAFE" if gp_data.get('is_whitelisted') == '1' else "🟡 CAUTION"
        )
        table.add_row(
            "Has Trading Cooldown",
            "⚠️ Yes" if gp_data.get('trading_cooldown') == '1' else "✅ No",
            "🟡 MEDIUM" if gp_data.get('trading_cooldown') == '1' else "🟢 SAFE"
        )
        
        # Owner and Creator Information
        if gp_data.get('owner_address'):
            table.add_row("Owner Address", gp_data['owner_address'], "ℹ️")
        if gp_data.get('creator_address'):
            table.add_row("Creator Address", gp_data['creator_address'], "ℹ️")
        
        # DEX Information
        if gp_data.get('is_in_dex') == '1':
            table.add_row("DEX Listing", "✅ Listed", "🟢 SAFE")
            if gp_data.get('dex'):
                dex_list = json.loads(gp_data['dex']) if isinstance(gp_data['dex'], str) else gp_data['dex']
                table.add_row("DEX Platforms", ", ".join([d.get('name', 'Unknown') for d in dex_list]), "ℹ️")
        else:
            table.add_row("DEX Listing", "❌ Not Listed", "🔴 CAUTION")
        
        # Additional Risks
        if gp_data.get('other_potential_risks'):
            table.add_row(
                "Other Risks",
                str(gp_data['other_potential_risks']),
                "🔴 HIGH RISK" if gp_data['other_potential_risks'] else "🟢 NONE"
            )
    else:
        table.add_row("GoPlus API Error", str(goplus_data.get('error', 'Unknown error')), "🔴 ERROR")
    
    return table

def log_message(message: str, level: str = "INFO"):
    """Print a formatted log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    style_map = {
        "INFO": "blue",
        "SUCCESS": "green",
        "WARNING": "yellow",
        "ERROR": "red"
    }
    
    icon_map = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌"
    }
    
    text = Text()
    text.append(f"[{timestamp}] ", style="dim")
    text.append(f"{icon_map.get(level, 'ℹ️')} ", style="bold")
    text.append(message, style=style_map.get(level, "white"))
    
    console.print(text) 
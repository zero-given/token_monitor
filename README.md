# Uniswap V2 Pair Monitor

A comprehensive real-time monitoring system for Uniswap V2 pairs with advanced security analysis, token verification, and rich data visualization.

## System Architecture

The system consists of three main components:

1. **Pair Monitor (pair_monitor_enhanced.py)**
   - Connects to Ethereum mainnet via Infura
   - Monitors real-time Uniswap V2 pair creation events
   - Performs deep token analysis and security checks
   - Stores data in SQLite database
   - Maintains session-based monitoring with automatic recovery

2. **Flask Server (server.py)**
   - Provides REST API endpoints for pair data
   - Manages WebSocket connections for real-time updates
   - Handles database operations and data serving
   - Coordinates between monitor and frontend

3. **React Frontend (pair-monitor-ui)**
   - Modern Material-UI based interface
   - Real-time pair updates via WebSocket
   - Rich data visualization for pair analysis
   - Interactive security analysis display
   - Live system status monitoring

## Features

### Pair Detection & Analysis
- Real-time monitoring of new Uniswap V2 pairs
- Automatic pair verification and validation
- Historical pair tracking and session management
- Detailed token metadata collection

### Security Analysis
- Comprehensive honeypot detection
- Buy/sell tax analysis
- Transfer tax verification
- Contract verification status
- Source code analysis
- Top holder analysis
- Liquidity analysis
- Risk scoring system

### Token Verification
- Contract verification status
- Token metadata validation
- Supply distribution analysis
- Owner/creator analysis
- Security vulnerabilities check
- GoPlus API integration for additional security data

### Real-time Updates
- WebSocket-based live updates
- Instant pair detection notifications
- Live security analysis results
- System status monitoring
- Error reporting and recovery

### Data Persistence
- Session-based monitoring
- SQLite database storage
- Automatic recovery from interruptions
- Historical data retention

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Infura API key
- GoPlus API key (optional, for enhanced security checks)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zero-given/token_monitor.git
cd token_monitor
```

2. Install Python dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd pair-monitor-ui
npm install
```

4. Create a `.env` file in the root directory:
```
INFURA_API_KEY=your_infura_api_key_here
INFURA_NETWORK=mainnet
GOPLUS_API_KEY=your_goplus_api_key_here  # Optional
```

## Running the Application

The application consists of two main parts that need to be run in separate terminals:

### Terminal 1: Backend Server
From the root directory:
```bash
# Make sure you're in the project root directory
python server.py
```
You should see initialization logs including:
- "Initializing application..."
- "PairMonitor initialized"
- "Starting Flask server..."
- "Successfully connected to Ethereum network"

### Terminal 2: Frontend Development Server
From the root directory:
```bash
# Navigate to the frontend directory
cd pair-monitor-ui

# Install dependencies (if not done already)
npm install

# Start the development server
npm start
```
You should see:
- "Starting the development server..."
- "Compiled successfully!"
- A browser window should automatically open

### Verifying the Setup

1. Backend Verification:
   - Open `http://localhost:5001/pairs` in your browser
   - You should see JSON data of detected pairs

2. Frontend Verification:
   - Open `http://localhost:3001` in your browser
   - You should see the monitoring interface
   - The connection status should show "Connected"

3. Monitor Logs:
   - Watch the Terminal 1 output for pair detection logs
   - You should see periodic messages like "Completed periodic rescan"

If any component fails to start:
1. Ensure no other processes are using the required ports (5001, 3001)
2. Check that you're in the correct directory for each command
3. Verify that all prerequisites are installed
4. Check the terminal output for any error messages

## Component Details

### Pair Monitor
- Monitors Uniswap V2 factory events
- Performs token contract analysis
- Executes security checks
- Manages monitoring sessions
- Handles network interruptions
- Stores detailed pair data

### Flask Server
- REST API endpoints
- WebSocket server
- Database operations
- Session management
- Error handling
- Data validation

### Frontend
- Material-UI components
- Real-time WebSocket updates
- Rich data visualization
- Interactive analysis display
- System status monitoring
- Error reporting

## API Endpoints

- `GET /pairs`: Retrieve all monitored pairs
- `GET /pairs/<address>`: Get specific pair details
- `GET /status`: System status information
- `WS /`: WebSocket connection for real-time updates

## Data Structure

### Pair Information
```json
{
  "address": "0x...",
  "token0": {
    "address": "0x...",
    "name": "Token Name",
    "symbol": "TKN",
    "decimals": 18,
    "total_supply": "1000000",
    "security_info": {
      "is_honeypot": false,
      "buy_tax": "0",
      "sell_tax": "0",
      "goplus_details": {...}
    }
  },
  "token1": {...},
  "block_number": "12345678",
  "transaction_hash": "0x...",
  "created_at": "2023-...",
  "verified": true
}
```

## Configuration

- Backend port: 5001 (Flask server)
- Frontend port: 3001 (React development server)
- WebSocket: Enabled on backend port
- Database: SQLite (pairs.db)
- Session storage: ./monitoring_sessions/

## Error Handling

- Automatic reconnection to Ethereum network
- Session recovery after interruptions
- Failed transaction retry mechanism
- Error logging and reporting
- User notification system

## License

MIT License 
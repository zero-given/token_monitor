# Uniswap V2 Pair Monitor

A real-time monitoring tool for new Uniswap V2 pairs with security analysis and token verification.

## Features

- Real-time monitoring of new Uniswap V2 pairs
- Security analysis for each token in the pair
- Honeypot detection
- Tax analysis (buy, sell, transfer)
- Contract verification status
- Token holder statistics
- Real-time WebSocket updates
- Modern React frontend with Material-UI
- Python Flask backend with SQLite storage

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Infura API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pair-monitor.git
cd pair-monitor
```

2. Install Python dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install web3 python-dotenv aiohttp flask flask-socketio flask-cors
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
```

## Running the Application

1. Start the Python backend:
```bash
python pair_monitor.py
```

2. Start the React frontend (in a separate terminal):
```bash
cd pair-monitor-ui
npm start
```

3. Open your browser and navigate to `http://localhost:3001`

## Configuration

- Backend port: 5000 (Flask server)
- Frontend port: 3001 (React development server)
- WebSocket: Enabled on backend port
- Database: SQLite (pairs.db)

## License

MIT License 
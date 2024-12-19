from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from typing import List, Dict
import asyncio
from datetime import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    db = sqlite3.connect('pairs.db')
    db.row_factory = dict_factory
    return db

# Store connected WebSocket clients
clients: List[WebSocket] = []

@app.get("/pairs")
async def get_pairs():
    """Get all pairs from the database"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Get pairs with their security checks
        cursor.execute("""
            SELECT p.*, s.* 
            FROM pairs p 
            LEFT JOIN security_checks s ON p.address = s.pair_address 
            ORDER BY p.block_number DESC
            LIMIT 100
        """)
        
        pairs = cursor.fetchall()
        return pairs
    finally:
        db.close()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except:
        clients.remove(websocket)

@app.post("/broadcast")
async def broadcast_message(request: Request):
    """Broadcast a message to all connected WebSocket clients"""
    data = await request.json()
    
    # Convert Web3 types to JSON serializable format
    def convert_to_json_serializable(obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.hex()
        return str(obj)
    
    # Serialize the data
    json_data = json.loads(
        json.dumps(data, default=convert_to_json_serializable)
    )
    
    # Broadcast to all connected clients
    for client in clients:
        try:
            await client.send_json(json_data)
        except:
            clients.remove(client)
    
    return {"status": "success", "message": "Broadcast sent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000) 
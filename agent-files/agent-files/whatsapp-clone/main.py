"""
WhatsApp Web Clone - FastAPI Backend
Real-time messaging application
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Query
from typing import Dict, List, Optional
from datetime import datetime
import json
import uuid

# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="WhatsApp Web Clone",
    description="A real-time messaging application",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============================================================================
# Data Models
# ============================================================================

class Message:
    def __init__(self, sender: str, receiver: str, content: str, timestamp: str = None):
        self.id = str(uuid.uuid4())[:8]
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.read = False
    
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp,
            "read": self.read
        }

class User:
    def __init__(self, username: str, display_name: str):
        self.username = username
        self.display_name = display_name
        self.last_seen = datetime.now().isoformat()
        self.online = False
    
    def to_dict(self):
        return {
            "username": self.username,
            "display_name": self.display_name,
            "last_seen": self.last_seen,
            "online": self.online
        }

# ============================================================================
# In-Memory Storage
# ============================================================================

# Connected WebSocket clients
connected_clients: Dict[str, WebSocket] = {}

# User registry
users: Dict[str, User] = {
    "alice": User("alice", "Alice Johnson"),
    "bob": User("bob", "Bob Smith"),
    "charlie": User("charlie", "Charlie Brown"),
    "diana": User("diana", "Diana Prince"),
    "emma": User("emma", "Emma Wilson"),
}

# Messages storage (simplified - in production use a database)
messages: List[Message] = [
    Message("alice", "bob", "Hey Bob! How are you?"),
    Message("bob", "alice", "Hi Alice! I'm doing great, thanks!"),
    Message("alice", "bob", "Want to grab coffee later?"),
    Message("charlie", "alice", "Alice, can you review my pull request?"),
    Message("diana", "alice", "Meeting at 3pm confirmed ✓"),
]

# ============================================================================
# Connection Manager
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        if username in users:
            users[username].online = True
        
        # Notify others about online status
        await self.broadcast_presence(username, True)
    
    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
        if username in users:
            users[username].online = False
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)
    
    async def broadcast_presence(self, username: str, online: bool):
        message = {
            "type": "presence",
            "username": username,
            "online": online,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)

manager = ConnectionManager()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    with open("templates/index.html", "r") as f:
        return f.read()

@app.get("/api/users")
async def get_users():
    """Get all users with their online status"""
    return {
        "users": [user.to_dict() for user in users.values()],
        "total": len(users)
    }

@app.get("/api/conversations/{username}")
async def get_conversations(username: str):
    """Get all conversations for a user"""
    user_messages = [
        msg.to_dict() for msg in messages 
        if msg.sender == username or msg.receiver == username
    ]
    
    # Group by conversation partner
    conversations = {}
    for msg in user_messages:
        partner = msg["receiver"] if msg["sender"] == username else msg["sender"]
        if partner not in conversations:
            conversations[partner] = []
        conversations[partner].append(msg)
    
    # Get last message for each conversation
    conversation_list = []
    for partner, msgs in conversations.items():
        last_msg = msgs[-1]
        conversation_list.append({
            "partner": partner,
            "partner_name": users[partner].display_name if partner in users else partner,
            "last_message": last_msg["content"],
            "last_message_time": last_msg["timestamp"],
            "messages": msgs
        })
    
    # Sort by last message time
    conversation_list.sort(key=lambda x: x["last_message_time"], reverse=True)
    
    return {"conversations": conversation_list}

@app.get("/api/messages/{user1}/{user2}")
async def get_messages(user1: str, user2: str):
    """Get messages between two users"""
    user_messages = [
        msg.to_dict() for msg in messages 
        if (msg.sender == user1 and msg.receiver == user2) or
           (msg.sender == user2 and msg.receiver == user1)
    ]
    return {"messages": user_messages}

# ============================================================================
# WebSocket Endpoint
# ============================================================================

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                # Create and store new message
                new_message = Message(
                    sender=username,
                    receiver=data["to"],
                    content=data["content"]
                )
                messages.append(new_message)
                
                message_data = new_message.to_dict()
                
                # Send to receiver if online
                if data["to"] in manager.active_connections:
                    await manager.send_personal_message({
                        "type": "message",
                        **message_data
                    }, manager.active_connections[data["to"]])
                
                # Confirm to sender
                await manager.send_personal_message({
                    "type": "message_sent",
                    **message_data
                }, websocket)
                
            elif data["type"] == "typing":
                # Broadcast typing indicator
                if data["to"] in manager.active_connections:
                    await manager.send_personal_message({
                        "type": "typing",
                        "from": username,
                        "to": data["to"]
                    }, manager.active_connections[data["to"]])
    
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast_presence(username, False)

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
FastAPI Advanced Level - File 15: Advanced Features
================================================

This file covers cutting-edge FastAPI features including:
- WebSocket connections
- Server-Sent Events (SSE)
- Advanced routing patterns
- Custom response classes
- Streaming responses
- File uploads and downloads
- GraphQL integration
- Custom OpenAPI schemas
- Advanced dependency injection
- Plugin architecture
- Real-time notifications
- Chat applications

These features enable building modern, interactive web applications.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import uuid
from pathlib import Path
import aiofiles
import csv
import io
from contextlib import asynccontextmanager

# ==================================================
# 1. WEBSOCKET MODELS AND MANAGERS
# ==================================================

class ConnectionManager:
    """
    WebSocket connection manager for handling multiple connections
    """
    
    def __init__(self):
        # Store active connections
        self.active_connections: List[WebSocket] = []
        # Store connections by room/channel
        self.rooms: Dict[str, List[WebSocket]] = {}
        # Store user information
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, room: str = None, user_id: str = None):
        """
        Accept new WebSocket connection
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Add to room if specified
        if room:
            if room not in self.rooms:
                self.rooms[room] = []
            self.rooms[room].append(websocket)
        
        # Store user connection
        if user_id:
            self.user_connections[user_id] = websocket
        
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, room: str = None, user_id: str = None):
        """
        Remove WebSocket connection
        """
        # Remove from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from room
        if room and room in self.rooms:
            if websocket in self.rooms[room]:
                self.rooms[room].remove(websocket)
            if not self.rooms[room]:
                del self.rooms[room]
        
        # Remove user connection
        if user_id and user_id in self.user_connections:
            del self.user_connections[user_id]
        
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send message to specific WebSocket
        """
        await websocket.send_text(message)
    
    async def send_to_user(self, message: str, user_id: str):
        """
        Send message to specific user
        """
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)
    
    async def broadcast(self, message: str):
        """
        Broadcast message to all connected clients
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.active_connections.remove(connection)
    
    async def broadcast_to_room(self, message: str, room: str):
        """
        Broadcast message to specific room
        """
        if room in self.rooms:
            for connection in self.rooms[room]:
                try:
                    await connection.send_text(message)
                except WebSocketDisconnect:
                    self.rooms[room].remove(connection)

# Global connection manager
manager = ConnectionManager()

# ==================================================
# 2. WEBSOCKET MESSAGE MODELS
# ==================================================

class WebSocketMessage(BaseModel):
    """
    WebSocket message model
    """
    type: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    user_id: Optional[str] = None
    room: Optional[str] = None

class ChatMessage(BaseModel):
    """
    Chat message model
    """
    user_id: str
    username: str
    message: str
    room: str
    timestamp: datetime = datetime.now()

# ==================================================
# 3. FASTAPI APPLICATION SETUP
# ==================================================

app = FastAPI(
    title="Advanced Features Demo",
    description="WebSockets, SSE, and advanced FastAPI features",
    version="1.0.0"
)

# Templates for HTML pages
templates = Jinja2Templates(directory="templates")

# ==================================================
# 4. WEBSOCKET ENDPOINTS
# ==================================================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Basic WebSocket endpoint for individual user connections
    """
    await manager.connect(websocket, user_id=user_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo message back with timestamp
            response = {
                "type": "echo",
                "data": message,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
            await manager.send_personal_message(json.dumps(response), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id=user_id)

@app.websocket("/ws/chat/{room}/{user_id}")
async def chat_websocket(websocket: WebSocket, room: str, user_id: str):
    """
    WebSocket endpoint for chat rooms
    """
    await manager.connect(websocket, room=room, user_id=user_id)
    
    # Send join notification
    join_message = {
        "type": "user_joined",
        "data": {
            "user_id": user_id,
            "room": room,
            "timestamp": datetime.now().isoformat()
        }
    }
    await manager.broadcast_to_room(json.dumps(join_message), room)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create chat message
            chat_message = {
                "type": "chat_message",
                "data": {
                    "user_id": user_id,
                    "username": message_data.get("username", user_id),
                    "message": message_data.get("message", ""),
                    "room": room,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Broadcast to room
            await manager.broadcast_to_room(json.dumps(chat_message), room)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room=room, user_id=user_id)
        
        # Send leave notification
        leave_message = {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "room": room,
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.broadcast_to_room(json.dumps(leave_message), room)

@app.websocket("/ws/notifications/{user_id}")
async def notifications_websocket(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time notifications
    """
    await manager.connect(websocket, user_id=user_id)
    
    try:
        # Send welcome notification
        welcome = {
            "type": "notification",
            "data": {
                "title": "Connected",
                "message": f"Welcome {user_id}! You're now connected to notifications.",
                "timestamp": datetime.now().isoformat()
            }
        }
        await manager.send_personal_message(json.dumps(welcome), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id=user_id)

# ==================================================
# 5. SERVER-SENT EVENTS (SSE)
# ==================================================

@app.get("/events/{user_id}")
async def stream_events(user_id: str):
    """
    Server-Sent Events endpoint for real-time updates
    """
    async def event_generator():
        counter = 0
        while True:
            # Check if client is still connected
            if await asyncio.sleep(1):
                pass
            
            # Send periodic updates
            counter += 1
            event_data = {
                "id": counter,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "data": f"Update #{counter}",
                "server_time": time.time()
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            
            # Send every 5 seconds
            await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/events/stock-prices")
async def stock_price_stream():
    """
    SSE endpoint for real-time stock price updates
    """
    import random
    
    async def price_generator():
        stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        
        while True:
            # Generate random stock price updates
            stock = random.choice(stocks)
            price = round(random.uniform(100, 500), 2)
            change = round(random.uniform(-10, 10), 2)
            
            event_data = {
                "symbol": stock,
                "price": price,
                "change": change,
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"event: stock-update\n"
            yield f"data: {json.dumps(event_data)}\n\n"
            
            await asyncio.sleep(2)
    
    return StreamingResponse(
        price_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

# ==================================================
# 6. STREAMING RESPONSES
# ==================================================

@app.get("/stream/csv")
async def stream_csv():
    """
    Stream CSV data as it's generated
    """
    async def generate_csv():
        # CSV header
        yield "id,name,email,created_at\n"
        
        # Generate data rows
        for i in range(10000):
            row = f"{i},User {i},user{i}@example.com,{datetime.now().isoformat()}\n"
            yield row
            
            # Small delay to simulate processing
            await asyncio.sleep(0.001)
    
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"}
    )

@app.get("/stream/json")
async def stream_json():
    """
    Stream JSON data in chunks
    """
    async def generate_json():
        yield '{"users": ['
        
        for i in range(1000):
            user = {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "created_at": datetime.now().isoformat()
            }
            
            if i > 0:
                yield ","
            
            yield json.dumps(user)
            
            await asyncio.sleep(0.01)
        
        yield "]}"
    
    return StreamingResponse(
        generate_json(),
        media_type="application/json"
    )

# ==================================================
# 7. FILE UPLOAD AND DOWNLOAD
# ==================================================

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload file with streaming to disk
    """
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Stream file to disk
    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await file.read(8192):  # Read in 8KB chunks
            await buffer.write(content)
    
    return {
        "filename": filename,
        "original_name": file.filename,
        "size": file_path.stat().st_size,
        "content_type": file.content_type,
        "upload_time": datetime.now().isoformat()
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download file with streaming
    """
    file_path = Path("uploads") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    async def file_generator():
        async with aiofiles.open(file_path, "rb") as file:
            while chunk := await file.read(8192):
                yield chunk
    
    return StreamingResponse(
        file_generator(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================================================
# 8. ADVANCED ROUTING PATTERNS
# ==================================================

class TimedRoute(APIRoute):
    """
    Custom route class that adds timing information
    """
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request: Request):
            start_time = time.time()
            response = await original_route_handler(request)
            process_time = time.time() - start_time
            
            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        return custom_route_handler

# Add custom route
app.router.route_class = TimedRoute

@app.get("/timed-endpoint")
async def timed_endpoint():
    """
    Endpoint that uses custom routing with timing
    """
    # Simulate some processing
    await asyncio.sleep(0.1)
    
    return {
        "message": "This endpoint was timed",
        "timestamp": datetime.now().isoformat()
    }

# ==================================================
# 9. CUSTOM OPENAPI SCHEMA
# ==================================================

def custom_openapi():
    """
    Custom OpenAPI schema with additional information
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Advanced Features API",
        version="1.0.0",
        description="This API demonstrates advanced FastAPI features including WebSockets, SSE, and more.",
        routes=app.routes,
    )
    
    # Add custom information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add custom tags
    openapi_schema["tags"] = [
        {"name": "websockets", "description": "WebSocket endpoints"},
        {"name": "sse", "description": "Server-Sent Events"},
        {"name": "streaming", "description": "Streaming responses"},
        {"name": "files", "description": "File operations"},
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ==================================================
# 10. REAL-TIME NOTIFICATION SYSTEM
# ==================================================

class NotificationService:
    """
    Service for sending real-time notifications
    """
    
    def __init__(self):
        self.manager = manager
    
    async def send_notification(self, user_id: str, title: str, message: str, type: str = "info"):
        """
        Send notification to specific user
        """
        notification = {
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "type": type,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.manager.send_to_user(json.dumps(notification), user_id)
    
    async def broadcast_notification(self, title: str, message: str, type: str = "info"):
        """
        Broadcast notification to all connected users
        """
        notification = {
            "type": "notification",
            "data": {
                "title": title,
                "message": message,
                "type": type,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await self.manager.broadcast(json.dumps(notification))

# Global notification service
notification_service = NotificationService()

@app.post("/notify/{user_id}")
async def send_notification(user_id: str, title: str, message: str, type: str = "info"):
    """
    Send notification to specific user
    """
    await notification_service.send_notification(user_id, title, message, type)
    return {"message": "Notification sent"}

@app.post("/broadcast")
async def broadcast_notification(title: str, message: str, type: str = "info"):
    """
    Broadcast notification to all users
    """
    await notification_service.broadcast_notification(title, message, type)
    return {"message": "Notification broadcasted"}

# ==================================================
# 11. HTML DEMO PAGES
# ==================================================

@app.get("/", response_class=HTMLResponse)
async def get_demo_page():
    """
    Main demo page with all features
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Advanced Features Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; }
            #messages { height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
            input, textarea { width: 100%; padding: 5px; margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Advanced Features Demo</h1>
            
            <div class="section">
                <h2>WebSocket Chat</h2>
                <div id="messages"></div>
                <input type="text" id="messageInput" placeholder="Type a message...">
                <button onclick="sendMessage()">Send</button>
                <button onclick="connectWebSocket()">Connect</button>
                <button onclick="disconnectWebSocket()">Disconnect</button>
            </div>
            
            <div class="section">
                <h2>Server-Sent Events</h2>
                <div id="events"></div>
                <button onclick="startSSE()">Start Events</button>
                <button onclick="stopSSE()">Stop Events</button>
            </div>
            
            <div class="section">
                <h2>Notifications</h2>
                <div id="notifications"></div>
                <input type="text" id="notificationTitle" placeholder="Title">
                <input type="text" id="notificationMessage" placeholder="Message">
                <button onclick="sendNotification()">Send Notification</button>
                <button onclick="broadcastNotification()">Broadcast</button>
            </div>
        </div>
        
        <script>
            let ws = null;
            let eventSource = null;
            const userId = 'user_' + Math.random().toString(36).substr(2, 9);
            
            function connectWebSocket() {
                ws = new WebSocket(`ws://localhost:8000/ws/chat/general/${userId}`);
                
                ws.onopen = function(event) {
                    addMessage('Connected to WebSocket');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    addMessage(`${data.type}: ${JSON.stringify(data.data)}`);
                };
                
                ws.onclose = function(event) {
                    addMessage('WebSocket connection closed');
                };
            }
            
            function disconnectWebSocket() {
                if (ws) {
                    ws.close();
                }
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                if (ws && input.value) {
                    const message = {
                        username: userId,
                        message: input.value
                    };
                    ws.send(JSON.stringify(message));
                    input.value = '';
                }
            }
            
            function addMessage(message) {
                const messages = document.getElementById('messages');
                messages.innerHTML += `<div>${new Date().toLocaleTimeString()}: ${message}</div>`;
                messages.scrollTop = messages.scrollHeight;
            }
            
            function startSSE() {
                eventSource = new EventSource(`/events/${userId}`);
                
                eventSource.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    document.getElementById('events').innerHTML += 
                        `<div>Event: ${JSON.stringify(data)}</div>`;
                };
            }
            
            function stopSSE() {
                if (eventSource) {
                    eventSource.close();
                }
            }
            
            function sendNotification() {
                const title = document.getElementById('notificationTitle').value;
                const message = document.getElementById('notificationMessage').value;
                
                fetch(`/notify/${userId}?title=${title}&message=${message}`, {
                    method: 'POST'
                });
            }
            
            function broadcastNotification() {
                const title = document.getElementById('notificationTitle').value;
                const message = document.getElementById('notificationMessage').value;
                
                fetch(`/broadcast?title=${title}&message=${message}`, {
                    method: 'POST'
                });
            }
            
            // Connect to notifications WebSocket
            const notificationWs = new WebSocket(`ws://localhost:8000/ws/notifications/${userId}`);
            notificationWs.onmessage = function(event) {
                const data = JSON.parse(event.data);
                document.getElementById('notifications').innerHTML += 
                    `<div><strong>${data.data.title}</strong>: ${data.data.message}</div>`;
            };
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/status")
async def get_status():
    """
    Get system status including WebSocket connections
    """
    return {
        "active_connections": len(manager.active_connections),
        "rooms": {room: len(connections) for room, connections in manager.rooms.items()},
        "user_connections": len(manager.user_connections),
        "timestamp": datetime.now().isoformat()
    }

"""
How to Run This Example:
1. Save this file as 15_advanced_features.py
2. Create a templates directory (mkdir templates)
3. Install dependencies: pip install fastapi uvicorn aiofiles python-multipart jinja2
4. Run: uvicorn 15_advanced_features:app --reload
5. Open: http://127.0.0.1:8000/ for the demo page

Key Features Demonstrated:
1. WebSocket connections for real-time communication
2. Server-Sent Events for server-to-client streaming
3. File upload and download with streaming
4. Custom routing with timing
5. Custom OpenAPI schema
6. Real-time notifications
7. Chat room functionality
8. Streaming CSV and JSON responses

WebSocket URLs:
- ws://localhost:8000/ws/{user_id} - Basic WebSocket
- ws://localhost:8000/ws/chat/{room}/{user_id} - Chat room
- ws://localhost:8000/ws/notifications/{user_id} - Notifications

SSE URLs:
- /events/{user_id} - Personal events
- /events/stock-prices - Stock price updates

API Endpoints:
- POST /upload - File upload
- GET /download/{filename} - File download
- GET /stream/csv - Stream CSV data
- GET /stream/json - Stream JSON data
- POST /notify/{user_id} - Send notification
- POST /broadcast - Broadcast notification
- GET /status - System status

Advanced Concepts:
1. Connection management for WebSockets
2. Real-time bidirectional communication
3. Event-driven architecture
4. Streaming large datasets
5. Custom middleware and routing
6. Production-ready WebSocket patterns
7. Error handling for real-time connections
8. Scalable notification systems
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
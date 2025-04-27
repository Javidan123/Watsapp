from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Dict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origians=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        client_ip = websocket.client.host
        self.active_connections[client_ip] = websocket 
        print(f"Connected: {client_ip}")

    async def disconnect(self, websocket: WebSocket, client_name: str):
        for name, connection in self.active_connections.items():
            if connection == websocket:
                del self.active_connections[name]
                print(f"Disconnected: {name}")
                break
    
    async def send_personal_message(self, ip: str, message: str):
        connection = self.active_connections.get(ip)
        if connection:
            await connection.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)


    async def getActiveConnections(self):
        return list(self.active_connections.keys())
    
    async def brodcast_clients(self):
        clients_list  = ",".join(self.active_connections.keys())
        for connection in self.active_connections.values():
            await connection.send_text(f"CLIENT_LIST:{clients_list}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_ip = websocket.client.host
    await websocket.accept()
    await manager.connect(websocket)
    await manager.broadcast_clients()
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_ip} from server: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast_clients()

@app.post("/send/{ip}")
async def send_message_ip(ip: str, message: str):
    await manager.send_personal_message(ip, message)
    return {"message": "Message sent"}

@app.get("/clients")
async def get_clients():
    return {"clients": await manager.getActiveConnections()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.1.127", port=8000)
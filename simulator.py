from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import random
import asyncio
import uvicorn

app = FastAPI()

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your React dev URL if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Client connected ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Client disconnected ({len(self.active_connections)} total)")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    previous_temp = random.uniform(21, 25)

    try:
        while True:
            # Random fluctuation around previous temp
            temperature = round(previous_temp + random.uniform(-0.7, 0.7), 2)
            humidity = round(random.uniform(40, 55), 2)
            power = round(random.uniform(1.0, 1.5), 2)
            voltage = round(random.uniform(228, 232), 1)
            fan_speed = random.randint(1200, 1500)

            # Detect sudden temperature drop (>1°C)
            temp_drop = previous_temp - temperature
            door_opened = temp_drop > 1.0  # simulate alarm condition

            data = {
                "temperature": temperature,
                "humidity": humidity,
                "power": power,
                "voltage": voltage,
                "fan_speed": fan_speed,
                "door_opened": door_opened,
            }

            await manager.broadcast(data)
            previous_temp = temperature
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

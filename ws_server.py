# ws_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List

app = FastAPI()

# Liberar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Salas = { id_sala: [websockets] }
salas: Dict[str, List[WebSocket]] = {}

@app.websocket("/ws/{sala_id}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str):
    await websocket.accept()

    if sala_id not in salas:
        salas[sala_id] = []
    salas[sala_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            for conn in salas[sala_id]:
                if conn != websocket:
                    await conn.send_text(data)
    except WebSocketDisconnect:
        salas[sala_id].remove(websocket)
        if not salas[sala_id]:
            del salas[sala_id]

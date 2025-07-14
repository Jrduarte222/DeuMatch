from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict
import asyncio
import json
import time
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebRTC-Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

salas: Dict[str, Dict[str, WebSocket]] = {}
connection_metadata: Dict[str, Dict] = {}  # connection_id -> info
hosts_por_sala: Dict[str, str] = {}

HEARTBEAT_INTERVAL = 25
CONNECTION_TIMEOUT = 90

@app.websocket("/ws/{sala_id}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str):
    await websocket.accept()
    connection_id = f"{sala_id}_{time.time()}"
    role = "viewer"

    if sala_id not in salas:
        salas[sala_id] = {}
    salas[sala_id][connection_id] = websocket
    connection_metadata[connection_id] = {
        "last_activity": time.time(),
        "sala_id": sala_id,
        "role": role
    }

    logger.info(f"✅ Nova conexão: {connection_id}")
    await websocket.send_json({"type": "connection-id", "connectionId": connection_id})

    try:
        async def send_heartbeats():
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if connection_id in connection_metadata:
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                    except:
                        break

        heartbeat_task = asyncio.create_task(send_heartbeats())

        while True:
            data = await websocket.receive_text()
            connection_metadata[connection_id]["last_activity"] = time.time()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "pong":
                    continue

                if msg_type == "register" and message.get("role") == "host":
                    connection_metadata[connection_id]["role"] = "host"
                    hosts_por_sala[sala_id] = connection_id
                    logger.info(f"🎥 {connection_id} registrado como HOST para sala {sala_id}")
                    continue

                if msg_type == "viewer-join":
                    connection_metadata[connection_id]["role"] = "viewer"
                    host_id = hosts_por_sala.get(sala_id)

                    if host_id and host_id in salas[sala_id]:
                        await salas[sala_id][host_id].send_text(json.dumps({
                            "type": "viewer-join",
                            "viewerId": connection_id  # correto
                        }))
                    continue

                target_id = None
                if msg_type == "offer":
                    target_id = message.get("viewerId")
                elif msg_type == "answer":
                    target_id = hosts_por_sala.get(sala_id)
                elif msg_type == "candidate":
                    target_id = message.get("viewerId")

                if target_id and target_id in salas.get(sala_id, {}):
                    await salas[sala_id][target_id].send_text(data)
                    logger.info(f"➡️ Mensagem {msg_type} de {connection_id} para {target_id}")
                else:
                    logger.warning(f"⚠️ Destinatário {target_id} não encontrado para mensagem {msg_type}")

            except json.JSONDecodeError:
                logger.error(f"⚠️ Mensagem inválida: {data[:200]}")

    except WebSocketDisconnect:
        logger.info(f"❌ Conexão fechada: {connection_id}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        salas[sala_id].pop(connection_id, None)
        connection_metadata.pop(connection_id, None)
        if hosts_por_sala.get(sala_id) == connection_id:
            del hosts_por_sala[sala_id]
        if not salas[sala_id]:
            del salas[sala_id]

@app.get("/ws_status")
async def get_ws_status():
    return JSONResponse(content={
        "salas_ativas": list(salas.keys()),
        "hosts_ativos": hosts_por_sala,
        "conexoes_ativas": sum(len(v) for v in salas.values()),
        "ultimas_atividades": {
            k: time.ctime(v["last_activity"]) for k, v in connection_metadata.items()
        }
    })

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_connections())

async def cleanup_inactive_connections():
    while True:
        await asyncio.sleep(60)
        now = time.time()
        inactive = [
            cid for cid, meta in connection_metadata.items()
            if now - meta["last_activity"] > CONNECTION_TIMEOUT
        ]
        for connection_id in inactive:
            sala_id = connection_metadata[connection_id]["sala_id"]
            try:
                await salas[sala_id][connection_id].close()
            except:
                pass
            salas[sala_id].pop(connection_id, None)
            connection_metadata.pop(connection_id, None)
            if hosts_por_sala.get(sala_id) == connection_id:
                del hosts_por_sala[sala_id]
            if not salas[sala_id]:
                del salas[sala_id]
        if inactive:
            logger.info(f"🧹 Limpeza: {len(inactive)} conexões inativas removidas")

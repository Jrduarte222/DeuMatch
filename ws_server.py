from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from fastapi.responses import JSONResponse
import asyncio
import json
import time
import logging

app = FastAPI()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebRTC-Server")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estruturas de dados
salas: Dict[str, Dict[str, WebSocket]] = {}  # {sala_id: {connection_id: websocket}}
connection_metadata: Dict[str, Dict] = {}    # {connection_id: {last_activity, sala_id, role}}

HEARTBEAT_INTERVAL = 25
CONNECTION_TIMEOUT = 90

@app.websocket("/ws/{sala_id}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str):
    await websocket.accept()
    connection_id = f"{sala_id}_{time.time()}"
    role = "viewer"

    # Registrar conexão
    if sala_id not in salas:
        salas[sala_id] = {}
    salas[sala_id][connection_id] = websocket
    connection_metadata[connection_id] = {
        "last_activity": time.time(),
        "sala_id": sala_id,
        "role": role
    }

    logger.info(f"✅ Nova conexão: {connection_id}")

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

                if message.get("type") == "pong":
                    continue

                # Definir transmissor
                if message.get("type") == "register" and message.get("role") == "host":
                    connection_metadata[connection_id]["role"] = "host"
                    logger.info(f"🎥 {connection_id} registrado como HOST")
                    continue

                # Viewer entrou: notificar host
                if message.get("type") == "viewer-join":
                    host_id = next((cid for cid, meta in connection_metadata.items()
                                    if meta["sala_id"] == sala_id and meta["role"] == "host"), None)
                    if host_id and host_id in salas[sala_id]:
                        await salas[sala_id][host_id].send_text(json.dumps({
                            "type": "viewer-join",
                            "viewerId": connection_id
                        }))
                    continue

                # Mensagens direcionadas (offer, answer, candidate)
                target_id = message.get("viewerId") or message.get("target")
                if target_id and target_id in salas[sala_id]:
                    await salas[sala_id][target_id].send_text(data)
                    logger.info(f"➡️ Mensagem {message.get('type')} enviada para {target_id}")
                else:
                    logger.warning(f"⚠️ Destinatário {target_id} não encontrado")

            except json.JSONDecodeError:
                logger.error(f"⚠️ Mensagem inválida: {data[:200]}")

    except WebSocketDisconnect:
        logger.info(f"❌ Conexão fechada: {connection_id}")
    except Exception as e:
        logger.error(f"⚠️ Erro na conexão {connection_id}: {str(e)}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()

        if sala_id in salas and connection_id in salas[sala_id]:
            del salas[sala_id][connection_id]
            if not salas[sala_id]:
                del salas[sala_id]

        if connection_id in connection_metadata:
            del connection_metadata[connection_id]

@app.get("/ws_status")
async def get_ws_status():
    return JSONResponse(content={
        "salas_ativas": list(salas.keys()),
        "conexoes_ativas": sum(len(v) for v in salas.values()),
        "ultimas_atividades": {
            k: time.ctime(v["last_activity"])
            for k, v in connection_metadata.items()
        }
    })

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
            if sala_id in salas and connection_id in salas[sala_id]:
                try:
                    await salas[sala_id][connection_id].close()
                except:
                    pass
                del salas[sala_id][connection_id]
                if not salas[sala_id]:
                    del salas[sala_id]
            if connection_id in connection_metadata:
                del connection_metadata[connection_id]

        if inactive:
            logger.info(f"🧹 Limpeza: {len(inactive)} conexões inativas removidas")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_inactive_connections())
# ws_server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from fastapi.responses import JSONResponse
import asyncio
import json
import time

app = FastAPI()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estrutura para gerenciar salas e conexões
salas: Dict[str, Dict[str, WebSocket]] = {}  # { sala_id: { connection_id: websocket } }
last_activity: Dict[str, float] = {}  # { connection_id: last_activity_timestamp }

@app.websocket("/ws/{sala_id}")
async def websocket_endpoint(websocket: WebSocket, sala_id: str):
    await websocket.accept()
    connection_id = f"{sala_id}_{time.time()}"

    # Registrar nova conexão
    if sala_id not in salas:
        salas[sala_id] = {}
    salas[sala_id][connection_id] = websocket
    last_activity[connection_id] = time.time()

    print(f"✅ Nova conexão: {connection_id} na sala {sala_id}")

    try:
        # Tarefa para enviar ping periodicamente
        async def send_pings():
            while True:
                await asyncio.sleep(25)  # Ping a cada 25 segundos
                if connection_id in last_activity:
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                    except:
                        break

        ping_task = asyncio.create_task(send_pings())

        # Loop principal para receber mensagens
        while True:
            data = await websocket.receive_text()
            last_activity[connection_id] = time.time()

            try:
                message = json.loads(data)
                
                # Ignorar pong/respostas de heartbeat
                if message.get("type") in ["pong", "heartbeat"]:
                    continue
                    
                print(f"📩 Mensagem recebida na sala {sala_id}: {data[:100]}...")

                # Retransmitir para outros participantes da sala
                for conn_id, conn in salas[sala_id].items():
                    if conn_id != connection_id:
                        try:
                            await conn.send_text(data)
                        except:
                            continue

            except json.JSONDecodeError:
                print(f"⚠️ Mensagem inválida: {data}")

    except WebSocketDisconnect:
        print(f"❌ Conexão fechada: {connection_id}")
    except Exception as e:
        print(f"⚠️ Erro na conexão {connection_id}: {str(e)}")
    finally:
        # Limpeza
        ping_task.cancel()
        if sala_id in salas and connection_id in salas[sala_id]:
            del salas[sala_id][connection_id]
            if not salas[sala_id]:
                del salas[sala_id]
        if connection_id in last_activity:
            del last_activity[connection_id]

# Rota para verificar conexões ativas
@app.get("/ws_status")
async def ws_status():
    active_connections = sum(len(connections) for connections in salas.values())
    return JSONResponse(content={
        "salas_ativas": list(salas.keys()),
        "total_conexoes": active_connections,
        "ultima_atividade": {k: time.ctime(v) for k, v in last_activity.items()}
    })

# Tarefa em background para limpar conexões inativas
@app.on_event("startup")
async def startup_event():
    async def cleanup_inactive():
        while True:
            await asyncio.sleep(60)
            now = time.time()
            inactive = [cid for cid, last in last_activity.items() 
                       if now - last > 90]  # 1.5min sem atividade
            
            for connection_id in inactive:
                sala_id = connection_id.split("_")[0]
                if sala_id in salas and connection_id in salas[sala_id]:
                    try:
                        await salas[sala_id][connection_id].close()
                    except:
                        pass
                    del salas[sala_id][connection_id]
                    if not salas[sala_id]:
                        del salas[sala_id]
                if connection_id in last_activity:
                    del last_activity[connection_id]
                
            print(f"🧹 Limpeza: {len(inactive)} conexões inativas removidas")

    asyncio.create_task(cleanup_inactive())
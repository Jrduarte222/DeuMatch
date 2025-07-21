from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from database import get_db
from models import Movimento
from datetime import datetime, timedelta

router = APIRouter()

# === CRIAR MOVIMENTO (pedido de desbloqueio) ===
@router.post("/movimentos")
def criar_movimento(
    cliente_id: int = Form(...),
    participante_id: int = Form(...),
    tipo: str = Form(...),  # 'fotos', 'videos' ou 'acompanhante'
    valor: int = Form(1000),  # R$10,00 padrão
    metodo: str = Form("pix"),
    db: Session = Depends(get_db)
):
    if tipo not in ["fotos", "videos", "acompanhante"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'fotos', 'videos' ou 'acompanhante'.")

    # Verifica se já existe um pedido "aguardando" para este cliente/participante/tipo
    existente = db.query(Movimento).filter(
        Movimento.cliente_id == cliente_id,
        Movimento.participante_id == participante_id,
        Movimento.tipo == tipo,
        Movimento.status == "aguardando"
    ).first()

    if existente:
        return {"message": "Pedido já existe", "movimento": existente.id}

    # Cria um novo movimento
    movimento = Movimento(
        cliente_id=cliente_id,
        participante_id=participante_id,
        valor=valor,
        metodo=metodo,
        tipo=tipo,
        status="aguardando",
        expiracao=None  # Definida após liberação
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return {"message": "Pedido registrado com sucesso", "movimento": movimento.id}


# === LISTAR TODOS MOVIMENTOS (ADMIN) ===
@router.get("/movimentos/list")
def listar_todos_movimentos(db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).order_by(Movimento.timestamp.desc()).all()
    return [
        {
            "id": m.id,
            "cliente_id": m.cliente_id,
            "participante_id": m.participante_id,
            "tipo": m.tipo,
            "valor": m.valor,
            "metodo": m.metodo,
            "status": m.status,
            "repassado": m.repassado,
            "timestamp": m.timestamp,
            "expiracao": m.expiracao,
        }
        for m in movimentos
    ]


# === LISTAR MOVIMENTOS DE UM CLIENTE ===
@router.get("/movimentos/cliente/{cliente_id}")
def listar_movimentos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).filter(Movimento.cliente_id == cliente_id).all()
    resultado = {}
    agora = datetime.utcnow()

    for mov in movimentos:
        status = mov.status or "aguardando"

        # Verifica expiração
        if status == "liberado" and mov.expiracao and mov.expiracao < agora:
            mov.status = "expirado"
            db.commit()
            status = "expirado"

        # Monta o retorno compatível com o frontend
        if status == "liberado":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = True
        elif status == "aguardando":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = "aguardando"
        elif status == "expirado":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = False

    return resultado


# === LIBERAR PEDIDO (ADMIN) ===
@router.put("/movimentos/liberar/{movimento_id}")
def liberar_movimento(movimento_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == movimento_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado.")
    movimento.status = "liberado"
    movimento.expiracao = datetime.utcnow() + timedelta(hours=1)  # expira em 1 hora
    db.commit()
    return {"message": f"Movimento {movimento.id} liberado por 1 hora."}


# === REPASSAR PAGAMENTO (ADMIN) ===
@router.post("/movimentos/repassar/{movimento_id}")
def repassar_pagamento(movimento_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == movimento_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado.")
    if movimento.repassado:
        raise HTTPException(status_code=400, detail="Pagamento já foi repassado.")
    movimento.repassado = True
    db.commit()
    return {"message": "Pagamento repassado com sucesso"}

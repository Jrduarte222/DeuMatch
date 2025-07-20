from fastapi import APIRouter, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Movimento
from datetime import datetime, timedelta

router = APIRouter()

# === CRIAR MOVIMENTO (pedido de desbloqueio) ===
@router.post("/movimentos")
def criar_movimento(
    cliente_id: int = Form(...),
    participante_id: int = Form(...),
    tipo: str = Form(...),  # fotos ou videos
    valor: int = Form(1000),  # R$10,00
    metodo: str = Form("pix"),
    db: Session = Depends(get_db)
):
    print(f"[DEBUG] Criando movimento: cliente={cliente_id}, participante={participante_id}, tipo={tipo}, valor={valor}, metodo={metodo}")
    if tipo not in ["fotos", "videos"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'fotos' ou 'videos'.")

    movimento = Movimento(
        cliente_id=cliente_id,
        participante_id=participante_id,
        valor=valor,
        metodo=metodo,
        tipo=tipo,
        status="aguardando",
        expiracao=None  # será definida apenas quando o admin liberar
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    print(f"[DEBUG] Movimento criado: {movimento.__dict__}")
    return {"message": "Pedido registrado com sucesso", "movimento": movimento}


# === LISTAR TODOS MOVIMENTOS (ADMIN) ===
@router.get("/movimentos/list")
def listar_todos_movimentos(db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).all()
    return [m.__dict__ for m in movimentos]


# === LISTAR MOVIMENTOS DE UM CLIENTE ===
@router.get("/movimentos/cliente/{cliente_id}")
def listar_movimentos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).filter(Movimento.cliente_id == cliente_id).all()
    resultado = {}
    agora = datetime.utcnow()

    for mov in movimentos:
        status = mov.status or "aguardando"

        # Verificar se o desbloqueio expirou
        if status == "liberado" and mov.expiracao and mov.expiracao < agora:
            print(f"[DEBUG] Desbloqueio expirado - mov.id={mov.id}")
            mov.status = "expirado"
            db.commit()
            status = "expirado"

        if status == "liberado":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = True
        elif status == "aguardando":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = "aguardando"
        elif status == "expirado":
            # Considera como bloqueado (não retorna nada liberado)
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = None

    print(f"[DEBUG] Movimentos cliente {cliente_id}: {resultado}")
    return resultado


# === LIBERAR PEDIDO (ADMIN) ===
@router.put("/movimentos/liberar/{movimento_id}")
def liberar_movimento(movimento_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == movimento_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado.")
    movimento.status = "liberado"
    movimento.expiracao = datetime.utcnow() + timedelta(hours=1)  # Expira em 1 hora
    db.commit()
    return {"message": f"Movimento {movimento.id} liberado por 1 hora."}


# === REPASSAR PAGAMENTO ===
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

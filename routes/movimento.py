from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Movimento

router = APIRouter()

# === CRIAR MOVIMENTO (pedido de desbloqueio) ===
@router.post("/movimentos")
def criar_movimento(
    cliente_id: int,
    participante_id: int,
    tipo: str,  # fotos ou videos
    valor: int = 1000,  # R$10,00
    metodo: str = "pix",
    db: Session = Depends(get_db)
):
    if tipo not in ["fotos", "videos"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'fotos' ou 'videos'.")

    movimento = Movimento(
        cliente_id=cliente_id,
        participante_id=participante_id,
        valor=valor,
        metodo=metodo,
        tipo=tipo,
        status="aguardando"
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return {"message": "Pedido registrado com sucesso", "movimento": movimento}


# === LISTAR MOVIMENTOS ===
@router.get("/movimentos", response_model=List[dict])
def listar_movimentos(db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).all()
    return [m.__dict__ for m in movimentos]


# === LISTAR MOVIMENTOS DE UM CLIENTE ===
@router.get("/movimentos/cliente/{cliente_id}")
def listar_movimentos_cliente(cliente_id: int, db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).filter(Movimento.cliente_id == cliente_id).all()
    resultado = {}
    for mov in movimentos:
        if mov.status == "liberado":
            resultado.setdefault(mov.participante_id, {})[mov.tipo] = True
    return resultado


# === LIBERAR PEDIDO (ADMIN) ===
@router.put("/movimentos/liberar/{movimento_id}")
def liberar_movimento(movimento_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == movimento_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado.")
    movimento.status = "liberado"
    db.commit()
    return {"message": "Movimento liberado com sucesso"}


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

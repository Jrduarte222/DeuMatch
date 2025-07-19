from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from models import Movimento

router = APIRouter()

# === SCHEMAS ===
class MovimentoSchema(BaseModel):
    cliente_id: int
    participante_id: int
    valor: int
    metodo: str  # "pix" ou "cartao"
    tipo: str    # "fotos" ou "videos"

class MovimentoResponse(BaseModel):
    id: int
    cliente_id: int
    participante_id: int
    valor: int
    metodo: str
    tipo: str
    repassado: bool

    class Config:
        orm_mode = True

# === REGISTRAR MOVIMENTO ===
@router.post("/movimentos")
def registrar_movimento(mov: MovimentoSchema, db: Session = Depends(get_db)):
    if mov.tipo not in ["fotos", "videos"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'fotos' ou 'videos'.")

    movimento = Movimento(
        cliente_id=mov.cliente_id,
        participante_id=mov.participante_id,
        valor=mov.valor,
        metodo=mov.metodo,
        tipo=mov.tipo,
        repassado=False
    )
    db.add(movimento)
    db.commit()
    db.refresh(movimento)
    return {"message": "Movimento registrado com sucesso", "movimento": movimento}

# === LISTAR MOVIMENTOS DO CLIENTE (DESBLOQUEIOS) ===
@router.get("/movimentos/cliente/{cliente_id}")
def listar_desbloqueios(cliente_id: int, db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).filter(Movimento.cliente_id == cliente_id).all()
    desbloqueios = {}

    for mov in movimentos:
        if mov.participante_id not in desbloqueios:
            desbloqueios[mov.participante_id] = {"fotos": False, "videos": False}
        if mov.tipo == "fotos":
            desbloqueios[mov.participante_id]["fotos"] = True
        elif mov.tipo == "videos":
            desbloqueios[mov.participante_id]["videos"] = True

    return desbloqueios

# === LISTAR TODOS OS MOVIMENTOS ===
@router.get("/movimentos", response_model=List[MovimentoResponse])
def listar_movimentos(db: Session = Depends(get_db)):
    return db.query(Movimento).all()

# === REPASSAR PAGAMENTO ===
@router.post("/movimentos/repassar/{mov_id}")
def repassar_pagamento(mov_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == mov_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado.")
    movimento.repassado = True
    db.commit()
    return {"message": "Pagamento repassado com sucesso."}

# === LIMPAR MOVIMENTOS ===
@router.delete("/movimentos/limpar")
def limpar_movimentos(db: Session = Depends(get_db)):
    db.query(Movimento).delete()
    db.commit()
    return {"message": "Todos os movimentos foram removidos."}

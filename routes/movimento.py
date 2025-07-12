from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import Movimento, User
from datetime import date

router = APIRouter()

# Modelo de entrada
class MovimentoRequest(BaseModel):
    cliente_id: int
    participante_id: int
    valor: int
    metodo: str

# POST /movimentos – registrar novo desbloqueio
@router.post("/movimentos")
def registrar_movimento(
    dados: MovimentoRequest,
    db: Session = Depends(get_db),
):
    novo = Movimento(
        cliente_id=dados.cliente_id,
        participante_id=dados.participante_id,
        valor=dados.valor,
        metodo=dados.metodo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"mensagem": "Movimento registrado", "movimento_id": novo.id}

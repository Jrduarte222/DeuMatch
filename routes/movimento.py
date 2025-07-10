from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Movimento, User
from datetime import date
from typing import List
from fastapi import Depends

router = APIRouter()


# POST /movimentos – registrar novo desbloqueio
@router.post("/movimentos")
def registrar_movimento(
    cliente_id: int,
    participante_id: int,
    valor: int,
    metodo: str,
    db: Session = Depends(get_db),
):
    novo = Movimento(
        cliente_id=cliente_id,
        participante_id=participante_id,
        valor=valor,
        metodo=metodo,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return {"mensagem": "Movimento registrado", "movimento_id": novo.id}


# GET /movimentos/hoje – listar movimentos do dia
@router.get("/movimentos/hoje")
def listar_movimentos_do_dia(db: Session = Depends(get_db)):
    hoje = date.today()
    movimentos = (
        db.query(Movimento, User.name.label("cliente_nome"), User.email.label("cliente_email"))
        .join(User, Movimento.cliente_id == User.id)
        .filter(Movimento.timestamp >= hoje)
        .all()
    )

    resultado = []
    for m, cliente_nome, cliente_email in movimentos:
        participante = db.query(User).filter_by(id=m.participante_id).first()
        resultado.append({
            "id": m.id,
            "cliente": cliente_nome,
            "cliente_email": cliente_email,
            "participante": participante.name if participante else "Desconhecido",
            "valor": m.valor,
            "metodo": m.metodo,
            "hora": m.timestamp.strftime("%H:%M"),
            "repassado": m.repassado,
        })

    return resultado


# PATCH /movimentos/repassar/{id} – marcar como repassado
@router.patch("/movimentos/repassar/{id}")
def marcar_como_repassado(id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado")

    movimento.repassado = True
    db.commit()
    return {"mensagem": "Marcado como repassado"}

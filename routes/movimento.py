from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models import Movimento, User
from datetime import date
from datetime import datetime, timedelta

router = APIRouter()

# Modelo de entrada
class MovimentoRequest(BaseModel):
    cliente_id: int
    participante_id: int
    valor: int
    metodo: str

class MovimentoResponse(BaseModel):
    id: int
    cliente_id: int
    participante_id: int
    cliente: Optional[str] = None
    cliente_email: Optional[str] = None
    participante: Optional[str] = None
    valor: int
    metodo: str
    data: str
    hora: str
    repassado: bool

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

@router.get("/movimentos/cliente/{cliente_id}")
def participantes_desbloqueados(cliente_id: int, db: Session = Depends(get_db)):
    uma_hora_atras = datetime.utcnow() - timedelta(hours=1)
    
    movimentos = db.query(Movimento).filter(
        Movimento.cliente_id == cliente_id,
        Movimento.timestamp >= uma_hora_atras
    ).all()
    
    ids = list({m.participante_id for m in movimentos})
    return ids
@router.get("/movimentos/list")
def listar_movimentos(db: Session = Depends(get_db)):
    movimentos = db.query(Movimento).order_by(Movimento.timestamp.desc()).all()
    
    # Enriquecer os dados com informações dos usuários
    resultados = []
    for mov in movimentos:
        cliente = db.query(User).filter(User.id == mov.cliente_id).first()
        participante = db.query(User).filter(User.id == mov.participante_id).first()
        
        resultados.append({
            "id": mov.id,
            "cliente_id": mov.cliente_id,
            "participante_id": mov.participante_id,
            "cliente": cliente.name if cliente else "Cliente desconhecido",
            "cliente_email": cliente.email if cliente else "",
            "participante": participante.name if participante else "Participante desconhecido",
            "valor": mov.valor,
            "metodo": mov.metodo,
            "data": mov.timestamp.date().isoformat(),
            "hora": mov.timestamp.time().strftime("%H:%M"),
            "repassado": mov.repassado
        })
    
    return resultados

# Rota para marcar como repassado
@router.patch("/movimentos/repassar/{movimento_id}")
def marcar_repassado(movimento_id: int, db: Session = Depends(get_db)):
    movimento = db.query(Movimento).filter(Movimento.id == movimento_id).first()
    if not movimento:
        raise HTTPException(status_code=404, detail="Movimento não encontrado")
    
    movimento.repassado = True
    db.commit()
    
    # Atualizar saldo do participante
    participante = db.query(User).filter(User.id == movimento.participante_id).first()
    if participante:
        participante.saldo += movimento.valor
        db.commit()
    
    return {"mensagem": "Pagamento marcado como repassado"}

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User

router = APIRouter()

ADMIN_PIX = "51985984212"

class PagamentoRequest(BaseModel):
    participante_id: int
    valor: int = 1000  # Valor padrão R$10,00

@router.post("/pagamento/pix")
def solicitar_pagamento(dados: PagamentoRequest, db: Session = Depends(get_db)):
    participante = db.query(User).filter(User.id == dados.participante_id).first()
    if not participante or participante.role != "participante":
        raise HTTPException(status_code=404, detail="Participante não encontrado")

    return {
        "valor": dados.valor,
        "valor_reais": f"R$ {dados.valor / 100:.2f}",
        "qrcode_img": "/qr-admin-pix.jpg",
        "chave_pix_admin": ADMIN_PIX,
        "recebedor": "Admin"
    }

# app/routes/pagamento.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User

router = APIRouter()

# Chave Pix fixa do administrador
ADMIN_PIX = "51985984212"

# Modelo de entrada via JSON
class PagamentoRequest(BaseModel):
    participante_id: int

@router.post("/pagamento/pix")
def solicitar_pagamento(dados: PagamentoRequest, db: Session = Depends(get_db)):
    participante = db.query(User).filter(User.id == dados.participante_id).first()
    if not participante or participante.role != "participante":
        raise HTTPException(status_code=404, detail="Participante não encontrado")

    return {
        "valor": 1000,
        "valor_reais": "R$ 10,00",
        "qrcode_img": "/qrcode-pix.png",  # imagem salva em public/
        "chave_pix_admin": ADMIN_PIX,
        "recebedor": "Admin"
    }


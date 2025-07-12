from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter()

# Chave Pix fixa do administrador (em fallback)
ADMIN_PIX = "51985984212"

@router.post("/pagamento/pix")
def solicitar_pagamento(participante_id: int, db: Session = Depends(get_db)):
    participante = db.query(User).filter(User.id == participante_id).first()
    if not participante or participante.role != "participante":
        raise HTTPException(status_code=404, detail="Participante não encontrado")

    # Usa a chave do participante se houver, senão usa a chave padrão
    chave_destino = participante.pix or ADMIN_PIX

    return {
        "valor": 1000,  # em centavos
        "valor_reais": "R$ 10,00",
        "mensagem": "Pagamento via PicPay – inclui taxa de R$ 2,00",
        "link_picpay": f"https://picpay.me/{chave_destino}/10.00",
        "chave_pix_admin": chave_destino,
        "recebedor": participante.name
    }

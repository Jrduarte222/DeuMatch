from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User

router = APIRouter()

# Chave Pix fixa do administrador
ADMIN_PIX = "51985984212"

@router.post("/pagamento/solicitar")
def solicitar_pagamento(participante_id: int, db: Session = Depends(get_db)):
    participante = db.query(User).filter(User.id == participante_id).first()
    if not participante or participante.role != "participante":
        raise HTTPException(status_code=404, detail="Participante não encontrado")

    return {
        "valor": 1000,  # em centavos
        "valor_reais": "R$ 10,00",
        "mensagem": "Pagamento via PicPay – inclui taxa de R$ 2,00",
        "link_picpay": f"https://picpay.me/{ADMIN_PIX}/10.00",
        "chave_pix_admin": ADMIN_PIX,
        "recebedor": participante.name
    }

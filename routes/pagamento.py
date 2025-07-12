from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Movimento, User

router = APIRouter()

# POST /pagamento/pix – gera link PicPay com a chave do admin
@router.post("/pagamento/pix")
def gerar_pagamento(participante_id: int, db: Session = Depends(get_db)):
    # Buscar participante
    participante = db.query(User).filter_by(id=participante_id, role="participante").first()
    if not participante:
        raise HTTPException(status_code=404, detail="Participante não encontrado")

    # Buscar administrador com chave Pix
    admin = db.query(User).filter_by(role="administrador").first()
    if not admin or not admin.pix:
        raise HTTPException(status_code=400, detail="Administrador sem chave Pix cadastrada")

    # Criar link PicPay
    valor = 10.00
    link_picpay = f"https://picpay.me/{admin.pix}/{valor:.2f}"

    return {
        "mensagem": "Link de pagamento gerado",
        "link_picpay": link_picpay,
        "chave_pix_admin": admin.pix,
        "valor": valor,
        "participante_id": participante_id,
        "admin_id": admin.id
    }

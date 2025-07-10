from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Boolean
from database import Base
from datetime import datetime

# Tabela de usuários
class User(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # participante, cliente, administrador
    bio = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    foto1 = Column(String, nullable=True)
    foto2 = Column(String, nullable=True)
    galeria = Column(Text, nullable=True)
    video = Column(String, nullable=True)

    # Campos para pagamento e controle
    forma_pagamento = Column(String(50), nullable=True)       # Clientes
    forma_recebimento = Column(String(50), nullable=True)     # Participantes
    chave_pix = Column(String(100), nullable=True)            # Participantes
    tipo_chave_pix = Column(String(50), nullable=True)        # CPF, celular, etc.
    valor_sugerido = Column(String(20), nullable=True)        # Ex: "20.00"
    saldo = Column(Integer, default=0)                        # Em centavos

    # Termos de uso
    aceitou_termos = Column(Boolean, default=False)

# Tabela de mensagens do chat
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

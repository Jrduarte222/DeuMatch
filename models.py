from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Boolean, ForeignKey
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
    video = Column(Text, nullable=True)
    exclusao_pendente = Column(Boolean, default=False)

    # Campos para pagamento e controle
    forma_pagamento = Column(String(50), nullable=True)       # Clientes
    forma_recebimento = Column(String(50), nullable=True)     # Participantes
    chave_pix = Column(String(100), nullable=True)            # Participantes
    tipo_chave_pix = Column(String(50), nullable=True)        # CPF, celular, etc.
    saldo = Column(Integer, default=0)                        # Em centavos
    valor_acompanhante = Column(Integer, default=0)           # Valor fixo do serviço (centavos)

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


# Tabela de movimentações financeiras
class Movimento(Base):
    __tablename__ = "movimentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    participante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(String(20), nullable=False)                 # fotos, videos, acompanhante
    valor = Column(Integer, nullable=False)                   # valor em centavos
    metodo = Column(String(20), nullable=False)               # "pix" ou "cartao"
    status = Column(String(20), default="aguardando")         # aguardando ou liberado
    timestamp = Column(DateTime, default=datetime.utcnow)
    repassado = Column(Boolean, default=False)
    expiracao = Column(DateTime, nullable=True)               # hora de expiração do desbloqueio

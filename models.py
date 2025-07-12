from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # participante, cliente, administrador
    bio = Column(Text, nullable=True)
    status = Column(String(50), default='ativo')  # ativo, suspenso
    foto1 = Column(String, nullable=True)
    foto2 = Column(String, nullable=True)
    video = Column(String, nullable=True)

    # Campos para pagamento
    forma_pagamento = Column(String(50), nullable=True)       # Clientes
    forma_recebimento = Column(String(50), nullable=True)     # Participantes
    chave_pix = Column(String(100), nullable=True)            # Participantes
    tipo_chave_pix = Column(String(50), nullable=True)        # CPF, celular, etc.
    saldo = Column(Integer, default=0)                        # Em centavos

    # Termos e controle
    aceitou_termos = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relações
    movimentos_cliente = relationship("Movimento", foreign_keys="Movimento.cliente_id", back_populates="cliente")
    movimentos_participante = relationship("Movimento", foreign_keys="Movimento.participante_id", back_populates="participante")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    content = Column(Text, nullable=False)  # Alterado de String para Text
    timestamp = Column(DateTime, default=datetime.utcnow)
    lida = Column(Boolean, default=False)

    # Relações
    remetente = relationship("User", foreign_keys=[sender_id])
    destinatario = relationship("User", foreign_keys=[receiver_id])

class Movimento(Base):
    __tablename__ = "movimentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    participante_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    valor = Column(Integer, nullable=False)  # valor em centavos
    metodo = Column(String(20), nullable=False)  # "pix" ou "cartao"
    timestamp = Column(DateTime, default=datetime.utcnow)
    repassado = Column(Boolean, default=False)
    data_repassado = Column(DateTime, nullable=True)
    
    # Relações
    cliente = relationship("User", foreign_keys=[cliente_id], back_populates="movimentos_cliente")
    participante = relationship("User", foreign_keys=[participante_id], back_populates="movimentos_participante")

    # Índices para melhor performance nas consultas
    __table_args__ = (
        Index('idx_movimentos_cliente', 'cliente_id'),
        Index('idx_movimentos_participante', 'participante_id'),
        Index('idx_movimentos_timestamp', 'timestamp'),
        Index('idx_movimentos_repassado', 'repassado'),
    )
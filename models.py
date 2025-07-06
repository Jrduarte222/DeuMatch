from sqlalchemy import Column, String, Text, BigInteger, Integer, DateTime
from database import Base
from datetime import datetime

# Tabela de usuários
class User(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    bio = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    foto1 = Column(String, nullable=True)
    foto2 = Column(String, nullable=True)
    galeria = Column(Text, nullable=True)
    video = Column(String, nullable=True)

# Tabela de mensagens do chat
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, nullable=False)
    receiver_id = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

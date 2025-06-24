from sqlalchemy import Column, Integer, String, Text
from database import Base

class User(Base):  # Renomeado para manter consistência com o users.py
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    bio = Column(Text)
    status = Column(String)
    foto1 = Column(String)        # primeira imagem visível
    foto2 = Column(String)        # segunda imagem visível
    galeria = Column(Text)        # demais imagens separadas por vírgula

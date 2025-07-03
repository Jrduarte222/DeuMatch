from sqlalchemy import Column, String, Text, BigInteger
from database import Base


class User(Base):
    __tablename__ = "usuarios"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False)
    bio = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    foto1 = Column(String, nullable=True)         # primeira imagem visível
    foto2 = Column(String, nullable=True)         # segunda imagem visível
    galeria = Column(Text, nullable=True)         # demais imagens separadas por vírgula
    video = Column(String, nullable=True)         # vídeo do perfil

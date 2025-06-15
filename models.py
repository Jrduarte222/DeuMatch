from sqlalchemy import Column, Integer, String, Text
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    bio = Column(Text)
    role = Column(String)
    status = Column(String)
    fotos = Column(Text)  # salvará os nomes das imagens separadas por vírgula

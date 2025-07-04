import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Busca a variável DATABASE_URL do ambiente (Render)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError("Variável DATABASE_URL não encontrada no ambiente.")

# Cria o engine de conexão
engine = create_engine(DATABASE_URL)

# Sessão padrão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

# Função para obter sessão do banco (usada em Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

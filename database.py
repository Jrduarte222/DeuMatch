import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis do .env localmente
load_dotenv()

# Busca a variável DATABASE_URL (Render ou local)
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria o engine de conexão
engine = create_engine(DATABASE_URL)

# Sessão padrão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos
Base = declarative_base()

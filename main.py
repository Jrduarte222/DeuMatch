from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routes.users import router as users_router
import os

app = FastAPI()

# CORS liberado (para conectar com frontend e painel admin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Após testes, restrinja para segurança
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação automática das tabelas
Base.metadata.create_all(bind=engine)

# Monta pasta de arquivos estáticos (fotos)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Importa e inclui todas as rotas de users.py
app.include_router(users_router)

# Rota raiz
@app.get("/")
def root():
    return {"status": "API Deu Match está ativa 🚀"}

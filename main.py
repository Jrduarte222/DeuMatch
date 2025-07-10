from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from routes import users, chat, movimento  # Importando tudo de uma vez (boa prática)

app = FastAPI()

# Inclusão das rotas
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(movimento.router)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por domínio seguro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação automática das tabelas
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "API Deu Match está ativa com Cloudinary 🚀"}

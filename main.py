from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import users, chat
from database import Base, engine
from routes import movimentos

app = FastAPI()
app.include_router(movimentos.router)

# Inclusão das rotas
app.include_router(users.router)
app.include_router(chat.router)

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

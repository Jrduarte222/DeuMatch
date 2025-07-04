# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes import users
from database import Base, engine

app = FastAPI()

# Inclusão das rotas definidas em users.py
app.include_router(users.router)

# Middleware CORS (libera tudo — ideal para testes e apps públicos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por domínio seguro
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação automática das tabelas
Base.metadata.create_all(bind=engine)


# Rota raiz de verificação
@app.get("/")
def root():
    return {"status": "API Deu Match está ativa com Cloudinary 🚀"}

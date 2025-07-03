from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from database import Base, engine, SessionLocal
from models import User
from routes import users
import os
import cloudinary.uploader
from cloudinary_config import *

app = FastAPI()

app.include_router(users.router)

# CORS liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação das tabelas
Base.metadata.create_all(bind=engine)

# Servir arquivos estáticos (mantido para compatibilidade)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"status": "API Deu Match está ativa com Cloudinary 🚀"}

# Rota de registro
@app.post("/users/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    bio: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    fotos: list[UploadFile] = File(...),
    video: UploadFile = File(None)
):
    db = SessionLocal()
    nomes_imagens = []

    for foto in fotos:
        result = cloudinary.uploader.upload(await foto.read(), folder="deumatch/fotos")
        nomes_imagens.append(result['secure_url'])

    video_url = None
    if video:
        video_result = cloudinary.uploader.upload(await video.read(), folder="deumatch/videos", resource_type="video")
        video_url = video_result['secure_url']

    usuario = User(
        name=name,
        email=email,
        bio=bio,
        role=role,
        status=status,
        foto1=nomes_imagens[0] if len(nomes_imagens) > 0 else None,
        foto2=nomes_imagens[1] if len(nomes_imagens) > 1 else None,
        galeria=",".join(nomes_imagens[2:]) if len(nomes_imagens) > 2 else "",
        video=video_url
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Usuário registrado com sucesso!"}

# Rota de atualização
@app.put("/users/update/{id}")
async def atualizar_usuario(
    id: int,
    email: str = Form(...),
    bio: str = Form(...),
    status: str = Form(...),
    fotos: list[UploadFile] = File(None),
    video: UploadFile = File(None)
):
    db = SessionLocal()
    usuario = db.query(User).filter(User.id == id, User.email == email).first()

    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.bio = bio
    usuario.status = status

    if fotos:
        nomes_imagens = []
        for foto in fotos:
            result = cloudinary.uploader.upload(await foto.read(), folder="deumatch/fotos")
            nomes_imagens.append(result['secure_url'])

        usuario.foto1 = nomes_imagens[0] if len(nomes_imagens) > 0 else usuario.foto1
        usuario.foto2 = nomes_imagens[1] if len(nomes_imagens) > 1 else usuario.foto2
        usuario.galeria = ",".join(nomes_imagens[2:]) if len(nomes_imagens) > 2 else usuario.galeria

    if video:
        result = cloudinary.uploader.upload(await video.read(), folder="deumatch/videos", resource_type="video")
        usuario.video = result['secure_url']

    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Perfil atualizado com sucesso!"}

# Rota para listar
@app.get("/users/list")
def listar_usuarios():
    db = SessionLocal()
    usuarios = db.query(User).all()
    db.close()

    usuarios_serializados = []
    for usuario in usuarios:
        user_dict = usuario.__dict__.copy()
        user_dict.pop("_sa_instance_state", None)
        if user_dict.get("galeria"):
            user_dict["galeria"] = user_dict["galeria"].split(",") if user_dict["galeria"] else []
        usuarios_serializados.append(user_dict)

    return JSONResponse(content=usuarios_serializados)

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

# CORS liberado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação das tabelas no banco
Base.metadata.create_all(bind=engine)

# Inclui as rotas externas (se houver)
app.include_router(users.router)

# Diretório de compatibilidade para arquivos estáticos (não mais usado com Cloudinary)
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rota de status
@app.get("/")
def root():
    return {"status": "API Deu Match está ativa com Cloudinary 🚀"}

# Rota de registro de usuários
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

    # Upload das fotos para o Cloudinary
    for foto in fotos:
        result = cloudinary.uploader.upload(await foto.read(), folder="deumatch/fotos")
        nomes_imagens.append(result['secure_url'])

    # Upload do vídeo para o Cloudinary
    video_url = None
    if video:
        video_result = cloudinary.uploader.upload(await video.read(), folder="deumatch/videos", resource_type="video")
        video_url = video_result['secure_url']

    # Criação do usuário no banco
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

# Rota de atualização de perfil
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

    # Upload das novas fotos no Cloudinary
    if fotos:
        nomes_imagens = []
        for foto in fotos:
            result = cloudinary.uploader.upload(await foto.read(), folder="deumatch/fotos")
            nomes_imagens.append(result["secure_url"])

        usuario.foto1 = nomes_imagens[0] if len(nomes_imagens) > 0 else usuario.foto1
        usuario.foto2 = nomes_imagens[1] if len(nomes_imagens) > 1 else usuario.foto2
        usuario.galeria = ",".join(nomes_imagens[2:]) if len(nomes_imagens) > 2 else usuario.galeria

    # Upload de novo vídeo
    if video:
        result = cloudinary.uploader.upload(await video.read(), folder="deumatch/videos", resource_type="video")
        usuario.video = result["secure_url"]

    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Perfil atualizado com sucesso!"}

# Rota para listar todos os usuários
@app.get("/users/list")
def listar_usuarios():
    db = SessionLocal()
    usuarios = db.query(User).all()
    db.close()

    usuarios_serializados = []
    for usuario in usuarios:
        user_dict = usuario.__dict__.copy()
        user_dict.pop("_sa_instance_state", None)
        usuarios_serializados.append(user_dict)

    return JSONResponse(content=usuarios_serializados)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from database import Base, engine, SessionLocal
from models import User
import os
import time

app = FastAPI()

# CORS liberado para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação automática das tabelas no novo banco
Base.metadata.create_all(bind=engine)

# Diretório de uploads
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rota raiz
@app.get("/")
def root():
    return {"status": "API Deu Match está ativa 🚀"}

# Rota de registro com vídeo
@app.post("/users/register")
async def register_user(
    id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    bio: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    fotos: list[UploadFile] = File(...),
    video: UploadFile = File(None)  # NOVO
):
    db = SessionLocal()
    nomes_imagens = []

    for index, foto in enumerate(fotos):
        ext = foto.filename.split('.')[-1]
        filename = f"{int(time.time())}_{index}.{ext}"
        caminho = os.path.join(UPLOAD_FOLDER, filename)
        with open(caminho, "wb") as buffer:
            buffer.write(await foto.read())
        nomes_imagens.append(filename)

    # Salvar vídeo
    video_filename = None
    if video:
        ext = video.filename.split('.')[-1]
        video_filename = f"{int(time.time())}_video.{ext}"
        caminho_video = os.path.join(UPLOAD_FOLDER, video_filename)
        with open(caminho_video, "wb") as buffer:
            buffer.write(await video.read())

    usuario = User(
        id=id,
        name=name,
        email=email,
        bio=bio,
        role=role,
        status=status,
        foto1=nomes_imagens[0] if len(nomes_imagens) > 0 else None,
        foto2=nomes_imagens[1] if len(nomes_imagens) > 1 else None,
        galeria=",".join(nomes_imagens[2:]) if len(nomes_imagens) > 2 else "",
        video=video_filename
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
    fotos: list[UploadFile] = File(None)
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
        for index, foto in enumerate(fotos):
            ext = foto.filename.split('.')[-1]
            filename = f"{int(time.time())}_{index}.{ext}"
            caminho = os.path.join(UPLOAD_FOLDER, filename)
            with open(caminho, "wb") as buffer:
                buffer.write(await foto.read())
            nomes_imagens.append(filename)

        usuario.foto1 = nomes_imagens[0] if len(nomes_imagens) > 0 else usuario.foto1
        usuario.foto2 = nomes_imagens[1] if len(nomes_imagens) > 1 else usuario.foto2
        usuario.galeria = ",".join(nomes_imagens[2:]) if len(nomes_imagens) > 2 else ""

    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Perfil atualizado com sucesso!"}

# Rota para listar usuários
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

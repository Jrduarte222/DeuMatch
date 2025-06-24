from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from database import Base, engine, SessionLocal
from models import User
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# CORS liberado (para conectar com frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # depois restrinja para segurança
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Criação automática das tabelas
Base.metadata.create_all(bind=engine)

# Diretório para imagens
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Rota raiz (home)
@app.get("/")
def root():
    return {"status": "API Deu Match está ativa 🚀"}

# ✅ Rota de registro de participante
@app.post("/users/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    bio: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    fotos: list[UploadFile] = File(...)
):
    db = SessionLocal()
    nomes_imagens = []

    for foto in fotos:
        caminho = os.path.join(UPLOAD_FOLDER, foto.filename)
        with open(caminho, "wb") as buffer:
            buffer.write(await foto.read())
        nomes_imagens.append(foto.filename)

    usuario = Usuario(
        name=name,
        email=email,
        bio=bio,
        role=role,
        status=status,
        fotos=",".join(nomes_imagens)
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Usuário registrado com sucesso!"}

# ✅ Rota oficial para listar todos os participantes

@app.put("/users/update")
async def atualizar_usuario(
    email: str = Form(...),
    bio: str = Form(...),
    status: str = Form(...),
    fotos: list[UploadFile] = File(None)
):
    db = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.bio = bio
    usuario.status = status

    if fotos:
        nomes_imagens = []
        for foto in fotos:
            caminho = os.path.join(UPLOAD_FOLDER, foto.filename)
            with open(caminho, "wb") as buffer:
                buffer.write(await foto.read())
            nomes_imagens.append(foto.filename)
        # Adiciona novas fotos às existentes
        fotos_existentes = usuario.fotos.split(",") if usuario.fotos else []
        usuario.fotos = ",".join(fotos_existentes + nomes_imagens)

    
    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Perfil atualizado com sucesso!"}

@app.get("/users/list")
def listar_usuarios():
    db = SessionLocal()
    usuarios = db.query(Usuario).all()
    db.close()

    usuarios_serializados = []
    for usuario in usuarios:
        user_dict = usuario.__dict__.copy()
        user_dict.pop("_sa_instance_state", None)
        usuarios_serializados.append(user_dict)

    return JSONResponse(content=usuarios_serializados)
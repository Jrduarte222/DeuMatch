# app/routes/users.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, validator
import cloudinary.uploader
import cloudinary
import time
import os

from database import get_db
from models import User as DBUser

router = APIRouter()

# === CONFIG CLOUDINARY ===
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# === FUNÇÃO DE UPLOAD ===
def upload_to_cloudinary(file: UploadFile, folder: str = "usuarios"):
    result = cloudinary.uploader.upload(file.file, folder=folder, resource_type="auto")
    return result["secure_url"]

# === SCHEMA DE RETORNO ===
class UserSchema(BaseModel):
    id: int
    name: str
    email: str
    role: str
    bio: Optional[str] = None
    status: Optional[str] = "disponível"
    foto1: Optional[str] = None
    foto2: Optional[str] = None
    galeria: Optional[List[str]] = []
    video: Optional[str] = None

    @validator("galeria", pre=True)
    def split_galeria(cls, v):
        if isinstance(v, str):
            return v.split(",") if v else []
        return v

    class Config:
        from_attributes = True

# === SCHEMA COM SENHA (interno) ===
class UserWithPasswordSchema(UserSchema):
    senha: Optional[str] = None

# === CADASTRO DE USUÁRIO ===
@router.post("/users/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    senha: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form("disponível"),
    fotos: List[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),

    forma_pagamento: Optional[str] = Form(None),
    forma_recebimento: Optional[str] = Form(None),
    tipo_pix: Optional[str] = Form(None),
    pix: Optional[str] = Form(None),
    aceitou_termos: bool = Form(...),

    db: Session = Depends(get_db)
):
    if not aceitou_termos:
        raise HTTPException(status_code=400, detail="Você deve aceitar os termos de uso.")

    existing_user = db.query(DBUser).filter(DBUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    if role == "participante":
        if not all([forma_recebimento, tipo_pix, pix]):
            raise HTTPException(status_code=400, detail="Participantes devem informar chave Pix e tipo de chave.")
    elif role == "cliente":
        if not forma_pagamento:
            raise HTTPException(status_code=400, detail="Clientes devem informar a forma de pagamento.")

    # Upload das fotos
    foto1 = None
    foto2 = None
    galeria = []

    if fotos:
        for index, foto in enumerate(fotos):
            url = upload_to_cloudinary(foto)
            if index == 0:
                foto1 = url
            elif index == 1:
                foto2 = url
            else:
                galeria.append(url)

    video_url = upload_to_cloudinary(video) if video else None

    user = DBUser(
        name=name,
        email=email,
        role=role,
        senha=senha,
        bio=bio,
        status=status,
        foto1=foto1,
        foto2=foto2,
        galeria=",".join(galeria),
        video=video_url,
        forma_pagamento=forma_pagamento,
        forma_recebimento=forma_recebimento,
        tipo_pix=tipo_pix,
        pix=pix,
        aceitou_termos=aceitou_termos
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário registrado com sucesso", "user": user}

# === LOGIN SIMPLES ===
@router.post("/users/login")
def login_user(
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.email == email, DBUser.senha == senha).first()
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if user.status == "suspenso":
        raise HTTPException(status_code=403, detail="Usuário suspenso")
    return {"message": "Login autorizado", "user": user}

# === ATUALIZAR PERFIL ===
@router.put("/users/update/{id}")
async def update_user(
    id: int,
    email: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    senha: Optional[str] = Form(None),
    fotos: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.id == id, DBUser.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if bio:
        user.bio = bio
    if status:
        user.status = status
    if senha:
        user.senha = senha

    if fotos:
        galeria = []
        for index, foto in enumerate(fotos):
            url = upload_to_cloudinary(foto)
            if index == 0:
                user.foto1 = url
            elif index == 1:
                user.foto2 = url
            else:
                galeria.append(url)
        user.galeria = ",".join(galeria) if galeria else ""

    db.commit()
    db.refresh(user)
    return {"message": "Perfil atualizado com sucesso", "user": user}

# === LISTAR USUÁRIOS (exceto suspensos) ===
@router.get("/users/list", response_model=List[UserWithPasswordSchema])
async def list_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(DBUser)
    if role:
        query = query.filter(DBUser.role == role)
    return query.filter(DBUser.status != "suspenso").all()

# === SUSPENDER USUÁRIO ===
@router.post("/admin/suspend/{id}")
def suspender_usuario(id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    user.status = "suspenso"
    db.commit()
    return {"message": "Usuário suspenso com sucesso"}

# === EXCLUIR USUÁRIO ===
@router.delete("/admin/delete/{id}")
def excluir_usuario(id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(user)
    db.commit()
    return {"message": "Usuário excluído com sucesso"}

# === LIMPAR TODOS ===
@router.post("/admin/limpar-tudo")
def limpar_usuarios(db: Session = Depends(get_db)):
    db.query(DBUser).delete()
    db.commit()
    return {"message": "Todos os usuários foram removidos do banco."}

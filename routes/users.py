# app/routes/users.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, validator
import os, shutil, time

from database import get_db
from models import User as DBUser

router = APIRouter()

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
        from_attributes = True  # Pydantic v2+

# === CADASTRO COM FOTOS E VÍDEO ===
@router.post("/users/register")
async def register_user(
    id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form("disponível"),
    fotos: List[UploadFile] = File(...),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    existing_user = db.query(DBUser).filter(DBUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    foto1 = None
    foto2 = None
    galeria = []

    timestamp = str(int(time.time()))
    for index, foto in enumerate(fotos):
        ext = foto.filename.split(".")[-1]
        filename = f"{timestamp}_{index}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        if index == 0:
            foto1 = filename
        elif index == 1:
            foto2 = filename
        else:
            galeria.append(filename)

    video_filename = None
    if video:
        video_ext = video.filename.split(".")[-1]
        video_filename = f"{timestamp}_video.{video_ext}"
        video_path = os.path.join(UPLOAD_DIR, video_filename)
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

    user = DBUser(
        id=id,
        name=name,
        email=email,
        role=role,
        bio=bio,
        status=status,
        foto1=foto1,
        foto2=foto2,
        galeria=",".join(galeria),
        video=video_filename
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário registrado com sucesso", "user": user}

# === ATUALIZAR PERFIL ===
@router.put("/users/update/{id}")
async def update_user(
    id: int,
    email: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
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

    if fotos:
        galeria = []
        timestamp = str(int(time.time()))
        for index, foto in enumerate(fotos):
            ext = foto.filename.split(".")[-1]
            filename = f"{id}_u{index+1}_{timestamp}.{ext}"
            filepath = os.path.join(UPLOAD_DIR, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            galeria.append(filename)

        user.foto1 = galeria[0] if len(galeria) > 0 else user.foto1
        user.foto2 = galeria[1] if len(galeria) > 1 else user.foto2
        user.galeria = ",".join(galeria[2:]) if len(galeria) > 2 else ""

    db.commit()
    db.refresh(user)
    return {"message": "Perfil atualizado com sucesso", "user": user}

# === LISTAR USUÁRIOS ===
@router.get("/users/list", response_model=List[UserSchema])
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

# === EXCLUIR TODOS OS USUÁRIOS ===
@router.post("/admin/limpar-tudo")
def limpar_usuarios(db: Session = Depends(get_db)):
    db.query(DBUser).delete()
    db.commit()
    return {"message": "Todos os usuários foram removidos do banco."}


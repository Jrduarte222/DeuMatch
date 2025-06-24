# app/routes/users.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import os, shutil, time

from ..database import get_db
from ..models import User as DBUser

router = APIRouter()

UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

    class Config:
        orm_mode = True

# POST /users/register
@router.post("/users/register")
async def register_user(
    id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form("disponível"),
    fotos: List[UploadFile] = File(...),
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
        filename = f"{id}_{index+1}_{timestamp}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        if index == 0:
            foto1 = filename
        elif index == 1:
            foto2 = filename
        else:
            galeria.append(filename)

    user = DBUser(
        id=id,
        name=name,
        email=email,
        role=role,
        bio=bio,
        status=status,
        foto1=foto1,
        foto2=foto2,
        galeria=",".join(galeria)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário registrado com sucesso", "user": user}

# PUT /users/update/{id}
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

# GET /users/list
@router.get("/users/list", response_model=List[UserSchema])
async def list_users(role: Optional[str] = None, db: Session = Depends(get_db)):
    if role:
        return db.query(DBUser).filter(DBUser.role == role).all()
    return db.query(DBUser).all()

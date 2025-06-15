# app/routes/users.py - múltiplas fotos com timestamp para evitar sobreposição
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from pydantic import BaseModel
import os, shutil, time

router = APIRouter()

fake_users_db = []
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class User(BaseModel):
    id: int
    name: str
    email: str
    role: str
    bio: Optional[str] = None
    status: Optional[str] = "disponível"
    foto1: Optional[str] = None
    foto2: Optional[str] = None
    galeria: Optional[List[str]] = []

@router.post("/register")
async def register_user(
    id: int = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    bio: Optional[str] = Form(...),
    status: Optional[str] = Form("disponível"),
    fotos: List[UploadFile] = File(...)
):
    for u in fake_users_db:
        if u.email == email:
            raise HTTPException(status_code=400, detail="Email já registrado")

    foto1 = None
    foto2 = None
    galeria = []

    if fotos:
        timestamp = str(int(time.time()))
        for index, foto in enumerate(fotos):
            ext = foto.filename.split(".")[-1]
            filename = f"{id}_{index + 1}_{timestamp}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            if index == 0:
                foto1 = filename
            elif index == 1:
                foto2 = filename
            else:
                galeria.append(filename)

    user = User(
        id=id,
        name=name,
        email=email,
        role=role,
        bio=bio,
        status=status,
        foto1=foto1,
        foto2=foto2,
        galeria=galeria
    )
    fake_users_db.append(user)
    return {"message": "Usuário registrado com sucesso", "user": user}
from fastapi import UploadFile, File, Form

@router.put("/update")
async def update_user(
    email: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    fotos: Optional[List[UploadFile]] = File(None)
):
    for user in fake_users_db:
        if user.email == email:
            if bio:
                user.bio = bio
            if status:
                user.status = status

            galeria = []
            if fotos:
                timestamp = str(int(time.time()))
                for index, foto in enumerate(fotos):
                    ext = foto.filename.split(".")[-1]
                    filename = f"{user.id}_u{index+1}_{timestamp}.{ext}"
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(foto.file, buffer)
                    galeria.append(filename)

                # Atualiza as fotos, mantendo as 2 primeiras como públicas
                user.foto1 = galeria[0] if len(galeria) > 0 else user.foto1
                user.foto2 = galeria[1] if len(galeria) > 1 else user.foto2
                user.galeria = galeria[2:] if len(galeria) > 2 else []

            return {"message": "Perfil atualizado com sucesso", "user": user}

    raise HTTPException(status_code=404, detail="Usuário não encontrado")


@router.get("/list")
async def list_users(role: Optional[str] = None):
    if role:
        return [u for u in fake_users_db if u.role == role]
    return fake_users_db

@router.put("/suspender")
async def suspender_usuario(email: str = Form(...)):
    for user in fake_users_db:
        if user.email == email:
            user.status = "suspenso"
            return {"message": "Usuário suspenso"}
    raise HTTPException(status_code=404, detail="Usuário não encontrado")


@router.delete("/{email}")
async def excluir_usuario(email: str):
    global fake_users_db
    fake_users_db = [u for u in fake_users_db if u.email != email]
    return {"message": f"Usuário {email} excluído com sucesso"}


@router.delete("/limpar")
async def limpar_todos():
    fake_users_db.clear()
    return {"message": "Todos os usuários foram excluídos"}


from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Usuario
import os, shutil, time

router = APIRouter()
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔹 Registro de usuário
@router.post("/users/register")
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    bio: Optional[str] = Form(""),
    status: Optional[str] = Form("disponível"),
    fotos: List[UploadFile] = File(...)
):
    db: Session = SessionLocal()

    if db.query(Usuario).filter(Usuario.email == email).first():
        db.close()
        raise HTTPException(status_code=400, detail="Email já registrado")

    nomes_fotos = []
    timestamp = str(int(time.time()))
    for index, foto in enumerate(fotos):
        ext = foto.filename.split(".")[-1]
        filename = f"{email.replace('@', '_')}_{index+1}_{timestamp}.{ext}"
        caminho = os.path.join(UPLOAD_DIR, filename)
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        nomes_fotos.append(filename)

    novo_usuario = Usuario(
        name=name,
        email=email,
        role=role,
        bio=bio,
        status=status,
        fotos=",".join(nomes_fotos)
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    db.close()

    return {"message": "Usuário registrado com sucesso", "user": novo_usuario}


# 🔹 Atualização de perfil
@router.put("/users/update")
async def update_user(
    email: str = Form(...),
    bio: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    fotos: Optional[List[UploadFile]] = File(None)
):
    db: Session = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if bio:
        usuario.bio = bio
    if status:
        usuario.status = status

    if fotos:
        timestamp = str(int(time.time()))
        novas_fotos = []
        for index, foto in enumerate(fotos):
            ext = foto.filename.split(".")[-1]
            filename = f"{email.replace('@', '_')}_u{index+1}_{timestamp}.{ext}"
            caminho = os.path.join(UPLOAD_DIR, filename)
            with open(caminho, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            novas_fotos.append(filename)

        # Adiciona às existentes
        fotos_anteriores = usuario.fotos.split(",") if usuario.fotos else []
        usuario.fotos = ",".join(fotos_anteriores + novas_fotos)

    db.commit()
    db.refresh(usuario)
    db.close()

    return {"message": "Perfil atualizado com sucesso", "user": usuario}


# 🔹 Listar todos os usuários
@router.get("/users/list")
def listar_usuarios():
    db: Session = SessionLocal()
    usuarios = db.query(Usuario).all()
    db.close()

    lista = []
    for u in usuarios:
        user_dict = u.__dict__.copy()
        user_dict.pop("_sa_instance_state", None)
        lista.append(user_dict)

    return lista


# 🔹 Suspender um usuário
@router.put("/users/suspend")
def suspender_usuario(email: str = Form(...)):
    db: Session = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    usuario.status = "suspenso"
    db.commit()
    db.close()
    return {"message": "Usuário suspenso com sucesso"}


# 🔹 Excluir usuário
@router.delete("/users/delete")
def excluir_usuario(email: str):
    db: Session = SessionLocal()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:
        db.close()
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(usuario)
    db.commit()
    db.close()
    return {"message": f"Usuário {email} excluído com sucesso"}


# 🔹 Excluir todos os usuários
@router.delete("/users/limpar")
def limpar_todos():
    db: Session = SessionLocal()
    db.query(Usuario).delete()
    db.commit()
    db.close()
    return {"message": "Todos os usuários foram excluídos"}

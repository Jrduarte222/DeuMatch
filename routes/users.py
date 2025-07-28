# app/routes/users.py
import cloudinary.uploader
import cloudinary
import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, validator
from fastapi import status
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
    valor_acompanhante: Optional[int] = 0
    exclusao_pendente: Optional[bool] = False

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
    tipo_chave_pix: Optional[str] = Form(None),
    chave_pix: Optional[str] = Form(None),
    valor_acompanhante: Optional[int] = Form(0),
    aceitou_termos: bool = Form(...),

    db: Session = Depends(get_db)
):
    if not aceitou_termos:
        raise HTTPException(status_code=400, detail="Você deve aceitar os termos de uso.")

    existing_user = db.query(DBUser).filter(DBUser.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já registrado")

    if role == "participante":
        if not all([forma_recebimento, tipo_chave_pix, chave_pix]):
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
        tipo_chave_pix=tipo_chave_pix,
        chave_pix=chave_pix,
        valor_acompanhante=valor_acompanhante,

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
@router.put("/users/update/{user_id}")
async def update_user(
    user_id: int,
    name: str = Form(...),
    email: str = Form(...),
    bio: str = Form(""),
    status: str = Form("disponível"),
    senha: str = Form(None),
    valor_acompanhante: Optional[int] = Form(0),
    fotos: List[UploadFile] = None,
    videos: List[UploadFile] = None,
    db: Session = Depends(get_db),
):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user.name = name
    user.email = email
    user.bio = bio
    user.status = status
    user.valor_acompanhante = valor_acompanhante
    if senha:
        user.senha = senha  # Em produção, usar hash

    # Upload de novas fotos (mantendo antigas)
    if fotos:
        if len(fotos) > 20:
            raise HTTPException(status_code=400, detail="Máximo de 20 fotos permitido.")
        existing_fotos = [user.foto1, user.foto2] + (user.galeria.split(',') if user.galeria else [])
        for foto in fotos:
            upload_result = cloudinary.uploader.upload(foto.file, folder="usuarios")
            existing_fotos.append(upload_result["secure_url"])
        user.foto1 = existing_fotos[0] if len(existing_fotos) > 0 else None
        user.foto2 = existing_fotos[1] if len(existing_fotos) > 1 else None
        user.galeria = ",".join(existing_fotos[2:]) if len(existing_fotos) > 2 else None

    # Upload de novos vídeos (mantendo antigos)
    if videos:
        if len(videos) > 5:
            raise HTTPException(status_code=400, detail="Máximo de 5 vídeos permitido.")
        existing_videos = user.video.split(',') if user.video else []
        for video in videos:
            upload_result = cloudinary.uploader.upload(video.file, resource_type="video", folder="usuarios")
            existing_videos.append(upload_result["secure_url"])
        user.video = ",".join(existing_videos)

    db.commit()
    db.refresh(user)
    return {"mensagem": "Perfil atualizado com sucesso!", "user": user}

# === EXCLUIR MÍDIA DO PERFIL ===
@router.delete("/users/{user_id}/delete_media")
def delete_media(
    user_id: int,
    media_url: str,
    tipo: str,
    db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    try:
        # Extrair public_id da URL
        parts = media_url.split('/')
        file_name = parts[-1].split('.')[0]
        public_id = f"usuarios/{file_name}"

        # Excluir do Cloudinary
        resource_type = "video" if tipo == "video" else "image"
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)

        # Remover do banco
        if tipo == "foto":
            fotos = [user.foto1, user.foto2] + (user.galeria.split(',') if user.galeria else [])
            fotos = [f for f in fotos if f and f != media_url]
            user.foto1 = fotos[0] if len(fotos) > 0 else None
            user.foto2 = fotos[1] if len(fotos) > 1 else None
            user.galeria = ','.join(fotos[2:]) if len(fotos) > 2 else None
        elif tipo == "video":
            videos = user.video.split(',') if user.video else []
            videos = [v for v in videos if v != media_url]
            user.video = ','.join(videos) if videos else None

        db.commit()
        return {"message": "Mídia excluída com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir mídia: {str(e)}")

# === LISTAR USUÁRIOS ===
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

# === PEDIDO DE EXCLUSÃO (usando exclusao_pendente) ===
@router.post("/users/request_delete")
def request_delete(
    user_id: int = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.exclusao_pendente:
        raise HTTPException(status_code=400, detail="Pedido de exclusão já solicitado")

    user.exclusao_pendente = True
    db.commit()
    return {"message": "Pedido de Exclusão registrado. Aguarde aprovação do administrador."}

# === LISTAR PEDIDOS DE EXCLUSÃO (usando exclusao_pendente) ===
@router.get("/admin/pedidos_exclusao")
def listar_pedidos_exclusao(db: Session = Depends(get_db)):
    users = db.query(DBUser).filter(DBUser.exclusao_pendente == True).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "timestamp": u.updated_at if hasattr(u, "updated_at") else None} for u in users]

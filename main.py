from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
from database import Base, engine, SessionLocal
from models import Usuario

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajuste depois para segurança
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

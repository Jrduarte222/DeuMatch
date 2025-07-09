# routes/chat.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Message
from datetime import datetime
from pydantic import BaseModel
from typing import List
from models import User

router = APIRouter()

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

@router.post("/messages/send", response_model=MessageOut)
def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    new_message = Message(
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        timestamp=datetime.utcnow()
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

@router.get("/messages/conversation", response_model=List[MessageOut])
def get_conversation(user1: int, user2: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        ((Message.sender_id == user1) & (Message.receiver_id == user2)) |
        ((Message.sender_id == user2) & (Message.receiver_id == user1))
    ).order_by(Message.timestamp.asc()).all()
    
    return messages
class SenderInfo(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

@router.get("/messages/received_full/{user_id}", response_model=List[SenderInfo])
def get_message_senders_with_names(user_id: int, db: Session = Depends(get_db)):
    remetentes_ids = db.query(Message.sender_id).filter(
        Message.receiver_id == user_id
    ).distinct().all()

    remetente_ids = [r[0] for r in remetentes_ids]

    remetentes = db.query(User).filter(User.id.in_(remetente_ids)).all()
    return remetentes
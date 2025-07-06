from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Message

router = APIRouter()

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

@router.post("/messages/send")
def send_message(msg: MessageCreate):
    db: Session = SessionLocal()
    message = Message(
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        content=msg.content,
        timestamp=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    db.close()
    return {"status": "sent", "message": message}

@router.get("/messages/conversation")
def get_conversation(user1: int, user2: int):
    db: Session = SessionLocal()
    messages = db.query(Message).filter(
        ((Message.sender_id == user1) & (Message.receiver_id == user2)) |
        ((Message.sender_id == user2) & (Message.receiver_id == user1))
    ).order_by(Message.timestamp.asc()).all()
    db.close()
    return messages

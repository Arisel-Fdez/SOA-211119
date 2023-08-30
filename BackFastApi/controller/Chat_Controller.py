from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from model.User_model import User as UserModel
from router.schemas import UserCheck, MessageResponse, GroupChatMessage
from config.database import SessionLocal
from .User_Controller import notify_user_via_websocket, notify_clients, group_chats

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat/message", response_model=MessageResponse)
async def send_group_chat_message(user: UserCheck, message: GroupChatMessage, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if not db_user or user.password != db_user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    user_group_chat = group_chats.get((db_user.address,db_user.state, db_user.city, db_user.postal_code))
    if user_group_chat:
        message_to_send = f"{db_user.name}: {message.message}"
        await user_group_chat.notify_users(message_to_send)

    # Notificar a todos los clientes conectados a través de websockets
    message_to_clients = f"Mensaje Nuevo: {db_user.name}"
    await notify_clients(message_to_clients)
    message_to_clients = json.dumps({"message": f"Mensaje Nuevo: {db_user.name}"})
    await notify_clients(message_to_clients)

    return {"message": "Group chat message sent"}
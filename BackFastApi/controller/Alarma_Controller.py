from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from model.User_model import User as UserModel
from router.schemas import UserCheck, MessageResponse
from config.database import SessionLocal
from .User_Controller import notify_user_via_websocket, notify_clients, GroupChat, group_chats
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/alarma", response_model=MessageResponse)
async def set_alarm_status(user: UserCheck, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if not db_user or user.password != db_user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Verificar que el usuario tiene una alarma asociada
    if not db_user.alarma:
        raise HTTPException(status_code=400, detail="No alarm associated with the user")

    # Cambiar el estado de la alarma
    db_user.alarma.status = not db_user.alarma.status
    db.commit()

    # Notificar al chat grupal del usuario sobre el cambio de estado de la alarma
    user_group_chat = group_chats.get((db_user.address, db_user.state, db_user.city, db_user.postal_code))
    if user_group_chat:
        message = f"Alarma {'activada' if db_user.alarma.status else 'desactivada'} por: {db_user.name}"
        user_group_chat.notify_users(message)

    # Notificar a los demás usuarios en la misma dirección y código postal
    users_to_notify = db.query(UserModel).filter(
        UserModel.id != db_user.id,
        UserModel.address == db_user.address,
        UserModel.state == db_user.state,
        UserModel.city == db_user.city,
        UserModel.postal_code == db_user.postal_code,
        UserModel.alarma != None
    ).all()

    for user_to_notify in users_to_notify:
        message = f"Alarma {'activada' if db_user.alarma.status else 'desactivada'} por: {db_user.name}"
        await notify_user_via_websocket(user_to_notify.id, message)

    # Notificar a todos los clientes conectados a través de websockets
    message_to_clients = f"Alarma {'activada' if db_user.alarma.status else 'desactivada'} por: {db_user.name}"
    await notify_clients(message_to_clients)
    message_to_clients = json.dumps({"": f"Alarma {'Activada' if db_user.alarma.status else 'Desativada'}: {db_user.name}"})
    await notify_clients(message_to_clients)

    return {"message": f"Alarm {'activated' if db_user.alarma.status else 'deactivated'} and notifications sent"}

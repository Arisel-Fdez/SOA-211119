from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import random   
import websockets  
import json



from model.User_model import User as UserModel, Alarma
from router.schemas import UserCreate, User ,UserLogin, UserCheck,MessageResponse, GroupChatMessage
from config.database import SessionLocal



# Creamos un conjunto para almacenar las conexiones WebSocket activas
active_websockets = set()

async def notify_clients(message: str):
    for websocket in active_websockets:
        await websocket.send_text(message)

async def notify_user_via_websocket(user_id: int, message: str):
    # Buscar la conexión WebSocket del usuario en el conjunto de conexiones activas
    websocket = next((ws for ws in active_websockets if getattr(ws, "user_id", None) == user_id), None)
    if websocket:
        await websocket.send_text(message)
    else:
        # Si el usuario no tiene una conexión WebSocket activa, puedes manejarlo de acuerdo a tus necesidades.
        # Por ejemplo, puedes almacenar el mensaje en una cola de mensajes para enviarlo cuando el usuario se conecte.
        pass

# Función para enviar un mensaje a todos los clientes conectados
async def send_message_to_clients(message):
    for websocket in active_websockets:
        await websocket.send(message)

# Función para manejar nuevas conexiones WebSocket
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            # Aquí puedes manejar cualquier mensaje recibido desde el cliente si lo necesitas
            data = await websocket.receive_text()
            print(f"Received data: {data}")
    except:
        pass
    finally:
        # Cuando el cliente se desconecta, lo eliminamos del conjunto de conexiones activas
        active_websockets.remove(websocket)




# Agregamos las clases Node y BinaryTree aquí
class Node:
    def __init__(self, name, email, tree):
        self.name = name
        self.email = email
        self.tree = tree
        self.left = None
        self.right = None
        self.group_chat = None  # Referencia al chat grupal al que pertenece el usuario


class BinaryTree:
    def __init__(self):
        self.root = None

    def add_node(self, node):
        if self.root is None:
            self.root = node
        else:
            self._add_recursive(self.root, node)

    def _add_recursive(self, current_node, new_node):
        if new_node.tree < current_node.tree:
            if current_node.left is None:
                current_node.left = new_node
            else:
                self._add_recursive(current_node.left, new_node)
        elif new_node.tree > current_node.tree:
            if current_node.right is None:
                current_node.right = new_node
            else:
                self._add_recursive(current_node.right, new_node)


    def inorder(self, node):
        if node is None:
            return []
        return self.inorder(node.left) + [(node.tree, node.name, node.email)] + self.inorder(node.right)

    def preorder(self, node):
        if node is None:
            return []
        return [(node.tree, node.name, node.email)] + self.preorder(node.left) + self.preorder(node.right)

    def postorder(self, node):
        if node is None:
            return []
        return self.postorder(node.left) + self.postorder(node.right) + [(node.tree, node.name, node.email)]

tree = BinaryTree()

router = APIRouter()

group_chats = {}  # Define group_chats as a global variable

SECRET_KEY = "61339a84fbd5e7d837ec8f143d69d3d6a46be2629524ca9938b401d6cf1a9793"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class Token(BaseModel):
    access_token: str
    token_type: str


def get_group_chats():
    return group_chats


def load_users_to_tree(db: Session):
    users = db.query(UserModel).all()

    for user in users:
        node = Node(user.name, user.email, user.tree)
        if (user.address, user.city, user.postal_code) not in group_chats:
            group_chats[(user.address, user.city, user.postal_code)] = GroupChat(user.address, user.city, user.postal_code)
        group_chats[(user.address, user.city, user.postal_code)].add_user(user.id)
        node.group_chat = group_chats[(user.address, user.city, user.postal_code)]
        tree.add_node(node)

def create_alarma(user_obj: UserModel, db: Session):
    # Crea una alarma para el usuario recién creado
    alarma_obj = Alarma(status=True, user_id=user_obj.id)
    db.add(alarma_obj)
    db.commit()
    db.refresh(alarma_obj)
    return alarma_obj


class GroupChat:
    def __init__(self, address, city, postal_code):
        self.address = address
        self.city = city
        self.postal_code = postal_code
        self.users = set()  # Conjunto para almacenar los usuarios en el chat grupal

    def add_user(self, user_id):
        self.users.add(user_id)

    def remove_user(self, user_id):
        self.users.discard(user_id)

    async def notify_users(self, message):  # Make this method an async function
        for user_id in self.users:
            # Notificar a cada usuario en el chat grupal a través de sus conexiones WebSocket
            message_to_send = f"Group Chat: {message}"
            await notify_user_via_websocket(user_id, message_to_send)




load_users_to_tree(SessionLocal())

@router.post("/users", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_obj = UserModel(**user.dict())
    user_obj.tree = random.randint(1, 1000)  # Generate a random number between 1 and 1000
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)

    user_pydantic = User.from_orm(user_obj)
    user_obj_with_token = user_pydantic.dict()
    user_obj_with_token["token"] = create_access_token(data={"sub": user_obj.id})

    # Aquí es donde añadimos al usuario al árbol y al chat grupal correspondiente
    node = Node(user_obj.name, user_obj.email, user_obj.tree)
    group_chat = group_chats.get((user_obj.address,user_obj.state, user_obj.city, user_obj.postal_code))
    if group_chat:
        group_chat.add_user(user_obj.id)
        node.group_chat = group_chat
    tree.add_node(node)

    # Crea la alarma para el usuario recién creado
    create_alarma(user_obj, db)

    # Notificar a los demás usuarios en la misma dirección y código postal
    users_to_notify = db.query(UserModel).filter(
        UserModel.id != user_obj.id,
        UserModel.address == user_obj.address,
        UserModel.state == user_obj.state,
        UserModel.city == user_obj.city,
        UserModel.postal_code == user_obj.postal_code,
        UserModel.alarma != None
    ).all()

    for user_to_notify in users_to_notify:
        message = f"Nuevo usuario registrado: {user_obj.name}"
        await notify_user_via_websocket(user_to_notify.id, message)

    # Notificar a todos los clientes conectados a través de websockets
    message_to_clients = f"Nuevo usuario Registrado: {user_obj.name}"
    await notify_clients(message_to_clients)
    message_to_clients = json.dumps({"": f"Nuevo usuario Registrado: {user_obj.name}"})
    await notify_clients(message_to_clients)
    return user_obj_with_token


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_handler(websocket)

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if not db_user or user.password != db_user.password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/inorden")
def get_users_inorder():
    return tree.inorder(tree.root)

@router.get("/users/preorden")
def get_users_preorder():
    return tree.preorder(tree.root)

@router.get("/users/postorden")
def get_users_postorder():
    return tree.postorder(tree.root)

from pydantic import BaseModel, Field

class UserBase(BaseModel):
    name: str 
    email: str
    password: str
    phone: str
    address: str
    state: str
    city: str
    calle: str
    postal_code: str
    interior_number: str
    tree: int = Field(None)

class UserCreate(UserBase):
    tree: int = Field(None)

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str


class UserCheck(BaseModel):
    email: str
    password: str

class AlarmaCheck(BaseModel):
    email: str
    password: str

class MessageResponse(BaseModel):
    message: str


class GroupChatMessage(BaseModel):
    message: str

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)  
    phone = Column(String)
    address = Column(String)
    state = Column(String)
    city = Column(String)
    calle = Column(String)
    postal_code = Column(String)
    interior_number = Column(String)
    tree = Column(Integer)

    alarma = relationship("Alarma", back_populates="user", uselist=False)

class Alarma(Base):
    __tablename__ = "alarmas"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)  # Added unique=True to enforce one-to-one relationship

    user = relationship("User", back_populates="alarma")

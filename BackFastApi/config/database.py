from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.model import Base
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Crea una instancia de 'Engine'
engine = create_engine('postgresql://angelito:211125@localhost:5432/movil')

# Crea todas las tablas
Base.metadata.create_all(engine)

# Definición de la función SessionLocal
SessionLocal = sessionmaker(bind=engine)


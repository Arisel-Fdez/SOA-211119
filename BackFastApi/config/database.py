from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.User_model import Base

# Crea una instancia de 'Engine'
engine = create_engine('postgresql://postgres:yeremi224@localhost:5432/movil')

# Crea todas las tablas
Base.metadata.create_all(engine)

# Definición de la función SessionLocal
SessionLocal = sessionmaker(bind=engine)


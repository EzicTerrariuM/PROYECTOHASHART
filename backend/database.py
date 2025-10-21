from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

# ⚙️ Si la variable de entorno falla, usamos la URL fija (quemada)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL or DATABASE_URL.strip() == "":
    DATABASE_URL = "postgresql+psycopg2://postgres:BlFHAohMNOWOZXlhOmnyjcVdrlWQFZUN@postgres.railway.internal:5432/railway"

# 🔧 Asegurar compatibilidad (Railway suele dar 'postgres://' sin psycopg2)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependencia de sesión para FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

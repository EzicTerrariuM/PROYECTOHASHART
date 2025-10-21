from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

# Leer variable del entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# 🔥 Si Railway da el formato sin "psycopg2", lo arreglamos automáticamente
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# 🚨 Validar que la URL exista
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL no está configurada o está vacía")

# Crear motor de conexión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

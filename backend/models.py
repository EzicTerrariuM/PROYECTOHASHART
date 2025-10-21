from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from backend.database import Base

class ArchivoHash(Base):
    __tablename__ = "archivos_hash"

    id_hash = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, nullable=False)
    hash_base = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    hash_con_salt = Column(String, nullable=False)
    fecha_creacion = Column(TIMESTAMP, nullable=False)

    verificaciones = relationship("Verificacion", back_populates="archivo")


class Estado(Base):
    __tablename__ = "estados"

    id_estado = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, nullable=False)

    verificaciones = relationship("Verificacion", back_populates="estado")


class Verificacion(Base):
    __tablename__ = "verificaciones"

    id_verificacion = Column(Integer, primary_key=True, index=True)
    id_hash = Column(Integer, ForeignKey("archivos_hash.id_hash"), nullable=False)
    fecha_verificacion = Column(TIMESTAMP, nullable=False)
    id_estado = Column(Integer, ForeignKey("estados.id_estado"), nullable=False)

    archivo = relationship("ArchivoHash", back_populates="verificaciones")
    estado = relationship("Estado", back_populates="verificaciones")

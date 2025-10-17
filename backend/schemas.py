from datetime import datetime
from pydantic import BaseModel

# ---------- ARCHIVOS HASH ----------
class ArchivoHashBase(BaseModel):
    nombre_archivo: str
    hash_base: str
    salt: str
    hash_con_salt: str


class ArchivoHashCreate(ArchivoHashBase):
    fecha_creacion: datetime = datetime.now()


class ArchivoHash(ArchivoHashBase):
    id_hash: int
    fecha_creacion: datetime

    class Config:
        from_attributes = True  # reemplaza orm_mode=True


# ---------- ESTADOS ----------
class EstadoBase(BaseModel):
    descripcion: str


class EstadoCreate(EstadoBase):
    pass


class Estado(EstadoBase):
    id_estado: int

    class Config:
        from_attributes = True


# ---------- VERIFICACIONES ----------
class VerificacionBase(BaseModel):
    id_hash: int
    id_estado: int


class VerificacionCreate(VerificacionBase):
    fecha_verificacion: datetime = datetime.now()


class Verificacion(VerificacionBase):
    id_verificacion: int
    fecha_verificacion: datetime

    class Config:
        from_attributes = True

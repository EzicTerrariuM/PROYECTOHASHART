from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# ------------------------------
# Schemas para Documentos
# ------------------------------
class DocumentoBase(BaseModel):
    nombre: str
    hash_pdf: str
    imagen_asociada: str

class DocumentoCreate(DocumentoBase):
    pass

class Documento(DocumentoBase):
    id: int
    creado_en: datetime

    class Config:
        from_attributes = True


# ------------------------------
# Schemas para Verificaciones
# ------------------------------
class VerificacionBase(BaseModel):
    documento_id: int
    resultado: bool

class VerificacionCreate(VerificacionBase):
    pass

class Verificacion(VerificacionBase):
    id: int
    fecha_verificacion: datetime

    class Config:
        from_attributes = True


# ------------------------------
# Schemas para Imagenes
# ------------------------------
class ImagenBase(BaseModel):
    nombre: str
    datos: bytes
    salt: Optional[str] = None

class ImagenCreate(ImagenBase):
    pass

class Imagen(ImagenBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

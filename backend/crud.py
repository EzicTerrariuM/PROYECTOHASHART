from sqlalchemy.orm import Session
from backend import models, schemas

# ------------------------------
# CRUD para documentos
# ------------------------------

def crear_documento(db: Session, documento: schemas.DocumentoCreate):
    nuevo = models.Documento(
        nombre=documento.nombre,
        hash_pdf=documento.hash_pdf,
        imagen_asociada=documento.imagen_asociada
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def obtener_documento_por_hash(db: Session, hash_pdf: str):
    return db.query(models.Documento).filter(models.Documento.hash_pdf == hash_pdf).first()

def obtener_documento(db: Session, documento_id: int):
    return db.query(models.Documento).filter(models.Documento.id == documento_id).first()

def listar_documentos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Documento).offset(skip).limit(limit).all()


# ------------------------------
# CRUD para verificaciones
# ------------------------------

def crear_verificacion(db: Session, verificacion: schemas.VerificacionCreate):
    nueva = models.Verificacion(
        documento_id=verificacion.documento_id,
        resultado=verificacion.resultado
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_verificaciones(db: Session, documento_id: int):
    return db.query(models.Verificacion).filter(models.Verificacion.documento_id == documento_id).all()


# ------------------------------
# CRUD para imagenes
# ------------------------------

def crear_imagen(db: Session, imagen: schemas.ImagenCreate):
    nueva = models.Imagen(
        nombre=imagen.nombre,
        datos=imagen.datos,
        salt=imagen.salt
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def obtener_imagen_por_id(db: Session, imagen_id: int):
    return db.query(models.Imagen).filter(models.Imagen.id == imagen_id).first()


def obtener_imagen_por_nombre(db: Session, nombre: str):
    return db.query(models.Imagen).filter(models.Imagen.nombre == nombre).first()

def listar_imagenes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Imagen).offset(skip).limit(limit).all()

from sqlalchemy.orm import Session
import models, schemas

def crear_archivo(db: Session, archivo: schemas.ArchivoHashCreate):
    nuevo = models.ArchivoHash(**archivo.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def obtener_archivos(db: Session):
    return db.query(models.ArchivoHash).all()

def crear_verificacion(db: Session, verificacion: schemas.VerificacionCreate):
    nueva = models.Verificacion(**verificacion.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva
def obtener_por_hash(db: Session, hash_con_salt: str):
    return db.query(models.ArchivoHash).filter(models.ArchivoHash.hash_con_salt == hash_con_salt).first()

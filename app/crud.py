from sqlalchemy.orm import Session
from . import models, schemas

def create_file_record(db: Session, file: schemas.FileRecordCreate):
    db_record = models.FileRecord(**file.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def get_all_records(db: Session):
    return db.query(models.FileRecord).all()

def get_record_by_hash(db: Session, hash_value: str):
    return db.query(models.FileRecord).filter(models.FileRecord.hash_value == hash_value).first()

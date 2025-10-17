from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(Integer, primary_key=True, index=True)
    pdf_name = Column(String)
    image_name = Column(String)
    hash_value = Column(String, unique=True, index=True)
    pdf_path = Column(String)
    image_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

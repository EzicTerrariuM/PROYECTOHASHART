from pydantic import BaseModel
from datetime import datetime

class FileRecordBase(BaseModel):
    pdf_name: str
    image_name: str
    hash_value: str

class FileRecordCreate(FileRecordBase):
    pdf_path: str
    image_path: str

class FileRecordResponse(FileRecordBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

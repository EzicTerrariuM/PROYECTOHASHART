from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import hashlib
import cv2
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import tempfile
import os
from backend import models, schemas, crud
from backend.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Verificación de Hashes + PDF")

# --- Configurar CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes restringirlo si quieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Funciones auxiliares ---
def get_pdf_sha3_hash(file_path):
    """Genera un hash SHA3-256 del PDF"""
    sha3 = hashlib.sha3_256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha3.update(chunk)
    return sha3.hexdigest()

def get_deterministic_salt(image_path):
    """Crea un salt determinístico basado en la imagen"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("No se pudo cargar la imagen.")
    height, width, _ = img.shape
    salt = ""
    step = max(width // 10, 1)
    for y in range(0, height, step):
        for x in range(0, width, step):
            pixel = img[y, x]
            salt += f"{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}"
    return salt

def generate_sha3_hash(data):
    """Genera el hash SHA3-256 final combinando PDF + salt"""
    sha3 = hashlib.sha3_256()
    sha3.update(data.encode())
    return sha3.hexdigest()

# --- Endpoint para crear hash y guardar en BD ---
@app.post("/crear_hash/")
async def crear_hash(pdf: UploadFile = File(...), image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Guardar archivos temporales
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
            pdf_tmp.write(await pdf.read())
            pdf_path = pdf_tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
            img_tmp.write(await image.read())
            image_path = img_tmp.name

        # Generar hash
        pdf_hash = get_pdf_sha3_hash(pdf_path)
        salt = get_deterministic_salt(image_path)
        combined_data = pdf_hash + salt
        final_hash = generate_sha3_hash(combined_data)

        # Crear PDF con QR
        qr_pdf_stream = BytesIO()
        c = canvas.Canvas(qr_pdf_stream, pagesize=letter)
        qr_file = f"{tempfile.gettempdir()}/qr_temp.png"
        qrcode.make(final_hash).save(qr_file)
        c.drawImage(qr_file, 150, 400, width=300, height=300)
        c.setFont("Helvetica", 12)
        c.drawCentredString(300, 380, "SHA3-256 PDF+Image Hash")
        c.drawCentredString(300, 365, final_hash[:32])
        c.drawCentredString(300, 350, final_hash[32:])
        c.showPage()
        c.save()
        qr_pdf_stream.seek(0)

        # Combinar PDF original con QR
        original_pdf = PdfReader(pdf_path)
        qr_pdf = PdfReader(qr_pdf_stream)
        writer = PdfWriter()

        for page in original_pdf.pages:
            writer.add_page(page)
        writer.add_page(qr_pdf.pages[0])

        output_filename = f"{tempfile.gettempdir()}/PDF_with_QR.pdf"
        with open(output_filename, "wb") as f:
            writer.write(f)

        # Guardar en la base de datos
        archivo_data = schemas.ArchivoHashCreate(
            nombre_archivo=pdf.filename,
            hash_base=pdf_hash,
            salt=salt,
            hash_con_salt=final_hash
        )
        crud.crear_archivo(db, archivo_data)

        # Devolver el PDF con el QR generado
        return FileResponse(output_filename, filename="PDF_with_QR.pdf")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- Endpoint para verificar archivo + imagen ---
@app.post("/verificar_hash/")
async def verificar_hash(pdf: UploadFile = File(...), image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Guardar archivos temporales
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
            pdf_tmp.write(await pdf.read())
            pdf_path = pdf_tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
            img_tmp.write(await image.read())
            image_path = img_tmp.name

        # Recalcular el hash
        pdf_hash = get_pdf_sha3_hash(pdf_path)
        salt = get_deterministic_salt(image_path)
        combined_data = pdf_hash + salt
        final_hash = generate_sha3_hash(combined_data)

        # Buscar en BD
        archivo_db = crud.obtener_por_hash(db, final_hash)
        if archivo_db:
            return {"verificado": True, "mensaje": "El archivo coincide con un registro existente.", "hash": final_hash}
        else:
            return {"verificado": False, "mensaje": "El archivo no coincide con ningún registro.", "hash": final_hash}

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

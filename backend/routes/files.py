from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import crud, schemas
import hashlib, tempfile, qrcode, cv2, os
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

router = APIRouter()

def get_pdf_sha3_hash(file_path):
    sha3 = hashlib.sha3_256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha3.update(chunk)
    return sha3.hexdigest()

def get_deterministic_salt(image_path):
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
    sha3 = hashlib.sha3_256()
    sha3.update(data.encode())
    return sha3.hexdigest()

@router.post("/process", response_class=FileResponse)
async def process(pdf: UploadFile = File(...), image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
            pdf_tmp.write(await pdf.read())
            pdf_path = pdf_tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp:
            img_tmp.write(await image.read())
            image_path = img_tmp.name

        pdf_hash = get_pdf_sha3_hash(pdf_path)
        salt = get_deterministic_salt(image_path)
        combined_data = pdf_hash + salt
        final_hash = generate_sha3_hash(combined_data)

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
        record_data = schemas.FileRecordCreate(
            pdf_name=pdf.filename,
            image_name=image.filename,
            hash_value=final_hash,
            pdf_path=pdf_path,
            image_path=image_path,
        )
        crud.create_file_record(db, record_data)

        return FileResponse(output_filename, filename="PDF_with_QR.pdf")

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/records")
def list_records(db: Session = Depends(get_db)):
    return crud.get_all_records(db)

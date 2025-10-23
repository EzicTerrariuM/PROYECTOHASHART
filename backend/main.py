import random
from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import qrcode
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from backend.utils import generate_pdf_hash
from backend.database import get_db

app = FastAPI()

def agregar_pagina_qr(pdf_bytes: bytes, qr_url: str, imagen_bytes: bytes) -> bytes:
    """Agrega una página al PDF con QR, imagen asociada y textos."""
    # Crear PDF temporal con ReportLab
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 1 * inch, "PROYECTO HASHART")

    # Subtítulo
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 1.5 * inch, "PARA VERIFICAR TU DOCUMENTO ESCANEA EL CODIGO QR")

    # Generar QR
    qr = qrcode.QRCode(box_size=6, border=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_io = BytesIO()
    qr_img.save(qr_io, format="PNG")
    qr_io.seek(0)
    qr_pil = Image.open(qr_io)
    qr_pil.save("temp_qr.png")  # Necesario para drawImage
    c.drawImage("temp_qr.png", width/2 - 1*inch, height - 3*inch, 2*inch, 2*inch)

    # Imagen asociada
    imagen_io = BytesIO(imagen_bytes)
    imagen_pil = Image.open(imagen_io)
    imagen_pil.thumbnail((2*inch, 2*inch))
    imagen_pil.save("temp_img.png")
    c.drawImage("temp_img.png", width/2 - 1*inch, height - 5*inch, 2*inch, 2*inch)

    # Créditos
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 0.5 * inch, "Proyecto de tesis de la Universidad de San Buenaventura")
    c.drawCentredString(width / 2, 0.3 * inch, "Creado por Juan Campo & Juan Lara")

    c.showPage()
    c.save()

    # Combinar PDF original con nueva página
    buffer.seek(0)
    new_pdf = PdfReader(buffer)
    original_pdf = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in original_pdf.pages:
        writer.add_page(page)
    for page in new_pdf.pages:
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()

@app.post("/registrar_pdf/")
async def registrar_pdf(pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Validar que sea PDF
        if pdf.content_type != "application/pdf":
            return JSONResponse(content={"error": "El archivo debe ser un PDF"}, status_code=400)

        pdf_bytes = await pdf.read()
        pdf_hash = generate_pdf_hash(pdf_bytes)

        # Obtener imagen aleatoria de la BD
        query = text("SELECT nombre, datos FROM imagenes")
        imagenes = db.execute(query).fetchall()
        if not imagenes:
            return JSONResponse(content={"error": "No hay imágenes en la base de datos"}, status_code=500)
        imagen_asociada = random.choice(imagenes)

        # Guardar en tabla documentos
        insert_query = text(
            "INSERT INTO documentos (nombre, hash_pdf, imagen_asociada) "
            "VALUES (:nombre, :hash_pdf, :imagen_asociada)"
        )
        db.execute(insert_query, {
            "nombre": pdf.filename,
            "hash_pdf": pdf_hash,
            "imagen_asociada": imagen_asociada[0]
        })
        db.commit()

        # Crear URL de verificación
        qr_url = f"https://proyectohashart.up.railway.app/verificar_pdf/"

        # Generar PDF con página extra
        pdf_final = agregar_pagina_qr(pdf_bytes, qr_url, imagen_asociada[1])

        return StreamingResponse(
            BytesIO(pdf_final),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf.filename}"}
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

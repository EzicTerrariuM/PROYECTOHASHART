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
from backend.utils import generate_pdf_hash
from backend.database import get_db
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

origins = [
    "http://localhost:3000",  # React local
    "https://tu-dominio-frontend.com",  # tu frontend en producción
    "*",  # opcional, permite todos (útil para pruebas)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/registrar_pdf/")
async def registrar_pdf(pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Leer PDF y generar hash
        pdf_bytes = await pdf.read()
        pdf_hash = generate_pdf_hash(pdf_bytes)

        # Obtener imagen aleatoria de la BD
        query = text("SELECT nombre, datos FROM imagenes")
        imagenes = db.execute(query).fetchall()
        if not imagenes:
            return JSONResponse(content={"error": "No hay imágenes en la base de datos"}, status_code=500)
        imagen_asociada_nombre, imagen_asociada_bytes = random.choice(imagenes)

        # Guardar en tabla documentos
        insert_query = text(
            "INSERT INTO documentos (nombre, hash_pdf, imagen_asociada) "
            "VALUES (:nombre, :hash_pdf, :imagen_asociada)"
        )
        db.execute(insert_query, {
            "nombre": pdf.filename,
            "hash_pdf": pdf_hash,
            "imagen_asociada": imagen_asociada_nombre
        })
        db.commit()

        # Generar QR con la URL de verificación
        verification_url = f"https://tu-dominio.com/verificar/{pdf_hash}"
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Crear PDF final con página adicional
        original_pdf = BytesIO(pdf_bytes)
        output_pdf = BytesIO()

        # Página adicional con QR e imagen
        width, height = letter
        c = canvas.Canvas(output_pdf, pagesize=letter)

        top_margin = height - inch
        # Título
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, top_margin, "PROYECTO HASHART")
        # Instrucciones
        c.setFont("Helvetica", 14)
        c.drawCentredString(width/2, top_margin - 30, "PARA VERIFICAR TU DOCUMENTO ESCANEA EL CÓDIGO QR")

        # QR
        qr_size = 150
        qr_x = width/2 - qr_size/2
        qr_y = top_margin - 200
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        c.drawInlineImage(Image.open(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)

        # Imagen asociada
        img_x = width/2 - 100
        img_y = qr_y - 220
        imagen = Image.open(BytesIO(imagen_asociada_bytes))
        imagen.thumbnail((200, 200))
        c.drawInlineImage(imagen, img_x, img_y)

        # Pie de página
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width/2, 30, "Proyecto de tesis de la Universidad de San Buenaventura")
        c.drawCentredString(width/2, 15, "Creado por Juan Campo & Juan Lara")

        c.showPage()
        c.save()

        # Combinar PDF original con la página adicional
        from PyPDF2 import PdfReader, PdfWriter

        output_pdf.seek(0)
        additional_pdf_reader = PdfReader(output_pdf)
        original_pdf_reader = PdfReader(original_pdf)
        pdf_writer = PdfWriter()

        for page in original_pdf_reader.pages:
            pdf_writer.add_page(page)
        for page in additional_pdf_reader.pages:
            pdf_writer.add_page(page)

        final_pdf = BytesIO()
        pdf_writer.write(final_pdf)
        final_pdf.seek(0)

        return StreamingResponse(
            final_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf.filename}"}
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/verificar_pdf/")
async def verificar_pdf(pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Leer PDF y generar hash
        pdf_bytes = await pdf.read()
        pdf_hash = generate_pdf_hash(pdf_bytes)

        # Buscar el documento en la tabla 'documentos'
        query_doc = text("SELECT id FROM documentos WHERE hash_pdf = :hash_pdf")
        result = db.execute(query_doc, {"hash_pdf": pdf_hash}).fetchone()

        if result:
            documento_id = result[0]
            resultado = True
        else:
            documento_id = None
            resultado = False

        # Guardar la verificación
        if documento_id:
            insert_verificacion = text(
                "INSERT INTO verificaciones (documento_id, resultado) VALUES (:documento_id, :resultado)"
            )
            db.execute(insert_verificacion, {"documento_id": documento_id, "resultado": resultado})
            db.commit()

        return JSONResponse(content={"hash": pdf_hash, "valido": resultado})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
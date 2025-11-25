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

# Dominios permitidos para CORS
origins = [
    "http://localhost:3000",
    "https://proyectohashart-front-production.up.railway.app",
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

        # Generar QR con la URL hacia el frontend de Railway
        verification_url = f"https://proyectohashart-front-production.up.railway.app/upload?hash={pdf_hash}"
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Crear PDF que contiene solo la página con el QR y la imagen
        output_pdf = BytesIO()
        width, height = letter
        c = canvas.Canvas(output_pdf, pagesize=letter)

        top_margin = height - inch
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, top_margin, "PROYECTO HASHART")

        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, top_margin - 30, "Escanea este código QR para verificar tu documento")

        # QR centrado
        qr_size = 200
        qr_x = width / 2 - qr_size / 2
        qr_y = height / 2 - qr_size / 2 + 100
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        c.drawInlineImage(Image.open(qr_buffer), qr_x, qr_y, width=qr_size, height=qr_size)

        # Imagen asociada debajo del QR
        imagen = Image.open(BytesIO(imagen_asociada_bytes))
        imagen.thumbnail((200, 200))
        img_x = width / 2 - imagen.width / 2
        img_y = qr_y - imagen.height - 40
        c.drawInlineImage(imagen, img_x, img_y, width=imagen.width, height=imagen.height)

        # Pie de página
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width / 2, 40, "Proyecto de tesis de la Universidad de San Buenaventura")
        c.drawCentredString(width / 2, 25, "Creado por Juan Campo & Juan Lara")

        c.showPage()
        c.save()

        output_pdf.seek(0)

        return StreamingResponse(
            output_pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=QR_{pdf.filename}"}
        )

    except Exception as e:
        print("Error en registrar_pdf:", e)
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

        # Guardar la verificación si el documento existe
        if documento_id:
            insert_verificacion = text(
                "INSERT INTO verificaciones (documento_id, resultado) VALUES (:documento_id, :resultado)"
            )
            db.execute(insert_verificacion, {"documento_id": documento_id, "resultado": resultado})
            db.commit()

        return JSONResponse(content={"hash": pdf_hash, "valido": resultado})

    except Exception as e:
        print("Error en verificar_pdf:", e)
        return JSONResponse(content={"error": str(e)}, status_code=500)
    a

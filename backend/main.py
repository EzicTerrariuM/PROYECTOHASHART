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

app = FastAPI()

@app.post("/registrar_pdf/")
async def registrar_pdf(pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Validar que sea un PDF
        if pdf.content_type != "application/pdf":
            return JSONResponse(content={"error": "El archivo debe ser un PDF"}, status_code=400)

        # Leer PDF y generar hash
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

        # Devolver el PDF como descarga
        return StreamingResponse(
            BytesIO(pdf_bytes), 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pdf.filename}"}
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/verificar_pdf/")
async def verificar_pdf(pdf: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Validar que sea un PDF
        if pdf.content_type != "application/pdf":
            return JSONResponse(content={"error": "El archivo debe ser un PDF"}, status_code=400)

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

        # Guardar la verificación solo si se encontró el documento
        if documento_id:
            insert_verificacion = text(
                "INSERT INTO verificaciones (documento_id, resultado) VALUES (:documento_id, :resultado)"
            )
            db.execute(insert_verificacion, {"documento_id": documento_id, "resultado": resultado})
            db.commit()

        return JSONResponse(content={"hash": pdf_hash, "valido": resultado})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

import os
from sqlalchemy.orm import Session
from backend import crud, schemas
from backend.database import SessionLocal

# Carpeta donde están las imágenes
IMAGES_DIR = r"C:\Users\fireb\Downloads\Outputs"

# Conexión a la base de datos
db: Session = SessionLocal()

# Iterar sobre los archivos de la carpeta
for filename in os.listdir(IMAGES_DIR):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        
        # Crear esquema de imagen
        imagen_db = schemas.ImagenCreate(
            nombre=filename,
            datos=image_bytes
        )

        # Guardar en la base de datos
        crud.crear_imagen(db, imagen_db)
        print(f"Imagen subida: {filename}")

db.close()
print("¡Todas las imágenes se subieron correctamente!")

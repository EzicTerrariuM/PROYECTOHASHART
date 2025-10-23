import hashlib
from PIL import Image
from io import BytesIO
import qrcode

def generate_pdf_hash(pdf_bytes: bytes) -> str:
    """
    Genera un hash SHA256 del PDF.
    """
    return hashlib.sha256(pdf_bytes).hexdigest()

def get_random_pixel_salt_from_bytes(image_bytes: bytes, num_pixels: int = 10) -> str:
    """
    Genera un salt determinista a partir de píxeles seleccionados de la imagen en bytes.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = image.size

    pixels = []
    for i in range(num_pixels):
        x = (i * 37) % width
        y = (i * 73) % height
        pixels.append(image.getpixel((x, y)))

    pixel_bytes = b''.join(bytes([r, g, b]) for r, g, b in pixels)
    salt = hashlib.sha256(pixel_bytes).hexdigest()
    return salt

def generate_verification_qr(url: str) -> Image.Image:
    """
    Genera un QR code para la URL de verificación y lo devuelve como imagen PIL.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    return qr_img

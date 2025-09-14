from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
from io import BytesIO
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

# Use relative imports because main.py is inside app/
from .crypto_utils import encrypt_message, decrypt_message
from .stego_utils import embed_into_image, extract_from_image

# ⚡ Create FastAPI app first
app = FastAPI()

# ⚡ Add CORS middleware AFTER app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/embed")
async def embed_message(
    image_file: UploadFile = File(...),
    message: str = Form(...),
    password: str = Form(...)
):
    image_bytes = await image_file.read()
    image = Image.open(BytesIO(image_bytes))
        
    encrypted_message, AES_key, nonce, auth_tag, salt = encrypt_message(message, password)
    
    input_buffer = BytesIO()
    image.save(input_buffer, format="PNG")
    input_buffer.seek(0)
    
    output_buffer = BytesIO()
    embed_into_image(encrypted_message, salt, nonce, auth_tag, input_buffer, output_buffer)
    
    output_buffer.seek(0)
    return StreamingResponse(
        output_buffer,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename=stego_{image_file.filename}"}
    )

@app.post("/extract")
async def extract_message(
    image_file: UploadFile = File(...),
    password: str = Form(...)
):
    image_bytes = await image_file.read()
    image = Image.open(BytesIO(image_bytes))

    input_buffer = BytesIO()
    image.save(input_buffer, format="PNG")
    input_buffer.seek(0)

    extracted = extract_from_image(input_buffer)
    salt, nonce, auth_tag, encrypted_message = extracted

    AES_key = PBKDF2(password, salt, 32, count=100000, hmac_hash_module=SHA256)
    message_in_string = decrypt_message(encrypted_message, AES_key, nonce, auth_tag)

    return JSONResponse({"message": message_in_string})

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import base64
from typing import Optional
from steg_logic import encode_message, decode_message, compare_images

app = FastAPI(title="Steganography API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/hide")
async def hide_message(
    cover_image: UploadFile = File(...),
    secret_text: Optional[str] = Form(None),
    secret_file: Optional[UploadFile] = File(None),
    password: Optional[str] = Form(None)
):
    if not secret_text and not secret_file:
        raise HTTPException(status_code=400, detail="Must provide secret text or a secret file")
        
    cover_path = os.path.join(UPLOAD_DIR, cover_image.filename)
    with open(cover_path, "wb") as buffer:
        shutil.copyfileobj(cover_image.file, buffer)
        
    payload = {}
    if secret_text:
        payload["text"] = secret_text
        
    if secret_file:
        file_content = await secret_file.read()
        encoded_file = base64.b64encode(file_content).decode('utf-8')
        payload["file"] = {
            "filename": secret_file.filename,
            "data": encoded_file
        }
        
    try:
        output_filename = f"stego_{cover_image.filename}"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        encode_message(cover_path, payload, key=password, output_path=output_path)
        
        return FileResponse(
            output_path, 
            media_type="image/png", 
            filename=output_filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up cover image
        if os.path.exists(cover_path):
            os.remove(cover_path)

@app.post("/api/extract")
async def extract_message(
    stego_image: UploadFile = File(...),
    password: Optional[str] = Form(None)
):
    stego_path = os.path.join(UPLOAD_DIR, stego_image.filename)
    with open(stego_path, "wb") as buffer:
        shutil.copyfileobj(stego_image.file, buffer)
        
    try:
        payload = decode_message(stego_path, key=password)
        return JSONResponse(content=payload)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to extract message")
    finally:
        if os.path.exists(stego_path):
            os.remove(stego_path)

@app.post("/api/compare")
async def compare_image(
    original_image: UploadFile = File(...),
    stego_image: UploadFile = File(...)
):
    orig_path = os.path.join(UPLOAD_DIR, "orig_" + original_image.filename)
    stego_path = os.path.join(UPLOAD_DIR, "compare_" + stego_image.filename)
    diff_path = os.path.join(UPLOAD_DIR, "diff.png")
    
    with open(orig_path, "wb") as buffer:
        shutil.copyfileobj(original_image.file, buffer)
    with open(stego_path, "wb") as buffer:
        shutil.copyfileobj(stego_image.file, buffer)
        
    try:
        stats = compare_images(orig_path, stego_path, diff_path)
        
        # Read diff image and convert to base64
        with open(diff_path, "rb") as dfile:
            encoded_diff = base64.b64encode(dfile.read()).decode('utf-8')
            stats['diff_image_b64'] = f"data:image/png;base64,{encoded_diff}"
            
        return JSONResponse(content=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(orig_path):
            os.remove(orig_path)
        if os.path.exists(stego_path):
            os.remove(stego_path)
        if os.path.exists(diff_path):
            os.remove(diff_path)

# Image Steganography Web App

A full-stack web application for hiding secret text or files inside images using least significant bit (LSB) steganography. The application also supports optional AES encryption and provides image comparison metrics to show how much the carrier image changed.

## Features

- Hide text inside PNG or JPEG images.
- Hide a file inside an image and restore it during extraction.
- Optionally encrypt the hidden payload with a password.
- Extract hidden messages and files from stego images.
- Compare an original image with a stego image.
- View changed pixels, percentage changed, LSB differences, MSE, PSNR, and a difference map.
- Simple browser frontend backed by a FastAPI API.

## Project Structure

```text
stego_web_app/
├── backend/
│   ├── main.py
│   ├── steg_logic.py
│   ├── requirements.txt
│   └── temp_uploads/
└── frontend/
    ├── index.html
    ├── script.js
    └── styles.css
```

## Requirements

- Python 3.9 or newer
- A modern web browser

## Run Locally

### 1. Install backend dependencies

Open a terminal in the `backend` directory:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the API

```bash
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### 3. Open the frontend

Open `frontend/index.html` in a browser. Keep the FastAPI server running while using the application.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/hide` | Embeds text or a file in an image and returns a stego PNG. |
| `POST` | `/api/extract` | Extracts a hidden text or file payload. |
| `POST` | `/api/compare` | Compares two images and returns metrics plus a difference map. |

## How It Works

The app stores payload data as JSON and writes its binary representation into the least significant bits of image color channels. A delimiter marks the end of the hidden payload. When a password is supplied, the JSON payload is encrypted before it is embedded.

## Security Notes

This project is intended for learning and local demonstrations. Do not use it for highly sensitive data without a security review. The current implementation uses AES-ECB and a simple password-to-key conversion, and the API is configured with permissive CORS for local development.

## License

No license has been selected for this project yet.
import json
import base64
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ---------- AES ENCRYPTION/DECRYPTION ----------
def encrypt_message(message: str, key: str) -> str:
    key_bytes = pad(key.encode(), 16)
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    enc = cipher.encrypt(pad(message.encode('utf-8'), 16))
    return base64.b64encode(enc).decode()

def decrypt_message(enc: str, key: str) -> str:
    key_bytes = pad(key.encode(), 16)
    enc_bytes = base64.b64decode(enc)
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(enc_bytes), 16)
    return decrypted.decode('utf-8')

# ---------- CONVERT TO BINARY ----------
def to_bin(data: str) -> str:
    return ''.join(format(ord(char), '08b') for char in data)

# ---------- ENCODE MESSAGE ----------
def encode_message(image_path: str, payload: dict, key: str = None, output_path: str = None):
    # Determine the message to hide.
    json_str = json.dumps(payload)
    if key and len(key) >= 4:
        # If we have a key, encrypt the payload and wrap it in a special struct so we know it's encrypted
        encrypted = encrypt_message(json_str, key)
        final_payload = f"ENCRYPTED|{encrypted}"
    else:
        final_payload = f"PLAIN|{json_str}"
    
    # We append a custom delimiter to signify the end of the message
    delimiter = "1111111111111110" 
    binary_msg = to_bin(final_payload) + delimiter
    
    img = Image.open(image_path)
    img = img.convert('RGB')
    
    data_index = 0
    pixels = list(img.getdata())
    new_pixels = []
    
    for pixel in pixels:
        if data_index < len(binary_msg):
            r, g, b = pixel
            r = (r & ~1) | int(binary_msg[data_index])
            data_index += 1
            if data_index < len(binary_msg):
                g = (g & ~1) | int(binary_msg[data_index])
                data_index += 1
            if data_index < len(binary_msg):
                b = (b & ~1) | int(binary_msg[data_index])
                data_index += 1
            new_pixels.append((r, g, b))
        else:
            new_pixels.append(pixel)
            
    img.putdata(new_pixels)
    if not output_path:
        # Auto-generate name if not provided
        output_path = image_path.replace(".png", "_stego.png").replace(".jpg", "_stego.png").replace(".jpeg", "_stego.png")
    
    img.save(output_path, "PNG")
    return output_path

# ---------- DECODE MESSAGE ----------
def decode_message(stego_image_path: str, key: str = "") -> dict:
    image = Image.open(stego_image_path)
    binary_data = ""
    
    # Delimiter in binary: 1111111111111110
    delimiter = "1111111111111110"
    
    found = False
    for pixel in image.getdata():
        if found:
            break
        for color in pixel[:3]:
            binary_data += str(color & 1)
            
            if binary_data.endswith(delimiter):
                binary_data = binary_data[:-len(delimiter)]
                found = True
                break
    
    if not found:
        # If delimiter not found
        raise ValueError("No hidden data found or image is corrupted.")
    
    chars = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    extracted_str = ""
    for byte in chars:
        if len(byte) == 8:
            extracted_str += chr(int(byte, 2))
            
    if extracted_str.startswith("ENCRYPTED|"):
        encrypted_data = extracted_str.split("|", 1)[1]
        try:
            decrypted_str = decrypt_message(encrypted_data, key)
            return json.loads(decrypted_str)
        except Exception as e:
            raise ValueError("Incorrect key or corrupted image.")
    elif extracted_str.startswith("PLAIN|"):
        plain_str = extracted_str.split("|", 1)[1]
        return json.loads(plain_str)
    else:
        raise ValueError("Unrecognized data format in image.")
        
# ---------- IMAGE COMPARISON ----------
import math

def compare_images(orig_path: str, stego_path: str, diff_path: str) -> dict:
    orig = Image.open(orig_path).convert('RGB')
    stego = Image.open(stego_path).convert('RGB')
    
    if orig.size != stego.size:
        raise ValueError(f"Images are not the same size. Original: {orig.size}, Stego: {stego.size}")
        
    orig_pixels = list(orig.getdata())
    stego_pixels = list(stego.getdata())
    
    diff_pixels = []
    
    changed_pixels = 0
    lsb_diffs = 0
    sq_error_sum = 0
    
    for p1, p2 in zip(orig_pixels, stego_pixels):
        r1, g1, b1 = p1
        r2, g2, b2 = p2
        
        # Amplified difference
        diff_r = abs(r1 - r2) * 255
        diff_g = abs(g1 - g2) * 255
        diff_b = abs(b1 - b2) * 255
        
        diff_pixels.append((diff_r, diff_g, diff_b))
        
        if p1 != p2:
            changed_pixels += 1
            if r1 != r2: lsb_diffs += 1
            if g1 != g2: lsb_diffs += 1
            if b1 != b2: lsb_diffs += 1
            
        sq_error_sum += (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
        
    diff_img = Image.new('RGB', orig.size)
    diff_img.putdata(diff_pixels)
    diff_img.save(diff_path, "PNG")
    
    total_pixels = orig.width * orig.height
    total_channels = total_pixels * 3
    
    mse = sq_error_sum / total_channels
    if mse == 0:
        psnr = float('inf')
    else:
        psnr = 20 * math.log10(255.0 / math.sqrt(mse))
        
    percent_changed = (changed_pixels / total_pixels) * 100
    
    return {
        "dimensions": f"{orig.width}x{orig.height}",
        "changed_pixels": changed_pixels,
        "percent_changed": f"{percent_changed:.4f}%",
        "lsb_differences": lsb_diffs,
        "mse": round(mse, 5),
        "psnr": f"{round(psnr, 2)} dB"
    }

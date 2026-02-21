# Service de gestion du stockage de fichiers (simulation S3) - app/services/infra/storage.py
import shutil
import os
import uuid
from fastapi import UploadFile



# --- GESTION FICHIERS (Simulation S3) ---
UPLOAD_DIR = "uploads" 

def _save_file_locally(file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    extension = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_name) # Plus propre pour Windows/Linux
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # On retourne le chemin URL (sans le slash initial pour la DB, on le gérera au rendu)
    return f"uploads/{unique_name}"
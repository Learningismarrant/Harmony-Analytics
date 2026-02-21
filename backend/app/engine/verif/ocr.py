# Service de reconnaissance optique de caractères (OCR) pour les titres - app/services/engine/verif_engine/ocr.py
import os
import re
import pytesseract
import tempfile

from datetime import datetime

from PIL import Image
from pdf2image import convert_from_path



#Utilise le chemin exact où se trouve pdftoppm.exe
# Teste C:\poppler\bin si Library\bin ne fonctionne pas
POPPLER_PATH = r'C:\poppler\Library\bin' 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def clean_titre_format(raw_titre: str):
    """
    Nettoyage strict pour PROMETE : 8 chiffres / (0) + 1 ou 2 chiffres
    """
    # 1. On ne garde que les chiffres
    digits = re.sub(r"\D", "", raw_titre)
    
    if len(digits) >= 9:
        main_part = digits[:8] # Les 8 premiers chiffres
        suffix = digits[8:]    # Le reste
        
        # Règle du suffixe : si 2 chiffres, le premier doit être 0 (ex: 103 -> 03)
        if len(suffix) >= 2:
            last_two = suffix[-2:]
            if not last_two.startswith('0'):
                suffix_final = "0" + last_two[1]
            else:
                suffix_final = last_two
        else:
            suffix_final = suffix
            
        return f"{main_part} / {suffix_final}"
    
    return raw_titre

def perform_ocr_test(file_path: str, doc_id: str):
    # Vérification de sécurité avant de commencer
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Fichier introuvable sur le disque : {file_path}"}
    try:
        # 1. CONVERSION (PDF -> IMAGE)
        if file_path.lower().endswith(".pdf"):
            print(f"Tentative de conversion PDF: {file_path}")
            images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
           
            temp_img_path = f"temp_ocr_{doc_id}.jpg"
            images[0].save(temp_img_path, "JPEG")
            path_to_read = temp_img_path
        else:
            path_to_read = file_path

        # 2. LECTURE TESSERACT
        with Image.open(path_to_read) as img:
            text = pytesseract.image_to_string(img, lang='fra+eng')

        # 3. NETTOYAGE FICHIER TEMPORAIRE
        if file_path.lower().endswith(".pdf") and os.path.exists(f"temp_ocr_{doc_id}.jpg"):
            os.remove(f"temp_ocr_{doc_id}.jpg")

        # 4. EXTRACTION CIBLÉE
        
        # Numéro de titre complet et nettoyé
        num_titre_raw = "Inconnu"
        num_titre_match = re.search(r"titre\s*[:\s]*([^\n]+)", text, re.I)
        if num_titre_match:
            num_titre_raw = clean_titre_format(num_titre_match.group(1).strip())
        
        # Séparation pour PROMETE
        titre_principal = ""
        titre_suffixe = ""
        if "/" in num_titre_raw:
            parts = num_titre_raw.split("/")
            titre_principal = parts[0].strip()
            titre_suffixe = parts[1].strip()

        # Numéro de titulaire
        num_titulaire_match = re.search(r"titulaire\s*[:\s]*(\d+)", text, re.I)
        num_titulaire = num_titulaire_match.group(1).strip() if num_titulaire_match else "Inconnu"

        # Date d'expiration (Stratégie Max Date)
        date_exp = "Inconnu"
        all_dates = re.findall(r"(\d{2}/\d{2}/\d{4})", text)
        if all_dates:
            try:
                date_objects = [datetime.strptime(d, "%d/%m/%Y") for d in all_dates]
                date_exp = max(date_objects).strftime("%d/%m/%Y")
            except:
                date_exp = all_dates[0] # Fallback sur la première trouvée

        return {
            "status": "success",
            "extracted": {
                "num_titre_complet": num_titre_raw,
                "promete_titre": titre_principal,
                "promete_version": titre_suffixe,
                "num_titulaire": num_titulaire,
                "date_expiration": date_exp
            },
            
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
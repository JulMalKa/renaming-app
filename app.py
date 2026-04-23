from csv import reader
import re
import cv2
import numpy as np
import easyocr
from pathlib import Path
from pdf2image import convert_from_path

VIN_REGEX = re.compile(r'\b([A-Z0-9]{12}[0-9]{5})(?:\([A-Z0-9]+\))?\b')
LPN_REGEX = re.compile(r'\b[A-Z]{1}[A-Z0-9]{1,2}\s?[0-9A-Z]{4,5}\b')

CATEGORIES = {
    "temp" : ["POZWOLENIE", "CZASOWE", "CEL", "WYDANIA", "CZASOWEGO"],
    "vp" : ["WSPÓLNOTA", "EUROPEJSKA", "DOWÓD", "REJESTRACYJNY", "DR", "DRBAU", "BAT", "DRIBAT", "BAR", "BAU"],
    "ec" : ["CEMT-Nachweis", "CEMT", "ECMT"],
    "coc" : ["CO2", "CO", "mg/kWh", "THC"]
}

EXTENSIONS = {
        "temp" : "_VP_01",
        "vp": "_VP_01",
        "ec": "_EC_02",
        "coc": "_COC_03"
    }

def get_unique_filepath(folder: Path, base_name: str) -> Path:
    new_path = folder / f"{base_name}.pdf"
    counter = 1
    
    while new_path.exists():
        new_path = folder / f"{base_name}_{counter}.pdf"
        counter += 1
        
    return new_path


def categorize_document(text: str) -> str:
    text_lower = text.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in text_lower for keyword in keywords):
            return category
    return None



def read_image(reader: easyocr.Reader, image: np.ndarray) -> str:
    results = reader.readtext(image)
    return " ".join([text for _, text, _ in results]) 


def check_for_vp(image: np.ndarray) -> tuple[np.ndarray, bool]:
    image_np = np.array(image)
    qr_detector = cv2.QRCodeDetector()
    
    _retval, points = qr_detector.detect(image_np)
    
    if points is None:
        return image_np, False
    
    print(f"found QR points: {points}")
    
    cx = int(points[:, 0, 0].mean())
    cy = int(points[:, 0, 1].mean())
    h, w = image_np.shape[:2]

    # rotation based on QR code placement - we want QR code to be in the right bottom corner
    if cx < w/2 and cy < h/2:
        image_np = cv2.rotate(image_np, cv2.ROTATE_180)                 # up left to right bottom
    elif cx > w/2 and cy < h/2:
        image_np = cv2.rotate(image_np, cv2.ROTATE_90_CLOCKWISE)        # right top to right bottom
    elif cx < w/2 and cy > h/2:
        image_np = cv2.rotate(image_np, cv2.ROTATE_90_COUNTERCLOCKWISE) # left bottom to right bottom

    return image_np, True


# ================= ocr ===================

def process_and_rename_images(folder: Path, reader: easyocr.Reader) -> dict:
    vin_lpn_map = {}

    for pdf_path in folder.glob("*.pdf"):
        images = convert_from_path(str(pdf_path))
        
        temp_lpn = None
        vin_last4 = None
        doc_category = None

        for image in images:
            rotated_image, has_qr = check_for_vp(image)
            all_text = read_image(reader, rotated_image) 

            if has_qr:
                doc_category = "vp"
            else:
                doc_category = categorize_document(all_text)
            
            lpn_match = LPN_REGEX.search(all_text)
            vin_match = VIN_REGEX.search(all_text)

            if lpn_match:
                temp_lpn = lpn_match.group().replace(" ", "")
            if vin_match:
                vin_last4 = vin_match.group(1)[-4:]

            if doc_category:
                break
                
        if vin_last4 and vin_last4 not in vin_lpn_map:
            vin_lpn_map[vin_last4] = temp_lpn

        extension = EXTENSIONS.get(doc_category, "_UNKNOWN")
        vin_identifier = vin_last4 if vin_last4 else "x"
        base_name = f"PL_{vin_identifier}{extension}"
        
        new_path = get_unique_filepath(folder, base_name)
        pdf_path.rename(new_path)
        
    return vin_lpn_map

def final_rename(folder: Path, vin_lpn_map: dict):
    for pdf_path in folder.glob("*.pdf"):
        filename = pdf_path.name
        
        vin_match = re.search(r'([0-9]{4})', filename) 
        vin = vin_match.group() if vin_match else "x"
        
        extension_match = re.search(r'_(VP_01|EC_02|COC_03)', filename)
        extension = f"_{extension_match.group(1)}" if extension_match else "_UNKNOWN"
        
        lpn = vin_lpn_map.get(vin) or vin

        base_name = f"PL_{lpn}{extension}"
        final_path = get_unique_filepath(folder, base_name)
        
        pdf_path.rename(final_path)



DOWNLOADS_FOLDER = Path.home() / "Downloads"
OCR_READER = easyocr.Reader(['pl', 'en'], gpu=False)

print(f"Processing folder: {DOWNLOADS_FOLDER}")
    
mapped_data = process_and_rename_images(DOWNLOADS_FOLDER, OCR_READER)
print("\ncollected map VIN - LPN:")
print(mapped_data)

print("\nFinal renaming")
final_rename(DOWNLOADS_FOLDER, mapped_data)
print("Renaming completed.")


            
        


   

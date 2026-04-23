import easyocr
from pdf2image import convert_from_path
import numpy as np
import re
import os

folder = os.path.join(os.path.expanduser("~"), "Downloads")
reader = easyocr.Reader(['pl', 'en'], gpu=False)


for file in os.listdir(folder):
    if file.endswith(".pdf"):
        pdf_path = os.path.join(folder, file)
        images = convert_from_path(pdf_path)

        temp_lpn = None
        vin_last4 = None

        for page_num, image in enumerate(images):
            results = reader.readtext(np.array(image))
            all_text = " ".join([text for _, text, _ in results])

            vin_match = re.search(r'\b([A-Z0-9]{12}[0-9]{5})(?:\([A-Z0-9]+\))?\b', all_text)
            lpn_match = re.search(r'\b(?:A\s)?[A-Z]{1}[0-9]{1,2}[\s][0-9A-Z]{4,5}\b', all_text)
            # to_rotate = re.search(r'<|>|v')

            if lpn_match:
                temp_lpn = lpn_match.group().replace(" ", "")

            if vin_match:
                vin_last4 = vin_match.group(1)[-4:]
            
            print(vin_last4, " ; ", temp_lpn)

            # print("page number ", page_num, file)
            # print(all_text)
           



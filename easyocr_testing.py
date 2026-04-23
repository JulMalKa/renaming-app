import easyocr
from pdf2image import convert_from_path
import numpy as np
import re
import os

folder = os.path.join(os.path.expanduser("~"), "Downloads")
reader = easyocr.Reader(['pl', 'en'], gpu=False)
vin_lpn_map = {}


for file in os.listdir(folder):
    if file.endswith(".pdf"):
        pdf_path = os.path.join(folder, file)
        images = convert_from_path(pdf_path)

        temp_lpn = None
        vin_last4 = None

        for page_num, image in enumerate(images):
            results = reader.readtext(np.array(image))
            all_text = " ".join([text for _, text, _ in results])

            print("page number ", page_num, file)
            print(all_text)

               



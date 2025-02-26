from PIL import Image
import pytesseract
import numpy as np

target_file = 'data/example.jpg'

img = np.array(Image.open(target_file))

text = pytesseract.image_to_string(img)

print("Extracted text:", text)

import cv2
import pytesseract
import numpy as np
import imutils
from doctr.io import DocumentFile
from doctr.models import ocr_predictor



# Load the image
target_image = "data/3.jpg"
# image = cv2.imread(target_image)
model = ocr_predictor(pretrained=True)
# PDF
doc = DocumentFile.from_images(target_image)
# Analyze
result = model(doc)
print(result)
# resized_image = cv2.resize(image, (120, 120), interpolation=cv2.INTER_AREA)

# # Save the processed image with bounding box
# cv2.imwrite(target_image, resized_image)
# print(pytesseract.image_to_string(target_image))
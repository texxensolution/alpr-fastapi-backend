import os
import shutil
from uuid import uuid4
from fastapi import UploadFile

UPLOAD_TEMP_DIR = "uploads"

os.makedirs(UPLOAD_TEMP_DIR, exist_ok=True)

def store_file(file: UploadFile) -> str:
    file_name = f"{uuid4()}-{file.filename}"

    file_path = os.path.join(UPLOAD_TEMP_DIR, file_name)

    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def delete_file(file_path: str):
    os.remove(file_path)    
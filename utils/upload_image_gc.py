import requests
import os
from typing import Literal, Optional
from pydantic import BaseModel


class UploadImageMessageDataField(BaseModel):
    image_key: str


class UploadImageMessageResponse(BaseModel):
    code: int
    msg: str
    data: Optional[UploadImageMessageDataField] = None


MAX_SIZE_MB = 10

def upload_image_gc(
    tenant_token: str,
    image_path: str,
    image_type: Literal['avatar', 'message'] = 'message'
):
    url = "https://open.larksuite.com/open-apis/im/v1/images"

    # Check if file exists
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"The file '{image_path}' does not exist.")

    # Check file size
    file_size = os.path.getsize(image_path)
    if file_size > MAX_SIZE_MB * 1024 * 1024:
        raise ValueError(f"Image size exceeds {MAX_SIZE_MB}MB limit.")

     # Prepare headers
    headers = {
        "Authorization": f"Bearer {tenant_token}",
    }

    # Prepare multipart/form-data
    with open(image_path, 'rb') as image_file:
        files = {
            "image": (os.path.basename(image_path), image_file, "application/octet-stream"),
        }

        data = {
            "image_type": image_type
        }

        try:
            response = requests.post(
                url, 
                headers=headers, 
                files=files, 
                data=data
            )

            return UploadImageMessageResponse(**response.json())
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
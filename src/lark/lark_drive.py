import os
import aiofiles
import logging
import httpx
from pydantic import BaseModel
from .exceptions import LarkBaseHTTPException
from .token_manager import TokenManager

PUT_MEDIA_ATTACHMENT_URL = (
    "https://open.larksuite.com/open-apis/drive/v1/medias/upload_all"
)

logger = logging.getLogger(__name__)


class PutMediaAttachmentResponse(BaseModel):
    class PutMediaAttachmentDataField(BaseModel):
        file_token: str

    code: int
    msg: str
    data: PutMediaAttachmentDataField


class LarkDrive:
    def __init__(self, token_manager: TokenManager, max_size_mb: int = 20):
        self._token_manager = token_manager
        self._MAX_SIZE_MB: int = max_size_mb * 1024 * 1024
        self._async_client = httpx.AsyncClient()
        logger.info("LarkDrive client initialized...")

    async def put_attachment(
        self,
        file_path: str,
    ):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        if os.path.getsize(file_path) > self._MAX_SIZE_MB:
            raise ValueError(
                f"File {file_path} exceeds the maximum size of {self._MAX_SIZE_MB} bytes"
            )

        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        response = await self._async_client.post(
            PUT_MEDIA_ATTACHMENT_URL,
            headers={"Authorization": f"Bearer {tenant_token}"},
            files={"file": open(file_path, "rb")},
        )

        response = PutMediaAttachmentResponse(**response.json())

        if response.code != 0:
            raise LarkBaseHTTPException(response.code, response.msg)

        return response

    async def download_attachment(
        self,
        media_url: str,
        save_as: str,
    ):
        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token
        headers = {"Authorization": f"Bearer {tenant_token}"}
        response = await self._async_client.get(url=media_url, headers=headers)
        if response.status_code != 200:
            return False
        async with aiofiles.open(
            save_as,
            "wb"
        ) as media_file:
            content = await response.aread()
            await media_file.write(content)
        return True

    async def close(self):
        await self._async_client.aclose()
        logger.info("LarkDrive client closed!")

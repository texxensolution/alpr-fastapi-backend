import httpx
import os
from .exceptions import LarkBaseHTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from .token_manager import TokenManager


class SendMessageDataBodyField(BaseModel):
    content: str


class SendMessageSenderField(BaseModel):
    id: str
    id_type: str
    sender_type: str
    tenant_key: str


class SendMessageDataField(BaseModel):
    body: SendMessageDataBodyField
    chat_id: str
    create_time: str
    deleted: bool
    message_id: str
    msg_type: str
    sender: SendMessageSenderField
    update_time: str
    updated: bool


class SendMessageResponse(BaseModel):
    code: int
    data: Optional[SendMessageDataField] = None
    msg: str
    
class SendMessagePayload(BaseModel):
    receive_id: str
    msg_type: str
    content: str


class PutAttachmentMessageDataField(BaseModel):
    image_key: str


class PutAttachmentResponse(BaseModel):
    code: int
    msg: str
    data: Optional[PutAttachmentMessageDataField] = None


class BuzzMessageResponse(BaseModel):
    code: int
    msg: str
    data: Optional[dict] = None

class LarkMessenger:
    def __init__(self, token_manager: TokenManager):
        self._token_manager = token_manager
        self.MAX_SIZE_MB: int = 10

    async def send_message(
        self,
        payload: SendMessagePayload,
        receive_id_type: str = "chat_id"
    ):
        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        url = "https://open.larksuite.com/open-apis/im/v1/messages"

        params = {"receive_id_type": receive_id_type}

        headers = {"Authorization": f"Bearer {tenant_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=url, json=payload.model_dump(), headers=headers, params=params
            )

            response = SendMessageResponse(**response.json())

            if response.code != 0:
                raise LarkBaseHTTPException(response.code, response.msg)

            return response

    async def put_attachment(
        self,
        attachment_path: str,
        image_type: Literal["avatar", "message"] = "message",
    ) -> PutAttachmentResponse:
        tenant_access_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        url = "https://open.larksuite.com/open-apis/im/v1/images"

        # check if file exists
        if not os.path.isfile(attachment_path):
            raise FileNotFoundError(f"The file '{attachment_path}' does not exist.")

        # check file size
        file_size = os.path.getsize(attachment_path)

        if file_size > self.MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Image size exceeds {self.MAX_SIZE_MB}MB limit.")

        # prepare headers
        headers = {
            "Authorization": f"Bearer {tenant_access_token}",
        }

        # prepare multipart/form-data
        with open(attachment_path, "rb") as image_file:
            files = {
                "image": (
                    os.path.basename(attachment_path),
                    image_file,
                    "application/octet-stream",
                ),
            }

            data = {"image_type": image_type}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, files=files, data=data
                )

                response = PutAttachmentResponse(**response.json())

                if response.code != 0:
                    raise LarkBaseHTTPException(response.code, response.msg)
                return response

    async def buzz_message(self, message_id: str, group_members_union_id: list[str]):
        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        formatted_url = "https://open.larksuite.com/open-apis/im/v1/messages/{message_id}/urgent_app".format(
            message_id=message_id
        )

        headers = {"Authorization": f"Bearer {tenant_token}"}

        params = {"user_id_type": "union_id"}

        body = {"user_id_list": group_members_union_id}

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url=formatted_url, json=body, headers=headers, params=params
            )

            response = BuzzMessageResponse(**response.json())

            if response.code != 0:
                raise LarkBaseHTTPException(response.code, response)
            
        return response

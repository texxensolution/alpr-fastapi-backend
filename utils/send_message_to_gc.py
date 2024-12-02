import requests
from pydantic import BaseModel
from typing import Optional


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
    

def send_message_to_gc(tenant_token: str, content: str):
    url = "https://open.larksuite.com/open-apis/im/v1/messages"

    params = {
        "receive_id_type": "chat_id"
    }

    headers = {
        "Authorization": f"Bearer {tenant_token}"
    }

    message = {
        "receive_id": "oc_b61235e79bac3d17d9107433e8267154",
        "msg_type": "interactive",
        "content": content
    }

    response = requests.post(
        url=url, 
        json=message, 
        headers=headers, 
        params=params
    )

    json_response = response.json()

    return SendMessageResponse(**json_response)


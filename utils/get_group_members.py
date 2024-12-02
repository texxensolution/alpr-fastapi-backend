import requests
from pydantic import BaseModel
from typing import List, Literal


class MemberItem(BaseModel):
    member_id_type: Literal['open_id', 'union_id', 'user_id']
    member_id: str
    name: str
    tenant_key: str


class GetGroupMemberListDataField(BaseModel):
    items: List[MemberItem]
    page_token: str
    has_more: bool
    member_total: int


class GetGroupMemberListResponse(BaseModel):
    code: int
    msg: str
    data: GetGroupMemberListDataField


def get_group_members(
    tenant_access_token: str, 
    group_chat_id: str = "oc_b61235e79bac3d17d9107433e8267154"
):
    formatted_url = "https://open.larksuite.com/open-apis/im/v1/chats/{chat_id}/members".format(chat_id=group_chat_id)
    headers = {
        "Authorization": f"Bearer {tenant_access_token}"
    }

    params = {
        "member_id_type": "union_id"
    }

    response = requests.get(formatted_url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Lark HTTP Request Error: {response.text}")

    content = response.json()

    return GetGroupMemberListResponse(**content)
    

    

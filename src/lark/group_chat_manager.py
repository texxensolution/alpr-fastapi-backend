import httpx
from pydantic import BaseModel
from typing import List, Literal
from .token_manager import TokenManager
from .exceptions import LarkBaseHTTPException


class MemberItem(BaseModel):
    member_id_type: Literal["open_id", "union_id", "user_id"]
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


class GroupChatManager:
    def __init__(self, token_manager: TokenManager):
        self._token_manager = token_manager

    async def get_members(
        self,
        group_chat_id: str,
        member_id_type: Literal["union_id", "open_id", "user_id"] = "union_id",
    ):
        tenant_access_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        formatted_url = (
            "https://open.larksuite.com/open-apis/im/v1/chats/{chat_id}/members".format(
                chat_id=group_chat_id
            )
        )

        headers = {"Authorization": f"Bearer {tenant_access_token}"}

        params = {"member_id_type": member_id_type}

        async with httpx.AsyncClient() as client:
            response = await client.get(formatted_url, headers=headers, params=params)

            response = GetGroupMemberListResponse(**response.json())

            if response.code != 0:
                raise LarkBaseHTTPException(response.code, response.msg)

            return response

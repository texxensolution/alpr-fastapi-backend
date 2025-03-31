import httpx
from typing import List, Dict, Optional, TypeVar, Generic
from pydantic import BaseModel, ConfigDict
from .token_manager import TokenManager
from typing import Literal, Type, Any
from .exceptions import LarkBaseHTTPException

GET_RECORDS_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{app_table}/records/{record_id}"
LIST_RECORDS_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{app_table}/records"
SEARCH_RECORDS_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
BATCH_UPDATE_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
CREATE_RECORDS_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
CREATE_RECORD_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
DELETE_RECORD_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
UPDATE_RECORD_URL = "https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"


T = TypeVar("T")

UserIdType = Literal["union_id", "user_id", "open_id"]


class BaseRecord(BaseModel, Generic[T]):
    record_id: str
    fields: T

    model_config = ConfigDict(populate_by_name=False)


class SearchResultDataResponse(BaseModel):
    items: list[dict]
    has_more: bool
    total: int


class SearchResultResponse(BaseModel):
    code: int
    msg: str
    data: Optional[SearchResultDataResponse] = None


class ListRecordBodyResponse(BaseModel, Generic[T]):
    class DataField(BaseModel, Generic[T]):
        has_more: bool
        page_token: Optional[str] = None
        total: int
        items: List[BaseRecord[T]] | None

    code: int
    msg: str
    data: DataField[T] | None = None


class BatchUpdateRecordResponse(BaseModel):
    code: int
    msg: str
    data: Optional[Dict] = None


class CreateRecordsDataResponse(BaseModel):
    records: List[dict]


class CreateRecordsBodyResponse(BaseModel):
    code: int
    msg: str
    data: Optional[CreateRecordsDataResponse] = None


class CreateRecordFieldsField(BaseModel):
    fields: dict
    record_id: str


class CreateRecordDataField(BaseModel):
    record: CreateRecordFieldsField


class CreateRecordBodyResponse(BaseModel):
    code: int
    msg: str
    data: Optional[CreateRecordDataField] = None


class DeletedRecordBodyResponse(BaseModel):
    deleted: bool
    record_id: str


class DeletedRecordResponse(BaseModel):
    code: int
    msg: str
    data: DeletedRecordBodyResponse


class UpdateRecordDataField(BaseModel):
    fields: dict
    record_id: str


class UpdateRecordRecordField(BaseModel):
    record: UpdateRecordDataField


class UpdateRecordResponse(BaseModel):
    code: int
    msg: str
    data: UpdateRecordRecordField


class BaseManager:
    def __init__(self, token_manager: TokenManager) -> None:
        self._token_manager = token_manager
        self._async_client = httpx.AsyncClient()

    async def create_record(
        self,
        app_token: str,
        table_id: str,
        fields: dict,
        user_id_type: UserIdType = "union_id",
    ):
        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        formatted_url = CREATE_RECORD_URL.format(
            app_token=app_token, table_id=table_id)

        payload = {"fields": fields}

        params = {"user_id_type": user_id_type}

        response = await self._async_client.post(
            formatted_url,
            headers={"Authorization": f"Bearer {tenant_token}"},
            json=payload,
            params=params,
        )

        response = CreateRecordBodyResponse(**response.json())

        if response.code != 0:
            raise LarkBaseHTTPException(response.code, response.msg)

        return response

    async def create_records(
        self,
        app_token: str,
        table_id: str,
        data: List[dict],
        user_id_type: UserIdType = "union_id",
    ):
        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        formatted_url = CREATE_RECORDS_URL.format(
            app_token=app_token, table_id=table_id
        )

        payload = {"records": data}

        response = await self._async_client.post(
            formatted_url,
            headers={"Authorization": f"Bearer {tenant_token}"},
            json=payload,
            params={"user_id_type": user_id_type},
        )

        response = CreateRecordsBodyResponse(**response.json())

        if response.code != 0:
            raise LarkBaseHTTPException(response.code, response.msg)

        return response

    async def search_records(
        self,
        app_token: str,
        table_id: str,
        filter: dict,
        user_id_type: UserIdType = "union_id",
        page_size: int = 100,
    ):
        formatted_url = SEARCH_RECORDS_URL.format(
            app_token=app_token, table_id=table_id
        )

        tenant_response = await self._token_manager.get_tenant_access_token()

        headers = {"Authorization": f"Bearer {tenant_response.tenant_access_token}"}

        params = {"user_id_type": user_id_type, "page_size": page_size}

        response = await self._async_client.post(
            formatted_url, params=params, headers=headers, json=filter
        )

        return SearchResultResponse(**response.json())

    async def list_records(
        self,
        app_token: str,
        app_table: str,
        record_model: Type[T] = Any,
        page_token: str | None = None,
        page_size: int = 500,
        filter: str = None,
        user_id_type: UserIdType = "union_id",
        view_id: str = None,
    ) -> ListRecordBodyResponse[T]:
        tenant_response = await self._token_manager.get_tenant_access_token()

        headers = {"Authorization": f"Bearer {
            tenant_response.tenant_access_token}"}

        params = {
            "page_size": page_size,
            "user_id_type": user_id_type,
            "filter": filter,
            "view_id": view_id,
        }

        formatted_url = LIST_RECORDS_URL.format(
            app_token=app_token, app_table=app_table
        )

        if page_token:
            params["page_token"] = page_token

        response = await self._async_client.get(
            formatted_url, headers=headers, params=params
        )

        response = ListRecordBodyResponse[record_model](**response.json())

        if response.code != 0:
            raise LarkBaseHTTPException(response.code, response.msg)

        return response

    async def update_record(
        self,
        app_token: str,
        table_id: str,
        record_id: str,
        data: dict,
        user_id_type: UserIdType = "union_id",
    ):
        formatted_url = UPDATE_RECORD_URL.format(
            app_token=app_token, table_id=table_id, record_id=record_id
        )

        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        headers = {"Authorization": f"Bearer {tenant_token}"}

        params = {"user_id_type": user_id_type}

        response = await self._async_client.put(
            url=formatted_url, headers=headers, params=params, json={
                "fields": data}
        )

        response = UpdateRecordResponse(**response.json())

        if response.code != 0:
            raise LarkBaseHTTPException(response.code, response.msg)

        return response

    async def update_records(
        self,
        app_token: str,
        table_id: str,
        records: dict,
        user_id_type: UserIdType = "union_id",
    ):
        formatted_url = BATCH_UPDATE_URL.format(
            app_token=app_token, table_id=table_id)

        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        headers = {"Authorization": f"Bearer {tenant_token}"}

        params = {"user_id_type": user_id_type}

        response = await self._async_client.post(
            formatted_url, headers=headers, json=records, params=params
        )

        data = BatchUpdateRecordResponse(**response.json())

        if data.code != 0:
            raise LarkBaseHTTPException(data.code, data.msg)

        return data

    async def delete_record(self, app_token: str, table_id: str, record_id: str):
        formatted_url = DELETE_RECORD_URL.format(
            app_token=app_token, table_id=table_id, record_id=record_id
        )

        tenant_token = (
            await self._token_manager.get_tenant_access_token()
        ).tenant_access_token

        headers = {"Authorization": f"Bearer {tenant_token}"}

        response = await self._async_client.put(formatted_url, headers=headers)

        data = DeletedRecordResponse(**response.json())

        if data.code != 0:
            raise LarkBaseHTTPException(code=data.code, msg=data.msg)

        return data

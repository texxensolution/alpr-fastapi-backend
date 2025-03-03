import os
import httpx
from datetime import datetime
import aiofiles
import base64
from src.lark.lark import Lark
from src.lark.messenger import SendMessagePayload
from src.core.dtos import Detection
from src.notifications import manual_search_message_builder, detection_message_builder
from src.core.config import settings
from more_itertools import chunked
from cachetools import TTLCache


cache = TTLCache(maxsize=100, ttl=1800)

class LarkNotification:
    def __init__(
        self,
        lark: Lark
    ):
        self._client = lark
        
    async def manual_search_notify(
        self,
        data: Detection,
        group_chat_id: str,
        chunked_buzz_size: int = 200
    ):
        try:
            payload = manual_search_message_builder(data)
            members_id = await self._get_gc_members_id(group_chat_id)
            members_id_chunks = list(chunked(members_id, chunked_buzz_size))
            send_message_obj = SendMessagePayload(
                receive_id=group_chat_id,
                msg_type="interactive",
                content=payload
            )
            message_response = await self._client.messenger.send_message(send_message_obj)
            try:
                await self._notify_web_app(data)
            except Exception:
                pass
            if data.status == "POSITIVE":
                for members_id_chunk in members_id_chunks:
                    await self._client.messenger.buzz_message(
                        message_id=message_response.data.message_id,
                        group_members_union_id=members_id_chunk
                    )
        except Exception as err:
            print(f"NotifyError: {str(err)}")
            

    async def detection_notify(
        self,
        data: Detection,
        group_chat_id: str,
        chunked_buzz_size: int = 200
    ):
        try:
            image_key = (
                await self._client.messenger.put_attachment(data.file_path)
            ).data.image_key
            payload = detection_message_builder(
                data=data,
                image_key=image_key
            )
            members_id = await self._get_gc_members_id(
                group_chat_id
            )
            members_id_chunks = list(chunked(members_id, chunked_buzz_size))
            send_message_obj = SendMessagePayload(
                receive_id=group_chat_id,
                msg_type="interactive",
                content=payload
            )
            message_response = await self._client.messenger.send_message(
                send_message_obj
            )
            try:
                await self._notify_web_app(data)
            except Exception:
                pass
            if data.status == "POSITIVE":
                for members_id_chunk in members_id_chunks:
                    await self._client.messenger.buzz_message(
                        message_id=message_response.data.message_id,
                        group_members_union_id=members_id_chunk
                    )
        except Exception as err:
            print(f"NotifyError: {str(err)}")

    async def _notify_web_app(
        self,
        data: Detection
    ):
        current_time = datetime.now()

        _data = {
            "plate_number": data.plate_number,
            "vehicle_model": data.accounts[0].car_model,
            "endorsement_date": (current_time).strftime('%Y-%m-%d'),
            "ch_code": data.accounts[0].ch_code,
            "location": [data.latitude, data.longitude],
            "detected_by": f"@{data.detected_by}",
            "status": data.status,
            "client_name": data.accounts[0].client,
            "similar_plate": data.accounts[0].plate
        }

        if data.file_path is not None: 
            if not os.path.exists(data.file_path):
                return
            async with aiofiles.open(data.file_path, 'rb') as file:
                image_data = base64.b64encode(await file.read()).decode('utf-8')
                _data['image'] = image_data

        async with httpx.AsyncClient() as client:
            await client.post(
                url=settings.NOTIFY_WEB_APP_URL,
                json=_data
            )
            
    async def _get_gc_members_id(self, group_chat_id: str) -> list[str]:
        if group_chat_id in cache:
            return cache[group_chat_id]
        response = await self._client.group_chat.get_members(
            group_chat_id
        )
        members_id = [member.member_id for member in response.data.items]
        cache[group_chat_id] = members_id
        return members_id

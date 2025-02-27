import os
import httpx
import asyncio
from datetime import datetime
import aiofiles
import base64
from src.lark.lark import Lark
from src.lark.messenger import SendMessagePayload
from src.core.dtos import Detection, CardTemplateDataField, CardTemplatePayload 
from src.core.config import settings
from more_itertools import chunked

class LarkNotification:
    def __init__(
        self,
        lark: Lark
    ):
        self._client = lark
    
    async def notify(
        self,
        data: Detection,
        group_chat_id: str
    ):
        try:
            image_key = (
                await self._client.messenger.put_attachment(data.file_path)
            ).data.image_key

            payload = self._message_builder(
                image_key=image_key,
                data=data,
            )

            members_id = await self._get_gc_members_id(
                group_chat_id
            )
            
            members_id_chunks = list(chunked(members_id, 100))

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
                async with asyncio.TaskGroup() as tg:
                    tasks = [
                        tg.create_task(
                            self._client.messenger.buzz_message(
                                message_id=message_response.data.message_id,
                                group_members_union_id=members_id_chunk
                            )
                        )
                        for members_id_chunk in members_id_chunks
                    ]
                    statuses = [task.result().code for task in tasks]
                    print(f"Buzz Statuses: {statuses}")

        except Exception as err:
            print(f"NotifyError: {str(err)}")

    async def _notify_web_app(
        self,
        data: Detection
    ):
        if not os.path.exists(data.file_path):
            return

        async with aiofiles.open(data.file_path, 'rb') as file:
            image_data = base64.b64encode(await file.read()).decode('utf-8')
        
        current_time = datetime.now()

        _data = {
            "plate_number": data.plate_number,
            "vehicle_model": data.accounts[0].car_model,
            "endorsement_date": (current_time).strftime('%Y-%m-%d'),
            "ch_code": data.accounts[0].ch_code,
            "location": [data.latitude, data.longitude],
            "detected_by": f"@{data.detected_by}",
            "image": image_data,
            "status": data.status,
            "client_name": data.accounts[0].client,
            "similar_plate": data.accounts[0].plate
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                url=settings.NOTIFY_WEB_APP_URL,
                json=_data
            )
            
    async def _get_gc_members_id(self, group_chat_id: str) -> list[str]:
        response = await self._client.group_chat.get_members(
            group_chat_id
        )
        return [member.member_id for member in response.data.items]

    def _message_builder(
        self,
        image_key: str,
        data: Detection
    ):
        if data.status == 'POSITIVE':
            is_positive = True
            card_id = "ctp_AAjkOym6PwjJ" 
        else:
            is_positive = False
            card_id = "ctp_AAjkwfIl3sUz"

        title = f"{data.status} PLATE | STICKER DETECTED!"
        content = f"Detected: **{data.plate_number}**\n"
        # template_color = "red" if data.is_similar == False else "yellow"
        
        if not is_positive:
            content += "\n\n"
            content += f"**Similar accounts**:\n"

        for positive_account in data.accounts:
            content += f"Client: **{positive_account.plate}** [**{positive_account.car_model}** - **{positive_account.client}**]\n"
            content += f"- Vehicle: {positive_account.car_model}\n"
            # content += f"- Client Name: {positive_account.client}\n"
            content += f"- Endorsement Date: {positive_account.endo_date}\n"
            content += f"- CH Code: {positive_account.ch_code}\n\n"

        content += f"\n 📷 Sent from <at id=\"{data.user_id}\"></at> device"
        content += f"\n 📍 Location (lat, lon): ({data.latitude}, {data.longitude})"

        template_data_field = CardTemplateDataField(
            template_id=card_id,
            template_variable={
                "title": title,
                "body": content,
                "image": image_key,
                "mention": data.union_id
            }
        )

        template_content = CardTemplatePayload(data=template_data_field)

        return template_content.model_dump_json()
    
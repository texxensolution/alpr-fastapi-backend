from typing import Literal
from pydantic import BaseModel
from models.notification import QueuedPlateDetected, QueuedPlateDetectedWithUnionId


class CardTemplateDataField(BaseModel):
    template_id: str
    template_variable: dict


class CardTemplatePayload(BaseModel):
    data: CardTemplateDataField
    type: Literal['template'] = 'template'


def message_builder(
    image_key: str,
    data: QueuedPlateDetected,
    status: Literal['POSITIVE', 'FOR_CONFIRMATION']
):

    if status == 'POSITIVE':
        is_positive = True
        card_id = "ctp_AAjkOym6PwjJ" 
    else:
        is_positive = False
        card_id = "ctp_AAjkwfIl3sUz"

    title = f"{status} PLATE | STICKER DETECTED!"
    content = f"Detected: **{data.plate_number}**\n"
    # template_color = "red" if data.is_similar == False else "yellow"
    
    if not is_positive:
        content += "\n"
        content += f"**Similar accounts**:\n"

    for positive_account in data.accounts:
        content += f"Client: **{positive_account.plate}** [**{positive_account.car_model}** - **{positive_account.client}**]\n"
        content += f"- Vehicle: {positive_account.car_model}\n"
        content += f"- Client Name: {positive_account.client}\n"
        content += f"- Endorsement Date: {positive_account.endo_date}\n"
        content += f"- CH Code: {positive_account.ch_code}\n\n"

    content += f"Sent from **{data.name}** device 📱"
    
    template_data_field = CardTemplateDataField(
        template_id=card_id,
        template_variable={
            "title": title,
            "body": content,
            "image": image_key
        }
    )

    template_content = CardTemplatePayload(data=template_data_field)

    return template_content.model_dump_json()


def message_builder_with_mention(
    image_key: str,
    data: QueuedPlateDetectedWithUnionId,
    status: Literal['POSITIVE', 'FOR_CONFIRMATION']
):

    if status == 'POSITIVE':
        is_positive = True
        card_id = "ctp_AAjkOym6PwjJ" 
    else:
        is_positive = False
        card_id = "ctp_AAjkwfIl3sUz"

    title = f"{status} PLATE | STICKER DETECTED!"
    content = f"Detected: **{data.plate_number}**\n"
    # template_color = "red" if data.is_similar == False else "yellow"
    
    if not is_positive:
        content += "\n\n"
        content += f"**Similar accounts**:\n"

    for positive_account in data.accounts:
        content += f"Client: **{positive_account.plate}** [**{positive_account.car_model}** - **{positive_account.client}**]\n"
        content += f"- Vehicle: {positive_account.car_model}\n"
        content += f"- Client Name: {positive_account.client}\n"
        content += f"- Endorsement Date: {positive_account.endo_date}\n"
        content += f"- CH Code: {positive_account.ch_code}\n\n"

    content += f"\n 📷 Sent from <at id=\"{data.user_id}\"></at> device"

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
  
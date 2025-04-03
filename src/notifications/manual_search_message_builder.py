from src.core.dtos import Detection, CardTemplateDataField, CardTemplatePayload

def manual_search_message_builder(
    data: Detection
):
    card_id = "ctp_AABkxMYSKOJN" 
    title = f"MANUAL: {data.status} {data.detected_type.upper()} FOUND!"
    content = f"Detected: **{data.plate_number}**\n"
    content += "\n"
    content += "**Matched Found:**\n"
    positive_account = data.accounts[0]
    content += f"Client: **{positive_account.plate}** [**{positive_account.car_model}** - **{positive_account.client}**]\n"
    content += f"- Vehicle: {positive_account.car_model}\n"
    content += f"- Endorsement Date: {positive_account.endo_date}\n"
    content += f"- CH Code: {positive_account.ch_code}\n\n"
    if data.user_type == 'internal':
        content += f"\n 📷 Sent from <at id=\"{data.user_id}\"></at> device"
    elif data.user_type == 'external':
        content += f"\n 📷 Sent from @{data.user_id} (freelance) device"

    content += f"\n 📍 Location (lat, lon): ({data.latitude}, {data.longitude})"

    template_data_field = CardTemplateDataField(
        template_id=card_id,
        template_variable={
            "title": title,
            "content": content,
            "mention": data.union_id,
            "location_url": f"https://www.google.com/maps?q={data.latitude},{data.longitude}"
        }
    )
    template_content = CardTemplatePayload(data=template_data_field)
    return template_content.model_dump_json()
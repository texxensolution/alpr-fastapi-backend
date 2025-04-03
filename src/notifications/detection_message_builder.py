from src.core.dtos import Detection, CardTemplateDataField, CardTemplatePayload


def detection_message_builder(
    data: Detection,
    image_key: str
):
    if data.status == 'POSITIVE':
        is_positive = True
        card_id = "ctp_AAjkOym6PwjJ" 
    else:
        is_positive = False
        card_id = "ctp_AAjkwfIl3sUz"

    title = f"{data.status} {data.detected_type.upper()} DETECTED!"
    content = f"Detected: **{data.plate_number}**\n"
    
    if not is_positive:
        content += "\n"
        content += "**Similar accounts**:\n"

    for positive_account in data.accounts:
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
            "body": content,
            "image": image_key
        }
    )

    template_content = CardTemplatePayload(data=template_data_field)

    return template_content.model_dump_json()
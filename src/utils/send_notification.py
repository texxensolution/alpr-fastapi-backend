import requests
import os
from src.core.dtos import Notification
from .upload_image import upload_image
from lark.token_manager import TokenManager


def send_notification_on_background(
    token_manager: TokenManager,
    data: Notification
):
    # url = "https://open.larksuite.com/open-apis/bot/v2/hook/0a318b33-68ae-4a7a-b7bb-22a3bfc905bc" # official
    url = "https://open.larksuite.com/open-apis/bot/v2/hook/aaa6a791-74df-4c6a-9d4d-216381147ed6"

    token_response = token_manager.get_tenant_access_token_sync()

    image_key = upload_image(
        data.file_path,
        access_token=token_response.tenant_access_token
    )

    is_positive = False if data.is_similar else True

    status = "POSITIVE" if is_positive else "FOR_CONFIRMATION"

    header_content = f"{status} PLATE | STICKER DETECTED!"
    content = f"Detected: **{data.plate_number}**\n"
    client_info = ""
    template_color = "red" if data.is_similar == False else "yellow"

    for positive_account in data.accounts:
        content += f"Client: **{positive_account.plate}** [**{positive_account.car_model}** - **{positive_account.client}**]\n"

        client_info += f"\nClient Information:\n- Plate | Sticker: **{positive_account.plate}**\n" \
                    f"- Vehicle: {positive_account.car_model}\n" \
                    f"- Client Name: **{positive_account.client}**\n" \
                    f"- Endorsement Date: {positive_account.endo_date}\n" \
                    f"- CH Code: {positive_account.ch_code}\n \n\n"
 
        content += client_info


    card_data = {
        "config": {
            "wide_screen_mode": True
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "content": content,
                    "tag": "lark_md"
                }
            },
            {
                "tag": "img",
                "img_key": image_key,
                "alt": {
                    "tag": "plain_text",
                    "content": ""
                },
                "mode": "fit_horizontal",
                "preview": True
            }
        ],
        "header": {
            "template": template_color,
            "title": {
                "content": header_content,
                "tag": "plain_text"
            }
        }
    }

    body = {"msg_type": "interactive", "card": card_data}
    headers = {"Content-Type": "application/json"}

    response = requests.post(url=url, json=body, headers=headers)

    if response.status_code == 200:
        print("Message sent successfully!")
        os.remove(data.file_path)
    else:
        print(f"Failed to send message. Status code: {response.status_code}, Response: {response.text}")

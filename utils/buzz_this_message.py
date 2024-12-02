import requests
from typing import List


def buzz_this_message(
    tenant_token: str,
    message_id: str,
    group_members_union_id: List[str]
):
    formatted_url = "https://open.larksuite.com/open-apis/im/v1/messages/{message_id}/urgent_app".format(message_id=message_id)

    headers = {
        "Authorization": f"Bearer {tenant_token}"
    }

    params = {
        "user_id_type": "union_id"
    }

    body = {
        "user_id_list": group_members_union_id
    }
    
    requests.patch(
        url=formatted_url, 
        json=body, 
        headers=headers, 
        params=params
    )

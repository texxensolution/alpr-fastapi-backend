from models.notification import Notification
from utils.upload_image_gc import upload_image_gc
from utils.message_builder import message_builder
from utils.send_message_to_gc import send_message_to_gc
from utils.get_group_members import get_group_members
from utils.buzz_this_message import buzz_this_message
from models.notification import QueuedPlateDetected
from lark.token_manager import TokenManager


def notify_group_chat(
    token_manager: TokenManager,
    data: QueuedPlateDetected
):
    if data.status == 'NOT_FOUND':
        return

    tenant_token = (token_manager.get_tenant_access_token_sync()).tenant_access_token
    
    upload_response = upload_image_gc(
        tenant_token=tenant_token,
        image_path=data.file_path
    )

    created_message = message_builder(
        image_key=upload_response.data.image_key,
        data=data,
        status=data.status
    )

    message_sent_response = send_message_to_gc(
        tenant_token=tenant_token,
        content=created_message
    )

    if data.status == 'POSITIVE':
        members = get_group_members(
            tenant_access_token=tenant_token
        )

        group_member_union_ids = [member.member_id for member in members.data.items]

        buzz_this_message(
            tenant_token=tenant_token,
            message_id=message_sent_response.data.message_id,
            group_members_union_id=group_member_union_ids
        )
    print("Job successfully processed.")



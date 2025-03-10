import jwt
import json
import asyncio
from src.core.config import settings
from fastapi import APIRouter, WebSocketDisconnect, WebSocket
from src.db.user import find_lark_account
from src.core.dependencies import GetDatabaseSession, GetTrackingDeviceManager
from src.core.device_tracking_manager import DeviceTrackingData



router = APIRouter(
    prefix='/api/v4',
    tags=['Websocket endpoints']
)

@router.get('/active/devices')
async def get_active_devices(
    tracking_device_manager: GetTrackingDeviceManager,
    page: int = 1,
    page_size: int = 50
):
    devices = tracking_device_manager.get_paginated_devices(
        page = page,
        page_size = page_size
    )
    return devices

@router.websocket('/ping')
async def device_tracking_connection(
    websocket: WebSocket,
    db: GetDatabaseSession,
    tracking_device_manager: GetTrackingDeviceManager
):
    try:
        await websocket.accept()
        token = websocket.headers.get('Authorization')

        if not token or not token.startswith('Bearer '):
            await websocket.close(code=4001)
            return

        token = token.replace('Bearer ', '')

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except Exception:
            await websocket.close(code=4001)
            return

        # print("auth payload", payload)
        user_id = payload['user_id']
        user_type = payload['user_type']
        raw_data = await websocket.receive_text()
        decoded_data = json.loads(raw_data)

        if user_type == 'external':
            location = decoded_data.get('location')
            current_data = DeviceTrackingData(
                name=user_id,
                location=[location[0], location[1]],
            )
        elif user_type == 'internal':
            location = decoded_data.get('location')
            account = find_lark_account(db, user_id)
            current_data = DeviceTrackingData(
                name=account.name,
                location=[location[0], location[1]]
            )

        tracking_device_manager.update_data(websocket, current_data)

        while True:
            raw_data = await websocket.receive_text()
            decoded_data = json.loads(raw_data)
            location = decoded_data.get('location')
            device_data= tracking_device_manager.get_data(websocket)
            device_data.location = location[0], location[1]
            tracking_device_manager.update_data(websocket, device_data)

            print('current_active_devices', tracking_device_manager.active_devices)

            await websocket.send_text('Updated current location')
            await asyncio.sleep(1)
    except WebSocketDisconnect as e:
        tracking_device_manager.remove_device(websocket)
        print("Websocket disconnection: ", e)
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.core.dependencies import GetStatusManager


router = APIRouter(
    prefix='/ws',
    tags=['Status (WebSocket) 3.0']
)


@router.websocket('/user/status')
async def user_status(
    websocket: WebSocket,
    status_manager: GetStatusManager
):
    try:
        headers = websocket.headers
        union_id = headers.get('union-id')
        if union_id is None:
            await websocket.close(code=1000, reason="No union id provided in headers")
        else:
            await websocket.accept()
            print("union_id", union_id)
            status_manager.add_user(union_id)
            try:
                while True:
                    text = await websocket.receive_text()
                    await asyncio.sleep(0.1)
            except WebSocketDisconnect:
                status_manager.remove_user(union_id)
                print("remove from status_manager:", union_id)
            # active_users[union_id] = "Active"
            # print("Active users", active_users)
    except WebSocketDisconnect:
        pass
    finally:
        print("websocket is closed")




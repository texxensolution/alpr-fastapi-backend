from fastapi import (
    WebSocket,
    WebSocketDisconnect,
    WebSocketException
)
from typing import (
    List   
)
from pydantic import BaseModel


class WebsocketManager:
    def __init__(self):
        self._active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self._active_connections.remove(websocket)
    
    async def send_message(
        self,
        message: str,
        websocket: WebSocket
    ):
        await websocket.send_text(message)

    async def broadcast(
        self,
        data: BaseModel
    ):
        for connection in self._active_connections:
            await connection.send_json(
                data.model_dump_json()
            )

        
    
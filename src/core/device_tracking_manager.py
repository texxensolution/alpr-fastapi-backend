import math
from typing import Dict, Tuple
from fastapi import WebSocket
from pydantic import BaseModel


class DeviceTrackingData(BaseModel):
    name: str
    location: Tuple[float, float]

class DeviceTrackingManager:
    def __init__(self):
        self._active_devices: Dict[WebSocket, DeviceTrackingData] = {}

    def init(
        self, 
        websocket: WebSocket,
        initial_data: DeviceTrackingData
    ):
        self._active_devices[websocket] = initial_data

    def update_data(
        self,
        websocket: WebSocket,
        data: DeviceTrackingData
    ):
        if websocket not in self._active_devices:
            self._active_devices[websocket] = data
        else:
            self._active_devices[websocket].location = data.location

    def remove_device(self, websocket: WebSocket):
        if websocket in self._active_devices:
            del self._active_devices[websocket]
    
    def get_data(self, websocket: WebSocket):
        return self._active_devices.get(websocket)
        
    @property
    def active_devices(self):
        return list(self._active_devices.values())

    def get_paginated_devices(self, page: int = 1, page_size: int = 10):
        """
        Returns a paginated list of active devices.

        :param page: The page number (1-based index).
        :param page_size: The number of devices per page.
        :return: A dictionary with paginated results and metadata.
        """
        total_devices = len(self._active_devices)
        total_pages = math.ceil(total_devices / page_size)

        # Ensure the requested page is within range
        if page < 1 or page > total_pages:
            return {
                "devices": [],
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_devices": total_devices,
            }

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        devices_list = list(self._active_devices.values())[start_idx:end_idx]

        return {
            "devices": devices_list,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_devices": total_devices,
        }
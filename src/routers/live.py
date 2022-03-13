"""
https://github.com/tiangolo/fastapi/issues/98#issuecomment-907452636
"""
from enum import Enum
import json
import math
from typing import Any, Dict, List, Literal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from ..db import client


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def message(self, message: Dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections:
            await connection.send_json(message)


class PicklistType(str, Enum):
    first = "first"
    second = "second"


class MessageRequest:
    class PicklistUpdate(BaseModel):
        type: Literal["picklist_update"]
        picklist_type: PicklistType
        team_number: int
        place: float


class MessageResponse:
    class PicklistData(BaseModel):
        type: Literal["picklist_data"] = "picklist_data"
        picklist_type: PicklistType
        data: List[int]


def map_picklist(picklist_type: PicklistType) -> List[Dict[str, Any]]:
    def map_func(e):
        return {
            "team_number": e["team_number"],
            "rank": e[f"{picklist_type}_rank"],
        }

    return map_func


def get_max_rank(arr: List[Dict[str, Any]]) -> int:
    place_list = set(map(lambda e: e["rank"], arr))
    return max(place_list)


def update_picklist(
    picklist_type: PicklistType, team_number: str, place: float, event_key: str
):
    db = client[event_key]
    collection = db["picklist"]
    current_picklist = get_picklist(picklist_type, event_key)
    print(current_picklist)
    current_pos = current_picklist.index(team_number) + 1
    if math.ceil(place) == current_pos or math.floor(place) == current_pos:
        return
    mov_type = "u" if place < current_pos else "d"
    to_place = math.ceil(place) if mov_type == "u" else math.floor(place)

    # current_picklist = get_picklist(picklist_type, event_key)

    pos_range = (
        range(current_pos + 1, to_place + 1)
        if current_pos < to_place
        else range(to_place, current_pos)
    )

    print("moving team ")
    collection.update_one(
        {"team_number": team_number},
        {"$set": {f"{picklist_type}_rank": to_place}},
    )

    for i in pos_range:
        new_rank = i + 1 if mov_type == "u" else i - 1
        print(f"moving team: {current_picklist[i - 1]} to rank {new_rank}")
        collection.update_one(
            {"team_number": current_picklist[i - 1]},
            {"$set": {f"{picklist_type}_rank": new_rank}},
        )


def get_picklist(picklist_type: PicklistType, event_key: str) -> List[int]:
    db = client[event_key]
    collection = db["picklist"]
    picklist_items = collection.find()
    relevent_items = list(map(map_picklist(picklist_type), picklist_items))
    max_rank = get_max_rank(relevent_items)

    team_numbers = []

    for i in range(1, max_rank + 1):
        for item in relevent_items:
            if item["rank"] == i:
                team_numbers.append(item["team_number"])
                break

    return team_numbers


picklist_manager = ConnectionManager()


async def handle_message(message: dict, websocket: WebSocket, event_key: str):
    if message["type"] == "picklist_update":
        data = MessageRequest.PicklistUpdate(**message)
        update_picklist(data.picklist_type, data.team_number, data.place, event_key)
        resp = MessageResponse.PicklistData(
            picklist_type=data.picklist_type,
            data=get_picklist(data.picklist_type, event_key),
        )
        await picklist_manager.broadcast(resp.dict())


async def websocket_picklist(websocket: WebSocket, event_key: str):
    await picklist_manager.connect(websocket)
    initial_data_first = MessageResponse.PicklistData(
        picklist_type=PicklistType.first, data=get_picklist(PicklistType.first, event_key)
    )
    initial_data_second = MessageResponse.PicklistData(
        picklist_type=PicklistType.second, data=get_picklist(PicklistType.second, event_key)
    )
    await picklist_manager.message(initial_data_first.dict(), websocket)
    await picklist_manager.message(initial_data_second.dict(), websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(data, websocket, event_key)

    except WebSocketDisconnect:
        picklist_manager.disconnect(websocket)

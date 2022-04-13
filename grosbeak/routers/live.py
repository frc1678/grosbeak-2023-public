"""
https://github.com/tiangolo/fastapi/issues/98#issuecomment-907452636
"""
from enum import Enum
import json
import math
from typing import Any, Dict, List, Literal, Optional, Tuple
from uuid import uuid4
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import BaseModel

from ..env import env
from ..db import client


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        id = str(uuid4())
        self.active_connections[id] = websocket
        return id

    def disconnect(self, websocket: WebSocket) -> Optional[str]:
        for id, connection in self.active_connections.items():
            if connection == websocket:
                del self.active_connections[id]
                return id
        return None

    async def message(self, message: Dict, websocket: Optional[WebSocket]):
        if websocket is not None:
            await websocket.send_json(message)

    async def broadcast(self, message: Dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

    def get_connection_by_id(self, id: str) -> Optional[WebSocket]:
        return self.active_connections.get(id)


class PicklistConnectionManager(ConnectionManager):
    current_editor: Optional[str] = None

    def login(self, password: str, user: str) -> bool:
        if password == env.PICKLIST_PASSWORD:
            self.current_editor = user
            return True
        return False

    def logout(self, user: str) -> bool:
        if self.current_editor == user:
            self.current_editor = None
            return True
        return False

    def can_edit(self, user: str) -> bool:
        return self.current_editor == user

    def disconnect(self, websocket: WebSocket) -> Optional[str]:
        id = super().disconnect(websocket)
        if id is not None and self.current_editor == id:
            self.current_editor = None
        return id


class MessageRequest:
    class PicklistUpdate(BaseModel):
        type: Literal["picklist_update"]
        to_place: int
        from_place: int

    class DNPToggle(BaseModel):
        type: Literal["dnp_update"]
        team_number: int

    class StartEdit(BaseModel):
        type: Literal["start_edit"]
        password: str


class MessageResponse:
    class PicklistData(BaseModel):
        type: Literal["picklist_data"] = "picklist_data"
        ranking: List[int]
        dnp: List[int]

    class Login(BaseModel):
        type: Literal["login"] = "login"
        success: bool


def get_max_rank(arr: List[Dict[str, Any]]) -> int:
    place_list = set(map(lambda e: e["rank"], arr))
    if len(place_list) == 0:
        return 0
    return max(place_list)


def update_picklist(to_place: int, from_place: int, event_key: str):
    if to_place == from_place:
        return
    logger.info(f"Received request to update picklist from {from_place} to {to_place}")
    db = client[event_key]
    collection = db["picklist"]
    current_picklist, _ = get_picklist(event_key)
    if len(current_picklist) == 0:
        return
    team_number = current_picklist[from_place - 1]
    logger.info(f"Current picklist: {current_picklist}")
    logger.info(f"Moving {team_number} from {from_place} to {to_place}")
    # current_picklist = get_picklist(picklist_type, event_key)

    collection.update_one(
        {"team_number": team_number},
        {"$set": {f"rank": to_place}},
    )

    if to_place > from_place:
        for i in range(from_place, to_place):
            logger.info(f"Moving up team (decrementing): {current_picklist[i]}")
            collection.update_one(
                {"team_number": current_picklist[i]},
                {"$inc": {f"rank": -1}},
            )
    else:
        for i in range(to_place - 1, from_place - 1):
            logger.info(f"Moving down team (incrementing): {current_picklist[i]}")
            collection.update_one(
                {"team_number": current_picklist[i]},
                {"$inc": {f"rank": 1}},
            )


def toggle_dnp(team_number: int, event_key: str):
    collection = client[event_key]["picklist"]
    current_item = collection.find_one({"team_number": team_number})
    max_rank = get_max_rank(list(collection.find()))
    if max_rank == 0:
        return
    if current_item is None:
        logger.error(
            "Tried to toggle dnp for team that doesn't exist. THIS IS BAD I THINK"
        )
        return
    if current_item["dnp"] == False:
        collection.update_one(
            {"team_number": team_number},
            {"$set": {"dnp": True, "rank": -1}},
        )
        # Move up all of the teams after this one
        for i in range(current_item["rank"] + 1, max_rank + 1):
            collection.update_one(
                {"rank": i},
                {"$inc": {"rank": -1}},
            )
    else:
        collection.update_one(
            {"team_number": team_number}, {"$set": {"dnp": False, "rank": max_rank + 1}}
        )


def get_picklist(event_key: str) -> Tuple[List[int], List[int]]:
    db = client[event_key]
    collection = db["picklist"]
    picklist_items = list(collection.find())
    logger.info(f"Picklist items len: {len(picklist_items)}")
    max_rank = get_max_rank(picklist_items)
    logger.info(f"Max rank: {max_rank}")
    if max_rank == 0:
        return [], []
    team_numbers = []

    for i in range(1, max_rank + 1):
        for item in picklist_items:
            if item["rank"] == i:
                team_numbers.append(item["team_number"])
                break
    logger.info(f"Team numbers: {team_numbers}")
    return (
        team_numbers,
        list(
            map(
                lambda x: x["team_number"],
                list(filter(lambda e: e["dnp"] == True, picklist_items)),
            )
        ),
    )


picklist_manager = PicklistConnectionManager()


async def reinform_clients(event_key: str):
    new_picklist, dnp_list = get_picklist(event_key)
    logger.info(f"New picklist: {new_picklist}")
    logger.info(f"DNP list: {dnp_list}")
    resp = MessageResponse.PicklistData(ranking=new_picklist, dnp=dnp_list)
    await picklist_manager.broadcast(resp.dict())


async def handle_message(message: dict, websocket_id: str, event_key: str):
    if message["type"] == "picklist_update":
        update_request_data = MessageRequest.PicklistUpdate(**message)
        update_picklist(update_request_data.to_place, update_request_data.from_place, event_key)
        await reinform_clients(event_key)
    elif message["type"] == "dnp_update":
        dnp_request_data = MessageRequest.DNPToggle(**message)
        toggle_dnp(dnp_request_data.team_number, event_key)
        await reinform_clients(event_key)
    elif message["type"] == "start_edit":
        logger.info("Starting edit")
        start_edit_request_data = MessageRequest.StartEdit(**message)
        await picklist_manager.message(
            MessageResponse.Login(
                success=picklist_manager.login(start_edit_request_data.password, websocket_id)
            ).dict(),
            picklist_manager.get_connection_by_id(websocket_id),
        )
    elif message["type"] == "stop_edit":
        logger.info("Stopping edit")
        picklist_manager.logout(websocket_id)


async def websocket_picklist(websocket: WebSocket, event_key: str):
    connection_id = await picklist_manager.connect(websocket)
    picklist, dnp = get_picklist(event_key)
    logger.info("Initial picklist: " + str(picklist))
    logger.info("Initial dnp: " + str(dnp))
    initial_data = MessageResponse.PicklistData(ranking=picklist, dnp=dnp)
    await picklist_manager.message(initial_data.dict(), websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(data, connection_id, event_key)

    except WebSocketDisconnect:
        picklist_manager.disconnect(websocket)

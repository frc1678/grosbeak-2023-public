from enum import Enum
import os
from typing import Dict, List, Literal, Union
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..auth import get_api_key
from ..db import client, allowed_collections
from ..env import env
from ..util import all_files_in_dir, serialize_documents, strip_extension
import json
router = APIRouter(prefix="/api", dependencies=[Security(get_api_key)])

class ErrorMessage(BaseModel):
    error: str

@router.get("/collection/{collection_name}", responses={404: {"model": ErrorMessage}})
def read_collection(collection_name: str, event_key: str = env.DB_NAME):
    db = client[event_key]
    if (
        collection_name in allowed_collections
        and collection_name in db.list_collection_names()
    ):
        collection = db[collection_name]
        return serialize_documents(list(collection.find()))
    else:
        return JSONResponse(content={"error": "Collection not found/allowed"}, status_code=404)


class ColorEnum(str, Enum):
    red = "red"
    blue = "blue"


class MatchScheduleTeam(BaseModel):
    number: str
    color: ColorEnum


class MatchScheduleMatch(BaseModel):
    teams: List[MatchScheduleTeam]



@router.get("/match-schedule/{event_key}", response_model=Dict[str, MatchScheduleMatch], responses={404: {"model": ErrorMessage}})
def read_match_schedule(event_key: str):
    return read_static_json("match-schedules", event_key)

@router.get("/team-list/{event_key}", response_model=List[str], responses={404: {"model": ErrorMessage}})
def read_team_list(event_key: str):
    return read_static_json("team-lists", event_key)

def read_static_json(folder: str, key: str):
    path = os.path.realpath(f"./static/{folder}/{key}.json")
    if path.startswith(os.path.realpath(f"./static/{folder}")) and os.path.exists(path):
        with open(path) as f:
            return JSONResponse(content=json.load(f))
    return JSONResponse(content={"error": "Match schedule not found"}, status_code=404)

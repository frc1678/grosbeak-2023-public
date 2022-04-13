from enum import Enum
from typing import Dict, List, Literal, Union
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..auth import get_api_key
from ..db import client, allowed_collections
from ..env import env
from ..util import all_files_in_dir, serialize_documents, strip_extension
import json

team_lists = list(map(strip_extension, all_files_in_dir("team-lists")))
match_schedules = list(map(strip_extension, all_files_in_dir("match-schedules")))

router = APIRouter(prefix="/api", dependencies=[Security(get_api_key)])


@router.get("/collection/{collection_name}")
def read_collection(collection_name: str, event_key: str = env.DB_NAME):
    db = client[event_key]
    if (
        collection_name in allowed_collections
        and collection_name in db.list_collection_names()
    ):
        collection = db[collection_name]
        return serialize_documents(list(collection.find()))
    else:
        return "Collection not found/allowed"


class ColorEnum(str, Enum):
    red = "red"
    blue = "blue"


class MatchScheduleTeam(BaseModel):
    number: str
    color: ColorEnum


class MatchScheduleMatch(BaseModel):
    teams: List[MatchScheduleTeam]


@router.get("/match-schedule/{event_key}", response_model=Dict[str, MatchScheduleMatch])
def read_match_schedule(event_key: str):
    if event_key in match_schedules:
        with open(f"./match-schedules/{event_key}.json") as f:
            return JSONResponse(content=json.load(f))
    else:
        return "Match schedule not found"


@router.get("/team-list/{event_key}", response_model=List[str])
def read_team_list(event_key: str):
    if event_key in team_lists:
        with open(f"./team-lists/{event_key}.json") as f:
            return JSONResponse(content=json.load(f))
    else:
        return "Team list not found"

from fastapi import APIRouter, Security
from pydantic import BaseModel, Field
from pydantic.types import constr

from grosbeak.auth import get_auth_level
from grosbeak.db import client
from grosbeak.env import env
from grosbeak.util import serialize_documents

router = APIRouter(prefix="/notes", dependencies=[Security(get_auth_level)])


@router.get("/all")
def all_notes(event_key: str = env.DB_NAME):
    db = client[event_key]
    collection = db["notes"]
    docs = serialize_documents(list(collection.find()))
    return {doc["team_number"]: doc["notes"] for doc in docs}


@router.get("/team/{team_number}")
def team_notes(team_number: str, event_key: str = env.DB_NAME):
    db = client[event_key]
    collection = db["notes"]
    note = collection.find_one({"team_number": team_number})
    if note is None:
        note = {"team_number": team_number, "notes": ""}
    return serialize_documents([note])[0]


class PutTeamNotes(BaseModel):
    team_number: str = Field(..., min_length=1)
    notes: str


@router.put("/team/")
def update_team_notes(data: PutTeamNotes, event_key: str = env.DB_NAME):
    db = client[event_key]
    collection = db["notes"]
    collection.update_one(
        {"team_number": data.team_number},
        {"$set": {"team_number": data.team_number, "notes": data.notes}},
        upsert=True,
    )
    return {}

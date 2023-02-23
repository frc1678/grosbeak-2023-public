import uuid
from typing import Literal
import pymongo

from .env import env

DocumentTypes = Literal["team", "tim", "aim"]
AllianceColors = Literal["red", "blue"]

COLLECTIONS: dict[str, DocumentTypes] = {
    "raw_obj_pit": "team",
    "tba_tim": "tim",
    "obj_tim": "tim",
    "obj_team": "team",
    "subj_team": "team",
    "predicted_aim": "aim",
    "predicted_team": "team",
    "tba_team": "team",
    "pickability": "team",
    "picklist": "team",
}

COLLECTION_KEYS: dict[DocumentTypes, list[str]] = {
    "team": ["team_number"],
    "tim": ["match_number", "team_number"],
    "aim": ["match_number", "alliance_color_is_red"],
}

STATIC_FILE_TYPES = {"match-schedule", "team-list"}

client: pymongo.MongoClient = pymongo.MongoClient(env.MONGO_URI)
# db = client[DB_NAME]
api_db = client["api"]

if "credentials" not in api_db.list_collection_names():
    api_db["credentials"].insert_one(
        {
            "description": "Admin Key",
            "level": 2,
            "api_key": str(uuid.uuid4()).replace("-", ""),
        }
    )

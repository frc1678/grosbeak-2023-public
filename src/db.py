import os
import pymongo

from .env import MONGO_URI

allowed_collections = [
    "raw_obj_pit",
    "tba_tim",
    "obj_tim",
    "obj_team",
    "subj_team",
    "predicted_aim",
    "predicted_team",
    "tba_team",
    "pickability",
    "picklist",
]


client = pymongo.MongoClient(MONGO_URI)
# db = client[DB_NAME]
api_db = client["api"]
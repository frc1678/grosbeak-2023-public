import os
import pymongo

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

MONGO_URI = os.environ.get("MONGO_URI")

if MONGO_URI is None or MONGO_URI == "":
    raise Exception("MONGO_URI environment variable not set")

DB_NAME = os.environ.get("DB_NAME")

if DB_NAME is None or DB_NAME == "":
    raise Exception("DB_NAME environment variable not set")


client = pymongo.MongoClient(MONGO_URI)
# db = client[DB_NAME]
api_db = client["api"]
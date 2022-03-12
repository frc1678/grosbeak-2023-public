import json
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pymongo
import os

from util import all_files_in_dir, serialize_documents, strip_extension

MONGO_URI = os.environ.get("MONGO_URI")

if MONGO_URI is None or MONGO_URI == "":
    raise Exception("MONGO_URI environment variable not set")

DB_NAME = os.environ.get("DB_NAME")

if DB_NAME is None or DB_NAME == "":
    raise Exception("DB_NAME environment variable not set")


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

team_lists = list(map(strip_extension, all_files_in_dir("../team-lists")))
match_schedules = list(map(strip_extension, all_files_in_dir("../match-schedules")))

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """<h1>Welcome to Grosbeak</h1>"""


@app.get("/collection/{collection_name}")
def read_collection(collection_name: str):
    if (
        collection_name in allowed_collections
        and collection_name in db.list_collection_names()
    ):
        collection = db[collection_name]
        return serialize_documents(collection.find())
    else:
        return "Collection not found/allowed"


@app.get("/match-schedule/{event_key}")
def read_match_schedule(event_key: str):
    if event_key in match_schedules:
        with open(f"../match-schedules/{event_key}.json") as f:
            return json.load(f)
    else:
        return "Match schedule not found"


@app.get("/team-list/{event_key}")
def read_team_list(event_key: str):
    if event_key in team_lists:
        with open(f"../team-lists/{event_key}.json") as f:
            return json.load(f)
    else:
        return "Team list not found"

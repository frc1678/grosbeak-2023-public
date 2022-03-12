import json
import time
from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi import status
import pymongo
from pymongo.database import Database
from loguru import logger
import os

from util import all_files_in_dir, serialize_documents, strip_extension

api_key_header_auth = APIKeyHeader(name="Authorization", auto_error=True)

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
# db = client[DB_NAME]
api_db = client["api"]
creds_collection = api_db["credentials"]

creds = serialize_documents(creds_collection.find())

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    logger.debug(f"api_key_header: {api_key_header}")
    logger.debug(f"cred length: {len(creds)}")
    for cred in creds:
        logger.debug(f"cred: {cred}")
        if cred["api_key"] == api_key_header:
            logger.debug("passed api key auth")
            return cred
    logger.debug("failed api key auth")
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )


@app.get("/", response_class=HTMLResponse)
def read_root():
    return """<h1>Welcome to Grosbeak</h1>"""


@app.get("/collection/{collection_name}", dependencies=[Security(get_api_key)])
def read_collection(collection_name: str, event_key: str = DB_NAME):
    db = client[event_key]
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

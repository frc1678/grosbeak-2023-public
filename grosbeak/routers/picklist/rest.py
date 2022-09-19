from typing import List
from fastapi import APIRouter, Query, Body
from grosbeak.db import client
from loguru import logger
from grosbeak.routers.picklist.live import get_picklist
from pydantic import BaseModel
from grosbeak.env import env
router = APIRouter(prefix="/rest")

@router.get("/list")
def get_list(event_key: str = Query(default=env.DB_NAME)):
    ranking, dnp = get_picklist(event_key)
    return {"ranking": ranking, "dnp": dnp}

class PicklistData(BaseModel):
    ranking: List[str]
    dnp: list

@router.put("/list")
async def update_list(event_key: str = Query(default=env.DB_NAME), data: PicklistData = Body(default=...)):
    logger.debug(f"Received picklist update request with {len(data.ranking)} ranks and {len(data.dnp)} dnps")
    picklist = client[event_key]["picklist"]
    for i, team in enumerate(data.ranking):
        picklist.update_one(
            {"team_number": team}, {"$set": {"rank": i + 1, "dnp": False}},
            upsert=True
        )
    for team in data.dnp:
        picklist.update_one({"team_number": team}, {"$set": {"rank": -1, "dnp": True}}, upsert=True)
    delete_resp = picklist.delete_many({"team_number": {"$nin": data.ranking + data.dnp}})
    if delete_resp.deleted_count > 0:
        logger.info(f"Deleted {delete_resp.deleted_count} teams from picklist")
    return {
        "deleted": delete_resp.deleted_count,
    }
        
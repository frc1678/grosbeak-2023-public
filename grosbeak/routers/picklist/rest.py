from typing import List
from fastapi import APIRouter, Query, Body
from grosbeak.db import client
from loguru import logger
from grosbeak.routers.picklist.live import get_picklist
from pydantic import BaseModel
from grosbeak.env import env
from fastapi.responses import JSONResponse
from grosbeak.routers.api import ErrorMessage

router = APIRouter(prefix="/rest")


@router.get("/list")
def get_list(event_key: str = Query(default=env.DB_NAME)):
    ranking, dnp = get_picklist(event_key)
    return {"ranking": ranking, "dnp": dnp}


class PicklistData(BaseModel):
    ranking: List[str]
    dnp: list


class UpdateListResponse(BaseModel):
    deleted: int


@router.put(
    "/list",
    responses={401: {"model": ErrorMessage}, 200: {"model": UpdateListResponse}},
)
async def update_list(
    password: str = Query(default=...),
    event_key: str = Query(default=env.DB_NAME),
    data: PicklistData = Body(default=...),
):
    if password != env.PICKLIST_PASSWORD:
        logger.warning("Incorrect password for picklist update")
        return JSONResponse(status_code=401, content={"error": "Incorrect password"})
    logger.debug(
        f"Received picklist update request with {len(data.ranking)} ranks and {len(data.dnp)} dnps"
    )
    picklist = client[event_key]["picklist"]
    for i, team in enumerate(data.ranking):
        picklist.update_one(
            {"team_number": team}, {"$set": {"rank": i + 1, "dnp": False}}, upsert=True
        )
    for team in data.dnp:
        picklist.update_one(
            {"team_number": team}, {"$set": {"rank": -1, "dnp": True}}, upsert=True
        )
    delete_resp = picklist.delete_many(
        {"team_number": {"$nin": data.ranking + data.dnp}}
    )
    if delete_resp.deleted_count > 0:
        logger.info(f"Deleted {delete_resp.deleted_count} teams from picklist")
    return {
        "deleted": delete_resp.deleted_count,
    }

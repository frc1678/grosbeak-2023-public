from typing import Union
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, Field
from pydantic.types import constr

from ..auth import get_api_key
from ..db import STATIC_FILE_TYPES, api_db, client

router = APIRouter(prefix="/admin")


class NewCredentialRequest(BaseModel):
    description: str
    level: int


class NewCredentialResponse(BaseModel):
    description: str
    level: int
    api_key: str


@router.post("/new-credential", response_model=NewCredentialResponse)
async def create_credential(
    *, data: NewCredentialRequest, user_level: dict = Depends(get_api_key)
):
    if user_level["level"] >= 2:
        creds = NewCredentialResponse(
            description=data.description,
            level=data.level,
            api_key=str(uuid.uuid4()).replace("-", ""),
        )
        api_db["credentials"].insert_one(creds.dict())
        return creds


class NewStaticRequest(BaseModel):
    type: str
    event_key: str = Field(..., min_length=5)
    data: Union[dict, list]

    @validator("type")
    def is_valid_type(cls, v):
        assert v in STATIC_FILE_TYPES, "Invalid type"
        return v


@router.put("/static")
def new_match_schedule(data: NewStaticRequest, user_level: dict = Depends(get_api_key)):
    if user_level["level"] < 2:
        return JSONResponse(status_code=403)
    collection = client["static"][data.type]
    collection.find_one_and_update(
        {"event_key": data.event_key}, {"$set": {"data": data.data}}, upsert=True
    )
    return {"error": None}

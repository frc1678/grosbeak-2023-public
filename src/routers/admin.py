import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import get_api_key
from ..db import api_db

router = APIRouter(prefix="/admin")


class NewCredentialRequest(BaseModel):
    description: str
    level: int

class NewCredentialResponse(BaseModel):
    description: str
    level: int
    api_key: str


@router.post("/new-credential", response_model=NewCredentialResponse)
async def create_credential(*, data: NewCredentialRequest, user_level: dict = Depends(get_api_key)):
    if user_level["level"] >= 2:
        creds = NewCredentialResponse(
            description=data.description,
            level=data.level,
            api_key=str(uuid.uuid4()).replace("-", ""),
        )
        api_db["credentials"].insert_one(creds.dict())
        return creds
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_api_key


router = APIRouter(prefix="/api")


class NewCredentialRequest(BaseModel):
    description: str
    level: int

class NewCredentialResponse(BaseModel):
    description: str
    level: int
    api_key: str


@router.post("/new-credential", response_model=NewCredentialResponse)
async def create_credential(*, data: NewCredentialRequest, user_level: int = Depends(get_api_key)):
    if user_level >= 2:
        return NewCredentialResponse(
            description=data.description,
            level=data.level,
            api_key=str(uuid.uuid4()).replace("-", ""),
        )
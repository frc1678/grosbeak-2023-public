from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from .db import api_db

from loguru import logger

from .util import serialize_documents

api_key_header_auth = APIKeyHeader(name="Authorization", auto_error=True)

creds_collection = api_db["credentials"]

creds = serialize_documents(creds_collection.find())

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
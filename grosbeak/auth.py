from fastapi import Depends, HTTPException, Header, Security, WebSocket, status
from fastapi.security import APIKeyHeader
from .db import api_db

from loguru import logger

from .util import serialize_documents

api_key_header_auth = APIKeyHeader(name="Authorization", auto_error=True)

creds_collection = api_db["credentials"]


def check_auth(api_key: str):
    creds_item = creds_collection.find_one({"api_key": api_key})
    if creds_item is None:
        return None
    return creds_item

async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    logger.debug(f"api_key_header: {api_key_header}")
    auth = check_auth(api_key_header)
    if auth is None:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
    return auth

async def protect_websocket(websocket: WebSocket, authorization: str = Header(None)):
    auth = check_auth(authorization)
    if auth is None:
        logger.info(f"Websocket connection denied with auth {auth}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    else:
        return auth
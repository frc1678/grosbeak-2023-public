from fastapi import APIRouter, Security, WebSocket
from grosbeak.auth import get_api_key, protect_websocket
from grosbeak.env import env
from grosbeak.routers.picklist.live import websocket_picklist
import grosbeak.routers.picklist.rest as rest

router = APIRouter(prefix="/picklist", dependencies=[Security(get_api_key)])


@router.websocket("/live")
async def websocket_picklist(
    websocket: WebSocket, event_key: str = env.DB_NAME, auth=Security(protect_websocket)
):
    if auth is not None:
        return await websocket_picklist(websocket, event_key)


router.include_router(rest.router)

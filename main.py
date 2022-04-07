import time
from typing import Optional
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from src.env import DB_NAME
from src.routers import api, admin, live, images


app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api.router)
app.include_router(admin.router)
app.include_router(images.router)

@app.websocket("/ws/picklist")
async def websocket_picklist(websocket: WebSocket, event_key: str = DB_NAME):
    return await live.websocket_picklist(websocket, event_key)

@app.get("/", response_class=HTMLResponse)
def read_root():
    return """<h1>Welcome to Grosbeak</h1>"""

# print(list(map(lambda x: x.path,app.routes)))


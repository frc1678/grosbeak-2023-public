import time
from typing import Optional
from fastapi import Depends, FastAPI, Request, Security, WebSocket
from fastapi.responses import FileResponse
from grosbeak.auth import get_api_key, protect_websocket
from grosbeak.env import env
from grosbeak.routers import api, admin, picklist
from fastapi.staticfiles import StaticFiles


app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(api.router)
app.include_router(picklist.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    return FileResponse("web/index.html")


app.mount("/", StaticFiles(directory="web"), name="web")


# print(list(map(lambda x: x.path,app.routes)))

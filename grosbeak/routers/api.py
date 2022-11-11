from enum import Enum
from functools import reduce
import os
from typing import Any, Dict, List, Literal, TypedDict, Union
from fastapi import APIRouter, Security, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from grosbeak.auth import get_api_key
from grosbeak.db import COLLECTION_KEYS, STATIC_FILE_TYPES, CachedViewerData, viewer_data_cache, ViewerData, client, COLLECTIONS
from grosbeak.env import env
from grosbeak.util import all_files_in_dir, serialize_documents, strip_extension
import json
from os.path import exists
from grosbeak.routers.notes import router as notes_router

router = APIRouter(prefix="/api", dependencies=[Security(get_api_key)])

router.include_router(notes_router)


class ErrorMessage(BaseModel):
    error: str


@router.get("/collection/{collection_name}", responses={404: {"model": ErrorMessage}})
def read_collection(collection_name: str, event_key: str = env.DB_NAME):
    db = client[event_key]
    if (
        collection_name in COLLECTIONS.keys()
        and collection_name in db.list_collection_names()
    ):
        collection = db[collection_name]
        return serialize_documents(list(collection.find()))
    else:
        return JSONResponse(
            content={"error": "Collection not found/allowed"}, status_code=404
        )


class ColorEnum(str, Enum):
    red = "red"
    blue = "blue"


class MatchScheduleTeam(BaseModel):
    number: str
    color: ColorEnum


class MatchScheduleMatch(BaseModel):
    teams: List[MatchScheduleTeam]


@router.get(
    "/match-schedule/{event_key}",
    response_model=Dict[str, MatchScheduleMatch],
    responses={404: {"model": ErrorMessage}},
)
def read_match_schedule(event_key: str):
    return read_static_json("match-schedule", event_key)


@router.get(
    "/team-list/{event_key}",
    response_model=List[str],
    responses={404: {"model": ErrorMessage}},
)
def read_team_list(event_key: str):
    return read_static_json("team-list", event_key)



def make_key(collection_type: str, document: Dict[str, Any]) -> List[str]:
    """
    Makes a key from a team, tim, or aim document for referencing
    """
    keys = []
    for header in COLLECTION_KEYS[collection_type]:
        if header == "alliance_color_is_red":
            alliance_color_is_red = document["alliance_color_is_red"]
            if alliance_color_is_red:
                keys.append("red")
            else:
                keys.append("blue")
        else:
            keys.append(str(document[header]))
        document.pop(header)
    return keys


def get_by_path(dictionary: Dict, path: List[str]) -> Any:
    """ """
    return reduce(lambda d, key: d.get(key) if d else None, path, dictionary)


def set_by_path(dictionary: Dict, path: List[str], value: Any):
    """
    Sets a value in a nested dictionary by a list of strings
    """
    #
    reduce(lambda d, key: d.setdefault(key, {}), path[:-1], dictionary)[
        path[-1]
    ] = value


def serialize_viewer_document(document: Dict[str, Any]):
    document.pop("_id", None)
    return document


@router.get("/viewer")
def get_viewer_data(
    use_strings: bool = False, event_key: str = env.DB_NAME, if_none_match: Union[str, None] = Header(default=None)
) -> ViewerData:
    """
    This function uses hard code "collections of collections" to try to relate different collections.
    This data is much easier for viewer to understand
    """
    db = client[event_key]

    db_hash = db.command("dbHash", collections=list(COLLECTIONS.keys()))["md5"]
    if if_none_match is not None and if_none_match == db_hash:
        return JSONResponse(status_code=304, headers={"ETag": db_hash})

    cached_viewer_data = viewer_data_cache.get(event_key, None)
    if cached_viewer_data is not None and cached_viewer_data.hash == db_hash:
        return JSONResponse(content=cached_viewer_data.data, headers={"ETag": db_hash})

    data: ViewerData = {"team": {}, "tim": {}, "aim": {}}

    for collection, collection_type in COLLECTIONS.items():
        documents = db[collection].find()
        for doc in documents:
            key = make_key(collection_type, doc)
            # Dictionary made from
            common_doc = get_by_path(data[collection_type], key)
            if common_doc is None:
                common_doc = {}
                set_by_path(data[collection_type], key, common_doc)
            # Sending _id to viewer is generally not a good idea and is just wasting space
            # https://stackoverflow.com/a/62706325
            sanitized = serialize_viewer_document(doc)
            if use_strings:
                for k, v in sanitized.items():
                    # Only convert non primitives (like lists, dicts, or other classes) to strings
                    if not isinstance(v, (float, int, str, bool)):
                        sanitized[k] = str(v)
            common_doc.update(sanitized)
    # Update the cache
    # TODO: The database might have changed by now, so we should check the hash again (or something better)
    viewer_data_cache[event_key] = CachedViewerData(data=data, hash=db_hash)
    return JSONResponse(content=data, headers={"ETag": db_hash})


def read_static_json(static_type: str, event_key: str):
    if static_type not in STATIC_FILE_TYPES:
        return JSONResponse(
            content={"error": "Static file type not found/allowed"},
            status_code=404,
        )
    collection = client["static"][static_type]
    document = collection.find_one({"event_key": event_key})
    if document is None:
        return JSONResponse(content={"error": "Static file not found"}, status_code=404)
    else:
        return JSONResponse(content=document["data"])

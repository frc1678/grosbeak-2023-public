"""
This should be cleaner
"""
import os
from typing import Any, Callable, Dict, Optional, Set, Type, TypedDict
from pydantic import BaseModel


def get_envs(envs: Dict[str, Callable[[str], Any]]) -> Dict[str, Optional[str]]:
    env_dict = dict()
    for env in envs:
        env_value = os.environ.get(env)
        if env_value is not None:
            try:
                env_dict[env] = envs[env](env_value)
            except:
                print("failed type cast")
                env_dict[env] = None
        else:
            print("env value is none")
            env_dict[env] = None
    return env_dict


class Envs(BaseModel):
    PICKLIST_PASSWORD: str
    DB_NAME: str
    MONGO_URI: str


env = Envs(**get_envs(Envs.__annotations__))

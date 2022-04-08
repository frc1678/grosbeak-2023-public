import argparse
import subprocess
import dotenv
from pydantic import BaseModel, constr
class Env(BaseModel):
    DB_NAME: constr(min_length=1)
    MONGO_URI: constr(min_length=1)
    PICKLIST_PASSWORD: constr(min_length=1)

def make_env_args(env: Env):
    config = env.dict()
    env_list = []
    for key, value in config.items():
        env_list.append(f"--env {key}={value}")
    return " ".join(env_list)

def deploy(config: Env):
    FULL_IMAGE_NAME = "ghcr.io/calvin-laurenson/grosbeak:latest"
    CONTAINER_NAME = "grosbeak-prod"

    STOP_CONTAINER = f"docker stop {CONTAINER_NAME}"
    REMOVE_IMAGE = f"docker rmi {FULL_IMAGE_NAME}"
    PULL_IMAGE = f"docker pull {FULL_IMAGE_NAME}"
    START_CONTAINER = f"docker run -d --name {CONTAINER_NAME} -p 8002:80 {make_env_args(config)} {FULL_IMAGE_NAME}"
    final_command = "; ".join([STOP_CONTAINER, REMOVE_IMAGE, PULL_IMAGE, START_CONTAINER])
    print(final_command)
    if input("Does this command look good? (y/N): ").lower() == "y":
        print(subprocess.check_output(["ssh", "picklist@citrus.ant.isi.edu", final_command]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually redeploy the grosbeak container on prod")
    parser.add_argument("env_file", help="The .env file to use")

    args = parser.parse_args()
    
    config = dotenv.dotenv_values(args.env_file)
    config = Env(**config)
    deploy(config)
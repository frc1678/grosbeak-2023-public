from typing import List
from os import listdir
from os.path import isfile, join


def all_files_in_dir(dir: str) -> List[str]:
    return [f for f in listdir(dir) if isfile(join(dir, f))]

def strip_extension(filename: str) -> str:
    return filename.split(".")[0]
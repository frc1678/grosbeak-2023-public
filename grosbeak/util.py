from os import listdir
from os.path import isfile, join


def all_files_in_dir(dir: str) -> list[str]:
    return [f for f in listdir(dir) if isfile(join(dir, f))]


def strip_extension(filename: str) -> str:
    return filename.split(".")[0]


def serialize_documents(docs: list[dict]) -> list[dict]:
    """Remove the '_id' from each document"""
    docs = list(docs)
    for doc in docs:
        doc.pop("_id", None)

    return docs

"""
This should be cleaner
"""
import os


MONGO_URI = os.environ.get("MONGO_URI")

if MONGO_URI is None or MONGO_URI == "":
    raise Exception("MONGO_URI environment variable not set")

DB_NAME = os.environ.get("DB_NAME")

if DB_NAME is None or DB_NAME == "":
    raise Exception("DB_NAME environment variable not set")

PICKLIST_PASSWORD = os.environ.get("PICKLIST_PASSWORD")

if PICKLIST_PASSWORD is None or PICKLIST_PASSWORD == "":
    raise Exception("PICKLIST_PASSWORD environment variable not set")
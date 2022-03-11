#!/bin/sh
cd src
uvicorn server:app --reload --env-file ../.env
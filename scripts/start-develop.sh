#!/bin/sh

set -o errexit
set -o nounset

aerich upgrade
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/bin/sh

set -o errexit
set -o nounset

aerich upgrade
gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4 --reload --access-logfile - --error-logfile - app.main:app

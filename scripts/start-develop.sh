#!/bin/sh

set -o errexit
set -o nounset

aerich upgrade
python manage.py runserver

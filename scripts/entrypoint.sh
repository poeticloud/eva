#!/bin/sh

set -o errexit
set -o nounset

postgres_ready() {
python << END
import asyncio
import asyncpg
import sys

async def run():
    await asyncpg.connect(dsn="${POSTGRES_DSN}")

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(run())
except (asyncpg.PostgresError, ConnectionError):
    sys.exit(1)
sys.exit(0)
END
}
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'

exec "$@"

# eva

Open Identity Management

## Init Database

```
cd src
PYTHONPATH=. alembic upgrade head
```

## Run Develop

```
CORS=True python3 src/server.py
```

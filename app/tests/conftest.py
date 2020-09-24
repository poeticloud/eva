from typing import Generator

import pytest
from fastapi.testclient import TestClient
from tortoise.contrib.test import finalizer, initializer

from app.core.config import settings
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def initialize_tests(request):
    initializer(["app.models"], db_url=settings.postgres_dsn_test)
    request.addfinalizer(finalizer)


@pytest.fixture(scope="module")
def event_loop(client: TestClient) -> Generator:
    yield client.task.get_loop()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

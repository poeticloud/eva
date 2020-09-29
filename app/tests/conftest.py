from typing import Generator

import pytest
from fastapi.testclient import TestClient
from tortoise.contrib.test import finalizer, initializer

from app.main import app


@pytest.fixture(scope="module")
def client():
    initializer(["app.models"])
    with TestClient(app) as test_client:
        yield test_client
    finalizer()


@pytest.fixture(scope="module")
def event_loop(client: TestClient) -> Generator:
    yield client.task.get_loop()

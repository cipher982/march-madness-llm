import importlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mm_ai.bracket import Bracket

os.environ.setdefault("FRONTEND_PORT", "3000")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

main_module = importlib.import_module("mm_ai.main")
app = main_module.app


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.messages.append(data)


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def initialized_bracket(data_dir: Path) -> Bracket:
    bracket = Bracket()
    bracket.load_initial_data(str(data_dir / "bracket_2024.json"))
    return bracket


@pytest.fixture
def fake_websocket() -> FakeWebSocket:
    return FakeWebSocket()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

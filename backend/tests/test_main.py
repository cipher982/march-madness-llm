import pytest
from fastapi.testclient import TestClient

from mm_ai.main import app


async def no_sleep(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
    _ = args, kwargs


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_bracket_start_endpoint_returns_expected_shape(client: TestClient) -> None:
    response = client.get("/api/bracket_start")
    assert response.status_code == 200
    payload = response.json()
    assert "bracket" in payload
    assert "regions" in payload["bracket"]
    assert len(payload["bracket"]["regions"]) == 4


def test_websocket_invalid_decider_returns_error(client: TestClient) -> None:
    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_json({"decider": "invalid_decider"})
        message = websocket.receive_json()
        assert message == {"error": "Invalid decider: invalid_decider"}


def test_websocket_invalid_json_payload_returns_error(client: TestClient) -> None:
    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_text("{bad-json")
        message = websocket.receive_json()
        assert message == {"error": "Invalid request payload: expected JSON object"}


def test_websocket_enforces_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mm_ai.main.get_rate_limit_config", lambda: (1, 60))
    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_json({"decider": "invalid_decider"})
        first_message = websocket.receive_json()
        assert first_message == {"error": "Invalid decider: invalid_decider"}

        websocket.send_json({"decider": "invalid_decider"})
        second_message = websocket.receive_json()
        assert second_message == {"error": "Rate limit exceeded. Please wait and retry."}


def test_generic_exception_handler_hides_internal_details(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_loader(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
        _ = args, kwargs
        raise RuntimeError("sensitive internal detail")

    monkeypatch.setattr("mm_ai.main.Bracket.load_initial_data", broken_loader)
    with TestClient(app, raise_server_exceptions=False) as safe_client:
        response = safe_client.get("/api/bracket_start")
        assert response.status_code == 500
        assert response.json() == {"message": "Internal server error"}


def test_websocket_seed_simulation_completes(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("mm_ai.deciders.asyncio.sleep", no_sleep)
    monkeypatch.setattr("mm_ai.simulator.asyncio.sleep", no_sleep)

    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_json({"decider": "seed", "use_current_state": False, "user_preferences": ""})
        seen_simulation_complete = False

        for _ in range(160):
            message = websocket.receive_json()
            if message.get("type") == "simulation_complete":
                seen_simulation_complete = True
                break

        assert seen_simulation_complete

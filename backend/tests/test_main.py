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
        assert message == {"error": "Invalid decider"}


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
        assert first_message == {"error": "Invalid decider"}

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

    with client.websocket_connect("/ws/simulate") as websocket:
        websocket.send_json({"decider": "seed", "use_current_state": False, "user_preferences": ""})
        seen_simulation_complete = False

        for _ in range(160):
            message = websocket.receive_json()
            if message.get("type") == "simulation_complete":
                seen_simulation_complete = True
                break

        assert seen_simulation_complete


def test_docs_disabled_by_default(client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_cors_disables_credentials(client: TestClient) -> None:
    resp = client.options(
        "/health",
        headers={
            "Origin": "https://marchmadness.drose.io",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "https://marchmadness.drose.io"
    assert "access-control-allow-credentials" not in {k.lower() for k in resp.headers}


def test_websocket_rejects_disallowed_origin_before_accept(client: TestClient) -> None:
    from starlette.websockets import WebSocketDisconnect

    for bad_origin in ("https://evil.example", "null", ""):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/simulate", headers={"origin": bad_origin}):
                pass

    with client.websocket_connect("/ws/simulate", headers={"origin": "https://marchmadness.drose.io"}) as ws:
        ws.send_json({"decider": "invalid_decider<script>"})
        assert ws.receive_json() == {"error": "Invalid decider"}


def test_websocket_rejects_overlong_user_preferences(client: TestClient) -> None:
    with client.websocket_connect("/ws/simulate") as ws:
        ws.send_json({"decider": "seed", "user_preferences": "a" * 501})
        message = ws.receive_json()
        assert "500" in message["error"]


def test_get_client_ip_trusted_proxy_only() -> None:
    from types import SimpleNamespace

    from starlette.datastructures import Headers

    from mm_ai.main import get_client_ip

    trusted_ws = SimpleNamespace(
        client=SimpleNamespace(host="172.18.0.5"),
        headers=Headers({"x-forwarded-for": "1.1.1.1, 198.51.100.44", "x-real-ip": "198.51.100.44"}),
    )
    assert get_client_ip(trusted_ws) == "198.51.100.44"

    trusted_xff_only = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers=Headers({"x-forwarded-for": "1.1.1.1, 198.51.100.77, 10.0.0.2"}),
    )
    assert get_client_ip(trusted_xff_only) == "198.51.100.77"

    untrusted_ws = SimpleNamespace(
        client=SimpleNamespace(host="198.51.100.99"),
        headers=Headers({"x-forwarded-for": "9.9.9.9", "x-real-ip": "9.9.9.9"}),
    )
    assert get_client_ip(untrusted_ws) == "198.51.100.99"


@pytest.mark.asyncio
async def test_rate_limit_sweeps_stale_and_caps_buckets() -> None:
    from collections import deque
    from time import monotonic

    from mm_ai.main import MAX_RATE_LIMIT_BUCKETS
    from mm_ai.main import SIMULATION_RATE_BUCKETS
    from mm_ai.main import is_rate_limited

    SIMULATION_RATE_BUCKETS["empty-ip"] = deque()
    SIMULATION_RATE_BUCKETS["expired-ip"] = deque([monotonic() - 10_000])
    assert await is_rate_limited("fresh-ip") is False
    assert "empty-ip" not in SIMULATION_RATE_BUCKETS
    assert "expired-ip" not in SIMULATION_RATE_BUCKETS

    now = monotonic()
    for i in range(MAX_RATE_LIMIT_BUCKETS + 50):
        SIMULATION_RATE_BUCKETS[f"ip-{i}"] = deque([now])

    await is_rate_limited("newest-ip")
    assert len(SIMULATION_RATE_BUCKETS) <= MAX_RATE_LIMIT_BUCKETS

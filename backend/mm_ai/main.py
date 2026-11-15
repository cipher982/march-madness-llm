import asyncio
import ipaddress
import json
import logging
import os
from collections import OrderedDict
from collections import deque
from collections.abc import Callable
from ipaddress import IPv4Network
from ipaddress import IPv6Network
from time import monotonic

from fastapi import FastAPI
from fastapi import Request
from fastapi import WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketDisconnect

from mm_ai.bracket import Bracket
from mm_ai.deciders import get_decision_function
from mm_ai.simulator import Simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _docs_enabled() -> bool:
    return os.getenv("ENABLE_API_DOCS", "").strip().lower() in {"1", "true", "yes"}


_docs_on = _docs_enabled()
app = FastAPI(
    docs_url="/docs" if _docs_on else None,
    redoc_url="/redoc" if _docs_on else None,
    openapi_url="/openapi.json" if _docs_on else None,
)

DEFAULT_ORIGINS = ["https://marchmadness.drose.io"]
MAX_RATE_LIMIT_BUCKETS = 10_000
MAX_USER_PREFERENCES_LENGTH = 500
SIMULATION_RATE_BUCKETS: OrderedDict[str, deque[float]] = OrderedDict()
SIMULATION_RATE_LOCK = asyncio.Lock()

_TRUSTED_PROXY_NETWORKS: tuple[IPv4Network | IPv6Network, ...] = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception for %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "details": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": "Resource not found"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


def get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("ALLOWED_ORIGINS")
    if configured_origins:
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

    frontend_port = os.getenv("FRONTEND_PORT", "3000")
    return [f"http://localhost:{frontend_port}", *DEFAULT_ORIGINS]


def get_data_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "../data", filename)


def _parse_positive_int(value: str, default_value: int) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return default_value
    return parsed if parsed > 0 else default_value


def get_rate_limit_config() -> tuple[int, int]:
    max_requests = _parse_positive_int(os.getenv("SIMULATION_RATE_LIMIT_COUNT", "12"), 12)
    window_seconds = _parse_positive_int(os.getenv("SIMULATION_RATE_LIMIT_WINDOW_SECONDS", "60"), 60)
    return max_requests, window_seconds


def _parse_ip(raw: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    candidate = raw.strip()
    if not candidate:
        return None
    if "%" in candidate:
        candidate = candidate.split("%", 1)[0]
    try:
        ip = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


def _is_trusted_proxy_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(ip in net for net in _TRUSTED_PROXY_NETWORKS)


def get_client_ip(websocket: WebSocket) -> str:
    peer_host = websocket.client.host if websocket.client and websocket.client.host else "unknown"
    peer_ip = _parse_ip(peer_host)
    if peer_ip is None or not _is_trusted_proxy_ip(peer_ip):
        return str(peer_ip) if peer_ip is not None else peer_host

    x_real_ip = websocket.headers.get("x-real-ip")
    if x_real_ip:
        parsed_real = _parse_ip(x_real_ip)
        if parsed_real is not None and not _is_trusted_proxy_ip(parsed_real):
            return str(parsed_real)

    xff = websocket.headers.get("x-forwarded-for", "")
    if xff:
        parsed_hops = [ip for part in xff.split(",") if (ip := _parse_ip(part)) is not None]
        for hop in reversed(parsed_hops):
            if not _is_trusted_proxy_ip(hop):
                return str(hop)
        if parsed_hops:
            return str(parsed_hops[-1])

    if x_real_ip:
        parsed_real = _parse_ip(x_real_ip)
        if parsed_real is not None:
            return str(parsed_real)

    return str(peer_ip)


def is_allowed_ws_origin(websocket: WebSocket) -> bool:
    origin = websocket.headers.get("origin")
    if origin is None:
        if os.getenv("ALLOW_WS_WITHOUT_ORIGIN", "").strip().lower() in {"1", "true", "yes"}:
            return True
        return bool(websocket.client and websocket.client.host == "testclient")

    normalized = origin.strip().rstrip("/")
    if not normalized or normalized.lower() == "null":
        return False
    allowed = {item.strip().rstrip("/") for item in get_allowed_origins() if item.strip()}
    return "*" in allowed or normalized in allowed


async def is_rate_limited(client_id: str) -> bool:
    max_requests, window_seconds = get_rate_limit_config()
    now = monotonic()
    oldest_allowed = now - window_seconds

    async with SIMULATION_RATE_LOCK:
        stale_keys = [
            key for key, bucket in SIMULATION_RATE_BUCKETS.items() if not bucket or bucket[-1] < oldest_allowed
        ]
        for key in stale_keys:
            del SIMULATION_RATE_BUCKETS[key]

        bucket = SIMULATION_RATE_BUCKETS.get(client_id)
        if bucket is None:
            while len(SIMULATION_RATE_BUCKETS) >= MAX_RATE_LIMIT_BUCKETS:
                SIMULATION_RATE_BUCKETS.popitem(last=False)
            bucket = deque()
            SIMULATION_RATE_BUCKETS[client_id] = bucket
        else:
            SIMULATION_RATE_BUCKETS.move_to_end(client_id)
            while bucket and bucket[0] < oldest_allowed:
                bucket.popleft()

        if len(bucket) >= max_requests:
            return True
        bucket.append(now)
        return False


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the NCAA March Madness Bracket Simulator!"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/bracket_start")
async def get_bracket() -> dict[str, dict]:
    bracket = Bracket()
    bracket.load_initial_data(get_data_path("bracket_2024.json"))
    bracket_data = bracket.to_dict()
    return {"bracket": bracket_data}


@app.get("/api/bracket_current")
async def get_current_bracket() -> dict[str, dict]:
    bracket = Bracket()
    bracket.load_initial_data(get_data_path("bracket_2024.json"))
    current_state_path = get_data_path("current_state.json")
    if os.path.exists(current_state_path):
        bracket.load_current_state(current_state_path)
    return {"bracket": bracket.to_dict()}


async def _send_simulation_error(websocket: WebSocket, message: str) -> None:
    await websocket.send_json({"error": message})


def _parse_simulation_request(payload: dict) -> tuple[str, bool, str]:
    decider = payload.get("decider")
    if not isinstance(decider, str) or not decider.strip():
        raise ValueError("Invalid decider")

    use_current_state = payload.get("use_current_state", False)
    if not isinstance(use_current_state, bool):
        raise ValueError("Invalid use_current_state: expected boolean")

    user_preferences = payload.get("user_preferences", "")
    if not isinstance(user_preferences, str):
        raise ValueError("Invalid user_preferences: expected string")
    if len(user_preferences) > MAX_USER_PREFERENCES_LENGTH:
        raise ValueError(f"Invalid user_preferences: maximum length is {MAX_USER_PREFERENCES_LENGTH} characters")

    return decider, use_current_state, user_preferences


def _build_bracket(use_current_state: bool) -> Bracket:
    bracket = Bracket()
    bracket.load_initial_data(get_data_path("bracket_2024.json"))
    if use_current_state:
        current_state_path = get_data_path("current_state.json")
        if os.path.exists(current_state_path):
            bracket.load_current_state(current_state_path)
    return bracket


@app.websocket("/ws/simulate")
async def simulate_websocket(websocket: WebSocket) -> None:
    if not is_allowed_ws_origin(websocket):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            try:
                data = await websocket.receive_json()
            except json.JSONDecodeError:
                await _send_simulation_error(websocket, "Invalid request payload: expected JSON object")
                continue

            if not isinstance(data, dict):
                await _send_simulation_error(websocket, "Invalid request payload: expected JSON object")
                continue

            try:
                decider, use_current_state, user_preferences = _parse_simulation_request(data)
            except ValueError as exc:
                await _send_simulation_error(websocket, str(exc))
                continue

            client_id = get_client_ip(websocket)
            if await is_rate_limited(client_id):
                await _send_simulation_error(websocket, "Rate limit exceeded. Please wait and retry.")
                continue

            decision_function: Callable | None = get_decision_function(decider)
            if decision_function is None:
                await _send_simulation_error(websocket, "Invalid decider")
                continue

            try:
                bracket = _build_bracket(use_current_state)
                simulator = Simulator(
                    bracket=bracket,
                    user_preferences=user_preferences,
                    websocket=websocket,
                )
                await simulator.simulate_tournament(decision_function)
            except WebSocketDisconnect:
                raise
            except Exception as exc:
                logger.error("Simulation failed for decider=%s: %s", decider, exc, exc_info=True)
                await _send_simulation_error(websocket, "Simulation failed. Please retry.")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

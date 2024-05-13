import logging
import os

from fastapi import FastAPI
from fastapi import Request
from fastapi import WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketDisconnect

from app.bracket import Bracket
from app.deciders import get_decision_function
from app.simulator import Simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

simulator = None

frontend_port = os.environ.get("FRONTEND_PORT")
assert frontend_port is not None, "FRONTEND_PORT is not set"
print(f"Frontend port: {frontend_port}")


class SimulateRequest(BaseModel):
    decider: str
    use_current_state: bool = False
    api_key: str = ""
    user_preferences: str = ""


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},  # Send the actual error message
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "details": exc.errors()},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": "Resource not found"},
        )
    # Add more specific HTTP exception handling here if needed
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost",
        # "http://localhost:8080",
        # "http://marchmadness.drose.io:50001",
        # "https://marchmadness.drose.io",
        # "http://api.marchmadness.drose.io",
        # "http://api.marchmadness.drose.io:50001",
        # "https://api.marchmadness.drose.io",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the NCAA March Madness Bracket Simulator!"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/api/bracket_start")
async def get_bracket():
    bracket = Bracket()
    bracket.load_initial_data(os.path.join(os.path.dirname(__file__), "../data", "bracket_2024.json"))
    bracket_data = bracket.to_dict()
    return {"bracket": bracket_data}


@app.get("/api/bracket_current")
async def get_current_bracket():
    bracket = Bracket()
    base_dir = os.path.dirname(__file__)
    bracket.load_initial_data(os.path.join(base_dir, "../data", "bracket_2024.json"))
    current_state_path = os.path.join(base_dir, "../data", "current_state.json")
    if os.path.exists(current_state_path):
        bracket.load_current_state(current_state_path)
    return {"bracket": bracket.to_dict()}


@app.websocket("/ws/simulate")
async def simulate_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            decider = data.get("decider")
            use_current_state = data.get("use_current_state", False)
            user_preferences = data.get("user_preferences", "")

            decision_function = get_decision_function(decider)
            if decision_function is None:
                await websocket.send_json({"error": f"Invalid decider: {decider}"})
                continue

            bracket = Bracket()
            fp_start = os.path.join(os.path.dirname(__file__), "../data", "bracket_2024.json")
            bracket.load_initial_data(fp_start)
            if use_current_state:
                fp_current = os.path.join(os.path.dirname(__file__), "../data", "current_state.json")
                bracket.load_current_state(fp_current)

            simulator = Simulator(
                bracket=bracket,
                api_key=data.get("api_key", ""),
                user_preferences=user_preferences,
                websocket=websocket,
            )
            await simulator.simulate_tournament(decision_function)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")

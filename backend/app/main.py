import asyncio
import logging
import os

from bracket import Bracket
from deciders import get_decision_function
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from simulator import Simulator
from starlette.exceptions import HTTPException as StarletteHTTPException

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

simulator = None


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
    allow_origins=["http://marchmadness.drose.io"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the NCAA March Madness Bracket Simulator!"}


class SimulateRequest(BaseModel):
    decider: str
    use_current_state: bool = False
    api_key: str = ""
    user_preferences: str = ""


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


@app.post("/api/simulate")
async def simulate(request: SimulateRequest):
    decider = request.decider
    use_current_state = request.use_current_state
    user_preferences = request.user_preferences
    logger.info(f"Received simulate request with decider: {decider}, use_current_state: {use_current_state}")

    decision_function = get_decision_function(decider)
    if decision_function is None:
        raise HTTPException(status_code=400, detail=f"Invalid decider: {decider}")

    bracket = Bracket()
    fp_start = os.path.join(os.path.dirname(__file__), "../data", "bracket_2024.json")
    bracket.load_initial_data(fp_start)
    if use_current_state:
        fp_current = os.path.join(os.path.dirname(__file__), "../data", "current_state.json")
        bracket.load_current_state(fp_current)

    global simulator
    simulator = Simulator(
        bracket=bracket,
        api_key=request.api_key,
        user_preferences=user_preferences,
    )
    asyncio.create_task(simulator.simulate_tournament(decision_function))

    return {
        "message": "Simulation started",
        "bracket": bracket.to_dict(),
    }


@app.get("/api/simulation_status")
async def get_simulation_status():
    global simulator
    if simulator:
        current_matchup = None
        current_winner = None
        if simulator.current_matchup:
            team1, team2 = simulator.current_matchup
            current_matchup = {
                "team1": team1.to_dict(),
                "team2": team2.to_dict(),
            }
            if simulator.current_winner:
                current_winner = simulator.current_winner.to_dict()

        logger.info(f"FastAPI: returning populated data {current_winner}")
        return {
            "bracket": simulator.bracket.to_dict(),
            "region": simulator.current_region,
            "round": simulator.current_round,
            "current_matchup": current_matchup,
            "current_winner": current_winner,
        }
    else:
        logger.info("FastAPI: returning empty data")
        return {
            "bracket": None,
            "region": None,
            "round": None,
            "current_matchup": None,
            "current_winner": None,
        }

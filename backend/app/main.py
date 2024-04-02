import os
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bracket import Bracket
from deciders import get_decision_function
from simulator import Simulator

logger = logging.getLogger(__name__)

app = FastAPI()


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
    current_state: str = ""
    api_key: str = ""


@app.post("/api/simulate")
async def simulate(request: SimulateRequest):
    decider = request.decider
    current_state = request.current_state
    logger.info(f"Received simulate request with decider: {decider}, current_state: {current_state}")

    decision_function = get_decision_function(decider)
    if decision_function is None:
        raise HTTPException(status_code=400, detail=f"Invalid decider: {decider}")

    bracket = Bracket()
    bracket.load_initial_data(os.path.join(os.path.dirname(__file__), "../data", "bracket_2024.json"))
    if current_state:
        bracket.load_current_state(current_state)

    simulator = Simulator(bracket, api_key=request.api_key)
    results = await simulator.simulate_tournament(decision_function)

    return {"message": "Simulation completed", "results": results}

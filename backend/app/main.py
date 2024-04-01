import os
import logging
from fastapi import FastAPI, HTTPException
from .deciders import get_decision_function
from .simulator import Simulator
from .bracket import Bracket
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI()

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

    simulator = Simulator(bracket)
    results = await simulator.simulate_tournament(decision_function)

    return {"message": "Simulation completed", "results": results}

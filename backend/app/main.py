from fastapi import FastAPI
from backend.app.simulator import Simulator
from backend.app.bracket import Bracket

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Welcome to the NCAA March Madness Bracket Simulator!"}


@app.post("/simulate")
async def simulate(decider: str, current_state: str = ""):
    bracket = Bracket()
    bracket.load_initial_data("bracket_2024.json")
    if current_state:
        bracket.load_current_state(current_state)

    simulator = Simulator(bracket)
    await simulator.simulate_tournament(decider)

    return {"message": "Simulation completed"}

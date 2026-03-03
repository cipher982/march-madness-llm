import logging
import os
import uuid
from typing import Any
from typing import Awaitable
from typing import Callable

from dotenv import load_dotenv
from fastapi import WebSocket
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

from mm_ai.bracket import Bracket
from mm_ai.bracket import Team
from mm_ai.deciders import ai_wizard

logger = logging.getLogger(__name__)

load_dotenv()
DecisionFunction = Callable[[Team, Team], Awaitable[Team]]

ROUND_NAMES = [
    "round_of_64",
    "round_of_32",
    "sweet_16",
    "elite_8",
    "final_4",
    "championship",
]


class Simulator:
    def __init__(self, bracket: Bracket, user_preferences: str, websocket: WebSocket):
        self.websocket = websocket
        self.bracket = bracket
        self.user_preferences = user_preferences
        self.simulation_id = str(uuid.uuid4())

        api_key = os.getenv("OPENAI_API_KEY")
        self.client = wrap_openai(AsyncOpenAI(api_key=api_key)) if api_key else None

    async def _send(self, payload: dict) -> None:
        """Single point of entry for all WebSocket sends.

        All simulation output flows through here, ensuring sends are always
        sequential (this method is only called from the single simulation
        coroutine — no concurrent callers, no lock needed).
        """
        await self.websocket.send_json(payload)

    async def _decide(self, team1: Team, team2: Team, decision_function: DecisionFunction) -> Team:
        if decision_function == ai_wizard:
            if self.client is None:
                raise RuntimeError("OPENAI_API_KEY is required when using decider='ai'")
            return await decision_function(team1, team2, self.user_preferences, self.client)
        return await decision_function(team1, team2)

    async def _play_match(
        self,
        team1: Team,
        team2: Team,
        region: str | None,
        round_name: str,
        decision_function: DecisionFunction,
    ) -> Team:
        """Decide a single match, emit match_update, then emit bracket_update."""
        winner = await self._decide(team1, team2, decision_function)

        logger.info("%s (%s) vs %s (%s) → %s", team1.name, team1.seed, team2.name, team2.seed, winner.name)

        await self._send(
            {
                "type": "match_update",
                "region": region,
                "round": round_name,
                "current_matchup": {
                    "team1": {"name": team1.name, "seed": team1.seed},
                    "team2": {"name": team2.name, "seed": team2.seed},
                },
                "current_winner": {"name": winner.name, "seed": winner.seed},
            }
        )
        return winner

    async def _simulate_round(
        self,
        region_name: str,
        round_name: str,
        decision_function: DecisionFunction,
    ) -> list[tuple[str, Team]]:
        matchups = self.bracket.get_matchups(region_name, round_name)
        if not matchups:
            raise RuntimeError(f"No matchups found for region={region_name} round={round_name}")

        round_results: list[tuple[str, Team]] = []

        for matchup_id, matchup in matchups.items():
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None and team2 is None:
                logger.warning("Skipping matchup %s: both teams missing", matchup_id)
                continue
            if team1 is None or team2 is None:
                raise RuntimeError(f"Incomplete matchup {matchup_id}: team1={team1} team2={team2}")

            winner = await self._play_match(team1, team2, region_name, round_name, decision_function)
            self.bracket.update_matchup_winner(region_name, round_name, matchup_id, winner)
            round_results.append((matchup_id, winner))

            await self._send({"type": "bracket_update", "bracket": self.bracket.to_dict()})

        next_round = self.bracket.get_next_round_name(round_name)
        if next_round is not None:
            current_round_obj = self.bracket.get_round_by_name(region_name, round_name)
            next_round_obj = self.bracket.get_round_by_name(region_name, next_round)
            if current_round_obj is None or next_round_obj is None:
                raise RuntimeError(f"Cannot build next round: {region_name}/{next_round}")
            self.bracket.create_next_round_matchups(current_round_obj, next_round_obj)

        return round_results

    async def _simulate_region(
        self,
        region_name: str,
        decision_function: DecisionFunction,
        starting_round: str = "round_of_64",
    ) -> Team:
        starting_index = ROUND_NAMES.index(starting_round)
        for round_name in ROUND_NAMES[starting_index:4]:
            logger.info("Simulating %s / %s ...", region_name, round_name)
            round_results = await self._simulate_round(region_name, round_name, decision_function)

            if round_name == "elite_8":
                if len(round_results) == 1:
                    region_winner = round_results[0][1]
                    logger.info("%s region winner: %s", region_name, region_winner.name)
                    return region_winner
                raise RuntimeError(f"Expected 1 Elite Eight result for {region_name}, got {len(round_results)}")

        raise RuntimeError(f"Simulation ended without producing a winner for {region_name}")

    async def _simulate_final_four(self, decision_function: DecisionFunction) -> None:
        logger.info("Simulating Final Four...")
        for matchup in self.bracket.final_four.matchups:
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None or team2 is None:
                logger.warning("Skipping Final Four matchup %s: missing team(s)", matchup.matchup_id)
                continue
            winner = await self._play_match(team1, team2, None, "final_4", decision_function)
            self.bracket.update_matchup_winner(None, "final_4", matchup.matchup_id, winner)
            self.bracket.update_final_four_and_championship()
            await self._send({"type": "bracket_update", "bracket": self.bracket.to_dict()})

    async def _simulate_championship(self, decision_function: DecisionFunction) -> None:
        logger.info("Simulating Championship...")
        matchup = self.bracket.championship
        team1, team2 = matchup.team1, matchup.team2
        if team1 is None or team2 is None:
            raise RuntimeError("Championship matchup is missing teams")
        winner = await self._play_match(team1, team2, None, "championship", decision_function)
        self.bracket.update_matchup_winner(None, "championship", matchup.matchup_id, winner)
        self.bracket.update_championship_winner(winner)
        await self._send({"type": "bracket_update", "bracket": self.bracket.to_dict()})

    async def simulate_tournament(self, decision_function: DecisionFunction) -> tuple[list[dict[str, Any]], Bracket]:
        logger.info("Starting NCAA March Madness Bracket Simulation...")

        results: list[dict[str, Any]] = []
        for region in ["east", "west", "south", "midwest"]:
            winner = await self._simulate_region(region, decision_function)
            results.append({"region": region, "winner": winner.name})

        self.bracket.update_final_four_and_championship()
        await self._simulate_final_four(decision_function)
        await self._simulate_championship(decision_function)

        tournament_winner = self.bracket.get_tournament_winner()
        results.append({"final_winner": tournament_winner.name if tournament_winner else None})

        await self._send({"type": "simulation_complete"})
        return results, self.bracket

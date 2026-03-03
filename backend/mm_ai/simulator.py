import asyncio
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
        self.current_region: str | None = None
        self.current_round: str | None = None
        self.current_matchup: tuple[Team, Team] | None = None
        self.current_winner: Team | None = None
        self.simulation_id = str(uuid.uuid4())
        self.max_concurrency = self._get_max_concurrency()
        self._state_lock = asyncio.Lock()

        api_key = os.getenv("OPENAI_API_KEY")
        self.client = wrap_openai(AsyncOpenAI(api_key=api_key)) if api_key else None

    @staticmethod
    def _get_max_concurrency() -> int:
        raw_concurrency = os.getenv("SIMULATION_CONCURRENCY", "3")
        try:
            return max(1, int(raw_concurrency))
        except ValueError:
            logger.warning("Invalid SIMULATION_CONCURRENCY=%s, defaulting to 3", raw_concurrency)
            return 3

    async def send_match_update(self, team1: Team, team2: Team, winner: Team) -> None:
        await self.websocket.send_json(
            {
                "type": "match_update",
                "region": self.current_region,
                "round": self.current_round,
                "current_matchup": {
                    "team1": {
                        "name": team1.name,
                        "seed": team1.seed,
                    },
                    "team2": {
                        "name": team2.name,
                        "seed": team2.seed,
                    },
                },
                "current_winner": {
                    "name": winner.name,
                    "seed": winner.seed,
                },
            }
        )

    async def send_bracket_update(self) -> None:
        await self.websocket.send_json(
            {
                "type": "bracket_update",
                "bracket": self.bracket.to_dict(),
            }
        )

    async def simulate_match(
        self,
        team1: Team,
        team2: Team,
        decision_function: DecisionFunction,
        played: bool = False,
    ) -> Team:
        if decision_function == ai_wizard:
            if self.client is None:
                raise RuntimeError("OPENAI_API_KEY is required when using decider='ai'")
            winner = await decision_function(team1, team2, self.user_preferences, self.client)
        else:
            winner = await decision_function(team1, team2)

        self.current_matchup = (team1, team2)
        self.current_winner = winner
        self.print_match_summary(team1, team2, winner, played)
        await self.send_match_update(team1, team2, winner)
        return winner

    def print_match_summary(self, team1: Team, team2: Team, winner: Team, played: bool = False) -> None:
        _ = played
        logger.info(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}), winner: {winner.name}")

    async def simulate_round(
        self,
        decision_function: DecisionFunction,
        region_name: str,
        round_name: str,
    ) -> list[tuple[str, Team]]:
        matchups = self.bracket.get_matchups(region_name, round_name)
        assert matchups, f"no matchups: {region_name}, {round_name}"
        round_results: list[tuple[str, Team]] = []

        sem = asyncio.Semaphore(self.max_concurrency)

        async def process_match(matchup_id: str, team1: Team, team2: Team) -> Team:
            async with sem:
                await asyncio.sleep(0.1)
                winner = await self.simulate_match(team1, team2, decision_function)
                async with self._state_lock:
                    round_results.append((matchup_id, winner))
                    self.bracket.update_matchup_winner(region_name, round_name, matchup_id, winner)
                    await self.send_bracket_update()
                return winner

        tasks: list[Awaitable[Team]] = []
        for matchup_id, matchup in matchups.items():
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None and team2 is None:
                logger.warning(f"Skipping matchup {matchup_id} due to missing teams.")
                continue
            elif team1 is None or team2 is None:
                raise Exception(f"Invalid matchup: {matchup}, team1: {team1}, team2: {team2}")
            else:
                tasks.append(process_match(matchup_id, team1, team2))

        await asyncio.gather(*tasks)

        next_round = self.bracket.get_next_round_name(round_name)
        if next_round is not None:
            current_round = self.bracket.get_round_by_name(region_name, round_name)
            next_round_obj = self.bracket.get_round_by_name(region_name, next_round)
            assert next_round_obj is not None
            assert current_round is not None
            async with self._state_lock:
                self.bracket.create_next_round_matchups(current_round, next_round_obj)
        return round_results

    async def simulate_region(
        self,
        decision_function: DecisionFunction,
        region_name: str,
        starting_round: str | None = None,
    ) -> Team:
        if starting_round is None:
            starting_round = "round_of_64"

        starting_index = ROUND_NAMES.index(starting_round)
        for round_name in ROUND_NAMES[starting_index:4]:
            self.current_round = round_name
            logger.info(f"Simulating {round_name} round...")
            logger.debug(f"\nSimulating {round_name} for {region_name} region...")
            round_results = await self.simulate_round(decision_function, region_name, round_name)
            logger.debug(f"{region_name} {round_name} results:")

            if round_name == "elite_8":
                if len(round_results) == 1:
                    region_winner = round_results[0][1]
                    logger.debug(f"\n{region_name} region winner: {region_winner.name}")
                    return region_winner
                else:
                    raise Exception(f"Error determining {region_name} region winner after elite 8 round.")

        raise Exception(f"Error determining {region_name} region winner.")

    async def simulate_final_four(self, decision_function: DecisionFunction) -> None:
        logger.debug("\nSimulating Final Four...")
        matchups = self.bracket.final_four.matchups
        final_four_results: list[Team] = []

        for matchup in matchups:
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None or team2 is None:
                logger.warning(f"Skipping {matchup.matchup_id} due to missing team(s).")
                continue
            winner = await self.simulate_match(team1, team2, decision_function)
            async with self._state_lock:
                self.bracket.update_matchup_winner(None, "final_4", matchup.matchup_id, winner)
                final_four_results.append(winner)
                self.bracket.update_final_four_and_championship()
                await self.send_bracket_update()

        logger.debug("Final Four results:")
        for team in final_four_results:
            logger.debug(f"{team.name}")

    async def simulate_championship(self, decision_function: DecisionFunction) -> None:
        logger.debug("\nSimulating Championship...")
        matchup = self.bracket.championship
        team1, team2 = matchup.team1, matchup.team2
        if team1 is None or team2 is None:
            raise Exception("Championship matchup is missing teams.")
        winner = await self.simulate_match(team1, team2, decision_function)
        async with self._state_lock:
            self.bracket.update_matchup_winner(None, "championship", matchup.matchup_id, winner)
            self.bracket.update_championship_winner(winner)
            await self.send_bracket_update()

    async def simulate_tournament(self, decision_function: DecisionFunction) -> tuple[list[dict[str, Any]], Bracket]:
        logger.debug("Starting NCAA March Madness Bracket Simulation...\n")

        results: list[dict[str, Any]] = []
        for region in ["east", "west", "south", "midwest"]:
            self.current_region = region
            winner = await self.simulate_region(decision_function, region)
            results.append({"region": region, "winner": winner.name})
        async with self._state_lock:
            self.bracket.update_final_four_and_championship()

        self.current_round = "final_4"
        await self.simulate_final_four(decision_function)

        self.current_round = "championship"
        await self.simulate_championship(decision_function)

        winner = self.bracket.get_tournament_winner()
        results.append({"final_winner": winner.name if winner else None})

        await self.send_bracket_update()
        await self.websocket.send_json({"type": "simulation_complete"})
        return results, self.bracket

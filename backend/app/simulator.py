import argparse
import asyncio
import os
import logging
from .deciders import get_decision_function
from .bracket import Bracket, Team

logger = logging.getLogger(__name__)

ROUND_NAMES = [
    "round_of_64",
    "round_of_32",
    "sweet_16",
    "elite_8",
    "final_4",
    "championship",
]


class Simulator:
    def __init__(self, bracket):
        self.bracket = bracket

    async def simulate_match(self, team1, team2, decision_function, played=False):
        winner = await decision_function(team1, team2)
        self.print_match_summary(team1, team2, winner, played)
        return winner

    def print_match_summary(self, team1, team2, winner, played=False):
        if played:
            logger.warning(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - Already Played")
        else:
            logger.info(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})")
        logger.debug(f"Winner: {winner.name}")

    async def simulate_round(self, decision_function, region_name, round_name):
        matchups = self.bracket.get_matchups(region_name, round_name)
        assert matchups, f"no matchups: {region_name}, {round_name}"
        round_results = []

        for matchup_id, matchup in matchups.items():
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None and team2 is None:
                logger.warning(f"Skipping matchup {matchup_id} due to missing teams.")
                continue
            elif team1 is None or team2 is None:
                raise Exception(f"Invalid matchup: {matchup}, team1: {team1}, team2: {team2}")
            else:
                winner = await self.simulate_match(team1, team2, decision_function)
                round_results.append((matchup_id, winner))
                self.bracket.update_matchup_winner(region_name, round_name, matchup_id, Team(winner.name, winner.seed))
        next_round = self.bracket.get_next_round_name(round_name)
        if next_round is not None:
            current_round = self.bracket.get_round_by_name(region_name, round_name)
            next_round_obj = self.bracket.get_round_by_name(region_name, next_round)
            self.bracket.create_next_round_matchups(current_round, next_round_obj)
        return round_results

    async def simulate_region(self, decision_function, region_name, starting_round=None) -> Team:
        if starting_round is None:
            starting_round = "round_of_64"

        starting_index = ROUND_NAMES.index(starting_round)
        for round_name in ROUND_NAMES[starting_index:4]:
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

    async def simulate_final_four(self, decision_function):
        logger.debug("\nSimulating Final Four...")
        matchups = self.bracket.final_four.matchups
        final_four_results = []

        for matchup in matchups:
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None or team2 is None:
                logger.warning(f"Skipping {matchup.matchup_id} due to missing team(s).")
                continue
            winner = await self.simulate_match(team1, team2, decision_function)
            self.bracket.update_matchup_winner(None, "final_4", matchup.matchup_id, winner)
            final_four_results.append(winner)
            self.bracket.update_final_four_and_championship()

        logger.debug("Final Four results:")
        for team in final_four_results:
            logger.debug(f"{team.name}")

    async def simulate_championship(self, decision_function):
        logger.debug("\nSimulating Championship...")
        matchup = self.bracket.championship
        team1, team2 = matchup.team1, matchup.team2
        winner = await self.simulate_match(team1, team2, decision_function)
        self.bracket.update_matchup_winner(None, "championship", matchup.matchup_id, winner)

    async def simulate_tournament(self, decision_function) -> list:
        logger.debug("Starting NCAA March Madness Bracket Simulation...\n")

        results = []
        for region in ["east", "west", "south", "midwest"]:
            starting_round = None
            logger.debug(f"Simulating {region} region...")
            logger.debug(f"Starting round: {starting_round}")
            winner = await self.simulate_region(decision_function, region, starting_round)
            results.append({"region": region, "winner": winner.name})
            assert results is not None, f"results is None: {results}"
        self.bracket.update_final_four_and_championship()

        await self.simulate_final_four(decision_function)
        await self.simulate_championship(decision_function)

        winner = self.bracket.get_tournament_winner()
        results.append({"final_winner": winner.name if winner else None})
        return results


def main():
    parser = argparse.ArgumentParser(description="NCAA March Madness Bracket Simulator")
    parser.add_argument(
        "--decider",
        type=str,
        default="seed",
        choices=["ai", "seed", "random"],
        help="Decision function to use for simulating games (default: seed)",
    )
    parser.add_argument(
        "--current-state",
        type=str,
        default=None,
        help="JSON file containing the current state of the bracket",
    )
    args = parser.parse_args()
    decision_function = get_decision_function(args.decider)
    if decision_function is None:
        raise ValueError(f"Invalid decider: {args.decider}")

    # Create bracket with data
    bracket = Bracket()
    bracket.load_initial_data(os.path.join(os.path.dirname(__file__), "../data", "bracket_2024.json"))
    if args.current_state:
        logger.debug("Loading current state...")
        bracket.load_current_state(args.current_state)
        logger.debug("Current state loaded.")

    logger.info(bracket)

    # Simulate tournament
    simulator = Simulator(bracket)
    asyncio.run(simulator.simulate_tournament(decision_function))


if __name__ == "__main__":
    main()

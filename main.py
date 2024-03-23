import argparse
import asyncio
import json
from collections import defaultdict
from deciders import ai_wizard, best_seed, random_winner
from termcolor import colored

ROUND_NAMES = {
    1: "Round of 64",
    2: "Round of 32",
    3: "Sweet 16",
    4: "Elite Eight",
    5: "Final Four",
    6: "NCAA Championship Game",
}


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Bracket:
    def __init__(self):
        self.teams = defaultdict(list)
        self.rounds = []
        self.region_states = {}
        self.region_winners = {}
        self.final_four_winners = []
        self.championship_winner = None

    def load_data(self, matchups_file):
        with open(matchups_file, "r") as f:
            data = json.load(f)

        for region, matchups in data["regions"].items():
            self.teams[region] = [Team(matchup["t1"][0], matchup["t1"][1]) for matchup in matchups] + [
                Team(matchup["t2"][0], matchup["t2"][1]) for matchup in matchups
            ]

    def get_next_round_matchups(self, winners):
        return [winners[i : i + 2] for i in range(0, len(winners), 2)]

    async def simulate_match(self, team1, team2, decision_function):
        winner = await decision_function(team1, team2)
        self.print_match_summary(team1, team2, winner)
        return winner

    def print_match_summary(self, team1, team2, winner):
        print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})", "cyan"))
        print(colored(f"Winner: {winner.name}\n", "green"))

    async def simulate_round(self, decision_function):
        region_teams = self.teams[self.current_region]
        current_round = self.region_states[self.current_region]["current_round"]
        round_name = ROUND_NAMES[current_round]
        print(colored(f"\n{round_name} ({self.current_region})", "yellow"))

        round_results = await asyncio.gather(
            *[
                self.simulate_match(region_teams[i], region_teams[i + 1], decision_function)
                for i in range(0, len(region_teams), 2)
            ]
        )
        self.rounds.append(
            [(region_teams[2 * i], region_teams[2 * i + 1], winner) for i, winner in enumerate(round_results)]
        )
        self.teams[self.current_region] = round_results
        self.print_round_summary(round_results)

    def print_round_summary(self, round_results):
        print(colored(f"Round winners: {', '.join(team.name for team in round_results)}", "green"))

    async def simulate_rounds_for_region(self, decision_function, region_name):
        self.current_region = region_name
        self.region_states[region_name] = {"current_round": 1, "finished": False}

        while len(self.teams[self.current_region]) > 1:
            await self.simulate_round(decision_function)
            self.region_states[region_name]["current_round"] += 1

        self.region_states[region_name]["finished"] = True
        return self.teams[self.current_region][0]

    async def simulate_final_four(self, decision_function):
        print(colored("\nSimulating Final Four matchups...", "yellow"))
        final_four_teams = list(self.region_winners.values())
        assert len(final_four_teams) == 4, "There should be exactly 4 teams in the Final Four"
        game1_winner = await self.simulate_match(final_four_teams[0], final_four_teams[1], decision_function)
        game2_winner = await self.simulate_match(final_four_teams[2], final_four_teams[3], decision_function)
        self.final_four_winners = [game1_winner, game2_winner]
        return self.final_four_winners

    async def simulate_championship_game(self, decision_function):
        print(colored("\nSimulating Championship game...", "yellow"))
        assert len(self.final_four_winners) == 2, "There should be exactly 2 teams in the Championship game"
        winner = await self.simulate_match(self.final_four_winners[0], self.final_four_winners[1], decision_function)
        self.championship_winner = winner

    async def simulate_tournament(self, decision_function):
        print(colored("Starting NCAA March Madness Bracket Simulation...\n", "yellow"))

        for region in self.teams:
            print(colored(f"===== Simulating games for {region} region =====", "yellow"))
            self.region_states[region] = {"current_round": 1, "finished": False}
            region_winner = await self.simulate_rounds_for_region(decision_function, region)
            self.region_winners[region] = region_winner
            print(colored(f"Region winner ({region}): {region_winner.name}\n", "magenta"))

        self.final_four_winners = await self.simulate_final_four(decision_function)
        await self.simulate_championship_game(decision_function)
        assert self.championship_winner is not None, "The championship winner not set"
        print(colored(f"\n🏆 Tournament Winner: {self.championship_winner.name} 🏆", "magenta"))


def main():
    parser = argparse.ArgumentParser(description="NCAA March Madness Bracket Simulator")
    parser.add_argument(
        "--decider",
        type=str,
        default="seed",
        choices=["ai", "seed", "random"],
        help="Decision function to use for simulating games (default: seed)",
    )
    args = parser.parse_args()

    decision_functions = {"ai": ai_wizard, "seed": best_seed, "random": random_winner}

    bracket = Bracket()
    bracket.load_data("bracket_2024.json")

    asyncio.run(bracket.simulate_tournament(decision_functions[args.decider]))


if __name__ == "__main__":
    main()

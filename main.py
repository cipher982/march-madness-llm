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
        self.matchups = defaultdict(dict)
        self.rounds = defaultdict(list)
        self.region_winners = {}
        self.final_four_winners = []
        self.championship_winner = None

    def load_data(self, matchups_file):
        with open(matchups_file, "r") as f:
            data = json.load(f)
        for region, matchups in data["regions"].items():
            for matchup in matchups:
                team1 = Team(matchup["t1"][0], matchup["t1"][1])
                team2 = Team(matchup["t2"][0], matchup["t2"][1])
                self.teams[region].append(team1)
                self.teams[region].append(team2)
                self.matchups[region][matchup["id"]] = (team1, team2)
        print("Data loaded. Teams per region:")
        for region, teams in self.teams.items():
            print(f"{region}: {len(teams)} teams")

    async def simulate_match(self, team1, team2, decision_function):
        winner = await decision_function(team1, team2)
        self.print_match_summary(team1, team2, winner)
        return winner

    def print_match_summary(self, team1, team2, winner):
        print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})", "cyan"))
        print(colored(f"Winner: {winner.name}\n", "green"))

    async def simulate_round_for_region(self, decision_function, region_name, round_number):
        current_matchups = list(self.matchups[region_name].values())
        round_results = await asyncio.gather(
            *[self.simulate_match(matchup[0], matchup[1], decision_function) for matchup in current_matchups]
        )
        return round_results

    def print_round_summary(self, round_results):
        print(colored(f"Round winners: {', '.join(team.name for team in round_results)}", "green"))

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

        for round_number in range(1, 5):
            print(f"===== {ROUND_NAMES[round_number]} =====")
            for region in ["east", "west", "south", "midwest"]:
                print(colored(f"\nRegion: {region}\n", "white"))
                round_results = await self.simulate_round_for_region(decision_function, region, round_number)

                if round_number == 4:
                    self.region_winners[region] = round_results[0]
                    print(colored(f"Region winner ({region}): {round_results[0].name}\n", "magenta"))

                new_matchups = []
                for i in range(0, len(round_results), 2):
                    if i + 1 < len(round_results):
                        new_matchups.append((round_results[i], round_results[i + 1]))
                self.matchups[region] = {i: new_matchups[i] for i in range(len(new_matchups))}

        # Run the Final Four and Championship game
        self.final_four_winners = await self.simulate_final_four(decision_function)
        await self.simulate_championship_game(decision_function)
        assert self.championship_winner is not None, "The championship winner was not set"
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

import argparse
import asyncio
import json
from deciders import ai_wizard, best_seed, random_winner
from termcolor import colored


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Bracket:
    def __init__(self):
        self.teams = []
        self.rounds = []

    def load_data(self, matchups_file):
        with open(matchups_file, "r") as f:
            data = json.load(f)

        self.teams = {}
        for region, matchups in data["regions"].items():
            self.teams[region] = []
            for matchup in matchups:
                team1 = Team(matchup["t1"][0], matchup["t1"][1])
                team2 = Team(matchup["t2"][0], matchup["t2"][1])
                self.teams[region].append(team1)
                self.teams[region].append(team2)

    def get_next_round_matchups(self, winners):
        return [winners[i : i + 2] for i in range(0, len(winners), 2)]  # noqa

    async def simulate_game(self, team1, team2, decision_function):
        winner = await decision_function(team1, team2)
        return winner

    async def simulate_round(self, decision_function):
        region_teams = self.teams[self.current_region]
        round_results = []
        for i in range(0, len(region_teams), 2):
            team1, team2 = region_teams[i], region_teams[i + 1]
            winner = await self.simulate_game(team1, team2, decision_function)
            round_results.append((team1, team2, winner))
            self.print_game_summary(team1, team2, winner)
        self.rounds.append(round_results)
        self.teams[self.current_region] = [result[2] for result in round_results]

    async def simulate_region(self, decision_function, region_name):
        self.current_region = region_name
        while len(self.teams[self.current_region]) > 1:
            await self.simulate_round(decision_function)
        return self.teams[self.current_region][0]

    async def simulate_tournament(self, decision_function):
        region_coroutines = [self.simulate_region(decision_function, region) for region in self.teams]
        region_winners = await asyncio.gather(*region_coroutines)

        print(colored("\nFinal Four Matchups:", "yellow"))
        final_four = self.get_next_round_matchups(region_winners)
        for team1, team2 in final_four:
            print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})", "cyan"))

        final_four_coroutines = [
            self.simulate_game(matchup[0], matchup[1], decision_function) for matchup in final_four
        ]
        finalists = await asyncio.gather(*final_four_coroutines)

        print(colored("\nChampionship Game:", "yellow"))
        print(
            colored(f"{finalists[0].name} ({finalists[0].seed}) vs {finalists[1].name} ({finalists[1].seed})", "cyan")
        )

        champion = await self.simulate_game(finalists[0], finalists[1], decision_function)
        print(colored(f"\n🏆 Tournament Winner: {champion.name} ({champion.seed}) 🏆", "magenta"))
        return champion

    def print_game_summary(self, team1, team2, winner):
        print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})", "cyan"))
        print(colored(f"Winner: {winner.name}\n", "green"))

    def print_round_summary(self, round_results):
        print(colored("\nRound Summary:", "yellow"))
        print(colored("-" * 60, "yellow"))
        header = colored(f"{'Team 1':<20} {'Team 2':<20} {'Winner':<20}", "cyan")
        print(header)
        print(colored("-" * 60, "yellow"))
        for team1, team2, winner in round_results:
            team1_name = f"{team1.name} ({team1.seed})"
            team2_name = f"{team2.name} ({team2.seed})"
            winner_name = f"{winner.name}"
            print(f"{team1_name:<20} {team2_name:<20} {winner_name:<20}")
        print(colored("-" * 60, "yellow"))


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

    # Create an event loop
    loop = asyncio.get_event_loop()

    # Run the simulate_tournament coroutine within the event loop
    _ = loop.run_until_complete(bracket.simulate_tournament(decision_functions[args.decider]))

    # Close the event loop
    loop.close()


if __name__ == "__main__":
    main()

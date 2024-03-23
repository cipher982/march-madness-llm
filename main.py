import json
from deciders import ai_wizard, best_seed, random_winner
import argparse


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

    def simulate_game(self, team1, team2, decision_function):
        winner = decision_function(team1, team2)
        print(f"Matchup: {team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - Winner: {winner.name}")
        return winner

    def simulate_round(self, decision_function):
        region_teams = self.teams[self.current_region]
        self.print_round_name(len(region_teams), self.current_region)
        winners = []
        round_results = []
        for i in range(0, len(region_teams), 2):
            team1, team2 = region_teams[i], region_teams[i + 1]
            winner = self.simulate_game(team1, team2, decision_function)
            winners.append(winner)
            round_results.append((team1, team2, winner))
        self.rounds.append(round_results)
        self.teams[self.current_region] = winners

    def simulate_region(self, decision_function, region_name):
        self.current_region = region_name
        while len(self.teams[self.current_region]) > 1:
            self.simulate_round(decision_function)
        return self.teams[self.current_region][0]

    def simulate_tournament(self, decision_function):
        region_winners = [self.simulate_region(decision_function, region) for region in self.teams]
        print("\nFinal Four Matchups:")
        final_four = self.get_next_round_matchups(region_winners)
        print("\n".join(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})" for team1, team2 in final_four))
        finalists = [self.simulate_game(matchup[0], matchup[1], decision_function) for matchup in final_four]
        print("\nChampionship Game:")
        print(f"{finalists[0].name} ({finalists[0].seed}) vs {finalists[1].name} ({finalists[1].seed})")
        champion = self.simulate_game(finalists[0], finalists[1], decision_function)
        return champion

    def print_round_name(self, num_teams, region_name):
        round_names = {
            64: "Round of 64",
            32: "Round of 32",
            16: "Sweet 16",
            8: "Elite Eight",
            4: "Final Four",
            2: "Championship",
            1: "Tournament Winner",
        }
        round_name = round_names.get(num_teams, "Starting Rounds")
        print(f"\n{region_name} {round_name} Matchups:\n")


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
    winner = bracket.simulate_tournament(decision_functions[args.decider])
    print(f"Tournament Winner: {winner.name} ({winner.seed})")


if __name__ == "__main__":
    main()

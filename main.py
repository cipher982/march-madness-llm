import json
import random


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Bracket:
    def __init__(self):
        self.teams = []
        self.rounds = []

    def load_data(self, file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
            for matchup in data["round_of_64"]:
                team1 = Team(matchup["team1"]["name"], matchup["team1"]["seed"])
                team2 = Team(matchup["team2"]["name"], matchup["team2"]["seed"])
                self.teams.append((team1, team2))

    def decide_winner(self, team1, team2, decision_function):
        return decision_function(team1, team2)

    def simulate_round(self, decision_function):
        winners = []
        round_results = []
        for matchup in self.teams:
            team1, team2 = matchup
            winner = self.decide_winner(team1, team2, decision_function)
            winners.append(winner)
            round_results.append((team1, team2, winner))
        self.teams = [(winners[i], winners[i + 1]) for i in range(0, len(winners), 2)]
        self.rounds.append(round_results)

    def simulate_tournament(self, decision_function):
        while len(self.teams) > 1:
            self.simulate_round(decision_function)
        return self.teams[0][0]

    def print_results(self):
        for i, round_results in enumerate(self.rounds):
            print(f"Round {i+1} Results:")
            for team1, team2, winner in round_results:
                print(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})")
                print(f"Winner: {winner.name} ({winner.seed})")
            print()


# Example Decision Functions
def random_choice(team1, team2):
    return random.choice([team1, team2])


def highest_seed(team1, team2):
    return team1 if team1.seed < team2.seed else team2


def longest_name(team1, team2):
    return team1 if len(team1.name) > len(team2.name) else team2


def main():
    bracket = Bracket()
    bracket.load_data("bracket_data.json")
    # Choose the decision function here. For example, highest_seed
    winner = bracket.simulate_tournament(highest_seed)
    print("Tournament Results:")
    bracket.print_results()
    print("Tournament Winner:")
    print(f"{winner.name} ({winner.seed})")


if __name__ == "__main__":
    main()

import random


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Bracket:
    def __init__(self):
        self.teams = []
        self.rounds = []

    def input_teams(self, team_list):
        self.teams = [Team(name, seed) for name, seed in team_list]

    def simulate_round(self):
        num_teams = len(self.teams)
        winners = []
        round_results = []
        for i in range(0, num_teams, 2):
            team1, team2 = self.teams[i], self.teams[i + 1]
            winner = random.choice([team1, team2])
            winners.append(winner)
            round_results.append((team1, team2, winner))
        self.teams = winners
        self.rounds.append(round_results)

    def simulate_tournament(self):
        while len(self.teams) > 1:
            self.simulate_round()
        return self.teams[0]

    def print_results(self):
        for i, round_results in enumerate(self.rounds):
            print(f"Round {i+1} Results:")
            for team1, team2, winner in round_results:
                print(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})")
                print(f"Winner: {winner.name} ({winner.seed})")
            print()


def main():
    bracket = Bracket()
    team_list = [
        ("Team A", 1),
        ("Team B", 16),
        ("Team C", 8),
        ("Team D", 9),
        ("Team E", 5),
        ("Team F", 12),
        ("Team G", 4),
        ("Team H", 13),
        # ... input the remaining teams and seeds
    ]
    bracket.input_teams(team_list)
    winner = bracket.simulate_tournament()
    print("Tournament Results:")
    bracket.print_results()
    print("Tournament Winner:")
    print(f"{winner.name} ({winner.seed})")


if __name__ == "__main__":
    main()

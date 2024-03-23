import random


class Region:
    def __init__(self, name, bracket):
        self.name = name
        self.bracket = bracket

    def simulate_games(self):
        def simulate_round(round_games):
            winners = {}
            next_round_games = {}
            for game_key, teams in round_games.items():
                if teams:
                    winner = random.choice(list(teams))
                    winners[game_key] = winner
                    print(f"Simulating game: {game_key}, Winner: {winner}")
                    # Add the winner to the next round's games
                    next_round_key = game_key[:-1] + str(int(game_key[-1]) + 1)
                    if next_round_key in round_games:
                        next_round_games[next_round_key] = {winner: {}}
            return winners, next_round_games

        current_round = self.bracket
        print(f"Starting simulation with bracket: {current_round}")
        while current_round:
            current_round, next_round = simulate_round(current_round)
            print(f"Current round winners: {current_round}")
            if next_round:
                current_round = next_round
            else:
                break
        self.winner = list(current_round.values())[0] if current_round else None
        print(f"Final winner: {self.winner}")


# Create an instance of the Midwest region
midwest_region = Region("Midwest", bracket)

# Simulate the games in the Midwest region
midwest_region.simulate_games()

# Get the winner of the Midwest region
winner = midwest_region.winner

print(f"The winner of the {midwest_region.name} region is: {winner}")

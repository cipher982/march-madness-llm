import json
import random
import os
from dotenv import load_dotenv

from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

PROMPT = """
Consider a March Madness tournament matchup between two teams.
Team 1, named '{team1.name}', is seeded {team1.seed}.
Team 2, named '{team2.name}', is seeded {team2.seed}.

Taking into account factors such as likely team performance, seed ranking, \
historical success in tournaments, or anything else helpful.
Choose one.
"""


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
        self.print_round_name(len(self.teams) * 2)
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

    def print_round_name(self, num_teams):
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
        print(f"\n{round_name} Matchups:\n")

    def print_results(self):
        for i, round_results in enumerate(self.rounds):
            print(f"Round {i+1} Results:")
            for team1, team2, winner in round_results:
                print(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})")
                print(f"Winner: {winner.name} ({winner.seed})")
            print()


def execute_function(function_name, arguments):
    if function_name == "decide_winner":
        team1 = Team(arguments["team1"]["name"], arguments["team1"]["seed"])
        team2 = Team(arguments["team2"]["name"], arguments["team2"]["seed"])
        return team1 if arguments["winner"] == team1.name else team2
    else:
        raise ValueError(f"Unknown function: {function_name}")


def use_ai(team1, team2):
    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "decide_winner",
                    "description": "Decide the winner between two teams",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team1": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "seed": {"type": "integer"},
                                },
                            },
                            "team2": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "seed": {"type": "integer"},
                                },
                            },
                            "winner": {"type": "string"},
                        },
                        "required": ["team1", "team2", "winner"],
                    },
                },
            }
        ]
        messages = [
            {
                "role": "user",
                "content": PROMPT.format(team1=team1, team2=team2),
            }
        ]
        completion = client.chat.completions.create(
            # model="gpt-3.5-turbo",
            model="gpt-4-0125-preview",
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            tool_choice="auto",
        )

        choice = completion.choices[0]
        if choice.message and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            winner = execute_function(function_name, arguments)
        else:
            print("AI did not provide a clear winner. Choosing randomly.")
            winner = random.choice([team1, team2])

        print(
            f"Matchup: {team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - "
            f"Winner: {winner.name} ({winner.seed})"
        )
        return winner
    except Exception as e:
        print(f"Error calling OpenAI or executing function: {e}")
        winner = random.choice([team1, team2])
        print(
            f"Error_rand: {team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - "
            f"Winner: {winner.name} ({winner.seed})"
        )
        return winner


def main():
    bracket = Bracket()
    bracket.load_data("bracket_data.json")
    winner = bracket.simulate_tournament(use_ai)
    print("Tournament Results:")
    bracket.print_results()
    print("Tournament Winner:")
    print(f"{winner.name} ({winner.seed})")


if __name__ == "__main__":
    main()

import random
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


PROMPT = """
Consider a March Madness tournament matchup between two teams.
Team 1, named '{team1.name}', is seeded {team1.seed}.
Team 2, named '{team2.name}', is seeded {team2.seed}.

Taking into account factors such as likely team performance, seed ranking, \
historical success in tournaments, or anything else helpful.
Choose one.
"""


def execute_function(function_name, arguments):
    if function_name == "decide_winner":
        team1 = Team(arguments["team1"]["name"], arguments["team1"]["seed"])
        team2 = Team(arguments["team2"]["name"], arguments["team2"]["seed"])
        return team1 if arguments["winner"] == team1.name else team2
    else:
        raise ValueError(f"Unknown function: {function_name}")


def ai_decider(team1, team2):
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

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


async def best_seed(team1, team2):
    if team1.seed < team2.seed:
        return team1
    elif team1.seed > team2.seed:
        return team2
    else:
        return random.choice([team1, team2])


async def random_winner(team1, team2):
    winner = random.choice([team1, team2])
    return winner


PROMPT = """
Consider a March Madness tournament matchup between two teams.
Team 1, named '{team1.name}', is seeded {team1.seed}.
Team 2, named '{team2.name}', is seeded {team2.seed}.

Taking into account factors such as likely team performance, seed ranking, \
historical success in tournaments, or anything else helpful.
Choose one.
"""


def ai_wizard(team1, team2):
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
        messages = [{"role": "user", "content": PROMPT.format(team1=team1, team2=team2)}]

        completion = client.chat.completions.create(
            # model="gpt-4-0125-preview",
            model="gpt-3.5-turbo-0125",
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            tool_choice="auto",
        )

        choice = completion.choices[0]
        if choice.message and choice.message.tool_calls:
            arguments = json.loads(choice.message.tool_calls[0].function.arguments)
            winner = Team(arguments["winner"], getattr(team1 if arguments["winner"] == team1.name else team2, "seed"))
        else:
            raise Exception("No decision made by AI")
        return winner
    except Exception as e:
        print(f"Error calling OpenAI or executing function: {e}")
        raise e

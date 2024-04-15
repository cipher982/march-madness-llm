import asyncio
import json
import random
from textwrap import dedent

from bracket import Team
from langsmith import traceable


def get_decision_function(decider):
    decision_functions = {"ai": ai_wizard, "seed": best_seed, "random": random_winner}
    return decision_functions.get(decider)


async def best_seed(team1: Team, team2: Team) -> Team:
    await asyncio.sleep(0.05)
    if team1.seed < team2.seed:
        return team1
    elif team1.seed > team2.seed:
        return team2
    else:
        return random.choice([team1, team2])


async def random_winner(team1: Team, team2: Team) -> Team:
    await asyncio.sleep(0.05)
    winner = random.choice([team1, team2])
    return winner


@traceable
async def ai_wizard(team1: Team, team2: Team, user_preferences: str, client=None) -> Team:
    if client is None:
        raise ValueError("OpenAI client is not initialized")
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

        prompt = dedent("""
        Consider a March Madness tournament matchup between two teams.
        Team 1, named '{team1.name}', is seeded {team1.seed}.
        Team 2, named '{team2.name}', is seeded {team2.seed}.
             
        You should also consider these user preferences to help you make a decision.
        If this is populated, then you should use the user preferences to help make a decision.
        Preferences: {user_preferences}.

        Now, taking into account factors such as likely team performance, seed ranking, \
        historical success in tournaments, or any user preferences, which team would you choose?
        Choose one.
        """)
        messages = [
            {"role": "user", "content": prompt.format(team1=team1, team2=team2, user_preferences=user_preferences)}
        ]

        response = await client.chat.completions.create(
            # model="gpt-4-0125-preview",
            model="gpt-3.5-turbo-0125",
            messages=messages,  # type: ignore
            tools=tools,  # type: ignore
            tool_choice="auto",
        )

        choice = response.choices[0]
        if choice.message and choice.message.tool_calls:
            arguments = json.loads(choice.message.tool_calls[0].function.arguments)
            winner_team = team1 if arguments["winner"] == team1.name else team2
            winner = Team(arguments["winner"], winner_team.seed)
        else:
            raise Exception("No decision made by AI")
        print(f"AI decision: {winner.name}")
        return winner
    except Exception as e:
        print(f"Error calling OpenAI or executing function: {e}")
        raise e

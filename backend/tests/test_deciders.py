from types import SimpleNamespace

import pytest

from mm_ai.bracket import Team
from mm_ai.deciders import ai_wizard
from mm_ai.deciders import best_seed
from mm_ai.deciders import get_decision_function
from mm_ai.deciders import random_winner


class FakeCompletions:
    def __init__(self, winner_name: str) -> None:
        self.winner_name = winner_name

    async def create(self, **kwargs) -> SimpleNamespace:  # noqa: ANN003
        _ = kwargs
        tool_call = SimpleNamespace(function=SimpleNamespace(arguments=f'{{"winner": "{self.winner_name}"}}'))
        message = SimpleNamespace(tool_calls=[tool_call])
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeClient:
    def __init__(self, winner_name: str) -> None:
        self.simulation_id = "test-simulation"
        self.chat = SimpleNamespace(completions=FakeCompletions(winner_name))


def test_get_decision_function_returns_expected_callable() -> None:
    assert get_decision_function("ai") == ai_wizard
    assert get_decision_function("seed") == best_seed
    assert get_decision_function("random") == random_winner
    assert get_decision_function("unknown") is None


@pytest.mark.asyncio
async def test_best_seed_returns_lower_seed() -> None:
    team1 = Team("Higher Seed", 2)
    team2 = Team("Lower Seed", 12)
    winner = await best_seed(team1, team2)
    assert winner == team1


@pytest.mark.asyncio
async def test_random_winner_returns_one_of_the_teams() -> None:
    team1 = Team("Team 1", 1)
    team2 = Team("Team 2", 2)
    winner = await random_winner(team1, team2)
    assert winner in (team1, team2)


@pytest.mark.asyncio
async def test_ai_wizard_requires_client() -> None:
    with pytest.raises(ValueError, match="OpenAI client is not initialized"):
        await ai_wizard(Team("A", 1), Team("B", 2), "prefer defense")


@pytest.mark.asyncio
async def test_ai_wizard_uses_tool_call_winner() -> None:
    team1 = Team("Team 1", 3)
    team2 = Team("Team 2", 7)
    winner = await ai_wizard(team1, team2, "prefer underdogs", FakeClient("Team 2"))
    assert winner.name == "Team 2"
    assert winner.seed == 7

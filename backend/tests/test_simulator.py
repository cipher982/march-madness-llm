import pytest

from mm_ai.bracket import Bracket
from mm_ai.bracket import Team
from mm_ai.simulator import Simulator


async def no_sleep(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
    _ = args, kwargs


async def lower_seed(team1: Team, team2: Team) -> Team:
    if team1.seed <= team2.seed:
        return team1
    return team2


@pytest.mark.asyncio
async def test_simulate_round_updates_matchups_and_emits_messages(
    monkeypatch: pytest.MonkeyPatch,
    initialized_bracket: Bracket,
    fake_websocket,
) -> None:
    monkeypatch.setattr("mm_ai.simulator.asyncio.sleep", no_sleep)

    simulator = Simulator(bracket=initialized_bracket, user_preferences="", websocket=fake_websocket)
    results = await simulator.simulate_round(lower_seed, "east", "round_of_64")

    assert len(results) == 8
    current_round = initialized_bracket.get_round_by_name("east", "round_of_64")
    assert current_round is not None
    assert all(matchup.winner is not None for matchup in current_round.matchups)

    next_round = initialized_bracket.get_round_by_name("east", "round_of_32")
    assert next_round is not None
    assert all(matchup.team1 is not None and matchup.team2 is not None for matchup in next_round.matchups)
    assert any(message["type"] == "match_update" for message in fake_websocket.messages)
    assert any(message["type"] == "bracket_update" for message in fake_websocket.messages)


@pytest.mark.asyncio
async def test_simulate_tournament_completes_and_sends_completion(
    monkeypatch: pytest.MonkeyPatch,
    initialized_bracket: Bracket,
    fake_websocket,
) -> None:
    monkeypatch.setattr("mm_ai.simulator.asyncio.sleep", no_sleep)

    simulator = Simulator(bracket=initialized_bracket, user_preferences="", websocket=fake_websocket)
    results, bracket = await simulator.simulate_tournament(lower_seed)

    assert results[-1]["final_winner"] == "UConn"
    assert bracket.get_tournament_winner() is not None
    assert fake_websocket.messages[-1]["type"] == "simulation_complete"

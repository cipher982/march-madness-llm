from pathlib import Path

import pytest

from mm_ai.bracket import Bracket
from mm_ai.bracket import Team


def test_load_initial_data_populates_round_of_64(initialized_bracket: Bracket) -> None:
    east_round = initialized_bracket.get_round_by_name("east", "round_of_64")
    assert east_round is not None

    first_matchup = east_round.matchups[0]
    assert first_matchup.matchup_id == "E1"
    assert first_matchup.team1 is not None
    assert first_matchup.team2 is not None
    assert first_matchup.team1.name == "UConn"
    assert first_matchup.team1.seed == 1
    assert first_matchup.team2.name == "Stetson"
    assert first_matchup.team2.seed == 16


def test_create_next_round_matchups_uses_winners(initialized_bracket: Bracket) -> None:
    current_round = initialized_bracket.get_round_by_name("east", "round_of_64")
    next_round = initialized_bracket.get_round_by_name("east", "round_of_32")
    assert current_round is not None
    assert next_round is not None

    winners = []
    for matchup in current_round.matchups:
        assert matchup.team1 is not None
        matchup.winner = matchup.team1
        winners.append(matchup.team1.name)

    initialized_bracket.create_next_round_matchups(current_round, next_round)

    for index, matchup in enumerate(next_round.matchups):
        assert matchup.team1 is not None
        assert matchup.team2 is not None
        assert matchup.team1.name == winners[index * 2]
        assert matchup.team2.name == winners[(index * 2) + 1]


def test_load_current_state_sets_region_winners_and_final_four(data_dir: Path) -> None:
    bracket = Bracket()
    bracket.load_initial_data(str(data_dir / "bracket_2024.json"))
    bracket.load_current_state(str(data_dir / "current_state.json"))

    east_winner = bracket.get_region_winner("east")
    west_winner = bracket.get_region_winner("west")
    south_winner = bracket.get_region_winner("south")
    midwest_winner = bracket.get_region_winner("midwest")

    assert east_winner is not None
    assert west_winner is not None
    assert south_winner is not None
    assert midwest_winner is not None
    assert east_winner.name == "UConn"
    assert west_winner.name == "Alabama"
    assert south_winner.name == "NC State"
    assert midwest_winner.name == "Purdue"

    final_four = bracket.final_four.matchups
    assert final_four[0].team1 is not None
    assert final_four[0].team2 is not None
    assert final_four[1].team1 is not None
    assert final_four[1].team2 is not None
    assert final_four[0].team1.name == "UConn"
    assert final_four[0].team2.name == "Alabama"
    assert final_four[1].team1.name == "NC State"
    assert final_four[1].team2.name == "Purdue"
    assert bracket.championship.team1 is None
    assert bracket.championship.team2 is None


def test_update_matchup_winner_final_four_sets_championship_matchup() -> None:
    bracket = Bracket()
    team_a = Team("Team A", 1)
    team_b = Team("Team B", 1)
    team_c = Team("Team C", 2)
    team_d = Team("Team D", 3)
    bracket.final_four.matchups[0].team1 = team_a
    bracket.final_four.matchups[0].team2 = team_b
    bracket.final_four.matchups[1].team1 = team_c
    bracket.final_four.matchups[1].team2 = team_d

    bracket.update_matchup_winner(None, "final_4", "F1", team_a)
    bracket.update_matchup_winner(None, "final_4", "F2", team_c)

    assert bracket.championship.team1 == team_a
    assert bracket.championship.team2 == team_c


def test_get_matchup_by_id_raises_for_unknown_matchup(initialized_bracket: Bracket) -> None:
    with pytest.raises(Exception, match="Matchup E99 not found"):
        initialized_bracket.get_matchup_by_id("east", "round_of_64", "E99")

import json
import os
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class Team:
    def __init__(self, name: str, seed: int):
        self.name = name
        self.seed = seed

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "seed": self.seed,
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.seed})"


class Matchup:
    def __init__(
        self,
        matchup_id: str,
        team1: Optional[Team] = None,
        team2: Optional[Team] = None,
        winner: Optional[Team] = None,
    ):
        self.matchup_id = matchup_id
        self.team1 = team1
        self.team2 = team2
        self.winner = winner

    def is_decided(self) -> bool:
        return self.team1 is not None and self.team2 is not None

    def to_dict(self) -> dict:
        return {
            "id": self.matchup_id,
            "team1": self.team1.to_dict() if self.team1 else None,
            "team2": self.team2.to_dict() if self.team2 else None,
            "winner": self.winner.to_dict() if self.winner else None,
        }

    def __str__(self) -> str:
        team1_str = str(self.team1) if self.team1 else "TBD"
        team2_str = str(self.team2) if self.team2 else "TBD"
        winner_str = str(self.winner) if self.winner else "TBD"
        return f"{self.matchup_id}: {team1_str} vs {team2_str} | Winner: {winner_str}"


class Round:
    def __init__(self, name: str, matchups: List[Matchup]):
        self.name = name
        self.matchups = matchups

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "matchups": [matchup.to_dict() for matchup in self.matchups],
        }

    def __str__(self) -> str:
        matchups_str = "\n".join(str(matchup) for matchup in self.matchups)
        return f"{self.name}:\n{matchups_str}"


class Region:
    def __init__(self, name: str, rounds: List[Round]):
        self.name = name
        self.rounds = rounds

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "rounds": [round.to_dict() for round in self.rounds],
        }

    def __str__(self) -> str:
        rounds_str = "\n\n".join(str(round) for round in self.rounds)
        return f"{self.name} Region:\n{rounds_str}"


class Bracket:
    def __init__(self):
        self.regions: List[Region] = []
        self.final_four: Round = Round("final_4", [])
        self.championship: Matchup = Matchup("C1")
        self._initialize_empty_bracket()

    def _initialize_empty_bracket(self):
        region_names = ["east", "west", "south", "midwest"]
        region_codes = ["E", "W", "S", "M"]

        for region_name, region_code in zip(region_names, region_codes):
            rounds = []
            matchup_id = 1
            for round_name, num_matchups in [("round_of_64", 8), ("round_of_32", 4), ("sweet_16", 2), ("elite_8", 1)]:
                matchups = [Matchup(f"{region_code}{matchup_id + i}") for i in range(num_matchups)]
                rounds.append(Round(round_name, matchups))
                matchup_id += num_matchups
            self.regions.append(Region(region_name, rounds))

        self.final_four = Round("final_4", [Matchup("F1"), Matchup("F2")])
        self.championship = Matchup("C1")

    def load_initial_data(self, filename: str) -> None:
        with open(filename) as file:
            data = json.load(file)

        for region_name, region_data in data["regions"].items():
            logger.debug(f"Loading data for {region_name} region")
            for matchup_data in region_data:
                matchup_id = matchup_data["id"]
                team1_data = matchup_data["t1"]
                team2_data = matchup_data["t2"]

                team1 = Team(team1_data[0], team1_data[1])
                team2 = Team(team2_data[0], team2_data[1])

                region = self.get_region_by_name(region_name)
                if region:
                    for round in region.rounds:
                        for matchup in round.matchups:
                            if matchup.matchup_id == matchup_id:
                                matchup.team1 = team1
                                matchup.team2 = team2
                                break
                else:
                    raise Exception(f"Region {region_name} not found")

    def load_current_state(self, filename: str) -> None:
        with open(filename) as file:
            data = json.load(file)

        logger.debug(f"Loading current state from {filename}")

        for region_name, region_data in data["regions"].items():
            logger.debug(f"Processing {region_name} region")
            region = self.get_region_by_name(region_name)
            if region:
                for round_name, round_data in region_data.items():
                    if round_data:
                        logger.debug(f"Processing {round_name} round")
                        round = self.get_round_by_name(region_name, round_name)
                        if round:
                            matchup_id_prefix = region_name[0].upper()
                            matchup_id_start = round.matchups[0].matchup_id[1:]
                            for i, (matchup_key, winner_name) in enumerate(round_data.items()):
                                matchup_id = f"{matchup_id_prefix}{int(matchup_id_start) + i}"
                                matchup = self.get_matchup_by_id(region_name, round.name, matchup_id)
                                if matchup:
                                    winner = next(
                                        (
                                            team
                                            for team in [matchup.team1, matchup.team2]
                                            if team and team.name == winner_name
                                        ),
                                        None,
                                    )
                                    matchup.winner = winner
                                else:
                                    raise Exception(f"Matchup {matchup_id} not found in {region_name} region")

                            # Create next round matchups
                            if round.name != "elite_8":
                                next_round_name = self.get_next_round_name(round.name)
                                assert next_round_name is not None
                                next_round = self.get_round_by_name(region_name, next_round_name)
                                assert next_round is not None
                                self.create_next_round_matchups(round, next_round)
                            else:
                                logger.debug(f"Skipping next round for {round_name} in {region_name}")
                    else:
                        logger.debug(f"No data found for {round_name} round in {region_name} region")
            else:
                raise Exception(f"Region {region_name} not found")

        logger.debug("Updating Final Four and Championship")
        self.update_final_four_and_championship()

    def get_next_round_name(self, current_round_name: str) -> Optional[str]:
        round_progression = ["round_of_64", "round_of_32", "sweet_16", "elite_8"]
        current_index = round_progression.index(current_round_name)
        if current_index < len(round_progression) - 1:
            return round_progression[current_index + 1]
        return None

    def get_region_by_name(self, name: str) -> Optional[Region]:
        for region in self.regions:
            if region.name == name:
                return region
        return None

    def create_next_round_matchups(self, current_round: Round, next_round: Round) -> None:
        winners = [matchup.winner for matchup in current_round.matchups if matchup.winner]
        next_round_matchups = next_round.matchups

        for i in range(len(next_round_matchups)):
            if i * 2 < len(winners):
                next_round_matchups[i].team1 = winners[i * 2]
                if i * 2 + 1 < len(winners):
                    next_round_matchups[i].team2 = winners[i * 2 + 1]
                else:
                    next_round_matchups[i].team2 = None
            else:
                next_round_matchups[i].team1 = None
                next_round_matchups[i].team2 = None

    def get_matchups(self, region_name: str, round_name: str) -> Dict[str, Matchup]:
        region = self.get_region_by_name(region_name)
        if region:
            round = self.get_round_by_name(region_name, round_name)
            if round:
                return {matchup.matchup_id: matchup for matchup in round.matchups}
        return {}

    def update_final_four_and_championship(self) -> None:
        region_winners = [
            region.rounds[-1].matchups[0].winner for region in self.regions if region.rounds[-1].matchups[0].winner
        ]

        # Update Final Four
        for i, matchup in enumerate(self.final_four.matchups):
            if not matchup.is_decided():
                if i * 2 < len(region_winners):
                    matchup.team1 = region_winners[i * 2]
                    matchup.team2 = region_winners[i * 2 + 1] if i * 2 + 1 < len(region_winners) else None

        # Update Championship
        final_four_winners = [matchup.winner for matchup in self.final_four.matchups if matchup.winner]
        if len(final_four_winners) == 2:
            self.championship.team1 = final_four_winners[0]
            self.championship.team2 = final_four_winners[1]
        else:
            self.championship.team1 = None
            self.championship.team2 = None

    def get_round_by_name(self, region_name: str, round_name: str) -> Optional[Round]:
        region = self.get_region_by_name(region_name)
        if region:
            for round in region.rounds:
                if round.name == round_name:
                    return round
        return None

    def get_matchup_by_id(self, region_name: Optional[str], round_name: str, matchup_id: str) -> Optional[Matchup]:
        if region_name:
            round = self.get_round_by_name(region_name, round_name)
            for matchup in round.matchups:  # type: ignore
                if matchup.matchup_id == matchup_id:
                    return matchup
        else:
            if round_name == "final_4":
                for matchup in self.final_four.matchups:
                    if matchup.matchup_id == matchup_id:
                        return matchup
            elif round_name == "championship":
                if self.championship.matchup_id == matchup_id:
                    return self.championship
        raise Exception(f"Matchup {matchup_id} not found in {region_name or 'Final Four/Championship'} {round_name}")

    def update_matchup_winner(self, region_name: Optional[str], round_name: str, matchup_id: str, winner: Team) -> None:
        if region_name:
            matchup = self.get_matchup_by_id(region_name, round_name, matchup_id)
            matchup.winner = winner  # type: ignore
        else:
            if round_name == "final_4":
                matchup = self.get_matchup_by_id(None, round_name, matchup_id)
                matchup.winner = winner  # type: ignore
                self.update_championship()
            elif round_name == "championship":
                self.championship.winner = winner

    def update_championship(self) -> None:
        final_four_winners = [matchup.winner for matchup in self.final_four.matchups if matchup.winner]
        if len(final_four_winners) == 2:
            self.championship.team1 = final_four_winners[0]
            self.championship.team2 = final_four_winners[1]

    def is_region_round_complete(self, region_name: str, round_name: str) -> bool:
        round = self.get_round_by_name(region_name, round_name)
        if round:
            return all(matchup.winner is not None for matchup in round.matchups)
        return False

    def get_region_winner(self, region_name: str) -> Optional[Team]:
        region = self.get_region_by_name(region_name)
        if region:
            elite_eight_round = region.rounds[-1]
            if len(elite_eight_round.matchups) == 1:
                return elite_eight_round.matchups[0].winner
        return None

    def update_final_four(self, matchup_id: int, winner: Team) -> None:
        if 0 <= matchup_id < len(self.final_four.matchups):
            self.final_four.matchups[matchup_id].winner = winner

    def update_championship_winner(self, winner: Team) -> None:
        self.championship.winner = winner

    def get_tournament_winner(self) -> Optional[Team]:
        return self.championship.winner

    def to_dict(self) -> dict:
        return {
            "regions": [region.to_dict() for region in self.regions],
            "finalFour": self.final_four.to_dict(),
            "championship": self.championship.to_dict(),
        }

    def __str__(self) -> str:
        regions_str = "\n\n".join(str(region) for region in self.regions)
        final_four_str = str(self.final_four)
        championship_str = str(self.championship)
        return f"Bracket:\n\n{regions_str}\n\nFinal Four:\n{final_four_str}\n\nChampionship:\n{championship_str}"


if __name__ == "__main__":
    bracket = Bracket()
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    bracket.load_initial_data(os.path.join(data_dir, "bracket_2024.json"))
    bracket.load_current_state(os.path.join(data_dir, "current_state.json"))
    logger.info(bracket)

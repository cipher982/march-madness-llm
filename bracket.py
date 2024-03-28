import json
from termcolor import colored


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed

    def __str__(self):
        return f"{self.name} ({self.seed})"

    def __repr__(self):
        return f"Team(name='{self.name}', seed={self.seed})"


class Bracket:
    def __init__(self, initial_data_file, current_state_file=None):
        self.matchups = {
            "regionals": {
                "east": {
                    "round_of_64": {
                        "E1": {"teams": (None, None), "winner": None},
                        "E2": {"teams": (None, None), "winner": None},
                        "E3": {"teams": (None, None), "winner": None},
                        "E4": {"teams": (None, None), "winner": None},
                        "E5": {"teams": (None, None), "winner": None},
                        "E6": {"teams": (None, None), "winner": None},
                        "E7": {"teams": (None, None), "winner": None},
                        "E8": {"teams": (None, None), "winner": None},
                    },
                    "round_of_32": {
                        "E1": {"teams": (None, None), "winner": None},
                        "E2": {"teams": (None, None), "winner": None},
                        "E3": {"teams": (None, None), "winner": None},
                        "E4": {"teams": (None, None), "winner": None},
                    },
                    "sweet_16": {
                        "E1": {"teams": (None, None), "winner": None},
                        "E2": {"teams": (None, None), "winner": None},
                    },
                    "elite_8": {"E1": {"teams": (None, None), "winner": None}},
                },
                "west": {
                    "round_of_64": {
                        "W1": {"teams": (None, None), "winner": None},
                        "W2": {"teams": (None, None), "winner": None},
                        "W3": {"teams": (None, None), "winner": None},
                        "W4": {"teams": (None, None), "winner": None},
                        "W5": {"teams": (None, None), "winner": None},
                        "W6": {"teams": (None, None), "winner": None},
                        "W7": {"teams": (None, None), "winner": None},
                        "W8": {"teams": (None, None), "winner": None},
                    },
                    "round_of_32": {
                        "W1": {"teams": (None, None), "winner": None},
                        "W2": {"teams": (None, None), "winner": None},
                        "W3": {"teams": (None, None), "winner": None},
                        "W4": {"teams": (None, None), "winner": None},
                    },
                    "sweet_16": {
                        "W1": {"teams": (None, None), "winner": None},
                        "W2": {"teams": (None, None), "winner": None},
                    },
                    "elite_8": {"W1": {"teams": (None, None), "winner": None}},
                },
                "south": {
                    "round_of_64": {
                        "S1": {"teams": (None, None), "winner": None},
                        "S2": {"teams": (None, None), "winner": None},
                        "S3": {"teams": (None, None), "winner": None},
                        "S4": {"teams": (None, None), "winner": None},
                        "S5": {"teams": (None, None), "winner": None},
                        "S6": {"teams": (None, None), "winner": None},
                        "S7": {"teams": (None, None), "winner": None},
                        "S8": {"teams": (None, None), "winner": None},
                    },
                    "round_of_32": {
                        "S1": {"teams": (None, None), "winner": None},
                        "S2": {"teams": (None, None), "winner": None},
                        "S3": {"teams": (None, None), "winner": None},
                        "S4": {"teams": (None, None), "winner": None},
                    },
                    "sweet_16": {
                        "S1": {"teams": (None, None), "winner": None},
                        "S2": {"teams": (None, None), "winner": None},
                    },
                    "elite_8": {"S1": {"teams": (None, None), "winner": None}},
                },
                "midwest": {
                    "round_of_64": {
                        "M1": {"teams": (None, None), "winner": None},
                        "M2": {"teams": (None, None), "winner": None},
                        "M3": {"teams": (None, None), "winner": None},
                        "M4": {"teams": (None, None), "winner": None},
                        "M5": {"teams": (None, None), "winner": None},
                        "M6": {"teams": (None, None), "winner": None},
                        "M7": {"teams": (None, None), "winner": None},
                        "M8": {"teams": (None, None), "winner": None},
                    },
                    "round_of_32": {
                        "M1": {"teams": (None, None), "winner": None},
                        "M2": {"teams": (None, None), "winner": None},
                        "M3": {"teams": (None, None), "winner": None},
                        "M4": {"teams": (None, None), "winner": None},
                    },
                    "sweet_16": {
                        "M1": {"teams": (None, None), "winner": None},
                        "M2": {"teams": (None, None), "winner": None},
                    },
                    "elite_8": {"M1": {"teams": (None, None), "winner": None}},
                },
            },
            "final_4": {"FF1": {"teams": (None, None), "winner": None}, "FF2": {"teams": (None, None), "winner": None}},
            "championship": {"C1": {"teams": (None, None), "winner": None}},
        }
        self.winner = None

        self.load_initial_data(initial_data_file)
        if current_state_file:
            self.update_current_state(current_state_file)

    def load_initial_data(self, filename):
        with open(filename) as file:
            data = json.load(file)

        for region in ["east", "west", "south", "midwest"]:
            for matchup in data["regions"][region]:
                team1 = Team(matchup["t1"][0], matchup["t1"][1])
                team2 = Team(matchup["t2"][0], matchup["t2"][1])
                matchup_id = matchup["id"]
                self.matchups["regionals"][region]["round_of_64"][matchup_id]["teams"] = (team1, team2)

    def update_current_state(self, current_state_file):
        print("\n===== Loading current state... =====\n")
        with open(current_state_file) as file:
            current_state = json.load(file)

        def update_matchups(matchups, current_state, region, round_name):
            for matchup_id, winner_name in current_state.items():
                matchup = matchups["regionals"][region][round_name][matchup_id]

                if round_name != "round_of_64":
                    prev_round = {
                        "round_of_32": "round_of_64",
                        "sweet_16": "round_of_32",
                        "elite_8": "sweet_16",
                    }[round_name]
                    prev_matchup_ids = [matchup_id[:-1] + str(int(matchup_id[-1]) * 2 - i) for i in range(2)]
                    team1 = matchups["regionals"][region][prev_round][prev_matchup_ids[0]]["winner"]
                    team2 = matchups["regionals"][region][prev_round][prev_matchup_ids[1]]["winner"]
                    matchup["teams"] = (team1, team2)

                if winner_name is not None:
                    team1, team2 = matchup["teams"]
                    if team1 is not None and team1.name == winner_name:
                        winner = team1
                    elif team2 is not None and team2.name == winner_name:
                        winner = team2
                    else:
                        raise ValueError(
                            f"Winner {winner_name} != teams in matchup={matchup_id}={team1.name}, {team2.name}"
                        )
                    matchup["winner"] = winner

        for region, rounds in current_state["regions"].items():
            for round_name, winners in rounds.items():
                print(f"Updating {region} {round_name} matchups...")
                if winners:
                    update_matchups(self.matchups, winners, region, round_name)

        print("Current state update complete.")
        self.print_bracket()

    def update_winner(self, region_name=None, round_name=None, matchup_id=None, winner=None):
        if region_name is None and round_name is None and matchup_id is None:
            # Championship round
            self.matchups["championship"]["C1"]["winner"] = winner
        else:
            self.matchups["regionals"][region_name][round_name][matchup_id]["winner"] = winner

    def update_teams(self, region_name, round_name, matchup_id, winner):
        matchup = self.matchups["regionals"][region_name][round_name][matchup_id]
        if matchup["teams"][0] is None:
            matchup["teams"] = (Team(winner.name, winner.seed), matchup["teams"][1])
        else:
            matchup["teams"] = (matchup["teams"][0], Team(winner.name, winner.seed))

    def determine_starting_round(self, region_name):
        regional_rounds = ["round_of_64", "round_of_32", "sweet_16", "elite_8"]
        print(f"Determining starting round for {region_name} region...")
        for round_name in regional_rounds:
            print(f"Checking if {round_name} is completed for {region_name} region...")
            if not self.round_completed(region_name, round_name):
                print(f"Found incomplete round: {round_name}")
                return round_name
            print(f"{round_name} is completed for {region_name} region.")
        print(f"All regional rounds completed for {region_name} region.")
        return "final_4"

    def round_completed(self, region, round_name):
        matchups = self.matchups["regionals"][region][round_name]
        for matchup in matchups.values():
            if matchup["winner"] is None:
                return False
        return True

    def get_matchups(self, region_name, round_name):
        return self.matchups["regionals"][region_name][round_name]

    def get_final_four(self):
        return self.matchups["final_4"]

    def update_final_four(self, ff_matchup_id, winner):
        if ff_matchup_id not in ["FF1", "FF2"]:
            raise ValueError(f"Invalid Final Four matchup ID: {ff_matchup_id}")

        matchup = self.matchups["final_4"][ff_matchup_id]
        if matchup["teams"][0] is None:
            matchup["teams"] = (winner, matchup["teams"][1])
        else:
            matchup["teams"] = (matchup["teams"][0], winner)

    def get_championship(self):
        return self.matchups["championship"]["C1"]["teams"]

    def update_championship(self, teams):
        self.matchups["championship"]["C1"]["teams"] = teams

    def get_winner(self):
        return self.matchups["championship"]["C1"]["winner"]

    def print_bracket(self):
        for region, rounds in self.matchups["regionals"].items():
            print(colored(f"\n{region.capitalize()} Region:", "blue", attrs=["bold"]))
            for round_name, matchups in rounds.items():
                print(colored(f"  {round_name.replace('_', ' ').title()}:", "magenta"))
                for matchup_id, matchup in matchups.items():
                    team1, team2 = matchup["teams"]
                    winner = matchup["winner"]
                    if team1 is None:
                        team1_info = "TBD"
                    else:
                        team1_info = colored(f"{team1.name} ({team1.seed})", "cyan")
                    if team2 is None:
                        team2_info = "TBD"
                    else:
                        team2_info = colored(f"{team2.name} ({team2.seed})", "cyan")
                    if winner is not None:
                        winner_info = colored(f"Winner: {winner.name} ({winner.seed})", "green")
                    else:
                        winner_info = colored("Winner: TBD", "red")
                    print(f"    {matchup_id}: {team1_info} vs. {team2_info} - {winner_info}")


if __name__ == "__main__":
    bracket = Bracket("bracket_2024.json")
    print("Initial bracket data loaded.")
    print("\nBracket after loading initial data:")
    bracket.print_bracket()

    bracket.update_current_state("current_state.json")
    print("\nBracket after updating current state:")
    bracket.print_bracket()

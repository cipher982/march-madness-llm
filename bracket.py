import json


class BracketData:
    def __init__(self, initial_data_file, current_state_file=None):
        self.matchups = {
            "regionals": {
                "east": {
                    "round_of_64": {},
                    "round_of_32": {},
                    "sweet_16": {},
                    "elite_8": {},
                },
                "west": {
                    "round_of_64": {},
                    "round_of_32": {},
                    "sweet_16": {},
                    "elite_8": {},
                },
                "south": {
                    "round_of_64": {},
                    "round_of_32": {},
                    "sweet_16": {},
                    "elite_8": {},
                },
                "midwest": {
                    "round_of_64": {},
                    "round_of_32": {},
                    "sweet_16": {},
                    "elite_8": {},
                },
            },
            "final_4": {},
            "championship": {},
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
                self.matchups["regionals"][region]["round_of_64"][matchup["id"]] = (matchup["t1"][0], matchup["t2"][0])

    def update_current_state(self, current_state_file):
        print("\n===== Loading current state... =====\n")
        with open(current_state_file) as file:
            current_state = json.load(file)

        def update_matchups(matchups, current_state, region, round_name):
            for matchup_id, winner in current_state.items():
                if winner is not None:
                    matchups["regionals"][region][round_name][matchup_id] = (winner,)

        for region, rounds in current_state["regions"].items():
            for round_name, winners in rounds.items():
                if winners:
                    update_matchups(self.matchups, winners, region, round_name)

        print("Current state update complete.")

    def round_completed(self, region, round_name):
        expected_matchups = {
            "round_of_64": 8,
            "round_of_32": 4,
            "sweet_16": 2,
            "elite_8": 1,
        }
        matchups = self.matchups["regionals"][region][round_name]
        if len(matchups) != expected_matchups[round_name]:
            return False
        for matchup in matchups.values():
            if len(matchup) != 1:
                return False
        return True

    def get_matchups(self, region_name, round_name):
        return self.matchups["regionals"][region_name][round_name]

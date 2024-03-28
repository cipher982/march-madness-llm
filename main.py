import argparse
import asyncio
from deciders import ai_wizard, best_seed, random_winner
from termcolor import colored
from bracket import Bracket

ROUND_NAMES = ["round_of_64", "round_of_32", "sweet_16", "elite_8", "final_4", "championship"]


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Simulator:
    def __init__(self, bracket):
        self.bracket = bracket

    async def simulate_match(self, team1, team2, decision_function, played=False):
        region_name, round_name, matchup_id = self.bracket.get_matchup_id(team1, team2)
        if matchup_id is not None:
            winner = self.bracket.get_match_winner(region_name, round_name, matchup_id)
            if winner is not None:
                return Team(winner[0], winner[1])
        winner = await decision_function(team1, team2)
        self.print_match_summary(team1, team2, winner, played)
        return winner

    def print_match_summary(self, team1, team2, winner, played=False):
        if played:
            print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed}) - Already Played", "yellow"))
        else:
            print(colored(f"{team1.name} ({team1.seed}) vs {team2.name} ({team2.seed})", "cyan"))
        print(colored(f"Winner: {winner.name}\n", "green"))

    async def simulate_round(self, decision_function, region_name, round_name):
        matchups = self.bracket.get_matchups(region_name, round_name)
        assert matchups is not None, f"no matchups: {region_name}, {round_name}"
        round_results = []

        for matchup_id, matchup in matchups.items():
            teams = matchup.get("teams")
            if teams[0] is None and teams[1] is None:
                print(f"Skipping matchup {matchup_id} due to missing teams.")
                continue
            elif teams[0] is None or teams[1] is None:
                raise Exception(f"Invalid matchup: {matchup}, team1: {teams[0]}, team2: {teams[1]}")
            else:
                winner = await self.simulate_match(teams[0], teams[1], decision_function)
                round_results.append((matchup_id, winner))
                self.bracket.update_winner(region_name, round_name, matchup_id, (winner.name, winner.seed))

        next_round = {
            "round_of_64": "round_of_32",
            "round_of_32": "sweet_16",
            "sweet_16": "elite_8",
            "elite_8": None,
        }[round_name]

        if next_round is not None:
            for matchup_id, winner in round_results:
                next_matchup_id = matchup_id[:-1] + str((int(matchup_id[-1]) + 1) // 2)
                self.bracket.update_teams(region_name, next_round, next_matchup_id, winner)

        return round_results

    async def simulate_region(self, decision_function, region_name, starting_round=None):
        if starting_round is None:
            starting_round = "round_of_64"

        starting_index = ROUND_NAMES.index(starting_round)
        for round_name in ROUND_NAMES[starting_index:4]:
            print(colored(f"\nSimulating {round_name} for {region_name} region...", "yellow"))
            round_results = await self.simulate_round(decision_function, region_name, round_name)
            print(colored(f"{region_name} {round_name} results:", "green"))
            for matchup_id, winner in round_results:
                print(colored(f"Matchup {matchup_id}: {winner.name}", "green"))
                self.bracket.update_winner(region_name, round_name, matchup_id, (winner.name, winner.seed))

            if round_name == "elite_8":
                if len(round_results) > 0:
                    print(colored(f"\n{region_name} region winner: {round_results[0][1].name}", "magenta"))
                    return round_results[0][1]
                else:
                    print(colored(f"\n{region_name} region winner: Not determined", "red"))
                    return None

    async def simulate_final_four(self, decision_function):
        print(colored("\nSimulating Final Four...", "yellow"))
        matchups = self.bracket.get_final_four()
        final_four_results = []

        for matchup_id, matchup in matchups.items():
            team1, team2 = matchup["teams"]
            if team1 is None or team2 is None:
                print(colored(f"Skipping {matchup_id} due to missing team(s).", "red"))
                continue
            winner = await self.simulate_match(team1, team2, decision_function)
            final_four_results.append(winner)
            self.bracket.update_final_four(matchup_id, winner)

        print(colored("Final Four results:", "green"))
        for team in final_four_results:
            print(colored(f"{team.name}", "green"))

        self.bracket.update_championship(
            (
                (final_four_results[0].name, final_four_results[0].seed),
                (final_four_results[1].name, final_four_results[1].seed),
            )
        )

    async def simulate_championship(self, decision_function):
        print(colored("\nSimulating Championship...", "yellow"))
        matchup = self.bracket.get_championship()
        team1 = Team(matchup[0][0], matchup[0][1])
        team2 = Team(matchup[1][0], matchup[1][1])
        winner = await self.simulate_match(team1, team2, decision_function)
        print(colored(f"\nChampionship winner: {winner.name}", "magenta"))
        self.bracket.update_winner(winner=(winner.name, winner.seed))

    async def simulate_tournament(self, decision_function):
        print(colored("Starting NCAA March Madness Bracket Simulation...\n", "yellow"))

        elite_eight_winners = []
        for region in ["east", "west", "south", "midwest"]:
            starting_round = None
            print(colored(f"Simulating {region} region...", "yellow"))
            print(colored(f"Starting round: {starting_round}", "green"))
            winner = await self.simulate_region(decision_function, region, starting_round)
            elite_eight_winners.append(winner)

        for i, winner in enumerate(elite_eight_winners):
            if winner is not None:
                self.bracket.update_final_four(f"FF{i // 2 + 1}", winner)

        await self.simulate_final_four(decision_function)
        await self.simulate_championship(decision_function)

        winner = self.bracket.get_tournament_winner()
        if winner is not None:
            print(colored(f"\nTournament winner: {winner[0]} ({winner[1]})", "magenta"))
        else:
            print(colored("\nTournament winner: Not determined", "red"))


def main():
    parser = argparse.ArgumentParser(description="NCAA March Madness Bracket Simulator")
    parser.add_argument(
        "--decider",
        type=str,
        default="seed",
        choices=["ai", "seed", "random"],
        help="Decision function to use for simulating games (default: seed)",
    )
    parser.add_argument(
        "--current-state",
        type=str,
        default=None,
        help="JSON file containing the current state of the bracket",
    )
    args = parser.parse_args()
    decision_functions = {"ai": ai_wizard, "seed": best_seed, "random": random_winner}
    decision_function = decision_functions[args.decider]
    bracket = Bracket("bracket_2024.json")
    simulator = Simulator(bracket)
    if args.current_state:
        print(colored("Loading current state...", "yellow"))
        simulator.bracket.update_current_state(args.current_state)
        print(colored("Current state loaded.", "green"))
    asyncio.run(simulator.simulate_tournament(decision_function))


if __name__ == "__main__":
    main()

import argparse
import asyncio
from deciders import ai_wizard, best_seed, random_winner
from termcolor import colored
from bracket import create_empty_bracket, Team

ROUND_NAMES = ["round_of_64", "round_of_32", "sweet_16", "elite_8", "final_4", "championship"]


class Simulator:
    def __init__(self, bracket):
        self.bracket = bracket

    async def simulate_match(self, team1, team2, decision_function, played=False):
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
        assert matchups, f"no matchups: {region_name}, {round_name}"
        round_results = []

        for matchup_id, matchup in matchups.items():
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None and team2 is None:
                print(f"Skipping matchup {matchup_id} due to missing teams.")
                continue
            elif team1 is None or team2 is None:
                raise Exception(f"Invalid matchup: {matchup}, team1: {team1}, team2: {team2}")
            else:
                winner = await self.simulate_match(team1, team2, decision_function)
                round_results.append((matchup_id, winner))
                self.bracket.update_matchup_winner(region_name, round_name, matchup_id, Team(winner.name, winner.seed))
        next_round = self.bracket.get_next_round_name(round_name)
        print(self.bracket)
        if next_round is not None:
            current_round = self.bracket.get_round_by_name(region_name, round_name)
            next_round_obj = self.bracket.get_round_by_name(region_name, next_round)
            self.bracket.create_next_round_matchups(current_round, next_round_obj)
        return round_results

    async def simulate_region(self, decision_function, region_name, starting_round=None):
        if starting_round is None:
            starting_round = "round_of_64"

        starting_index = ROUND_NAMES.index(starting_round)
        for round_name in ROUND_NAMES[starting_index:4]:
            print(colored(f"\nSimulating {round_name} for {region_name} region...", "yellow"))
            round_results = await self.simulate_round(decision_function, region_name, round_name)
            print(colored(f"{region_name} {round_name} results:", "green"))
            # for matchup_id, winner in round_results:
            # print(colored(f"Matchup {matchup_id}: {winner.name}", "green"))
            # self.bracket.update_matchup_winner(region_name, round_name, matchup_id, Team(winner.name, winner.seed))

            if round_name == "elite_8":
                if len(round_results) > 0:
                    print(colored(f"\n{region_name} region winner: {round_results[0][1].name}", "magenta"))
                    return round_results[0][1]
                else:
                    print(colored(f"\n{region_name} region winner: Not determined", "red"))
                    return None

    async def simulate_final_four(self, decision_function):
        print(colored("\nSimulating Final Four...", "yellow"))
        matchups = self.bracket.final_four.matchups
        final_four_results = []

        for matchup in matchups:
            team1, team2 = matchup.team1, matchup.team2
            if team1 is None or team2 is None:
                print(colored(f"Skipping {matchup.matchup_id} due to missing team(s).", "red"))
                continue
            winner = await self.simulate_match(team1, team2, decision_function)
            self.bracket.update_matchup_winner(None, "final_4", matchup.matchup_id, winner)
            final_four_results.append(winner)
            self.bracket.update_final_four_and_championship()

        print(colored("Final Four results:", "green"))
        for team in final_four_results:
            print(colored(f"{team.name}", "green"))

    async def simulate_championship(self, decision_function):
        print(colored("\nSimulating Championship...", "yellow"))
        matchup = self.bracket.championship
        team1, team2 = matchup.team1, matchup.team2
        winner = await self.simulate_match(team1, team2, decision_function)
        self.bracket.update_matchup_winner(None, "championship", matchup.matchup_id, winner)
        print(colored(f"\nChampionship winner: {winner.name}", "magenta"))

    async def simulate_tournament(self, decision_function):
        print(colored("Starting NCAA March Madness Bracket Simulation...\n", "yellow"))

        elite_eight_winners = []
        for region in ["east", "west", "south", "midwest"]:
            starting_round = None
            print(colored(f"Simulating {region} region...", "yellow"))
            print(colored(f"Starting round: {starting_round}", "green"))
            winner = await self.simulate_region(decision_function, region, starting_round)
            elite_eight_winners.append(winner)
        self.bracket.update_final_four_and_championship()

        await self.simulate_final_four(decision_function)
        await self.simulate_championship(decision_function)

        winner = self.bracket.get_tournament_winner()
        print(colored(f"\nTournament winner: {winner.name} ({winner.seed})", "magenta"))


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

    # Create bracket with data
    bracket = create_empty_bracket()
    bracket.load_initial_data("bracket_2024.json")
    if args.current_state:
        print(colored("Loading current state...", "yellow"))
        bracket.load_current_state(args.current_state)
        print(colored("Current state loaded.", "green"))

    print(bracket)

    # Simulate tournament
    simulator = Simulator(bracket)
    asyncio.run(simulator.simulate_tournament(decision_function))


if __name__ == "__main__":
    main()

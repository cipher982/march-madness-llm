import argparse
import asyncio
from deciders import ai_wizard, best_seed, random_winner
from termcolor import colored
from bracket import BracketData

ROUND_NAMES = ["round_of_64", "round_of_32", "sweet_16", "elite_8", "final_4", "championship"]


class Team:
    def __init__(self, name, seed):
        self.name = name
        self.seed = seed


class Bracket:
    def __init__(self, bracket_data):
        self.bracket_data = bracket_data

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
        matchups = self.bracket_data.get_matchups(region_name, round_name)
        round_results = []

        for matchup_id, matchup in matchups.items():
            if matchup[0] is not None and matchup[1] is not None:
                team1 = Team(matchup[0][0], matchup[0][1])
                team2 = Team(matchup[1][0], matchup[1][1])
                winner = await self.simulate_match(team1, team2, decision_function)
                round_results.append((matchup_id, winner))
            elif matchup[0] is not None:
                team = Team(matchup[0][0], matchup[0][1])
                round_results.append((matchup_id, team))
                await self.simulate_match(team, team, decision_function, played=True)

        return round_results

    async def simulate_region(self, decision_function, region_name):
        for round_name in ROUND_NAMES[:4]:
            print(colored(f"\nSimulating {round_name} for {region_name} region...", "yellow"))
            round_results = await self.simulate_round(decision_function, region_name, round_name)
            print(colored(f"{region_name} {round_name} results:", "green"))
            for matchup_id, winner in round_results:
                print(colored(f"Matchup {matchup_id}: {winner.name}", "green"))
                self.bracket_data.update_winner(region_name, round_name, matchup_id, (winner.name, winner.seed))

            if round_name == "elite_8":
                print(colored(f"\n{region_name} region winner: {round_results[0][1].name}", "magenta"))

    async def simulate_final_four(self, decision_function):
        print(colored("\nSimulating Final Four...", "yellow"))
        matchups = self.bracket_data.get_final_four()
        final_four_results = []

        for matchup_id, matchup in matchups.items():
            if matchup[0] is not None and matchup[1] is not None:
                team1 = Team(matchup[0][0], matchup[0][1])
                team2 = Team(matchup[1][0], matchup[1][1])
                winner = await self.simulate_match(team1, team2, decision_function)
                final_four_results.append(winner)
                self.bracket_data.update_final_four(matchup_id, ((winner.name, winner.seed),))

        print(colored("Final Four results:", "green"))
        for team in final_four_results:
            print(colored(f"{team.name}", "green"))

        self.bracket_data.update_championship(
            (
                (final_four_results[0].name, final_four_results[0].seed),
                (final_four_results[1].name, final_four_results[1].seed),
            )
        )

    async def simulate_championship(self, decision_function):
        print(colored("\nSimulating Championship...", "yellow"))
        matchup = self.bracket_data.get_championship()
        team1 = Team(matchup[0][0], matchup[0][1])
        team2 = Team(matchup[1][0], matchup[1][1])
        winner = await self.simulate_match(team1, team2, decision_function)
        print(colored(f"\nChampionship winner: {winner.name}", "magenta"))
        self.bracket_data.update_winner(winner.name)

    async def simulate_tournament(self, decision_function):
        print(colored("Starting NCAA March Madness Bracket Simulation...\n", "yellow"))

        for region in ["east", "west", "south", "midwest"]:
            await self.simulate_region(decision_function, region)

        await self.simulate_final_four(decision_function)
        await self.simulate_championship(decision_function)

        print(colored(f"\nTournament winner: {self.bracket_data.get_winner()}", "magenta"))


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
    bracket_data = BracketData("bracket_2024.json")
    bracket = Bracket(bracket_data)
    if args.current_state:
        bracket_data.update_current_state(args.current_state)
    asyncio.run(bracket.simulate_tournament(decision_function))


if __name__ == "__main__":
    main()

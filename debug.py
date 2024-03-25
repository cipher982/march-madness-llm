from bracket import BracketData


def main():
    initial_data_file = "bracket_2024.json"
    current_state_file = "current_state.json"

    bracket = BracketData(initial_data_file)
    print("Initial bracket data loaded.")

    print("\nBracket after loading initial data:")
    print_matchups(bracket.matchups)

    bracket.update_current_state(current_state_file)

    print("\nBracket after updating current state:")
    print_matchups(bracket.matchups)


def print_matchups(matchups, indent=0):
    for key, value in matchups.items():
        if isinstance(value, dict):
            print(" " * indent + str(key))
            print_matchups(value, indent + 2)
        else:
            print(" " * indent + f"{key}: {value}")


if __name__ == "__main__":
    main()

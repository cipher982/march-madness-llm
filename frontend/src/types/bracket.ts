export interface Team {
  name: string;
  seed: number;
}

export interface Matchup {
  id?: string;
  team1: Team | null;
  team2: Team | null;
  winner?: Team | null;
}

export interface Round {
  name: string;
  matchups: Matchup[];
}

export interface Region {
  name: string;
  rounds: Round[];
}

export interface BracketData {
  regions: Region[];
  finalFour: {
    name: string;
    matchups: Matchup[];
  };
  championship: Matchup;
}

export interface SimulationStatusData {
  region: string;
  round: string;
  current_matchup: Matchup | null;
  current_winner: Team | null;
}

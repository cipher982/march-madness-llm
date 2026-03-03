import React from "react";

import MatchupCard from "./MatchupCard";
import { SimulationStatusData } from "../types/bracket";

const ROUND_NAMES: Record<string, string> = {
  round_of_64: "Round of 64",
  round_of_32: "Round of 32",
  sweet_16: "Sweet 16",
  elite_8: "Elite 8",
  final_4: "Final Four",
  championship: "Championship",
};

interface SimulationStatusProps {
  simulationStatus: SimulationStatusData;
}

const SimulationStatus = ({ simulationStatus }: SimulationStatusProps) => {
  const { region, round, current_matchup: currentMatchup, current_winner: currentWinner } = simulationStatus;

  return (
    <div>
      <p>Current Region: {region ? `${region.charAt(0).toUpperCase()}${region.slice(1)}` : ""}</p>
      <p>Current Round: {round ? ROUND_NAMES[round] ?? round : ""}</p>
      {currentMatchup && (
        <div>
          <h4>Current Matchup:</h4>
          <MatchupCard matchup={currentMatchup} />
        </div>
      )}
      {currentMatchup && currentWinner && (
        <div>
          <h4>Winner:</h4>
          <p>{currentWinner.name}</p>
        </div>
      )}
    </div>
  );
};

export default SimulationStatus;

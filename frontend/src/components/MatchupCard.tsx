import React from "react";

import { TeamLogo } from "./TeamLogo";
import { Matchup, Team } from "../types/bracket";

interface MatchupCardProps {
  matchup: Matchup;
}

const TeamRow = ({ team, isWinner }: { team: Team | null; isWinner: boolean }) => {
  if (!team) {
    return <div className="team-info">TBD</div>;
  }

  return (
    <div className={`team-info ${isWinner ? "winner" : ""}`}>
      <TeamLogo teamName={team.name} size={30} />
      <span className="team-name">{team.name}</span>
      <span className="team-seed">({team.seed})</span>
    </div>
  );
};

const MatchupCard = ({ matchup }: MatchupCardProps) => {
  const { team1, team2, winner } = matchup;

  return (
    <div className="matchup-card">
      <TeamRow team={team1} isWinner={Boolean(winner && team1 && winner.name === team1.name)} />
      <div className="vs-text">VS</div>
      <TeamRow team={team2} isWinner={Boolean(winner && team2 && winner.name === team2.name)} />
    </div>
  );
};

export default MatchupCard;

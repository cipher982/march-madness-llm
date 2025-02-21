import React from "react";
import { TeamLogo } from "./TeamLogo.tsx";

const MatchupCard = ({ matchup }) => {
    const { team1, team2, winner } = matchup;

    return (
        <div className="matchup-card">
            <div className={`team-info ${winner?.name === team1?.name ? "winner" : ""}`}>
                <TeamLogo teamName={team1.name} size={30} />
                <span className="team-name">{team1.name}</span>
                <span className="team-seed">({team1.seed})</span>
            </div>
            <div className="vs-text">VS</div>
            <div className={`team-info ${winner?.name === team2?.name ? "winner" : ""}`}>
                <TeamLogo teamName={team2.name} size={30} />
                <span className="team-name">{team2.name}</span>
                <span className="team-seed">({team2.seed})</span>
            </div>
        </div>
    );
};

export default MatchupCard;
import React from 'react';

const MatchupCard = ({ matchup }) => {
    const { team1, team2, winner } = matchup;

    return (
        <div className="matchup-card">
            <div className={`team-info ${winner === team1 ? 'winner' : ''}`}>
                {/* <img src={team1.logo} alt={team1.name} className="team-logo" /> */}
                <span className="team-name">{team1.name}</span>
                <span className="team-seed">({team1.seed})</span>
            </div>
            <div className="vs-text">VS</div>
            <div className={`team-info ${winner === team2 ? 'winner' : ''}`}>
                {/* <img src={team2.logo} alt={team2.name} className="team-logo" /> */}
                <span className="team-name">{team2.name}</span>
                <span className="team-seed">({team2.seed})</span>
            </div>
        </div>
    );
};

export default MatchupCard;
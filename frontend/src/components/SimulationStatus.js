import React from 'react';
import { roundNames } from './BracketDisplay';
import MatchupCard from './MatchupCard';

const SimulationStatus = ({ simulationStatus }) => {
    const { region, round, current_matchup, current_winner } = simulationStatus;

    return (
        <div>
            <p>Current Region: {region ? region.charAt(0).toUpperCase() + region.slice(1) : ''}</p>
            <p>Current Round: {round ? roundNames[round] : ''}</p>
            {current_matchup && (
                <div>
                    <h4>Current Matchup:</h4>
                    <MatchupCard matchup={current_matchup} />
                </div>
            )}
            {current_matchup && current_winner && (
                <div>
                    <h4>Winner:</h4>
                    <p>{current_winner.name}</p>
                </div>
            )}
        </div>
    );
};

export default SimulationStatus;

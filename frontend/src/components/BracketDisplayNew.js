import React from 'react';
import { SingleEliminationBracket, SVGViewer } from '@g-loot/react-tournament-brackets';

const adaptData = (bracket) => {
    // This is a simplified example. You'll need to adapt it based on your actual data structure.
    return bracket.regions.flatMap(region =>
        region.rounds.map(round => ({
            id: round.id,
            name: round.name,
            participants: [
                { id: round.matchups[0].team1.id, name: round.matchups[0].team1.name },
                { id: round.matchups[0].team2.id, name: round.matchups[0].team2.name }
            ],
            state: round.matchups[0].winner ? 'finished' : 'pending',
            result: {
                winnerId: round.matchups[0].winner?.id,
                score: [round.matchups[0].team1Score, round.matchups[0].team2Score]
            }
        }))
    );
};

const BracketDisplay = ({ bracket }) => {
    if (!bracket) {
        return <div>No bracket data available</div>;
    }

    const adaptedData = adaptData(bracket);

    return (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
            <SVGViewer width={1000} height={600}>
                <SingleEliminationBracket matches={adaptedData} />
            </SVGViewer>
        </div>
    );
};

export default BracketDisplay;
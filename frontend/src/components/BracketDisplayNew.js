import React from 'react';
import { SingleEliminationBracket, SVGViewer } from '@g-loot/react-tournament-brackets';

const getMatchId = (region, round, matchIndex) => {
    const regionCode = region.name.slice(0, 1).toUpperCase();
    const roundCode = round.name.split('_').map(word => word.slice(0, 1)).join('').toUpperCase();
    return `${regionCode}_${roundCode}_M${matchIndex + 1}`;
};

const adaptData = (bracket) => {
    const adaptedData = bracket.regions.flatMap((region) =>
        region.rounds.map((round) => {
            const roundMatchups = round.matchups.map((matchup, matchIndex) => {
                const participants = [
                    {
                        id: matchup.team1.name,
                        name: matchup.team1.name,
                        resultText: matchup.winner?.name === matchup.team1.name ? 'WON' : null,
                        isWinner: matchup.winner?.name === matchup.team1.name,
                        status: matchup.winner ? 'PLAYED' : null,
                    },
                    {
                        id: matchup.team2.name,
                        name: matchup.team2.name,
                        resultText: matchup.winner?.name === matchup.team2.name ? 'WON' : null,
                        isWinner: matchup.winner?.name === matchup.team2.name,
                        status: matchup.winner ? 'PLAYED' : null,
                    },
                ];

                const match = {
                    id: getMatchId(region, round, matchIndex),
                    name: `${round.name} - Match`,
                    nextMatchId: null,
                    tournamentRoundText: round.name,
                    startTime: '',
                    state: matchup.winner ? 'DONE' : 'NO_SHOW',
                    participants,
                };

                return match;
            });

            return roundMatchups;
        })
    ).flat();

    // Add nextMatchId for each match
    adaptedData.forEach((match, index) => {
        const nextMatchIndex = Math.floor(index / 2);
        if (nextMatchIndex < adaptedData.length / 2) {
            match.nextMatchId = adaptedData[nextMatchIndex].id;
        }
    });

    return adaptedData;
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
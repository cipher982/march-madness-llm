export const roundNames = {
    "round_of_64": "Round of 64",
    "round_of_32": "Round of 32",
    "sweet_16": "Sweet 16",
    "elite_8": "Elite 8",
    "final_four": "Final Four",
    "championship": "Championship",
};


const TeamDisplay = ({ team }) => {
    if (!team) return 'TBD';
    const { name, seed } = team;
    return `${name} (${seed})`;
};

const MatchupDisplay = ({ matchup }) => {
    const { team1, team2, winner } = matchup;

    return (
        <div>
            <p>
                {winner?.name === team1?.name ? (
                    <strong>{TeamDisplay({ team: team1 })}</strong>
                ) : (
                    TeamDisplay({ team: team1 })
                )}
                {' vs '}
                {winner?.name === team2?.name ? (
                    <strong>{TeamDisplay({ team: team2 })}</strong>
                ) : (
                    TeamDisplay({ team: team2 })
                )}
            </p>
        </div>
    );
};
const BracketDisplay = ({ bracket }) => {
    if (!bracket) {
        return <div>No bracket data available.</div>;
    }

    return (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ maxWidth: '1000px', padding: '20px' }}>
                <div style={{ fontSize: '13px' }}>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <h2>Bracket</h2>
                    </div>
                    {bracket && (
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                {bracket.regions.map((region, index) => (
                                    <div key={index} style={{ flex: '1', marginRight: '20px' }}>
                                        <h3>{region.name.charAt(0).toUpperCase() + region.name.slice(1)}</h3>
                                        {region.rounds.map((round, roundIndex) => (
                                            <div key={roundIndex}>
                                                <h4>{roundNames[round.name]}</h4>
                                                {round.matchups.map((matchup, matchupIndex) => (
                                                    <MatchupDisplay key={matchupIndex} matchup={matchup} />
                                                ))}
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>

                            <div style={{ marginTop: '40px' }}>
                                <h3>Final Four</h3>
                                <div style={{ display: 'flex', justifyContent: 'center' }}>
                                    {bracket.finalFour.matchups.map((matchup, index) => (
                                        <div key={index} style={{ marginRight: '20px' }}>
                                            <MatchupDisplay matchup={matchup} />
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div style={{ marginTop: '20px' }}>
                                <h3>Championship</h3>
                                <div style={{ display: 'flex', justifyContent: 'center' }}>
                                    <MatchupDisplay matchup={bracket.championship} />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BracketDisplay;
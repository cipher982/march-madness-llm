import React, { useEffect, useState } from 'react';
import api from '../api';

const BracketDisplay = () => {
    const [bracket, setBracket] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchBracket = async () => {
            try {
                const response = await api.get('/bracket_start');
                setBracket(response.data.bracket);
                setLoading(false);
            } catch (error) {
                console.error('Error fetching bracket:', error);
                setError('Failed to fetch bracket data');
                setLoading(false);
            }
        };

        fetchBracket();
    }, []);

    if (loading) {
        return <div>Loading bracket...</div>;
    }

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div style={{ maxWidth: '1400px', padding: '20px' }}>
                <div style={{ fontSize: '16px' }}>
                    <h2>Initial Bracket</h2>
                    {bracket && (
                        <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                {bracket.regions.map((region, index) => (
                                    <div key={index} style={{ flex: '1', marginRight: '20px' }}>
                                        <h3>{region.name}</h3>
                                        {region.rounds.map((round, roundIndex) => (
                                            <div key={roundIndex}>
                                                <h4>{round.name}</h4>
                                                {round.matchups.map((matchup, matchupIndex) => (
                                                    <div key={matchupIndex}>
                                                        <p>
                                                            {matchup.team1 ? `${matchup.team1.name} (${matchup.team1.seed})` : 'TBD'}
                                                            {' vs '}
                                                            {matchup.team2 ? `${matchup.team2.name} (${matchup.team2.seed})` : 'TBD'}
                                                        </p>
                                                        {matchup.winner && (
                                                            <p>Winner: {matchup.winner.name}</p>
                                                        )}
                                                    </div>
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
                                            <p>
                                                {matchup.team1 ? `${matchup.team1.name} (${matchup.team1.seed})` : 'TBD'}
                                                {' vs '}
                                                {matchup.team2 ? `${matchup.team2.name} (${matchup.team2.seed})` : 'TBD'}
                                            </p>
                                            {matchup.winner && (
                                                <p>Winner: {matchup.winner.name}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div style={{ marginTop: '20px' }}>
                                <h3>Championship</h3>
                                <div style={{ display: 'flex', justifyContent: 'center' }}>
                                    <p>
                                        {bracket.championship.team1 ? `${bracket.championship.team1.name} (${bracket.championship.team1.seed})` : 'TBD'}
                                        {' vs '}
                                        {bracket.championship.team2 ? `${bracket.championship.team2.name} (${bracket.championship.team2.seed})` : 'TBD'}
                                    </p>
                                    {bracket.championship.winner && (
                                        <p>Winner: {bracket.championship.winner.name}</p>
                                    )}
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


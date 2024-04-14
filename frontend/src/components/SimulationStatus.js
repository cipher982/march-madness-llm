import React, { useState, useEffect } from 'react';
import { roundNames } from './BracketDisplay';
import BracketDisplay from './BracketDisplay';
import MatchupCard from './MatchupCard';
import api from '../api';

const SimulationStatus = () => {
    const [simulationStatus, setSimulationStatus] = useState({
        bracket: null,
        region: "",
        round: "",
        current_matchup: null,
        current_winner: null,
    });

    useEffect(() => {
        const fetchSimulationStatus = async () => {
            try {
                const response = await api.get("/simulation_status");
                const { bracket, region, round, current_matchup, current_winner } = response.data;
                console.log("Fetched simulation status:", response.data);
                setSimulationStatus({ bracket, region, round, current_matchup, current_winner });
                console.log("Current winner:", current_winner);
            } catch (error) {
                console.error("Error fetching simulation status:", error);
            }
        };

        console.log("Starting simulation status polling");
        const intervalId = setInterval(fetchSimulationStatus, 500);

        return () => {
            console.log("Stopping simulation status polling");
            clearInterval(intervalId);
        };
    }, []);

    console.log("Returning simulated status: ", simulationStatus)
    return (
        <div>
            <p>Current Region: {simulationStatus.region.charAt(0).toUpperCase() + simulationStatus.region.slice(1)}</p>
            <p>Current Round: {roundNames[simulationStatus.round]}</p>
            {simulationStatus.current_matchup && (
                <div>
                    <h4>Current Matchup:</h4>
                    <MatchupCard matchup={simulationStatus.current_matchup} />
                </div>
            )}
            {simulationStatus.current_matchup && simulationStatus.current_winner && (
                <div>
                    <h4>Winner:</h4>
                    <p>{simulationStatus.current_winner.name}</p>
                </div>
            )}
            {/* <BracketDisplay bracket={simulationStatus.bracket} /> */}
        </div>
    );
};
export default SimulationStatus;
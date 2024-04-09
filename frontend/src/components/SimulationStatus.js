import React, { useState, useEffect } from 'react';
import api from '../api';

const SimulationStatus = () => {
    const [simulationStatus, setSimulationStatus] = useState({ region: '', round: '' });

    useEffect(() => {
        const fetchSimulationStatus = async () => {
            try {
                const response = await api.get('/simulation_status');
                setSimulationStatus(response.data);
            } catch (error) {
                console.error('Error fetching simulation status:', error);
            }
        };

        const intervalId = setInterval(fetchSimulationStatus, 1000); // Fetch status every 1 second

        return () => {
            clearInterval(intervalId); // Clean up the interval on component unmount
        };
    }, []);

    return (
        <div>
            <p>Current Region: {simulationStatus.region}</p>
            <p>Current Round: {simulationStatus.round}</p>
        </div>
    );
};

export default SimulationStatus;
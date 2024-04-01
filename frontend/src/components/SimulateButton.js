import React, { useState } from "react";
import api from "../api";

console.log('simulatebutton.js file loaded');

const SimulateButton = ({ onSimulationComplete }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSimulate = async () => {
        const decider = "random";
        const currentState = "";

        try {
            setIsLoading(true);
            const response = await api.post("/simulate", {
                decider: decider,
                current_state: currentState,
            });
            console.log("Response data from backend:", response.data);
            onSimulationComplete(response.data.results);
        } catch (error) {
            console.error(error);
            // Handle the error, display an error message, etc.
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <button onClick={handleSimulate} disabled={isLoading}>
            {isLoading ? "Simulating..." : "Simulate Tournament"}
        </button>
    );
};

export default SimulateButton;
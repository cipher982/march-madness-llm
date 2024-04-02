import React, { useState } from "react";
import api from "../api";

console.log('simulatebutton.js file loaded');

const SimulateButton = ({ onSimulationComplete, onError, decider, apiKey }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSimulate = async () => {
        const useCurrentState = false;

        try {
            setIsLoading(true);
            const response = await api.post("/simulate", {
                decider: decider,
                use_current_state: useCurrentState,
                api_key: apiKey,
            });
            console.log("Response data from backend:", response.data);
            if (response.data.bracket.championship.winner) {
                onSimulationComplete(response.data.results, response.data.bracket);
            } else {
                throw new Error("Championship winner is missing");
            }
        } catch (error) {
            console.error(error);
            onError(error.response?.data?.message || "An error occurred");
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
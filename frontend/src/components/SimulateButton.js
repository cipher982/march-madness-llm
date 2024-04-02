import React, { useState } from "react";
import api from "../api";

console.log('simulatebutton.js file loaded');

const SimulateButton = ({ onSimulationComplete, onError, decider }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSimulate = async () => {
        const currentState = "";

        try {
            setIsLoading(true);
            const response = await api.post("/simulate", {
                decider: decider,
                current_state: currentState,
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
import React, { useState } from "react";
import axios from "axios";

const SimulateButton = ({ onSimulationComplete }) => {
    const [isLoading, setIsLoading] = useState(false);

    const handleSimulate = async () => {
        const decider = "random";
        const currentState = "";

        try {
            setIsLoading(true);
            const response = await axios.post("/simulate", {
                decider: decider,
                current_state: currentState,
            });
            // Pass the results array directly to the onSimulationComplete callback
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
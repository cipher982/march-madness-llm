import React from "react";
import api from "../api";

const SimulateButton = ({ onSimulationStart, onSimulationComplete, onError, decider, apiKey, userPreferences, isSimulating }) => {
    const handleClick = async () => {
        const useCurrentState = false;

        if (decider === "ai") {
            if (!apiKey || !apiKey.startsWith("sk-") || apiKey.length < 20) {
                onError("Does not look like a valid key to me 👎");
                return;
            }
        }

        try {
            onSimulationStart();
            const response = await api.post("/simulate", {
                decider: decider,
                use_current_state: useCurrentState,
                api_key: apiKey,
                user_preferences: userPreferences,
            });
            console.log("Response data from backend:", response.data);

            // Start polling for the simulation results
            const pollInterval = setInterval(async () => {
                try {
                    const pollResponse = await api.get("/simulation-status");
                    console.log("Poll response data:", pollResponse.data);

                    // Check if the simulation is complete
                    if (pollResponse.data.status === "complete") {
                        clearInterval(pollInterval);
                        onSimulationComplete(pollResponse.data.results, pollResponse.data.bracket);
                    }
                } catch (error) {
                    if (error.response && error.response.status === 404) {
                        // Simulation is complete, stop polling
                        clearInterval(pollInterval);
                        onSimulationComplete(null, null);
                    } else {
                        console.error("Error during polling:", error);
                        clearInterval(pollInterval);
                        onError("An error occurred while checking the simulation status");
                    }
                }
            }, 5000); // Poll every 5 seconds
        } catch (error) {
            console.error("Error during simulation:", error);
            onError("An error occurred during simulation");
        }
    };

    return (
        <button
            onClick={handleClick}
            disabled={isSimulating}
            className={`simulate-button ${isSimulating ? "simulating" : ""}`}
        >
            {isSimulating ? "Simulating..." : "Simulate"}
        </button>
    );
};

export default SimulateButton;
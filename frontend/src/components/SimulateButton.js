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
            if (response.data.bracket.championship.winner) {
                onSimulationComplete(response.data.results, response.data.bracket);
            } else {
                throw new Error("Championship winner is missing");
            }
        } catch (error) {
            console.error(error);
            onError(error.response?.data?.message || "An error occurred");
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
import React from "react";


const SimulateButton = ({ onSimulationStart, decider, apiKey, onError, userPreferences, isSimulating }) => {
    const handleClick = async () => {
        if (decider === "ai") {
            if (!apiKey || !apiKey.startsWith("sk-") || apiKey.length < 20) {
                onError("Does not look like a valid key to me 👎");
                return;
            }
        }

        onSimulationStart(decider, apiKey, userPreferences);
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
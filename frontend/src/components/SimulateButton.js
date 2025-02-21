import React from "react";


const SimulateButton = ({ onSimulationStart, decider, onError, userPreferences, isSimulating }) => {
    const handleClick = async () => {
        onSimulationStart(decider, userPreferences);
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
import React from "react";

type Decider = "random" | "seed" | "ai";

interface SimulateButtonProps {
  onSimulationStart: (decider: Decider, userPreferences: string) => void;
  decider: Decider;
  userPreferences: string;
  isSimulating: boolean;
}

const SimulateButton = ({ onSimulationStart, decider, userPreferences, isSimulating }: SimulateButtonProps) => {
  const handleClick = () => {
    onSimulationStart(decider, userPreferences);
  };

  return (
    <button onClick={handleClick} disabled={isSimulating} className={`simulate-button ${isSimulating ? "simulating" : ""}`}>
      {isSimulating ? "Simulating..." : "Simulate"}
    </button>
  );
};

export default SimulateButton;

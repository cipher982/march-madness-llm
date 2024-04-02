import React, { useState } from 'react';
import SimulateButton from './components/SimulateButton';

const App = () => {
  const [simulationResults, setSimulationResults] = useState(null);
  const [decider, setDecider] = useState("random"); // Default decider


  const handleSimulationComplete = (results) => {
    console.log('handleSimulationComplete called with results:', results);
    setSimulationResults(results);
  };

  return (
    <div>
      {/* Selector for choosing the decider */}
      <select value={decider} onChange={(e) => setDecider(e.target.value)}>
        <option value="random">Random</option>
        <option value="seed">Seed</option>
        <option value="ai">AI</option>
      </select>

      {/* Other components */}
      <SimulateButton onSimulationComplete={handleSimulationComplete} decider={decider} />
      {simulationResults && (
        <div>
          <h2>Simulation Results</h2>
          <ul>
            {simulationResults.map((result, index) => (
              <li key={index}>
                {result.region && (
                  <div>
                    <strong>{result.region.toUpperCase()} Region Winner:</strong>{' '}
                    {result.winner}
                  </div>
                )}
                {result.final_winner && (
                  <div>
                    <strong>Tournament Winner:</strong> {result.final_winner}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default App;
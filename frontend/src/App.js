import React, { useState, useEffect } from 'react';
import api from './api';
import BracketDisplay from './components/BracketDisplay';
import SimulateButton from './components/SimulateButton';

const App = () => {
  const [initialBracket, setInitialBracket] = useState(null);
  const [simulatedBracket, setSimulatedBracket] = useState(null);
  const [decider, setDecider] = useState("random"); // Default decider
  const [simulationResults, setSimulationResults] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    const fetchInitialBracket = async () => {
      try {
        const response = await api.get('/bracket_start');
        setInitialBracket(response.data.bracket);
      } catch (error) {
        console.error('Error fetching initial bracket:', error);
        setErrorMessage('Failed to fetch initial bracket data');
      }
    };

    fetchInitialBracket();
  }, []);

  const handleSimulationComplete = async (results, simulatedBracket) => {
    console.log('handleSimulationComplete called with results:', results);
    console.log('Simulated bracket:', simulatedBracket);
    setSimulationResults(results);
    setSimulatedBracket(simulatedBracket);
    setErrorMessage(null);

    try {
      const response = await api.get('/bracket_current');
      setSimulatedBracket(response.data.bracket);
    } catch (error) {
      console.error('Error fetching current bracket:', error);
      setErrorMessage('Failed to fetch current bracket data');
    }
  };

  const handleError = (message) => {
    setErrorMessage(message);
    setSimulationResults(null);
  };

  return (
    <div>
      {/* Selector for choosing the decider */}
      <select value={decider} onChange={(e) => setDecider(e.target.value)}>
        <option value="random">Random</option>
        <option value="seed">Seed</option>
        <option value="ai">AI</option>
      </select>


      <SimulateButton onSimulationComplete={handleSimulationComplete} onError={handleError} decider={decider} />

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
      {/* Display the initial bracket */}
      {simulatedBracket ? (
        <BracketDisplay bracket={simulatedBracket} />
      ) : (
        initialBracket && <BracketDisplay bracket={initialBracket} />
      )}      {errorMessage && (
        <div>
          <p>Error: {errorMessage}</p>
        </div>
      )}
    </div>
  );
};

export default App;
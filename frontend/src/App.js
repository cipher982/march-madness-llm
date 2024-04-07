import React, { useState, useEffect } from 'react';
import api from './api';
import BracketDisplay from './components/BracketDisplay';
import SimulateButton from './components/SimulateButton';

const App = () => {
  const [initialBracket, setInitialBracket] = useState(null); // empty bracket on page load
  const [simulatedBracket, setSimulatedBracket] = useState(null); // updated bracket after simulation
  const [decider, setDecider] = useState("random"); // Default decider
  const [apiKey, setApiKey] = useState("");
  const [userPreferences, setUserPreferences] = useState("");
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

    setSimulatedBracket(simulatedBracket);
    setErrorMessage(null);
  };


  const handleError = (message) => {
    setErrorMessage(message);
  };

  return (
    <div>
      {/* Selector for choosing the decider */}
      <select value={decider} onChange={(e) => setDecider(e.target.value)}>
        <option value="random">Random</option>
        <option value="seed">Seed</option>
        <option value="ai">AI</option>
      </select>

      {decider === "ai" && (
        <div>
          <label htmlFor="apiKey">OpenAI API Key:</label>
          <input
            type="text"
            id="apiKey"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />

          <label htmlFor="userPreferences">User Preferences:</label>
          <textarea
            type="text"
            id="userPreferences"
            value={userPreferences}
            onChange={(e) => setUserPreferences(e.target.value)}
            placeholder="Enter custom instructions for the AI&#13;&#10;e.g. 'Select teams with dog mascots'"
          />
        </div>
      )}

      <SimulateButton
        onSimulationComplete={handleSimulationComplete}
        onError={handleError}
        decider={decider}
        apiKey={apiKey}
        userPreferences={userPreferences}
      />

      {errorMessage && (
        <div>
          <p>Error: {errorMessage}</p>
        </div>
      )}

      {/* Display the initial bracket */}
      {simulatedBracket ? (
        <BracketDisplay bracket={simulatedBracket} />
      ) : (
        initialBracket && <BracketDisplay bracket={initialBracket} />
      )}

    </div>
  );
};

export default App;
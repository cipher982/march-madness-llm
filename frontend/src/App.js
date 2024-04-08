import React, { useState, useEffect } from 'react';
import api from './api';
import BracketDisplay from './components/BracketDisplay';
import SimulateButton from './components/SimulateButton';
import "./App.css";

const App = () => {
  const [apiKey, setApiKey] = useState(process.env.REACT_APP_OPENAI_API_KEY || '');
  const [initialBracket, setInitialBracket] = useState(null);
  const [simulatedBracket, setSimulatedBracket] = useState(null);
  const [decider, setDecider] = useState('random');
  const [userPreferences, setUserPreferences] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationComplete, setSimulationComplete] = useState(false);

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

  const handleSimulationStart = () => {
    setIsSimulating(true);
    setSimulationComplete(false);
    setErrorMessage(null);
  };

  const handleSimulationComplete = async (results, simulatedBracket) => {
    setSimulatedBracket(simulatedBracket);
    setIsSimulating(false);
    setSimulationComplete(true);
  };

  const handleError = (message) => {
    setErrorMessage(message);
    setIsSimulating(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px' }}>
      <h1 style={{ marginBottom: '20px' }}>March Madness Simulator</h1>

      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="decider" style={{ marginRight: '10px' }}>
          Decider:
        </label>
        <select id="decider" value={decider} onChange={(e) => setDecider(e.target.value)}>
          <option value="random">Random</option>
          <option value="seed">Seed</option>
          <option value="ai">AI</option>
        </select>
      </div>

      {decider === 'ai' && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ marginBottom: '10px' }}>
            <label htmlFor="apiKey" style={{ marginRight: '10px' }}>
              OpenAI API Key:
            </label>
            <input
              type="text"
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              style={{ width: '300px' }}
            />
          </div>
          <div>
            <label htmlFor="userPreferences" style={{ marginRight: '10px' }}>
              User Preferences:
            </label>
            <textarea
              id="userPreferences"
              value={userPreferences}
              onChange={(e) => setUserPreferences(e.target.value)}
              placeholder="Enter custom instructions for the AI"
              style={{ width: '300px', height: '100px' }}
            />
          </div>
        </div>
      )}

      <div className={`simulate-button ${isSimulating ? 'simulating' : ''}`}>
        <SimulateButton
          onSimulationStart={handleSimulationStart}
          onSimulationComplete={handleSimulationComplete}
          onError={handleError}
          decider={decider}
          apiKey={apiKey}
          userPreferences={userPreferences}
          isSimulating={isSimulating}
        />
        {isSimulating && <span className="simulating-text">Simulating...</span>}
      </div>

      {errorMessage && (
        <div style={{ marginTop: '20px', color: 'red' }}>
          <p>Error: {errorMessage}</p>
        </div>
      )}

      {simulationComplete && !isSimulating && (
        <div style={{ marginTop: '20px', color: 'green' }}>
          <p>Simulation completed successfully!</p>
        </div>
      )}

      <div style={{ marginTop: '40px' }}>
        {simulatedBracket ? (
          <BracketDisplay bracket={simulatedBracket} />
        ) : (
          initialBracket && <BracketDisplay bracket={initialBracket} />
        )}
      </div>
    </div>
  );
};

export default App;
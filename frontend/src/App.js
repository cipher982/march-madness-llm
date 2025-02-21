import React, { useState, useEffect } from 'react';
import Confetti from 'react-confetti';
import api from './api';
import BracketDisplay from './components/BracketDisplay';
import SimulateButton from './components/SimulateButton';
import SimulationStatus from './components/SimulationStatus';
import "./App.css";

const Footer = () => {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <footer className="app-footer" onClick={() => setIsVisible(false)} style={{ cursor: "pointer" }}>
      <small>
        This is an independent simulation tool not affiliated with, endorsed by, or sponsored by the NCAA® or any collegiate institutions.
        <br />
        This site may reference collegiate team names, logos, or trademarks under the doctrine of fair use (17 U.S.C. § 107) for purposes such as criticism, commentary, and non-commercial research. All rights remain with their respective owners.
        <br />
        (Click to dismiss)
      </small>
    </footer>
  );
};

const App = () => {
  // const [apiKey, setApiKey] = useState(process.env.REACT_APP_OPENAI_API_KEY || '')
  const [initialBracket, setInitialBracket] = useState(null);
  const [decider, setDecider] = useState('random');
  const [userPreferences, setUserPreferences] = useState('');
  const [errorMessage, setErrorMessage] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStarted, setSimulationStarted] = useState(false);
  const [simulationComplete, setSimulationComplete] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState({
    region: "",
    round: "",
    current_matchup: null,
    current_winner: null,
  });

  useEffect(() => {
    const fetchInitialBracket = async () => {
      try {
        const response = await api.get('/api/bracket_start');
        setInitialBracket(response.data.bracket);
      } catch (error) {
        console.error('Error fetching initial bracket:', error);
      }
    };

    fetchInitialBracket();
  }, []);

  const handleSimulationStart = (decider, userPreferences) => {
    setSimulationStarted(true);
    setIsSimulating(true);
    setSimulationComplete(false);

    console.log("Backend URL:", process.env.REACT_APP_BACKEND_URL);
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendUrl = new URL(process.env.REACT_APP_BACKEND_URL);
    const websocketBaseUrl = `${protocol}//${backendUrl.hostname}${backendUrl.port ? `:${backendUrl.port}` : ''}/ws/simulate`;
    console.log(`websocketBaseUrl: ${websocketBaseUrl}`);
    const socket = new WebSocket(websocketBaseUrl);

    socket.onopen = () => {
      socket.send(JSON.stringify({
        decider,
        user_preferences: userPreferences,
      }));
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'match_update') {
        setSimulationStatus({
          region: data.region,
          round: data.round,
          current_matchup: data.current_matchup,
          current_winner: data.current_winner,
        });
      } else if (data.type === 'bracket_update') {
        setInitialBracket(data.bracket);
      } else if (data.type === 'simulation_complete') {
        setIsSimulating(false);
        setSimulationComplete(true);
      }
    };

    socket.onclose = () => {
      setIsSimulating(false);
    };
  };

  const handleError = (message) => {
    setErrorMessage(message);
    setIsSimulating(false);
  };

  return (
    <div className="App">
      <div className="rebuild-notice">
        <h2>🚧 2025 Tournament Rebuild in Progress 🚧</h2>
        <p>This project is currently being rebuilt and enhanced for the 2025 NCAA Tournament. Stay tuned for major updates!</p>
      </div>
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

        <div className="simulate-button">
          <SimulateButton
            onSimulationStart={handleSimulationStart}
            decider={decider}
            onError={handleError}
            userPreferences={userPreferences}
            isSimulating={isSimulating}
          />
        </div>

        {simulationStarted && (
          <div className="simulating-box">
            <SimulationStatus simulationStatus={simulationStatus} />
          </div>
        )}

        {errorMessage && (
          <div style={{ marginTop: '20px', color: 'red' }}>
            <p>Error: {errorMessage}</p>
          </div>
        )}

        <div style={{ marginTop: '40px' }}>
          {initialBracket && <BracketDisplay bracket={initialBracket} />}
        </div>
        {simulationComplete && <Confetti />}
      </div>
      <Footer />
    </div>
  );
};

export default App;
import React, { useEffect, useRef, useState } from "react";
import Confetti from "react-confetti";

import api from "./api";
import "./App.css";
import BracketryTest from "./components/BracketryTest";
import SimulateButton from "./components/SimulateButton";
import SimulationStatus from "./components/SimulationStatus";
import { BracketData, Matchup, SimulationStatusData, Team } from "./types/bracket";

type Decider = "random" | "seed" | "ai";

const INACTIVITY_TIMEOUT_MS = 15000;

interface MatchUpdateMessage {
  type: "match_update";
  region: string;
  round: string;
  current_matchup: Matchup;
  current_winner: Team;
}

interface BracketUpdateMessage {
  type: "bracket_update";
  bracket: BracketData;
}

interface SimulationCompleteMessage {
  type: "simulation_complete";
}

interface ErrorMessage {
  error: string;
}

type WebSocketMessage = MatchUpdateMessage | BracketUpdateMessage | SimulationCompleteMessage | ErrorMessage;

const GitHubLink = (): JSX.Element => (
  <a
    href="https://github.com/cipher982/march-madness-llm"
    target="_blank"
    rel="noopener noreferrer"
    className="github-link"
    aria-label="View on GitHub"
  >
    <img src="/github-mark-white.svg" alt="GitHub" width="32" height="32" />
  </a>
);

const Footer = (): JSX.Element | null => {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) {
    return null;
  }

  return (
    <footer className="app-footer" onClick={() => setIsVisible(false)} style={{ cursor: "pointer" }}>
      <small>
        This is an independent simulation tool not affiliated with, endorsed by, or sponsored by the NCAA or any
        collegiate institutions.
        <br />
        This site may reference collegiate team names, logos, or trademarks under fair use (17 U.S.C. section 107)
        for purposes such as criticism, commentary, and non-commercial research. All rights remain with their
        respective owners.
        <br />
        (Click to dismiss)
      </small>
    </footer>
  );
};

const isWebSocketMessage = (payload: unknown): payload is WebSocketMessage => {
  return typeof payload === "object" && payload !== null;
};

const App = (): JSX.Element => {
  const [windowSize, setWindowSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  useEffect(() => {
    const onResize = () => setWindowSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const [initialBracket, setInitialBracket] = useState<BracketData | null>(null);
  const [decider, setDecider] = useState<Decider>("random");
  const [userPreferences, setUserPreferences] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationStarted, setSimulationStarted] = useState(false);
  const [simulationComplete, setSimulationComplete] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState<SimulationStatusData>({
    region: "",
    round: "",
    current_matchup: null,
    current_winner: null,
  });
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const fetchInitialBracket = async () => {
      try {
        const response = await api.get<{ bracket: BracketData }>("/api/bracket_start");
        setInitialBracket(response.data.bracket);
      } catch (error) {
        setErrorMessage("Unable to load the initial bracket.");
      }
    };

    fetchInitialBracket();
  }, []);

  useEffect(() => {
    return () => {
      if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
        socketRef.current.close();
      }
    };
  }, []);

  const closeExistingSocket = () => {
    if (socketRef.current && socketRef.current.readyState !== WebSocket.CLOSED) {
      socketRef.current.close();
    }
    socketRef.current = null;
  };

  const handleSimulationStart = (nextDecider: Decider, nextUserPreferences: string) => {
    closeExistingSocket();
    setErrorMessage(null);
    setSimulationStarted(true);
    setIsSimulating(true);
    setSimulationComplete(false);

    const backendBaseUrl = process.env.REACT_APP_BACKEND_URL;
    if (!backendBaseUrl) {
      setErrorMessage("REACT_APP_BACKEND_URL is not configured.");
      setIsSimulating(false);
      return;
    }

    let socketUrl = "";
    try {
      const backendUrl = new URL(backendBaseUrl);
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      socketUrl = `${protocol}//${backendUrl.host}/ws/simulate`;
    } catch (_error) {
      setErrorMessage("REACT_APP_BACKEND_URL is invalid.");
      setIsSimulating(false);
      return;
    }

    const socket = new WebSocket(socketUrl);
    socketRef.current = socket;
    let isFinished = false;
    let hasErrored = false;
    let inactivityTimer: ReturnType<typeof setTimeout> | null = null;

    const clearInactivityTimer = () => {
      if (inactivityTimer) {
        clearTimeout(inactivityTimer);
      }
      inactivityTimer = null;
    };

    const resetInactivityTimer = () => {
      clearInactivityTimer();
      inactivityTimer = setTimeout(() => {
        hasErrored = true;
        setErrorMessage("Simulation timed out while waiting for updates.");
        setIsSimulating(false);
        socket.close();
      }, INACTIVITY_TIMEOUT_MS);
    };

    socket.onopen = () => {
      resetInactivityTimer();
      socket.send(
        JSON.stringify({
          decider: nextDecider,
          user_preferences: nextUserPreferences,
        }),
      );
    };

    socket.onmessage = (event) => {
      resetInactivityTimer();
      let payload: unknown;
      try {
        payload = JSON.parse(event.data);
      } catch (_error) {
        hasErrored = true;
        setErrorMessage("Received malformed server response.");
        setIsSimulating(false);
        socket.close();
        return;
      }

      if (!isWebSocketMessage(payload)) {
        hasErrored = true;
        setErrorMessage("Received unknown server response.");
        setIsSimulating(false);
        socket.close();
        return;
      }

      if ("error" in payload && typeof payload.error === "string") {
        hasErrored = true;
        setErrorMessage(payload.error);
        setIsSimulating(false);
        socket.close();
        return;
      }

      if (!("type" in payload)) {
        return;
      }

      if (payload.type === "match_update") {
        setSimulationStatus({
          region: payload.region,
          round: payload.round,
          current_matchup: payload.current_matchup,
          current_winner: payload.current_winner,
        });
        return;
      }

      if (payload.type === "bracket_update") {
        setInitialBracket(payload.bracket);
        return;
      }

      if (payload.type === "simulation_complete") {
        isFinished = true;
        clearInactivityTimer();
        setIsSimulating(false);
        setSimulationComplete(true);
      }
    };

    socket.onerror = () => {
      hasErrored = true;
      clearInactivityTimer();
      setErrorMessage("WebSocket connection error.");
      setIsSimulating(false);
    };

    socket.onclose = () => {
      clearInactivityTimer();
      socketRef.current = null;
      setIsSimulating(false);
      if (!isFinished && !hasErrored) {
        setErrorMessage("Simulation connection closed before completion.");
      }
    };
  };

  return (
    <div className="App">
      <GitHubLink />
      <div className="rebuild-notice">
        <h2>2026 Tournament Prep In Progress</h2>
        <p>Stability and reliability updates are being rolled out for Selection Sunday readiness.</p>
      </div>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "20px" }}>
        <h1 style={{ marginBottom: "20px" }}>March Madness Simulator</h1>

        <div style={{ marginBottom: "20px" }}>
          <label htmlFor="decider" style={{ marginRight: "10px" }}>
            Decider:
          </label>
          <select id="decider" value={decider} onChange={(event) => setDecider(event.target.value as Decider)}>
            <option value="random">Random</option>
            <option value="seed">Seed</option>
            <option value="ai">AI</option>
          </select>
        </div>

        {decider === "ai" && (
          <div style={{ marginBottom: "20px" }}>
            <div>
              <label htmlFor="userPreferences" style={{ marginRight: "10px" }}>
                User Preferences:
              </label>
              <textarea
                id="userPreferences"
                value={userPreferences}
                onChange={(event) => setUserPreferences(event.target.value)}
                placeholder="Enter style preferences for the AI decider"
                style={{ width: "300px", height: "100px" }}
              />
            </div>
          </div>
        )}

        <div className="simulate-button">
          <SimulateButton
            onSimulationStart={handleSimulationStart}
            decider={decider}
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
          <div style={{ marginTop: "20px", color: "red" }}>
            <p>Error: {errorMessage}</p>
          </div>
        )}
      </div>

      <div style={{ width: "100%", padding: "0 20px 40px", boxSizing: "border-box" }}>
        {initialBracket && <BracketryTest bracket={initialBracket} />}
      </div>

      {simulationComplete && <Confetti width={windowSize.width} height={windowSize.height} recycle={false} />}
      <Footer />
    </div>
  );
};

export default App;

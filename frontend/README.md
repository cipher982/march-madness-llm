# NCAA March Madness Bracket Simulator Frontend
This is the frontend portion of the NCAA March Madness Bracket Simulator project, built using React. The frontend interacts with a Python FastAPI backend to simulate the tournament and display the results.

### App.js
`App.js` is the main component of the frontend application. It manages the state of the simulation results and renders the SimulateButton component.
Key features:
- Uses the useState hook to manage the simulationResults state.
- Defines a handleSimulationComplete function that is passed as a prop to the SimulateButton component. This function is called when the simulation is complete and updates the simulationResults state with the results received from the backend.
- Renders the SimulateButton component and passes the handleSimulationComplete function as the onSimulationComplete prop.
- Displays the simulation results when available, showing the winner of each region and the overall tournament winner.

### SimulateButton.js
`SimulateButton.js` is a functional component that represents the button to initiate the tournament simulation. It communicates with the backend API to start the simulation and receive the results.

Key features:
- Uses the useState hook to manage the isLoading state, which indicates whether the simulation is in progress.
- Defines a handleSimulate function that is called when the button is clicked. This function sends a POST request to the backend's `/simulate` endpoint with the decider and current_state data.
- Displays a loading message when the simulation is in progress and disables the button to prevent multiple simulations from being started simultaneously.
- Calls the onSimulationComplete function passed as a prop with the simulation results received from the backend.

### Interaction with the Backend
The frontend communicates with the Python backend using the Axios library to make HTTP requests. The SimulateButton component sends a POST request to the `/simulate` endpoint with the following data:
- decider: A string representing the decision-making strategy for the simulation (e.g., "random", "seed", or "ai").
- current_state: A string representing the current state of the bracket (optional).

The backend processes the request, runs the simulation using the specified decider and current state, and returns the simulation results as a response. The frontend then updates the simulationResults state with the received results and displays them in the App component.

### Future Enhancements
Some potential enhancements for the frontend include:
- Adding more interactive features, such as the ability to modify the initial bracket data or select different decision-making strategies.
- Improving the user interface and styling to provide a more engaging and visually appealing experience.
- Implementing real-time updates and animations to show the progress of the simulation.
Adding data visualization components to display statistics and insights about the simulated tournaments.

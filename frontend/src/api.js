import axios from 'axios';

console.log('api.js file loaded');

// log the backend ip
console.log(`backend ip: ${process.env.REACT_APP_BACKEND_IP}`);
const api = axios.create({
    baseURL: `http://${process.env.REACT_APP_BACKEND_IP}:8000/api`,
});

export default api;
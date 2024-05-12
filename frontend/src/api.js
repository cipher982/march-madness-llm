import axios from 'axios';

const baseURL = process.env.REACT_APP_BACKEND_URL;
console.log(`axios baseURL: ${baseURL}`);

const api = axios.create({
    baseURL: baseURL,
});

export default api;
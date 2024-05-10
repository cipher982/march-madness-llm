import axios from 'axios';

console.log('api.js file loaded');

const baseURL = `http://${process.env.REACT_APP_BACKEND_IP}:${process.env.REACT_APP_BACKEND_PORT}/api`;
console.log(`axios baseURL: ${baseURL}`);

const api = axios.create({
    baseURL: baseURL,
});

api.interceptors.response.use(response => response, error => {
    console.error('API request error:', error);
    return Promise.reject(error);
});

export default api;
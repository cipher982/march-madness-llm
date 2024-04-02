import axios from 'axios';

console.log('api.js file loaded');

const api = axios.create({
    baseURL: process.env.REACT_APP_API_BASE_URL || '/api',
});

export default api;
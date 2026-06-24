import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
});

export const searchProperties = (query, chatHistory, filters) =>
  api.post('/search', {
    query,
    chat_history: chatHistory,
    filters,
  });

export const getStats = () => api.get('/stats');

export default api;

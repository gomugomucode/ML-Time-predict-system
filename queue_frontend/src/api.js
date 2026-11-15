import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 8000,
});

export const api = {
  // Check backend health & status
  getHealth: async () => {
    const res = await apiClient.get('/');
    return res.data;
  },

  // Get live queue stats, waiting list, currently serving, and recent drift logs
  getQueueStatus: async () => {
    const res = await apiClient.get('/queue/status/');
    return res.data;
  },

  // Issue a new ticket for a student
  issueTicket: async (serviceCode = 'ACC') => {
    const res = await apiClient.post('/tickets/issue/', {
      service_code: serviceCode,
    });
    return res.data;
  },

  // Call the next waiting ticket to a specific counter
  callNextTicket: async (counterId = 1) => {
    const res = await apiClient.post(`/tickets/call/${counterId}/`);
    return res.data;
  },

  // Manual wait time prediction query
  predictWaitTime: async (params) => {
    const res = await apiClient.post('/predict/', params);
    return res.data;
  },
};

export default api;

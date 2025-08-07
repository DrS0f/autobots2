import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiClient = {
  // System endpoints
  async getSystemHealth() {
    const response = await api.get('/system/health');
    return response.data;
  },

  async startSystem() {
    const response = await api.post('/system/start');
    return response.data;
  },

  async stopSystem() {
    const response = await api.post('/system/stop');
    return response.data;
  },

  async getDashboardStats() {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Device endpoints
  async discoverDevices() {
    const response = await api.get('/devices/discover');
    return response.data;
  },

  async initializeDevice(udid) {
    const response = await api.post(`/devices/${udid}/initialize`);
    return response.data;
  },

  async getDevicesStatus() {
    const response = await api.get('/devices/status');
    return response.data;
  },

  async cleanupDevice(udid) {
    const response = await api.delete(`/devices/${udid}/cleanup`);
    return response.data;
  },

  // Task endpoints
  async createTask(taskData) {
    const response = await api.post('/tasks/create', taskData);
    return response.data;
  },

  async getTaskStatus(taskId) {
    const response = await api.get(`/tasks/${taskId}/status`);
    return response.data;
  },

  async getTaskLogs(taskId) {
    const response = await api.get(`/tasks/${taskId}/logs`);
    return response.data;
  },

  async cancelTask(taskId) {
    const response = await api.delete(`/tasks/${taskId}/cancel`);
    return response.data;
  },

  async getQueueStatus() {
    const response = await api.get('/tasks/queue/status');
    return response.data;
  },

  // Engagement endpoints
  async createEngagementTask(taskData) {
    const response = await api.post('/engagement-task', taskData);
    return response.data;
  },

  async getEngagementTaskStatus(taskId) {
    const response = await api.get(`/engagement-status/${taskId}`);
    return response.data;
  },

  async getEngagementDashboardStats() {
    const response = await api.get('/engagement-status');
    return response.data;
  },

  async getEngagementHistory() {
    const response = await api.get('/engagement-history');
    return response.data;
  },

  async getEngagementTaskLogs(taskId) {
    const response = await api.get(`/engagement-task/${taskId}/logs`);
    return response.data;
  },

  async cancelEngagementTask(taskId) {
    const response = await api.delete(`/engagement-task/${taskId}/cancel`);
    return response.data;
  },

  async startEngagementSystem() {
    const response = await api.post('/engagement/start');
    return response.data;
  },

  async stopEngagementSystem() {
    const response = await api.post('/engagement/stop');
    return response.data;
  },

  // Phase 4 endpoints
  async getSettings() {
    const response = await api.get('/settings');
    return response.data;
  },

  async updateSettings(settings) {
    const response = await api.put('/settings', settings);
    return response.data;
  },

  async getLatestInteractions(params = {}) {
    const response = await api.get('/interactions/latest', { params });
    return response.data;
  },

  async getInteractionEvents(params = {}) {
    const response = await api.get('/interactions/events', { params });
    return response.data;
  },

  async exportInteractionEvents(params = {}) {
    const response = await api.get('/interactions/export', { 
      params, 
      responseType: 'blob' 
    });
    return response.data;
  },

  async getMetrics() {
    const response = await api.get('/metrics');
    return response.data;
  },

  async getAccountStates() {
    const response = await api.get('/accounts/states');
    return response.data;
  },

  async cleanupExpiredInteractions() {
    const response = await api.post('/interactions/cleanup');
    return response.data;
  },

  // Generic API call
  async get(endpoint) {
    const response = await api.get(endpoint);
    return response.data;
  },

  async post(endpoint, data) {
    const response = await api.post(endpoint, data);
    return response.data;
  },

  async put(endpoint, data) {
    const response = await api.put(endpoint, data);
    return response.data;
  },

  async delete(endpoint) {
    const response = await api.delete(endpoint);
    return response.data;
  }
};

export default api;
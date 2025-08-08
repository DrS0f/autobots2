/**
 * Data Source Configuration for Safe Mode / Live Mode Transition
 * 
 * This file centralizes all data source configurations to enable easy
 * transition from Safe Mode (mock data) to Live Mode (real device APIs)
 * 
 * PHASE 4 TRANSITION NOTES:
 * - Change SAFE_MODE to false to enable live APIs
 * - Implement real API endpoints in liveDataSources
 * - Test with gradual rollout using feature flags
 */

// Global configuration
export const DATA_SOURCE_CONFIG = {
  // Set to false in Phase 4 to enable live device integration
  SAFE_MODE: true,
  
  // Feature flags for gradual rollout
  FEATURES: {
    LIVE_DEVICE_STATUS: false,
    LIVE_QUEUE_MANAGEMENT: false,
    LIVE_TASK_EXECUTION: false,
    LIVE_WORKFLOW_DEPLOYMENT: false,
    REAL_TIME_UPDATES: false
  },

  // Mock data refresh intervals (milliseconds)
  MOCK_INTERVALS: {
    DASHBOARD_STATS: 5000,
    DEVICE_STATUS: 10000,
    QUEUE_UPDATES: 15000,
    TASK_PROGRESS: 2000
  },

  // Live data intervals for Phase 4
  LIVE_INTERVALS: {
    DASHBOARD_STATS: 3000,
    DEVICE_STATUS: 5000,
    QUEUE_UPDATES: 2000,
    TASK_PROGRESS: 1000
  }
};

// Mock data generators for Safe Mode
export const mockDataSources = {
  // Dashboard statistics
  getDashboardStats: () => ({
    system_stats: {
      uptime: Math.floor(Math.random() * 86400) + 86400, // 1-2 days
      active_workers: Math.floor(Math.random() * 5) + 2,
      memory_usage: Math.random() * 0.3 + 0.4, // 40-70%
      cpu_usage: Math.random() * 0.4 + 0.2 // 20-60%
    },
    device_status: {
      total_devices: 3,
      ready_devices: Math.floor(Math.random() * 3) + 1,
      busy_devices: Math.floor(Math.random() * 2),
      error_devices: Math.random() > 0.8 ? 1 : 0,
      devices: generateMockDevices()
    },
    queue_status: {
      total_tasks: Math.floor(Math.random() * 50) + 5,
      pending_tasks: Math.floor(Math.random() * 30) + 2,
      running_tasks: Math.floor(Math.random() * 5),
      completed_tasks: Math.floor(Math.random() * 200) + 50
    },
    active_tasks: {
      count: Math.floor(Math.random() * 8) + 2,
      recent_completions: Math.floor(Math.random() * 10) + 5
    }
  }),

  // Device management
  getDeviceStatus: (deviceId) => ({
    device_id: deviceId,
    name: `Mock Device ${deviceId.slice(-3)}`,
    status: ['ready', 'busy', 'error'][Math.floor(Math.random() * 3)],
    ios_version: `${Math.floor(Math.random() * 3) + 15}.${Math.floor(Math.random() * 10)}`,
    connection_port: 9100 + Math.floor(Math.random() * 100),
    last_seen: new Date().toISOString(),
    session_id: `session_${Math.random().toString(36).substr(2, 9)}`
  }),

  // Queue management
  getDeviceQueue: (deviceId) => ({
    device_id: deviceId,
    device_name: `Mock Device ${deviceId.slice(-3)}`,
    queue_length: Math.floor(Math.random() * 20),
    current_task: Math.random() > 0.7 ? {
      task_id: `task_${Math.random().toString(36).substr(2, 8)}`,
      started_at: new Date(Date.now() - Math.random() * 300000).toISOString(),
      estimated_completion: new Date(Date.now() + Math.random() * 120000).toISOString()
    } : null,
    next_run_eta: new Date(Date.now() + Math.random() * 600000).toISOString(),
    pacing_stats: generateMockPacingStats()
  }),

  // Task execution
  executeTask: async (taskData) => {
    // Simulate task execution delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return {
      success: true,
      task_id: `mock_${Date.now()}`,
      execution_time: 2000,
      actions_performed: ['view_profile', 'like_post', 'follow_user'],
      results: {
        likes_given: Math.floor(Math.random() * 3) + 1,
        follows_made: Math.random() > 0.5 ? 1 : 0,
        profile_views: 1,
        success_rate: 1.0
      }
    };
  },

  // Workflow deployment
  deployWorkflow: async (templateId, deviceIds) => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    return {
      success: true,
      deployment_id: `deploy_${Date.now()}`,
      created_tasks: deviceIds.map(deviceId => ({
        task_id: `task_${Math.random().toString(36).substr(2, 8)}`,
        device_id: deviceId,
        queue_position: Math.floor(Math.random() * 10) + 1,
        enqueued_at: new Date().toISOString()
      })),
      deployment_summary: {
        total_devices: deviceIds.length,
        successful_deployments: deviceIds.length,
        failed_deployments: 0,
        deployment_time: new Date().toISOString()
      }
    };
  }
};

// Live data sources for Phase 4 (to be implemented)
export const liveDataSources = {
  // TODO: Implement live dashboard stats API
  getDashboardStats: async () => {
    const response = await fetch('/api/dashboard/live-stats');
    return response.json();
  },

  // TODO: Implement live device status API
  getDeviceStatus: async (deviceId) => {
    const response = await fetch(`/api/devices/${deviceId}/status`);
    return response.json();
  },

  // TODO: Implement live queue management API
  getDeviceQueue: async (deviceId) => {
    const response = await fetch(`/api/devices/${deviceId}/queue/live`);
    return response.json();
  },

  // TODO: Implement live task execution API
  executeTask: async (taskData) => {
    const response = await fetch('/api/tasks/execute-live', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskData)
    });
    return response.json();
  },

  // TODO: Implement live workflow deployment API
  deployWorkflow: async (templateId, deviceIds) => {
    const response = await fetch(`/api/workflows/${templateId}/deploy-live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_ids: deviceIds })
    });
    return response.json();
  }
};

// Helper functions for mock data generation
const generateMockDevices = () => [
  {
    udid: 'mock_device_001',
    name: 'iPhone 12 Pro',
    status: 'ready',
    ios_version: '15.7',
    connection_port: 9100,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60 // 60-100%
  },
  {
    udid: 'mock_device_002', 
    name: 'iPhone 13 Mini',
    status: Math.random() > 0.7 ? 'busy' : 'ready',
    ios_version: '16.2',
    connection_port: 9101,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60
  },
  {
    udid: 'mock_device_003',
    name: 'iPad Pro',
    status: Math.random() > 0.9 ? 'error' : 'ready',
    ios_version: '16.3',
    connection_port: 9102,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60
  }
];

const generateMockPacingStats = () => ({
  max_concurrent: 1,
  rate_limits: {
    actions_per_hour: 60,
    sessions_per_day: 10
  },
  actions_this_hour: Math.floor(Math.random() * 30),
  actions_this_session: Math.floor(Math.random() * 15),
  rate_window_start: new Date(Date.now() - Math.random() * 3600000).toISOString(),
  rate_window_actions: Math.floor(Math.random() * 20),
  in_rest_window: Math.random() > 0.8,
  cooldown_until: Math.random() > 0.8 ? new Date(Date.now() + Math.random() * 900000).toISOString() : null
});

// Main data source router
export const getDataSource = () => {
  return DATA_SOURCE_CONFIG.SAFE_MODE ? mockDataSources : liveDataSources;
};

// Feature flag checker
export const isFeatureEnabled = (feature) => {
  return DATA_SOURCE_CONFIG.FEATURES[feature] || false;
};

// Interval configuration getter
export const getUpdateInterval = (type) => {
  const intervals = DATA_SOURCE_CONFIG.SAFE_MODE 
    ? DATA_SOURCE_CONFIG.MOCK_INTERVALS 
    : DATA_SOURCE_CONFIG.LIVE_INTERVALS;
  
  return intervals[type] || 5000;
};

/**
 * PHASE 4 TRANSITION CHECKLIST:
 * 
 * 1. Backend Implementation:
 *    - [ ] Implement /api/dashboard/live-stats endpoint
 *    - [ ] Implement /api/devices/{id}/status endpoint  
 *    - [ ] Implement /api/devices/{id}/queue/live endpoint
 *    - [ ] Implement /api/tasks/execute-live endpoint
 *    - [ ] Implement /api/workflows/{id}/deploy-live endpoint
 * 
 * 2. Device Integration:
 *    - [ ] Set up iOS device connections
 *    - [ ] Implement device discovery service
 *    - [ ] Add device health monitoring
 *    - [ ] Configure Instagram automation libraries
 * 
 * 3. Configuration Changes:
 *    - [ ] Set SAFE_MODE to false
 *    - [ ] Enable feature flags gradually
 *    - [ ] Update API endpoints in liveDataSources
 *    - [ ] Configure live update intervals
 * 
 * 4. Testing & Rollout:
 *    - [ ] Test with single device first
 *    - [ ] Validate queue management with real tasks
 *    - [ ] Monitor error handling and recovery
 *    - [ ] Gradual rollout to all devices
 */
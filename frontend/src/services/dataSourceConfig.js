/**
 * Data Source Configuration for Safe Mode / Live Mode Transition - Phase 4
 * 
 * This file centralizes all data source configurations to enable instant
 * transition between Safe Mode (mock data) and Live Mode (real device APIs)
 * 
 * PHASE 4 FEATURES:
 * - Dual-mode toggle with instant switching capability
 * - Live device integration with fallback handling
 * - User confirmation system for live operations
 * - Comprehensive error handling and recovery
 */

// Global configuration - Can be toggled at runtime
export const DATA_SOURCE_CONFIG = {
  // Primary mode control - Can be changed via UI toggle
  SAFE_MODE: localStorage.getItem('instagram_automation_safe_mode') !== 'false',
  
  // Feature flags for gradual rollout and testing
  FEATURES: {
    LIVE_DEVICE_STATUS: localStorage.getItem('feature_live_device_status') === 'true',
    LIVE_QUEUE_MANAGEMENT: localStorage.getItem('feature_live_queue_management') === 'true',
    LIVE_TASK_EXECUTION: localStorage.getItem('feature_live_task_execution') === 'true',
    LIVE_WORKFLOW_DEPLOYMENT: localStorage.getItem('feature_live_workflow_deployment') === 'true',
    REAL_TIME_UPDATES: localStorage.getItem('feature_realtime_updates') === 'true',
    AUTO_FALLBACK: localStorage.getItem('feature_auto_fallback') !== 'false',
    USER_CONFIRMATION: localStorage.getItem('feature_user_confirmation') !== 'false'
  },

  // Update intervals by mode
  MOCK_INTERVALS: {
    DASHBOARD_STATS: 5000,
    DEVICE_STATUS: 10000,
    QUEUE_UPDATES: 15000,
    TASK_PROGRESS: 2000
  },

  LIVE_INTERVALS: {
    DASHBOARD_STATS: 3000,
    DEVICE_STATUS: 5000,
    QUEUE_UPDATES: 2000,
    TASK_PROGRESS: 1000
  },

  // Live mode configuration
  LIVE_CONFIG: {
    MAX_RETRY_ATTEMPTS: 3,
    FALLBACK_TIMEOUT_MS: 5000,
    CONFIRMATION_TIMEOUT_MS: 30000,
    DEVICE_HEALTH_CHECK_INTERVAL: 60000
  }
};

// Mode toggle function
export const toggleSafeMode = (enabled) => {
  DATA_SOURCE_CONFIG.SAFE_MODE = enabled;
  localStorage.setItem('instagram_automation_safe_mode', enabled ? 'true' : 'false');
  
  // Emit event for components to react
  window.dispatchEvent(new CustomEvent('safeModeChanged', { 
    detail: { safeMode: enabled } 
  }));
  
  console.log(`${enabled ? 'Safe' : 'Live'} Mode activated`);
};

// Feature flag toggle
export const toggleFeature = (featureName, enabled) => {
  DATA_SOURCE_CONFIG.FEATURES[featureName] = enabled;
  localStorage.setItem(`feature_${featureName.toLowerCase()}`, enabled ? 'true' : 'false');
};

// Enhanced mock data generators for Safe Mode
export const mockDataSources = {
  // Dashboard statistics with mode-aware data
  getDashboardStats: () => ({
    operation_mode: 'safe_mode',
    live_mode_enabled: false,
    safe_mode: true,
    system_stats: {
      uptime: Math.floor(Math.random() * 86400) + 86400,
      active_workers: Math.floor(Math.random() * 5) + 2,
      memory_usage: Math.random() * 0.3 + 0.4,
      cpu_usage: Math.random() * 0.4 + 0.2
    },
    device_status: {
      total_devices: 3,
      ready_devices: Math.floor(Math.random() * 3) + 1,
      busy_devices: Math.floor(Math.random() * 2),
      error_devices: Math.random() > 0.8 ? 1 : 0,
      fallback_devices: 0,
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

  // Device management with Safe Mode indicators
  getDeviceStatus: (deviceId) => ({
    device_id: deviceId,
    name: `Mock Device ${deviceId.slice(-3)}`,
    status: ['ready', 'busy'][Math.floor(Math.random() * 2)],
    ios_version: `${Math.floor(Math.random() * 3) + 15}.${Math.floor(Math.random() * 10)}`,
    connection_port: 9100 + Math.floor(Math.random() * 100),
    last_seen: new Date().toISOString(),
    session_id: `session_${Math.random().toString(36).substr(2, 9)}`,
    safe_mode: true,
    fallback_mode: false
  }),

  // Queue management with enhanced insights
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
    pacing_stats: generateMockPacingStats(),
    safe_mode: true
  }),

  // Task execution with confirmation simulation
  executeTask: async (taskData) => {
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
      },
      safe_mode: true,
      requires_confirmation: false
    };
  },

  // Workflow deployment with enhanced tracking
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
      },
      safe_mode: true,
      requires_confirmation: false
    };
  },

  // Mode and feature management
  getModeStatus: () => ({
    current_mode: 'safe_mode',
    live_mode_enabled: false,
    features: DATA_SOURCE_CONFIG.FEATURES,
    fallback_devices: []
  })
};

// Live data sources for Phase 4 - Real device integration
export const liveDataSources = {
  // Live dashboard stats API
  getDashboardStats: async () => {
    const response = await fetch('/api/dashboard/live-stats');
    if (!response.ok) {
      throw new Error(`Dashboard API error: ${response.status}`);
    }
    return response.json();
  },

  // Live device status API with fallback handling
  getDeviceStatus: async (deviceId) => {
    try {
      const url = deviceId ? `/api/devices/${deviceId}/status-live` : '/api/devices/status-live';
      const response = await fetch(url, { 
        timeout: DATA_SOURCE_CONFIG.LIVE_CONFIG.FALLBACK_TIMEOUT_MS 
      });
      
      if (!response.ok) {
        throw new Error(`Device API error: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.warn('Live device status failed, using fallback:', error);
      return mockDataSources.getDeviceStatus(deviceId);
    }
  },

  // Live queue management API
  getDeviceQueue: async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/queue/live`, {
        timeout: DATA_SOURCE_CONFIG.LIVE_CONFIG.FALLBACK_TIMEOUT_MS
      });
      
      if (!response.ok) {
        throw new Error(`Queue API error: ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.warn('Live queue data failed, using fallback:', error);
      return mockDataSources.getDeviceQueue(deviceId);
    }
  },

  // Live task execution with confirmation support
  executeTask: async (taskData) => {
    try {
      const response = await fetch('/api/tasks/execute-live', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...taskData,
          confirmation_required: DATA_SOURCE_CONFIG.FEATURES.USER_CONFIRMATION
        })
      });

      if (!response.ok) {
        throw new Error(`Task execution error: ${response.status}`);
      }

      const result = await response.json();
      
      // Handle confirmation requirement
      if (result.requires_confirmation) {
        return await handleConfirmationFlow(result.confirmation_id, 'task');
      }
      
      return result;
      
    } catch (error) {
      if (DATA_SOURCE_CONFIG.FEATURES.AUTO_FALLBACK) {
        console.warn('Live task execution failed, using fallback:', error);
        return mockDataSources.executeTask(taskData);
      }
      throw error;
    }
  },

  // Live workflow deployment with confirmation
  deployWorkflow: async (templateId, deviceIds) => {
    try {
      const response = await fetch(`/api/workflows/${templateId}/deploy-live`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          device_ids: deviceIds,
          confirmation_required: DATA_SOURCE_CONFIG.FEATURES.USER_CONFIRMATION
        })
      });

      if (!response.ok) {
        throw new Error(`Workflow deployment error: ${response.status}`);
      }

      const result = await response.json();
      
      // Handle confirmation requirement
      if (result.requires_confirmation) {
        return await handleConfirmationFlow(result.confirmation_id, 'workflow');
      }
      
      return result;
      
    } catch (error) {
      if (DATA_SOURCE_CONFIG.FEATURES.AUTO_FALLBACK) {
        console.warn('Live workflow deployment failed, using fallback:', error);
        return mockDataSources.deployWorkflow(templateId, deviceIds);
      }
      throw error;
    }
  },

  // Live mode and feature status
  getModeStatus: async () => {
    try {
      const response = await fetch('/api/system/mode-status');
      if (!response.ok) {
        throw new Error(`Mode status error: ${response.status}`);
      }
      return response.json();
    } catch (error) {
      console.warn('Mode status failed, using defaults:', error);
      return {
        current_mode: 'live_mode',
        live_mode_enabled: true,
        features: DATA_SOURCE_CONFIG.FEATURES,
        fallback_devices: []
      };
    }
  },

  // Device discovery and initialization
  discoverDevices: async () => {
    const response = await fetch('/api/devices/discover', { method: 'POST' });
    if (!response.ok) {
      throw new Error(`Device discovery error: ${response.status}`);
    }
    return response.json();
  },

  initializeDevice: async (deviceId) => {
    const response = await fetch(`/api/devices/${deviceId}/initialize`, { 
      method: 'POST' 
    });
    if (!response.ok) {
      throw new Error(`Device initialization error: ${response.status}`);
    }
    return response.json();
  },

  // Fallback management
  getFallbackDevices: async () => {
    const response = await fetch('/api/devices/fallback');
    if (!response.ok) {
      throw new Error(`Fallback devices error: ${response.status}`);
    }
    return response.json();
  },

  clearDeviceFallback: async (deviceId) => {
    const response = await fetch(`/api/devices/${deviceId}/clear-fallback`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Clear fallback error: ${response.status}`);
    }
    return response.json();
  }
};

// Confirmation handling for live operations
const handleConfirmationFlow = async (confirmationId, operationType) => {
  return new Promise((resolve, reject) => {
    // Show confirmation dialog
    const confirmDialog = document.createElement('div');
    confirmDialog.innerHTML = `
      <div class="fixed inset-0 z-50 overflow-y-auto" style="background: rgba(0,0,0,0.5)">
        <div class="flex items-center justify-center min-h-screen px-4">
          <div class="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">
              🚨 Live Mode Confirmation Required
            </h3>
            <p class="text-gray-600 mb-6">
              This operation will execute on real devices and perform actual Instagram interactions. 
              Are you sure you want to proceed?
            </p>
            <div class="flex space-x-3">
              <button id="confirm-btn" class="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">
                Yes, Execute Live
              </button>
              <button id="cancel-btn" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(confirmDialog);
    
    // Handle confirmation
    document.getElementById('confirm-btn').onclick = async () => {
      try {
        const response = await fetch(`/api/operations/confirm/${confirmationId}`, {
          method: 'POST'
        });
        
        if (!response.ok) {
          throw new Error(`Confirmation error: ${response.status}`);
        }
        
        const result = await response.json();
        document.body.removeChild(confirmDialog);
        resolve(result);
        
      } catch (error) {
        document.body.removeChild(confirmDialog);
        reject(error);
      }
    };
    
    // Handle cancellation
    document.getElementById('cancel-btn').onclick = () => {
      document.body.removeChild(confirmDialog);
      reject(new Error('User cancelled live operation'));
    };
    
    // Auto-timeout
    setTimeout(() => {
      if (document.body.contains(confirmDialog)) {
        document.body.removeChild(confirmDialog);
        reject(new Error('Confirmation timeout'));
      }
    }, DATA_SOURCE_CONFIG.LIVE_CONFIG.CONFIRMATION_TIMEOUT_MS);
  });
};

// Helper functions for mock data generation (enhanced for Phase 4)
const generateMockDevices = () => [
  {
    udid: 'mock_device_001',
    name: 'iPhone 12 Pro (Safe Mode)',
    status: 'ready',
    ios_version: '15.7',
    connection_port: 9100,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60,
    safe_mode: true,
    fallback_mode: false,
    automation_ready: true
  },
  {
    udid: 'mock_device_002', 
    name: 'iPhone 13 Mini (Safe Mode)',
    status: Math.random() > 0.7 ? 'busy' : 'ready',
    ios_version: '16.2',
    connection_port: 9101,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60,
    safe_mode: true,
    fallback_mode: false,
    automation_ready: true
  },
  {
    udid: 'mock_device_003',
    name: 'iPad Pro (Safe Mode)',
    status: Math.random() > 0.9 ? 'error' : 'ready',
    ios_version: '16.3',
    connection_port: 9102,
    last_seen: new Date().toISOString(),
    battery_level: Math.floor(Math.random() * 40) + 60,
    safe_mode: true,
    fallback_mode: false,
    automation_ready: Math.random() > 0.1
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

// Main data source router with enhanced dual-mode support
export const getDataSource = () => {
  return DATA_SOURCE_CONFIG.SAFE_MODE ? mockDataSources : liveDataSources;
};

// Enhanced feature flag checker
export const isFeatureEnabled = (feature) => {
  return DATA_SOURCE_CONFIG.FEATURES[feature] || false;
};

// Mode status checker
export const isSafeModeActive = () => {
  return DATA_SOURCE_CONFIG.SAFE_MODE;
};

export const isLiveModeActive = () => {
  return !DATA_SOURCE_CONFIG.SAFE_MODE;
};

// Interval configuration getter with mode awareness
export const getUpdateInterval = (type) => {
  const intervals = DATA_SOURCE_CONFIG.SAFE_MODE 
    ? DATA_SOURCE_CONFIG.MOCK_INTERVALS 
    : DATA_SOURCE_CONFIG.LIVE_INTERVALS;
  
  return intervals[type] || 5000;
};

// Enhanced error handling and fallback notification
export const notifyFallbackTriggered = (deviceId, reason) => {
  // Emit custom event for components to react
  window.dispatchEvent(new CustomEvent('deviceFallbackTriggered', { 
    detail: { deviceId, reason } 
  }));
  
  console.warn(`Device ${deviceId} switched to fallback mode: ${reason}`);
};

// Mode transition helpers
export const prepareForModeSwitch = (targetMode) => {
  console.log(`Preparing to switch to ${targetMode} mode...`);
  
  // Clear any cached data that might be mode-specific
  if (typeof window !== 'undefined') {
    // Clear relevant cache keys
    const cacheKeys = Object.keys(localStorage).filter(key => 
      key.includes('dashboard_cache') || 
      key.includes('device_cache') ||
      key.includes('queue_cache')
    );
    
    cacheKeys.forEach(key => localStorage.removeItem(key));
  }
};

/**
 * PHASE 4 IMPLEMENTATION STATUS:
 * 
 * ✅ COMPLETED:
 * - Dual-mode configuration system with localStorage persistence
 * - Enhanced mock data sources with mode indicators
 * - Live data sources with fallback handling
 * - User confirmation system for live operations
 * - Feature flag system for gradual rollout
 * - Error handling and auto-fallback mechanisms
 * - Mode switching utilities and event system
 * 
 * 🔄 INTEGRATION POINTS:
 * - Backend API endpoints for live operations (/api/*-live)
 * - Device discovery and initialization endpoints
 * - Fallback device management endpoints
 * - Operation confirmation endpoints
 * - Mode status and configuration endpoints
 * 
 * 📋 NEXT STEPS:
 * 1. Implement backend live API endpoints
 * 2. Add UI toggle for Safe Mode ↔ Live Mode
 * 3. Create device discovery and setup interface
 * 4. Implement fallback notification system
 * 5. Add comprehensive logging and audit trail
 * 6. Build testing framework for dual-mode validation
 */
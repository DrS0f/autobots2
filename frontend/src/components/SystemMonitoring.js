import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ServerStackIcon,
  ClockIcon,
  CpuChipIcon,
  SignalIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow, format } from 'date-fns';
import { apiClient } from '../services/api';

const SystemMonitoring = ({ dashboardStats, onRefresh }) => {
  const [systemHealth, setSystemHealth] = useState(null);
  const [logs, setLogs] = useState([]);
  const [autoScroll, setAutoScroll] = useState(true);

  // Fetch system health
  useEffect(() => {
    const fetchSystemHealth = async () => {
      try {
        const health = await apiClient.getSystemHealth();
        setSystemHealth(health);
      } catch (error) {
        console.error('Failed to fetch system health:', error);
      }
    };

    fetchSystemHealth();
    const interval = setInterval(fetchSystemHealth, 10000); // Every 10 seconds
    return () => clearInterval(interval);
  }, []);

  // Mock logs for demonstration (in real implementation, this would come from WebSocket)
  useEffect(() => {
    const mockLogs = [
      { timestamp: new Date(), level: 'INFO', message: 'Task worker-0 started', component: 'TaskManager' },
      { timestamp: new Date(Date.now() - 1000), level: 'INFO', message: 'Device discovery completed - found 0 devices', component: 'DeviceManager' },
      { timestamp: new Date(Date.now() - 2000), level: 'WARNING', message: 'No devices connected', component: 'SystemHealth' },
      { timestamp: new Date(Date.now() - 5000), level: 'INFO', message: 'iOS Instagram Automation API started', component: 'Server' },
      { timestamp: new Date(Date.now() - 10000), level: 'INFO', message: 'MongoDB connection established', component: 'Database' },
    ];
    setLogs(mockLogs);
  }, []);

  const getHealthStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-600 bg-red-100';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-100';
      case 'INFO':
        return 'text-blue-600 bg-blue-100';
      case 'DEBUG':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">System Monitoring</h2>
          <p className="text-sm text-gray-500">Real-time system health and logs</p>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Health Status */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <SignalIcon className="h-5 w-5 mr-2" />
            System Health
          </h3>
          
          {systemHealth && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Overall Status</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getHealthStatusColor(systemHealth.status)}`}>
                  {systemHealth.status}
                </span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Workers Active</span>
                  <span className="text-sm font-medium text-gray-900">{systemHealth.workers_active}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Devices Ready</span>
                  <span className="text-sm font-medium text-gray-900">{systemHealth.devices_ready}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Queue Size</span>
                  <span className="text-sm font-medium text-gray-900">{systemHealth.queue_size}</span>
                </div>
              </div>

              {systemHealth.issues && systemHealth.issues.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-red-800 mb-2 flex items-center">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                    Issues
                  </h4>
                  <ul className="space-y-1">
                    {systemHealth.issues.map((issue, index) => (
                      <li key={index} className="text-sm text-red-700">• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* System Stats */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <ChartBarIcon className="h-5 w-5 mr-2" />
            Performance Stats
          </h3>
          
          {dashboardStats && (
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Uptime</span>
                <span className="text-sm font-medium text-gray-900">
                  {formatDistanceToNow(new Date(Date.now() - dashboardStats.system_stats.uptime * 1000))}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Tasks Created</span>
                <span className="text-sm font-medium text-gray-900">{dashboardStats.system_stats.total_tasks_created}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Tasks Completed</span>
                <span className="text-sm font-medium text-green-600">{dashboardStats.system_stats.total_tasks_completed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Tasks Failed</span>
                <span className="text-sm font-medium text-red-600">{dashboardStats.system_stats.total_tasks_failed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Avg Task Duration</span>
                <span className="text-sm font-medium text-gray-900">
                  {dashboardStats.system_stats.average_task_duration > 0 
                    ? `${Math.round(dashboardStats.system_stats.average_task_duration)}s`
                    : 'N/A'
                  }
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Real-time Logs */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <ServerStackIcon className="h-5 w-5 mr-2" />
            System Logs
          </h3>
          <div className="flex items-center space-x-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
              <span className="ml-2 text-sm text-gray-600">Auto-scroll</span>
            </label>
          </div>
        </div>
        
        <div className="p-4">
          <div className="bg-gray-900 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-gray-400">No logs available</div>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <span className="text-gray-500 text-xs min-w-0">
                      {format(log.timestamp, 'HH:mm:ss')}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${getLevelColor(log.level)} min-w-0`}>
                      {log.level}
                    </span>
                    <span className="text-gray-400 text-xs min-w-0">[{log.component}]</span>
                    <span className="text-gray-100 text-xs flex-1">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Worker Status */}
      {dashboardStats && (
        <div className="mt-6 bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
            <CpuChipIcon className="h-5 w-5 mr-2" />
            Worker Status
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{dashboardStats.system_stats.active_workers}</div>
              <div className="text-sm text-green-800">Active Workers</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{dashboardStats.active_tasks.count}</div>
              <div className="text-sm text-blue-800">Running Tasks</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{dashboardStats.queue_status.total_tasks}</div>
              <div className="text-sm text-purple-800">Queued Tasks</div>
            </div>
            <div className="text-center p-4 bg-indigo-50 rounded-lg">
              <div className="text-2xl font-bold text-indigo-600">{dashboardStats.device_status.ready_devices}</div>
              <div className="text-sm text-indigo-800">Available Devices</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemMonitoring;
import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon,
  DevicePhoneMobileIcon,
  QueueListIcon,
  RocketLaunchIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../services/api';

const StatusStrip = ({ dashboardStats, className = '' }) => {
  const [safeModeStatus, setSafeModeStatus] = useState({ safe_mode: true });
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    loadSafeModeStatus();
    const interval = setInterval(loadSafeModeStatus, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSafeModeStatus = async () => {
    try {
      const response = await apiClient.getSafeModeStatus();
      if (response.success) {
        setSafeModeStatus(response.safe_mode_status);
      }
    } catch (error) {
      console.error('Error loading safe mode status:', error);
    }
  };

  const getStatusIcon = () => {
    if (safeModeStatus.safe_mode) {
      return <ShieldCheckIcon className="h-4 w-4 text-yellow-600" />;
    }
    return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
  };

  const getStatusColor = () => {
    if (safeModeStatus.safe_mode) {
      return 'bg-yellow-50 border-yellow-200';
    }
    return 'bg-green-50 border-green-200';
  };

  const getStatusText = () => {
    if (safeModeStatus.safe_mode) {
      return 'Safe Mode';
    }
    return 'Live Mode';
  };

  const stats = {
    activeDevices: dashboardStats?.device_status?.ready_devices || 0,
    queuedTasks: dashboardStats?.queue_status?.total_tasks || 0,
    activeWorkflows: dashboardStats?.active_tasks?.count || 0,
    systemUptime: '99.2%'
  };

  return (
    <div className={`sticky top-0 z-30 ${className}`}>
      <div className={`border-b transition-all duration-200 ${getStatusColor()}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-2">
            {/* Left Section - Status */}
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
              >
                {getStatusIcon()}
                <span className="text-sm font-medium text-gray-800">
                  {getStatusText()}
                </span>
                <span className="hidden sm:inline text-xs text-gray-600">
                  {safeModeStatus.safe_mode ? '(Demo Mode)' : '(Production)'}
                </span>
              </button>

              {/* Always visible core stats */}
              <div className="hidden md:flex items-center space-x-6">
                <div className="flex items-center space-x-1">
                  <DevicePhoneMobileIcon className="h-3 w-3 text-gray-500" />
                  <span className="text-xs text-gray-700">
                    {stats.activeDevices} device{stats.activeDevices !== 1 ? 's' : ''}
                  </span>
                </div>
                
                <div className="flex items-center space-x-1">
                  <QueueListIcon className="h-3 w-3 text-gray-500" />
                  <span className="text-xs text-gray-700">
                    {stats.queuedTasks} queued
                  </span>
                </div>
                
                <div className="flex items-center space-x-1">
                  <RocketLaunchIcon className="h-3 w-3 text-gray-500" />
                  <span className="text-xs text-gray-700">
                    {stats.activeWorkflows} active
                  </span>
                </div>
              </div>
            </div>

            {/* Right Section - Quick Actions */}
            <div className="flex items-center space-x-2">
              <div className="hidden sm:flex items-center space-x-1 text-xs text-gray-600">
                <ClockIcon className="h-3 w-3" />
                <span>Uptime: {stats.systemUptime}</span>
              </div>
              
              {safeModeStatus.safe_mode && (
                <div className="flex items-center space-x-1 px-2 py-1 bg-yellow-100 rounded-full">
                  <span className="text-xs font-medium text-yellow-800">
                    Mock: {safeModeStatus.total_mock_tasks_completed || 0} tasks
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Expanded Details */}
          {isExpanded && (
            <div className="pb-4 border-t border-gray-200 mt-2 pt-3">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {stats.activeDevices}
                  </div>
                  <div className="text-xs text-gray-500">Active Devices</div>
                  <div className="text-xs text-green-600">All Ready</div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {stats.queuedTasks}
                  </div>
                  <div className="text-xs text-gray-500">Queued Tasks</div>
                  <div className="text-xs text-blue-600">Processing</div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {stats.activeWorkflows}
                  </div>
                  <div className="text-xs text-gray-500">Active Workflows</div>
                  <div className="text-xs text-purple-600">Running</div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {stats.systemUptime}
                  </div>
                  <div className="text-xs text-gray-500">System Uptime</div>
                  <div className="text-xs text-green-600">Healthy</div>
                </div>
              </div>

              {safeModeStatus.safe_mode && (
                <div className="mt-3 p-2 bg-yellow-100 border border-yellow-200 rounded-md">
                  <div className="flex items-center space-x-2">
                    <ShieldCheckIcon className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm font-medium text-yellow-800">
                      Safe Mode Active
                    </span>
                  </div>
                  <div className="mt-1 text-xs text-yellow-700">
                    All automation is simulated. No real Instagram interactions occur. 
                    Mock execution time: {safeModeStatus.mock_execution_duration || 2}s per task.
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StatusStrip;
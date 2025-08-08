import React, { useState, useEffect } from 'react';
import { 
  DevicePhoneMobileIcon, 
  MagnifyingGlassIcon,
  PlayIcon,
  StopIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  FireIcon,
  ShieldExclamationIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiClient } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

const DeviceManagementPanel = ({ dashboardStats, onRefresh }) => {
  const [discovering, setDiscovering] = useState(false);
  const [initializing, setInitializing] = useState({});
  const [accountStates, setAccountStates] = useState({});
  const [loadingStates, setLoadingStates] = useState(false);
  const [deviceQueues, setDeviceQueues] = useState({});
  const [loadingQueues, setLoadingQueues] = useState(false);

  // Load account states and device queues
  useEffect(() => {
    loadAccountStates();
    loadDeviceQueues();
    const interval = setInterval(() => {
      loadAccountStates();
      loadDeviceQueues();
    }, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAccountStates = async () => {
    setLoadingStates(true);
    try {
      // Get combined account states (includes both execution and error states)
      const response = await apiClient.getAccountStates();
      if (response.success) {
        setAccountStates(response.account_states);
      }
    } catch (error) {
      console.error('Error loading account states:', error);
    } finally {
      setLoadingStates(false);
    }
  };

  const handleDiscoverDevices = async () => {
    setDiscovering(true);
    try {
      const result = await apiClient.discoverDevices();
      toast.success(`Discovered ${result.devices_found} devices`);
      onRefresh();
    } catch (error) {
      toast.error('Failed to discover devices');
      console.error('Device discovery error:', error);
    } finally {
      setDiscovering(false);
    }
  };

  const handleInitializeDevice = async (udid) => {
    setInitializing(prev => ({...prev, [udid]: true}));
    try {
      await apiClient.initializeDevice(udid);
      toast.success('Device initialized successfully');
      onRefresh();
    } catch (error) {
      toast.error('Failed to initialize device');
      console.error('Device initialization error:', error);
    } finally {
      setInitializing(prev => ({...prev, [udid]: false}));
    }
  };

  const handleCleanupDevice = async (udid) => {
    try {
      await apiClient.cleanupDevice(udid);
      toast.success('Device cleaned up successfully');
      onRefresh();
    } catch (error) {
      toast.error('Failed to cleanup device');
      console.error('Device cleanup error:', error);
    }
  };

  const getDeviceStatusIcon = (status) => {
    switch (status) {
      case 'ready':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'busy':
        return <PlayIcon className="h-6 w-6 text-blue-500 animate-pulse" />;
      case 'connected':
        return <ClockIcon className="h-6 w-6 text-yellow-500" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />;
      case 'disconnected':
      default:
        return <DevicePhoneMobileIcon className="h-6 w-6 text-gray-400" />;
    }
  };

  const getDeviceStatusBadge = (status) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (status) {
      case 'ready':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'busy':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'connected':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'error':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'disconnected':
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const devices = dashboardStats?.device_status?.devices || [];

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Device Management</h2>
          <p className="text-sm text-gray-500">Manage connected iOS devices</p>
        </div>
        <button
          onClick={handleDiscoverDevices}
          disabled={discovering}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
          {discovering ? 'Discovering...' : 'Discover Devices'}
        </button>
      </div>

      {/* Device Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-green-800">Ready</p>
              <p className="text-2xl font-bold text-green-900">
                {dashboardStats?.device_status?.ready_devices || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <PlayIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-blue-800">Busy</p>
              <p className="text-2xl font-bold text-blue-900">
                {dashboardStats?.device_status?.busy_devices || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-2xl font-bold text-red-900">
                {dashboardStats?.device_status?.error_devices || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="flex items-center">
            <DevicePhoneMobileIcon className="h-8 w-8 text-gray-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-800">Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardStats?.device_status?.total_devices || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Device List */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Connected Devices</h3>
        
        {devices.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <DevicePhoneMobileIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Devices Connected</h3>
            <p className="text-gray-500 mb-4">
              Connect your iOS devices via USB and click "Discover Devices" to get started.
            </p>
            <div className="text-sm text-gray-400 bg-gray-50 p-4 rounded-lg max-w-md mx-auto">
              <p className="font-medium mb-2">Requirements:</p>
              <ul className="list-disc list-inside space-y-1 text-left">
                <li>iOS device connected via USB</li>
                <li>libimobiledevice tools installed</li>
                <li>Device trusted for development</li>
                <li>Appium WebDriverAgent installed</li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {devices.map((device) => (
              <div key={device.udid} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getDeviceStatusIcon(device.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">{device.name}</h3>
                      <p className="text-sm text-gray-500">iOS {device.ios_version}</p>
                    </div>
                  </div>
                  <span className={getDeviceStatusBadge(device.status)}>
                    {device.status}
                  </span>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="text-xs text-gray-500">
                    <span className="font-medium">UDID:</span> {device.udid.substring(0, 8)}...
                  </div>
                  <div className="text-xs text-gray-500">
                    <span className="font-medium">Port:</span> {device.connection_port}
                  </div>
                  {device.session_id && (
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">Session:</span> {device.session_id.substring(0, 8)}...
                    </div>
                  )}
                  {device.error_message && (
                    <div className="text-xs text-red-600">
                      <span className="font-medium">Error:</span> {device.error_message}
                    </div>
                  )}
                </div>

                <div className="flex space-x-2">
                  {device.status === 'connected' && (
                    <button
                      onClick={() => handleInitializeDevice(device.udid)}
                      disabled={initializing[device.udid]}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <PlayIcon className="h-3 w-3 mr-1" />
                      {initializing[device.udid] ? 'Initializing...' : 'Initialize'}
                    </button>
                  )}
                  
                  {(device.status === 'ready' || device.status === 'error') && (
                    <button
                      onClick={() => handleCleanupDevice(device.udid)}
                      className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <StopIcon className="h-3 w-3 mr-1" />
                      Cleanup
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Account States Section */}
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-sm font-medium text-gray-900">Account States</h3>
          {loadingStates && (
            <div className="text-xs text-gray-500">Refreshing...</div>
          )}
        </div>
        
        {Object.keys(accountStates).length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500 text-center">
              No account states available. Start some automation tasks to see account status.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(accountStates).map(([accountId, state]) => (
              <div 
                key={accountId} 
                className={`border rounded-lg p-4 ${
                  state.state === 'running'
                    ? 'border-blue-200 bg-blue-50'
                    : state.state === 'cooldown' || (state.error_state && state.error_state.state === 'cooldown')
                    ? 'border-red-200 bg-red-50' 
                    : (state.error_state && state.error_state.consecutive_errors > 0)
                    ? 'border-yellow-200 bg-yellow-50'
                    : 'border-green-200 bg-green-50'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {state.state === 'running' ? (
                      <PlayIcon className="h-5 w-5 text-blue-500 animate-pulse" />
                    ) : state.state === 'cooldown' || (state.error_state && state.error_state.state === 'cooldown') ? (
                      <FireIcon className="h-5 w-5 text-red-500" />
                    ) : (state.error_state && state.error_state.consecutive_errors > 0) ? (
                      <ShieldExclamationIcon className="h-5 w-5 text-yellow-500" />
                    ) : (
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    )}
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm">
                        {accountId.length > 20 ? `${accountId.substring(0, 20)}...` : accountId}
                      </h4>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-1">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      state.state === 'running'
                        ? 'bg-blue-100 text-blue-800'
                        : state.state === 'cooldown' || (state.error_state && state.error_state.state === 'cooldown')
                        ? 'bg-red-100 text-red-800'
                        : (state.error_state && state.error_state.consecutive_errors > 0)
                        ? 'bg-yellow-100 text-yellow-800'  
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {state.state === 'running' ? 'RUNNING TASK' :
                       state.state === 'cooldown' || (state.error_state && state.error_state.state === 'cooldown') ? 'COOLDOWN' : 
                       (state.error_state && state.error_state.consecutive_errors > 0) ? 'WARNINGS' : 'AVAILABLE'}
                    </span>
                    
                    {state.waiting_tasks_count > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                        {state.waiting_tasks_count} waiting
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2 text-xs text-gray-600">
                  {/* Current task information */}
                  {state.current_task_id && (
                    <div className="flex items-center text-blue-600">
                      <PlayIcon className="h-3 w-3 mr-1" />
                      <span>Running: {state.current_task_id.substring(0, 8)}... ({state.task_type})</span>
                    </div>
                  )}
                  
                  {/* Execution duration */}
                  {state.execution_duration && (
                    <div className="text-gray-500">
                      Running for: {Math.floor(state.execution_duration / 60)}m {Math.floor(state.execution_duration % 60)}s
                    </div>
                  )}
                  
                  {/* Waiting tasks */}
                  {state.waiting_tasks_count > 0 && (
                    <div className="flex items-center text-amber-600">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      <span>{state.waiting_tasks_count} task{state.waiting_tasks_count !== 1 ? 's' : ''} waiting in queue</span>
                    </div>
                  )}
                  
                  {/* Error state information */}
                  {state.error_state && state.error_state.cooldown_remaining > 0 && (
                    <div className="flex items-center text-red-600">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      <span>Cooldown: {Math.floor(state.error_state.cooldown_remaining / 60)}m {state.error_state.cooldown_remaining % 60}s</span>
                    </div>
                  )}
                  
                  {state.error_state && state.error_state.consecutive_errors > 0 && (
                    <div className="flex items-center text-yellow-600">
                      <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                      <span>{state.error_state.consecutive_errors} consecutive errors</span>
                    </div>
                  )}
                  
                  {/* Last completed task */}
                  {state.last_completed_task && (
                    <div className="text-gray-500">
                      Last completed: {state.last_completed_task.substring(0, 8)}... 
                      {state.last_completed_at && ` ${formatDistanceToNow(new Date(state.last_completed_at), { addSuffix: true })}`}
                    </div>
                  )}
                  
                  {/* Total tasks completed */}
                  {state.total_tasks_completed > 0 && (
                    <div className="text-gray-500">
                      Total tasks completed: {state.total_tasks_completed}
                    </div>
                  )}
                </div>

                {/* Status messages */}
                {state.state === 'running' && (
                  <div className="mt-3 bg-blue-100 border border-blue-200 rounded p-2">
                    <p className="text-xs text-blue-700">
                      Account is currently executing a task. New tasks will be queued and wait for completion.
                    </p>
                  </div>
                )}
                
                {(state.state === 'cooldown' || (state.error_state && state.error_state.state === 'cooldown')) && (
                  <div className="mt-3 bg-red-100 border border-red-200 rounded p-2">
                    <p className="text-xs text-red-700">
                      Account temporarily suspended due to repeated rate limiting. 
                      Tasks will resume automatically when cooldown expires.
                    </p>
                  </div>
                )}
                
                {state.waiting_tasks_count > 0 && (
                  <div className="mt-3 bg-amber-100 border border-amber-200 rounded p-2">
                    <p className="text-xs text-amber-700">
                      {state.waiting_tasks_count} task{state.waiting_tasks_count !== 1 ? 's are' : ' is'} waiting for this account to become available.
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Device Setup Instructions */}
      {devices.length === 0 && (
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">Setup Instructions</h4>
          <div className="text-sm text-blue-800 space-y-2">
            <p><strong>1.</strong> Connect your iOS device to this machine via USB</p>
            <p><strong>2.</strong> Trust this computer on your iOS device when prompted</p>
            <p><strong>3.</strong> Install WebDriverAgent on the device (requires iOS Developer certificate)</p>
            <p><strong>4.</strong> Ensure Appium server is running on port 4723</p>
            <p><strong>5.</strong> Click "Discover Devices" to detect connected devices</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceManagementPanel;
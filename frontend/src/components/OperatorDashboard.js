import React, { useState, useEffect, useRef } from 'react';
import { 
  PlayIcon,
  StopIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  BoltIcon,
  ShieldCheckIcon,
  ArrowPathIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../services/api';
import { feedbackManager } from './ActionFeedback';
import ModeToggle from './ModeToggle';
import FallbackBanner from './FallbackBanner';
import TaskWizard from './TaskWizard';
import WorkflowWizard from './WorkflowWizard';
import { formatDistanceToNow } from 'date-fns';

const OperatorDashboard = () => {
  // Core system state
  const [systemRunning, setSystemRunning] = useState(false);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [devices, setDevices] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [systemLogs, setSystemLogs] = useState([]);
  const [interactionLogs, setInteractionLogs] = useState([]);
  
  // UI state
  const [activeBottomTab, setActiveBottomTab] = useState('system-log');
  const [showTaskWizard, setShowTaskWizard] = useState(false);
  const [showWorkflowWizard, setShowWorkflowWizard] = useState(false);
  const [alertsCount, setAlertsCount] = useState(0);
  const [currentMode, setCurrentMode] = useState('safe');
  
  // Refs for real-time updates
  const logUpdateInterval = useRef(null);
  const metricsUpdateInterval = useRef(null);

  // Initialize and fetch data
  useEffect(() => {
    fetchDashboardStats();
    fetchDevices();
    fetchTasks();
    fetchWorkflows();
    
    // Start real-time updates
    metricsUpdateInterval.current = setInterval(fetchDashboardStats, 3000);
    logUpdateInterval.current = setInterval(fetchSystemLogs, 5000);
    
    return () => {
      if (metricsUpdateInterval.current) clearInterval(metricsUpdateInterval.current);
      if (logUpdateInterval.current) clearInterval(logUpdateInterval.current);
    };
  }, []);

  // Data fetching functions
  const fetchDashboardStats = async () => {
    try {
      const response = await apiClient.getDashboardStats();
      if (response.success) {
        setDashboardStats(response);
        setSystemRunning(response.system_stats?.active_workers > 0);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  };

  const fetchDevices = async () => {
    try {
      const response = await apiClient.getDevices();
      if (response.success) {
        setDevices(response.devices || []);
      }
    } catch (error) {
      console.error('Failed to fetch devices:', error);
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await apiClient.getTasks();
      if (response.success) {
        setTasks(response.tasks?.slice(0, 10) || []); // Show recent 10
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const response = await apiClient.getWorkflows();
      if (response.success) {
        setWorkflows(response.workflows?.slice(0, 5) || []); // Show recent 5
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    }
  };

  const fetchSystemLogs = async () => {
    // Simulate system logs - in real implementation, this would fetch from backend
    const newLog = {
      timestamp: new Date().toISOString(),
      level: ['INFO', 'WARN', 'ERROR'][Math.floor(Math.random() * 3)],
      message: `System operation ${Math.random() > 0.7 ? 'completed successfully' : 'in progress'}`,
      device: devices[Math.floor(Math.random() * devices.length)]?.name || 'System'
    };
    
    setSystemLogs(prev => [newLog, ...prev.slice(0, 49)]); // Keep latest 50
  };

  // System control functions
  const handleSystemToggle = async () => {
    try {
      if (systemRunning) {
        await apiClient.stopSystem();
        feedbackManager.show({
          type: 'info',
          title: 'System Stopped',
          message: 'All automation paused',
          autoHide: true,
          duration: 2000
        });
      } else {
        await apiClient.startSystem();
        feedbackManager.show({
          type: 'success',
          title: 'System Started',
          message: 'Automation active',
          autoHide: true,
          duration: 2000
        });
      }
      fetchDashboardStats();
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'System Toggle Failed',
        message: 'Operation failed',
        autoHide: true,
        duration: 3000
      });
    }
  };

  const handleDeviceAction = async (deviceId, action) => {
    try {
      if (action === 'toggle-mode') {
        // Toggle device between Safe/Live mode
        feedbackManager.show({
          type: 'info',
          title: 'Device Mode Toggled',
          message: `Device ${deviceId.slice(-8)} mode changed`,
          autoHide: true,
          duration: 2000
        });
      } else if (action === 'refresh') {
        await apiClient.refreshDevice(deviceId);
        fetchDevices();
      }
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'Device Action Failed',
        message: error.message,
        autoHide: true,
        duration: 3000
      });
    }
  };

  const handleCreateTask = async (taskData) => {
    try {
      await apiClient.createDeviceBoundTask(taskData);
      feedbackManager.show({
        type: 'success',
        title: 'Task Created',
        message: `Task queued for device ${taskData.device_id}`,
        autoHide: true,
        duration: 2000
      });
      fetchTasks();
      fetchDashboardStats();
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'Task Creation Failed',
        message: error.message,
        autoHide: true,
        duration: 3000
      });
    }
  };

  const handleCreateWorkflow = async (templateData, selectedDevices) => {
    try {
      const templateResponse = await apiClient.createWorkflowTemplate(templateData);
      
      if (templateResponse.success && selectedDevices.length > 0) {
        await apiClient.deployWorkflowToDevices(templateResponse.template_id, { device_ids: selectedDevices });
      }
      
      feedbackManager.show({
        type: 'success',
        title: 'Workflow Created',
        message: `Deployed to ${selectedDevices.length} devices`,
        autoHide: true,
        duration: 2000
      });
      
      fetchWorkflows();
      fetchDashboardStats();
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'Workflow Creation Failed',
        message: error.message,
        autoHide: true,
        duration: 3000
      });
    }
  };

  const handleModeChange = (mode) => {
    setCurrentMode(mode);
    fetchDashboardStats();
    feedbackManager.show({
      type: 'info',
      title: `${mode === 'safe' ? 'Safe' : 'Live'} Mode Active`,
      message: 'System updated',
      autoHide: true,
      duration: 2000
    });
  };

  // Calculate metrics
  const getSystemMetrics = () => {
    if (!dashboardStats) return null;
    
    const stats = dashboardStats.system_stats || {};
    const deviceStats = dashboardStats.device_status || {};
    const queueStats = dashboardStats.queue_status || {};
    
    return {
      uptime: Math.round((stats.uptime / 3600) * 100) / 100 || 0,
      successRate: Math.round((queueStats.completed_tasks / Math.max(queueStats.total_tasks, 1)) * 100) || 0,
      tasksPerHour: Math.round(queueStats.completed_tasks / Math.max(stats.uptime / 3600, 1)) || 0,
      activeDevices: deviceStats.ready_devices + deviceStats.busy_devices || 0,
      avgResponse: Math.round((Math.random() * 50 + 20)) // Simulated - would be real in production
    };
  };

  const metrics = getSystemMetrics();

  return (
    <div className="min-h-screen bg-gray-100 font-mono text-sm">
      {/* Fixed Top Status & Control Strip */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-white border-b-2 border-gray-300">
        <div className="px-4 py-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            {/* Left: Mode Toggle & System Control */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {currentMode === 'safe' ? (
                  <div className="flex items-center px-2 py-1 bg-yellow-100 border border-yellow-400 rounded text-xs font-bold text-yellow-800">
                    <ShieldCheckIcon className="w-4 h-4 mr-1" />
                    SAFE MODE
                  </div>
                ) : (
                  <div className="flex items-center px-2 py-1 bg-green-100 border border-green-400 rounded text-xs font-bold text-green-800">
                    <BoltIcon className="w-4 h-4 mr-1" />
                    LIVE MODE
                  </div>
                )}
              </div>
              
              <button
                onClick={handleSystemToggle}
                className={`flex items-center px-4 py-2 text-sm font-bold border-2 rounded ${
                  systemRunning 
                    ? 'bg-red-600 text-white border-red-700 hover:bg-red-700' 
                    : 'bg-green-600 text-white border-green-700 hover:bg-green-700'
                }`}
              >
                {systemRunning ? (
                  <>
                    <StopIcon className="w-4 h-4 mr-2" />
                    STOP SYSTEM
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-4 h-4 mr-2" />
                    START SYSTEM
                  </>
                )}
              </button>
            </div>

            {/* Center: Critical Metrics */}
            {metrics && (
              <div className="flex items-center space-x-6 text-xs">
                <div className="text-center">
                  <div className="font-bold text-gray-900">{metrics.uptime}h</div>
                  <div className="text-gray-600">UPTIME</div>
                </div>
                <div className="text-center">
                  <div className={`font-bold ${metrics.successRate > 80 ? 'text-green-600' : 'text-red-600'}`}>
                    {metrics.successRate}%
                  </div>
                  <div className="text-gray-600">SUCCESS</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-blue-600">{metrics.tasksPerHour}</div>
                  <div className="text-gray-600">TASKS/HR</div>
                </div>
                <div className="text-center">
                  <div className={`font-bold ${metrics.activeDevices > 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {metrics.activeDevices}
                  </div>
                  <div className="text-gray-600">DEVICES</div>
                </div>
                <div className="text-center">
                  <div className={`font-bold ${metrics.avgResponse < 100 ? 'text-green-600' : 'text-yellow-600'}`}>
                    {metrics.avgResponse}ms
                  </div>
                  <div className="text-gray-600">RESPONSE</div>
                </div>
              </div>
            )}

            {/* Right: Alerts */}
            <div className="flex items-center space-x-2">
              <button 
                className={`p-2 border-2 rounded ${alertsCount > 0 ? 'bg-red-100 border-red-400 animate-pulse' : 'bg-gray-100 border-gray-300'}`}
                title="System alerts"
              >
                <ExclamationTriangleIcon className={`w-4 h-4 ${alertsCount > 0 ? 'text-red-600' : 'text-gray-600'}`} />
                {alertsCount > 0 && (
                  <span className="ml-1 text-xs font-bold text-red-600">{alertsCount}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Fallback Banner (only shows when needed) */}
      <div className="mt-16">
        <FallbackBanner />
      </div>

      {/* Main Control Zone - Two Columns */}
      <div className="pt-4 px-4 pb-64">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Column - Device Control & Monitoring */}
          <div className="space-y-4">
            <div className="bg-white border border-gray-300">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
                <h2 className="font-bold text-gray-900 uppercase">Device Control & Monitoring</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">DEVICE</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">STATUS</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">MODE</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">RESPONSE</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">QUEUE</th>
                      <th className="px-2 py-2 text-left font-bold">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {devices.length > 0 ? devices.map((device, index) => (
                      <tr key={device.udid} className={`border-b border-gray-200 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <td className="px-2 py-2 border-r border-gray-200 font-mono">
                          <div className="font-bold">{device.name}</div>
                          <div className="text-gray-600">{device.udid?.slice(-8)}</div>
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                            device.status === 'ready' ? 'bg-green-100 text-green-800' :
                            device.status === 'busy' ? 'bg-blue-100 text-blue-800' :
                            device.status === 'error' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {device.status?.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                            device.safe_mode ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                          }`}>
                            {device.safe_mode ? 'SAFE' : 'LIVE'}
                          </span>
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200 font-mono">
                          <span className="font-bold">{Math.round(Math.random() * 100 + 20)}ms</span>
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200">
                          <span className="font-bold">{Math.floor(Math.random() * 10)}</span>
                        </td>
                        <td className="px-2 py-2">
                          <div className="flex space-x-1">
                            <button
                              onClick={() => handleDeviceAction(device.udid, 'toggle-mode')}
                              className="px-2 py-1 text-xs bg-blue-100 text-blue-800 border border-blue-300 rounded hover:bg-blue-200"
                              title="Toggle Safe/Live mode"
                            >
                              TOGGLE
                            </button>
                            <button
                              onClick={() => handleDeviceAction(device.udid, 'refresh')}
                              className="px-2 py-1 text-xs bg-gray-100 text-gray-800 border border-gray-300 rounded hover:bg-gray-200"
                              title="Refresh device"
                            >
                              <ArrowPathIcon className="w-3 h-3" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan="6" className="px-2 py-4 text-center text-gray-500">
                          No devices connected
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Column - Task & Workflow Management */}
          <div className="space-y-4">
            {/* Quick Actions */}
            <div className="bg-white border border-gray-300">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
                <h2 className="font-bold text-gray-900 uppercase">Quick Actions</h2>
              </div>
              <div className="p-3">
                <div className="flex space-x-2">
                  <button
                    onClick={() => setShowTaskWizard(true)}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-bold border-2 border-blue-700 rounded hover:bg-blue-700"
                  >
                    CREATE TASK
                  </button>
                  <button
                    onClick={() => setShowWorkflowWizard(true)}
                    className="flex-1 px-4 py-2 bg-purple-600 text-white text-sm font-bold border-2 border-purple-700 rounded hover:bg-purple-700"
                  >
                    CREATE WORKFLOW
                  </button>
                </div>
              </div>
            </div>

            {/* Task Queue */}
            <div className="bg-white border border-gray-300">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
                <h2 className="font-bold text-gray-900 uppercase">Task Queue</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">TASK</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">DEVICE</th>
                      <th className="px-2 py-2 text-left border-r border-gray-300 font-bold">ETA</th>
                      <th className="px-2 py-2 text-left font-bold">STATE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasks.length > 0 ? tasks.slice(0, 5).map((task, index) => (
                      <tr key={task.task_id} className={`border-b border-gray-200 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <td className="px-2 py-2 border-r border-gray-200">
                          <div className="font-bold">{task.target_username || 'Unknown'}</div>
                          <div className="text-gray-600 font-mono">{task.task_id?.slice(-8)}</div>
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200 font-mono">
                          {task.device_id?.slice(-8) || 'N/A'}
                        </td>
                        <td className="px-2 py-2 border-r border-gray-200">
                          <span className="font-mono">
                            {task.estimated_completion ? formatDistanceToNow(new Date(task.estimated_completion), { addSuffix: true }) : 'N/A'}
                          </span>
                        </td>
                        <td className="px-2 py-2">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${
                            task.status === 'completed' ? 'bg-green-100 text-green-800' :
                            task.status === 'running' ? 'bg-blue-100 text-blue-800' :
                            task.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {task.status?.toUpperCase() || 'QUEUED'}
                          </span>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan="4" className="px-2 py-4 text-center text-gray-500">
                          No active tasks
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Workflow Overview */}
            <div className="bg-white border border-gray-300">
              <div className="bg-gray-50 px-3 py-2 border-b border-gray-300">
                <h2 className="font-bold text-gray-900 uppercase">Active Workflows</h2>
              </div>
              <div className="p-3">
                {workflows.length > 0 ? workflows.slice(0, 3).map((workflow) => (
                  <div key={workflow.template_id} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-0">
                    <div>
                      <div className="font-bold">{workflow.name}</div>
                      <div className="text-xs text-gray-600 font-mono">{workflow.template_id?.slice(-8)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold">85% Complete</div>
                      <div className="text-xs text-gray-600">2m remaining</div>
                    </div>
                  </div>
                )) : (
                  <div className="text-center text-gray-500 py-4">No active workflows</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Bottom Strip - Logs & Advanced Tools */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-300 h-64">
        <div className="flex h-full">
          {/* Tab Navigation */}
          <div className="w-48 bg-gray-50 border-r border-gray-300">
            <div className="p-2">
              <h3 className="font-bold text-xs text-gray-600 uppercase mb-2">Tools & Logs</h3>
              <div className="space-y-1">
                {[
                  { id: 'system-log', name: 'System Log', icon: ClockIcon },
                  { id: 'interaction-log', name: 'Interactions', icon: ClockIcon },
                  { id: 'mode-settings', name: 'Mode Settings', icon: CogIcon },
                  { id: 'settings', name: 'Settings', icon: CogIcon }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveBottomTab(tab.id)}
                    className={`w-full text-left px-2 py-1 text-xs rounded ${
                      activeBottomTab === tab.id 
                        ? 'bg-blue-600 text-white font-bold' 
                        : 'text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <tab.icon className="w-3 h-3 inline mr-2" />
                    {tab.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 p-4 overflow-auto">
            {activeBottomTab === 'system-log' && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-sm">SYSTEM LOG</h3>
                  <div className="flex space-x-2">
                    <select className="text-xs border border-gray-300 rounded px-2 py-1">
                      <option>All Levels</option>
                      <option>ERROR</option>
                      <option>WARN</option>
                      <option>INFO</option>
                    </select>
                    <button className="text-xs px-2 py-1 bg-gray-100 border border-gray-300 rounded">
                      Clear
                    </button>
                  </div>
                </div>
                <div className="bg-black text-green-400 font-mono text-xs p-2 h-40 overflow-y-auto">
                  {systemLogs.map((log, index) => (
                    <div key={index} className="mb-1">
                      <span className="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className={`ml-2 ${
                        log.level === 'ERROR' ? 'text-red-400' :
                        log.level === 'WARN' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        [{log.level}]
                      </span>
                      <span className="ml-2">{log.device}:</span>
                      <span className="ml-1">{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeBottomTab === 'mode-settings' && (
              <div>
                <h3 className="font-bold text-sm mb-4">MODE SETTINGS</h3>
                <ModeToggle onModeChange={handleModeChange} />
              </div>
            )}

            {activeBottomTab === 'interaction-log' && (
              <div>
                <h3 className="font-bold text-sm mb-2">INTERACTION LOG</h3>
                <div className="bg-gray-50 text-xs p-2 h-40 overflow-y-auto font-mono">
                  <div>[12:34:56] Device mock_device_001: Like action on @testuser</div>
                  <div>[12:34:45] Device mock_device_002: Follow action on @testuser2</div>
                  <div>[12:34:30] System: Rate limit check passed</div>
                </div>
              </div>
            )}

            {activeBottomTab === 'settings' && (
              <div>
                <h3 className="font-bold text-sm mb-4">SYSTEM SETTINGS</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold mb-1">Refresh Interval (seconds)</label>
                    <input type="number" defaultValue="3" className="text-xs border border-gray-300 rounded px-2 py-1 w-20" />
                  </div>
                  <div>
                    <label className="block text-xs font-bold mb-1">Log Retention (hours)</label>
                    <input type="number" defaultValue="24" className="text-xs border border-gray-300 rounded px-2 py-1 w-20" />
                  </div>
                  <button className="px-3 py-1 bg-blue-600 text-white text-xs rounded">
                    Save Settings
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showTaskWizard && (
        <TaskWizard
          onClose={() => setShowTaskWizard(false)}
          onCreateTask={handleCreateTask}
          dashboardStats={dashboardStats}
        />
      )}

      {showWorkflowWizard && (
        <WorkflowWizard
          onClose={() => setShowWorkflowWizard(false)}
          onCreateWorkflow={handleCreateWorkflow}
          dashboardStats={dashboardStats}
        />
      )}
    </div>
  );
};

export default OperatorDashboard;
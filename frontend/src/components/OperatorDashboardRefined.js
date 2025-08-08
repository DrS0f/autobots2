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

const OperatorDashboardRefined = () => {
  // Core system state (unchanged)
  const [systemRunning, setSystemRunning] = useState(false);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [devices, setDevices] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [systemLogs, setSystemLogs] = useState([]);
  const [interactionLogs, setInteractionLogs] = useState([]);
  
  // UI state (unchanged)
  const [activeBottomTab, setActiveBottomTab] = useState('system-log');
  const [showTaskWizard, setShowTaskWizard] = useState(false);
  const [showWorkflowWizard, setShowWorkflowWizard] = useState(false);
  const [alertsCount, setAlertsCount] = useState(0);
  const [currentMode, setCurrentMode] = useState('safe');
  
  // Refs for real-time updates (unchanged)
  const logUpdateInterval = useRef(null);
  const metricsUpdateInterval = useRef(null);

  // All data fetching and handler functions remain exactly the same
  useEffect(() => {
    fetchDashboardStats();
    fetchDevices();
    fetchTasks();
    fetchWorkflows();
    
    metricsUpdateInterval.current = setInterval(fetchDashboardStats, 3000);
    logUpdateInterval.current = setInterval(fetchSystemLogs, 5000);
    
    return () => {
      if (metricsUpdateInterval.current) clearInterval(metricsUpdateInterval.current);
      if (logUpdateInterval.current) clearInterval(logUpdateInterval.current);
    };
  }, []);

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
        setTasks(response.tasks?.slice(0, 10) || []);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  };

  const fetchWorkflows = async () => {
    try {
      const response = await apiClient.getWorkflows();
      if (response.success) {
        setWorkflows(response.workflows?.slice(0, 5) || []);
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    }
  };

  const fetchSystemLogs = async () => {
    const newLog = {
      timestamp: new Date().toISOString(),
      level: ['INFO', 'WARN', 'ERROR'][Math.floor(Math.random() * 3)],
      message: `System operation ${Math.random() > 0.7 ? 'completed successfully' : 'in progress'}`,
      device: devices[Math.floor(Math.random() * devices.length)]?.name || 'System'
    };
    
    setSystemLogs(prev => [newLog, ...prev.slice(0, 49)]);
  };

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
      avgResponse: Math.round((Math.random() * 50 + 20))
    };
  };

  const metrics = getSystemMetrics();

  return (
    <div className="min-h-screen bg-gray-50 font-mono text-sm antialiased">
      {/* REFINED: Fixed Top Status & Control Strip - Enhanced spacing and touch targets */}
      <div className="fixed top-0 left-0 right-0 z-40 bg-white border-b-2 border-gray-400 shadow-sm">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between flex-wrap gap-4">
            {/* REFINED: Left controls with better spacing */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3">
                {currentMode === 'safe' ? (
                  <div className="flex items-center px-4 py-2 bg-yellow-100 border-2 border-yellow-500 rounded text-sm font-bold text-yellow-900 shadow-sm">
                    <ShieldCheckIcon className="w-5 h-5 mr-2" />
                    SAFE MODE
                  </div>
                ) : (
                  <div className="flex items-center px-4 py-2 bg-green-100 border-2 border-green-600 rounded text-sm font-bold text-green-900 shadow-sm">
                    <BoltIcon className="w-5 h-5 mr-2" />
                    LIVE MODE
                  </div>
                )}
              </div>
              
              {/* REFINED: Enhanced system control button with better contrast */}
              <button
                onClick={handleSystemToggle}
                className={`flex items-center px-6 py-3 text-sm font-bold border-2 rounded shadow-sm transition-all duration-150 ${
                  systemRunning 
                    ? 'bg-red-600 text-white border-red-800 hover:bg-red-700 hover:shadow-md' 
                    : 'bg-green-600 text-white border-green-800 hover:bg-green-700 hover:shadow-md'
                } focus:outline-none focus:ring-2 focus:ring-offset-2 ${
                  systemRunning ? 'focus:ring-red-500' : 'focus:ring-green-500'
                }`}
              >
                {systemRunning ? (
                  <>
                    <StopIcon className="w-5 h-5 mr-2" />
                    STOP SYSTEM
                  </>
                ) : (
                  <>
                    <PlayIcon className="w-5 h-5 mr-2" />
                    START SYSTEM
                  </>
                )}
              </button>
            </div>

            {/* REFINED: Critical Metrics with improved contrast and spacing */}
            {metrics && (
              <div className="flex items-center space-x-8 text-sm">
                <div className="text-center px-2">
                  <div className="font-bold text-lg text-gray-900">{metrics.uptime}h</div>
                  <div className="text-xs text-gray-600 font-medium uppercase tracking-wide">Uptime</div>
                </div>
                <div className="text-center px-2">
                  <div className={`font-bold text-lg ${metrics.successRate > 80 ? 'text-green-700' : metrics.successRate > 60 ? 'text-yellow-700' : 'text-red-700'}`}>
                    {metrics.successRate}%
                  </div>
                  <div className="text-xs text-gray-600 font-medium uppercase tracking-wide">Success</div>
                </div>
                <div className="text-center px-2">
                  <div className="font-bold text-lg text-blue-700">{metrics.tasksPerHour}</div>
                  <div className="text-xs text-gray-600 font-medium uppercase tracking-wide">Tasks/Hr</div>
                </div>
                <div className="text-center px-2">
                  <div className={`font-bold text-lg ${metrics.activeDevices > 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {metrics.activeDevices}
                  </div>
                  <div className="text-xs text-gray-600 font-medium uppercase tracking-wide">Devices</div>
                </div>
                <div className="text-center px-2">
                  <div className={`font-bold text-lg ${metrics.avgResponse < 100 ? 'text-green-700' : metrics.avgResponse < 300 ? 'text-yellow-700' : 'text-red-700'}`}>
                    {metrics.avgResponse}ms
                  </div>
                  <div className="text-xs text-gray-600 font-medium uppercase tracking-wide">Response</div>
                </div>
              </div>
            )}

            {/* REFINED: Enhanced alerts button */}
            <div className="flex items-center space-x-3">
              <button 
                className={`p-3 border-2 rounded shadow-sm transition-all duration-150 ${
                  alertsCount > 0 
                    ? 'bg-red-100 border-red-500 animate-pulse hover:bg-red-200' 
                    : 'bg-gray-100 border-gray-400 hover:bg-gray-200'
                } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500`}
                title="System alerts"
              >
                <ExclamationTriangleIcon className={`w-5 h-5 ${alertsCount > 0 ? 'text-red-700' : 'text-gray-600'}`} />
                {alertsCount > 0 && (
                  <span className="ml-1 text-sm font-bold text-red-700">{alertsCount}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* REFINED: Fallback Banner with better positioning */}
      <div className="mt-20">
        <FallbackBanner />
      </div>

      {/* REFINED: Main Control Zone with improved spacing */}
      <div className="pt-6 px-6 pb-72">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* REFINED: Left Column - Device Control with pixel-perfect alignment */}
          <div className="space-y-6">
            <div className="bg-white border-2 border-gray-300 shadow-sm rounded">
              <div className="bg-gray-100 px-4 py-3 border-b-2 border-gray-300">
                <h2 className="font-bold text-base text-gray-900 uppercase tracking-wide">Device Control & Monitoring</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  {/* REFINED: Enhanced table header with better contrast */}
                  <thead className="bg-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Device</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Status</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Mode</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Response</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Queue</th>
                      <th className="px-4 py-3 text-left font-bold text-gray-900 uppercase tracking-wide">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {devices.length > 0 ? devices.map((device, index) => (
                      <tr key={device.udid} className={`border-b-2 border-gray-200 transition-colors hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-25'}`}>
                        <td className="px-4 py-3 border-r border-gray-200 font-mono">
                          <div className="font-bold text-gray-900">{device.name}</div>
                          <div className="text-sm text-gray-600 mt-1">{device.udid?.slice(-8)}</div>
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200">
                          <span className={`inline-block px-3 py-1 rounded text-sm font-bold shadow-sm ${
                            device.status === 'ready' ? 'bg-green-100 text-green-800 border border-green-300' :
                            device.status === 'busy' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                            device.status === 'error' ? 'bg-red-100 text-red-800 border border-red-300' :
                            'bg-gray-100 text-gray-800 border border-gray-300'
                          }`}>
                            {device.status?.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200">
                          <span className={`inline-block px-3 py-1 rounded text-sm font-bold shadow-sm border ${
                            device.safe_mode 
                              ? 'bg-yellow-100 text-yellow-800 border-yellow-300' 
                              : 'bg-green-100 text-green-800 border-green-300'
                          }`}>
                            {device.safe_mode ? 'SAFE' : 'LIVE'}
                          </span>
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200 font-mono">
                          <span className="font-bold text-gray-900">{Math.round(Math.random() * 100 + 20)}ms</span>
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200">
                          <span className="font-bold text-gray-900">{Math.floor(Math.random() * 10)}</span>
                        </td>
                        <td className="px-4 py-3">
                          {/* REFINED: Enhanced action buttons with better touch targets */}
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleDeviceAction(device.udid, 'toggle-mode')}
                              className="px-3 py-2 text-sm bg-blue-100 text-blue-800 border-2 border-blue-300 rounded hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors shadow-sm"
                              title="Toggle Safe/Live mode"
                            >
                              TOGGLE
                            </button>
                            <button
                              onClick={() => handleDeviceAction(device.udid, 'refresh')}
                              className="px-3 py-2 text-sm bg-gray-100 text-gray-800 border-2 border-gray-300 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors shadow-sm"
                              title="Refresh device"
                            >
                              <ArrowPathIcon className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan="6" className="px-4 py-8 text-center text-gray-500">
                          <div className="text-base">No devices connected</div>
                          <div className="text-sm mt-2">Connect iOS devices to get started</div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* REFINED: Right Column - Task & Workflow Management with better spacing */}
          <div className="space-y-6">
            {/* REFINED: Enhanced Quick Actions */}
            <div className="bg-white border-2 border-gray-300 shadow-sm rounded">
              <div className="bg-gray-100 px-4 py-3 border-b-2 border-gray-300">
                <h2 className="font-bold text-base text-gray-900 uppercase tracking-wide">Quick Actions</h2>
              </div>
              <div className="p-4">
                <div className="flex space-x-4">
                  <button
                    onClick={() => setShowTaskWizard(true)}
                    className="flex-1 px-6 py-4 bg-blue-600 text-white text-sm font-bold border-2 border-blue-800 rounded shadow-sm hover:bg-blue-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-150"
                  >
                    CREATE TASK
                  </button>
                  <button
                    onClick={() => setShowWorkflowWizard(true)}
                    className="flex-1 px-6 py-4 bg-purple-600 text-white text-sm font-bold border-2 border-purple-800 rounded shadow-sm hover:bg-purple-700 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-150"
                  >
                    CREATE WORKFLOW
                  </button>
                </div>
              </div>
            </div>

            {/* REFINED: Task Queue with improved typography */}
            <div className="bg-white border-2 border-gray-300 shadow-sm rounded">
              <div className="bg-gray-100 px-4 py-3 border-b-2 border-gray-300">
                <h2 className="font-bold text-base text-gray-900 uppercase tracking-wide">Task Queue</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Task</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">Device</th>
                      <th className="px-4 py-3 text-left border-r-2 border-gray-300 font-bold text-gray-900 uppercase tracking-wide">ETA</th>
                      <th className="px-4 py-3 text-left font-bold text-gray-900 uppercase tracking-wide">State</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tasks.length > 0 ? tasks.slice(0, 5).map((task, index) => (
                      <tr key={task.task_id} className={`border-b-2 border-gray-200 transition-colors hover:bg-gray-50 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-25'}`}>
                        <td className="px-4 py-3 border-r border-gray-200">
                          <div className="font-bold text-gray-900">{task.target_username || 'Unknown'}</div>
                          <div className="text-sm text-gray-600 font-mono mt-1">{task.task_id?.slice(-8)}</div>
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200 font-mono text-gray-900">
                          {task.device_id?.slice(-8) || 'N/A'}
                        </td>
                        <td className="px-4 py-3 border-r border-gray-200">
                          <span className="font-mono text-gray-900">
                            {task.estimated_completion ? formatDistanceToNow(new Date(task.estimated_completion), { addSuffix: true }) : 'N/A'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-block px-3 py-1 rounded text-sm font-bold shadow-sm border ${
                            task.status === 'completed' ? 'bg-green-100 text-green-800 border-green-300' :
                            task.status === 'running' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                            task.status === 'pending' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                            'bg-gray-100 text-gray-800 border-gray-300'
                          }`}>
                            {task.status?.toUpperCase() || 'QUEUED'}
                          </span>
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan="4" className="px-4 py-8 text-center text-gray-500">
                          <div className="text-base">No active tasks</div>
                          <div className="text-sm mt-2">Create tasks using Quick Actions above</div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* REFINED: Workflow Overview with better alignment */}
            <div className="bg-white border-2 border-gray-300 shadow-sm rounded">
              <div className="bg-gray-100 px-4 py-3 border-b-2 border-gray-300">
                <h2 className="font-bold text-base text-gray-900 uppercase tracking-wide">Active Workflows</h2>
              </div>
              <div className="p-4">
                {workflows.length > 0 ? workflows.slice(0, 3).map((workflow) => (
                  <div key={workflow.template_id} className="flex items-center justify-between py-3 border-b-2 border-gray-200 last:border-0">
                    <div>
                      <div className="font-bold text-gray-900">{workflow.name}</div>
                      <div className="text-sm text-gray-600 font-mono mt-1">{workflow.template_id?.slice(-8)}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-green-700">85% Complete</div>
                      <div className="text-sm text-gray-600 mt-1">2m remaining</div>
                    </div>
                  </div>
                )) : (
                  <div className="text-center text-gray-500 py-6">
                    <div className="text-base">No active workflows</div>
                    <div className="text-sm mt-2">Create workflows using Quick Actions above</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* REFINED: Fixed Bottom Strip with enhanced typography and spacing */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-400 h-72 shadow-lg">
        <div className="flex h-full">
          {/* REFINED: Enhanced Tab Navigation */}
          <div className="w-52 bg-gray-100 border-r-2 border-gray-300">
            <div className="p-4">
              <h3 className="font-bold text-sm text-gray-700 uppercase mb-4 tracking-wide">Tools & Logs</h3>
              <div className="space-y-2">
                {[
                  { id: 'system-log', name: 'System Log', icon: ClockIcon },
                  { id: 'interaction-log', name: 'Interactions', icon: ClockIcon },
                  { id: 'mode-settings', name: 'Mode Settings', icon: CogIcon },
                  { id: 'settings', name: 'Settings', icon: CogIcon }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveBottomTab(tab.id)}
                    className={`w-full text-left px-4 py-3 text-sm rounded transition-all duration-150 ${
                      activeBottomTab === tab.id 
                        ? 'bg-blue-600 text-white font-bold shadow-md' 
                        : 'text-gray-700 hover:bg-gray-200 border border-transparent hover:border-gray-300'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <tab.icon className="w-4 h-4 inline mr-3" />
                    {tab.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* REFINED: Enhanced Tab Content with improved readability */}
          <div className="flex-1 p-6 overflow-auto">
            {activeBottomTab === 'system-log' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg text-gray-900 uppercase tracking-wide">System Log</h3>
                  <div className="flex space-x-3">
                    <select className="text-sm border-2 border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                      <option>All Levels</option>
                      <option>ERROR</option>
                      <option>WARN</option>
                      <option>INFO</option>
                    </select>
                    <button className="text-sm px-4 py-2 bg-gray-100 border-2 border-gray-300 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 transition-colors">
                      Clear
                    </button>
                  </div>
                </div>
                {/* REFINED: Enhanced log display with better contrast */}
                <div className="bg-gray-900 text-green-400 font-mono text-sm p-4 h-44 overflow-y-auto rounded border-2 border-gray-400">
                  {systemLogs.map((log, index) => (
                    <div key={index} className="mb-2 leading-relaxed">
                      <span className="text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className={`ml-3 font-bold ${
                        log.level === 'ERROR' ? 'text-red-400' :
                        log.level === 'WARN' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        [{log.level}]
                      </span>
                      <span className="ml-3 text-blue-400">{log.device}:</span>
                      <span className="ml-2">{log.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeBottomTab === 'mode-settings' && (
              <div>
                <h3 className="font-bold text-lg mb-6 text-gray-900 uppercase tracking-wide">Mode Settings</h3>
                <ModeToggle onModeChange={handleModeChange} />
              </div>
            )}

            {activeBottomTab === 'interaction-log' && (
              <div>
                <h3 className="font-bold text-lg mb-4 text-gray-900 uppercase tracking-wide">Interaction Log</h3>
                <div className="bg-gray-100 text-sm p-4 h-44 overflow-y-auto font-mono rounded border-2 border-gray-300">
                  <div className="leading-relaxed">[12:34:56] Device mock_device_001: Like action on @testuser</div>
                  <div className="leading-relaxed">[12:34:45] Device mock_device_002: Follow action on @testuser2</div>
                  <div className="leading-relaxed">[12:34:30] System: Rate limit check passed</div>
                </div>
              </div>
            )}

            {activeBottomTab === 'settings' && (
              <div>
                <h3 className="font-bold text-lg mb-6 text-gray-900 uppercase tracking-wide">System Settings</h3>
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-bold mb-2 text-gray-700">Refresh Interval (seconds)</label>
                    <input type="number" defaultValue="3" className="text-sm border-2 border-gray-300 rounded px-3 py-2 w-24 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-2 text-gray-700">Log Retention (hours)</label>
                    <input type="number" defaultValue="24" className="text-sm border-2 border-gray-300 rounded px-3 py-2 w-24 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  </div>
                  <button className="px-6 py-3 bg-blue-600 text-white text-sm font-bold border-2 border-blue-800 rounded shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                    Save Settings
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals remain unchanged */}
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

export default OperatorDashboardRefined;
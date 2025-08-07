import React, { useState, useEffect } from 'react';
import { 
  DevicePhoneMobileIcon, 
  QueueListIcon,
  ChartBarIcon,
  ClockIcon,
  PlayIcon,
  StopIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import TaskManagementPanel from './TaskManagementPanel';
import DeviceManagementPanel from './DeviceManagementPanel';
import SystemMonitoring from './SystemMonitoring';
import TaskHistory from './TaskHistory';
import EngagementCrawler from './EngagementCrawler';
import SettingsPanel from './SettingsPanel';
import InteractionsLog from './InteractionsLog';
import { apiClient } from '../services/api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('tasks');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [systemRunning, setSystemRunning] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch dashboard stats
  const fetchDashboardStats = async () => {
    try {
      const stats = await apiClient.getDashboardStats();
      setDashboardStats(stats);
      setSystemRunning(stats.system_stats.is_running);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
      toast.error('Failed to fetch system stats');
      setLoading(false);
    }
  };

  // Auto-refresh dashboard stats
  useEffect(() => {
    fetchDashboardStats();
    const interval = setInterval(fetchDashboardStats, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const handleSystemToggle = async () => {
    try {
      if (systemRunning) {
        await apiClient.stopSystem();
        toast.success('System stopped');
      } else {
        await apiClient.startSystem();
        toast.success('System started');
      }
      fetchDashboardStats();
    } catch (error) {
      console.error('Failed to toggle system:', error);
      toast.error(`Failed to ${systemRunning ? 'stop' : 'start'} system`);
    }
  };

  const tabs = [
    { id: 'tasks', name: 'Task Management', icon: QueueListIcon },
    { id: 'engagement', name: 'Engagement Crawler', icon: ChatBubbleLeftRightIcon },
    { id: 'devices', name: 'Devices', icon: DevicePhoneMobileIcon },
    { id: 'monitoring', name: 'System Monitor', icon: ChartBarIcon },
    { id: 'history', name: 'Task History', icon: ClockIcon },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <DevicePhoneMobileIcon className="h-8 w-8 text-indigo-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">iOS Instagram Automation</h1>
                <p className="text-sm text-gray-500">Control Center Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* System Status */}
              <div className="flex items-center space-x-2">
                <div className={`h-3 w-3 rounded-full ${systemRunning ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
                <span className="text-sm font-medium text-gray-700">
                  {systemRunning ? 'Running' : 'Stopped'}
                </span>
              </div>
              
              {/* System Control Button */}
              <button
                onClick={handleSystemToggle}
                className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${
                  systemRunning 
                    ? 'bg-red-600 hover:bg-red-700' 
                    : 'bg-green-600 hover:bg-green-700'
                } transition-colors duration-200`}
              >
                {systemRunning ? (
                  <>
                    <StopIcon className="h-4 w-4 mr-2" />
                    Stop System
                  </>
                ) : (
                  <>
                    <PlayIcon className="h-4 w-4 mr-2" />
                    Start System
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Quick Stats Bar */}
      {dashboardStats && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">
                  {dashboardStats.device_status.ready_devices}
                </div>
                <div className="text-xs text-gray-500">Ready Devices</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {dashboardStats.queue_status.total_tasks}
                </div>
                <div className="text-xs text-gray-500">Queued Tasks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {dashboardStats.active_tasks.count}
                </div>
                <div className="text-xs text-gray-500">Active Tasks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {dashboardStats.system_stats.active_workers}
                </div>
                <div className="text-xs text-gray-500">Active Workers</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Tab Navigation */}
        <div className="mb-6">
          <div className="sm:hidden">
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value)}
              className="block w-full rounded-md border-gray-300 py-2 pl-3 pr-10 text-base focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
            >
              {tabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.name}
                </option>
              ))}
            </select>
          </div>
          <div className="hidden sm:block">
            <nav className="flex space-x-8" aria-label="Tabs">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`${
                      activeTab === tab.id
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors duration-200`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {activeTab === 'tasks' && (
            <TaskManagementPanel 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'engagement' && (
            <EngagementCrawler 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'devices' && (
            <DeviceManagementPanel 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'monitoring' && (
            <SystemMonitoring 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'history' && (
            <TaskHistory 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
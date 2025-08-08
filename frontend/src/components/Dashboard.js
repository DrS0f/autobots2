import React, { useState, useEffect } from 'react';
import { 
  DevicePhoneMobileIcon, 
  QueueListIcon,
  ChartBarIcon,
  ClockIcon,
  PlayIcon,
  StopIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  CogIcon,
  DocumentTextIcon,
  KeyIcon,
  RocketLaunchIcon,
  Bars3Icon,
  QuestionMarkCircleIcon,
  StarIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import TaskManagementPanel from './TaskManagementPanel';
import DeviceManagementPanel from './DeviceManagementPanel';
import SystemMonitoring from './SystemMonitoring';
import TaskHistory from './TaskHistory';
import EngagementCrawler from './EngagementCrawler';
import SettingsPanel from './SettingsPanel';
import InteractionsLog from './InteractionsLog';
import LicensePanel from './LicensePanel';
import WorkflowPanel from './WorkflowPanel';
import WelcomeModal from './WelcomeModal';
import GuidedTour from './GuidedTour';
import ScenarioSimulator from './ScenarioSimulator';
import DailyWorkflow from './DailyWorkflow';
import KPIChips from './KPIChips';
import TaskWizard from './TaskWizard';
import WorkflowWizard from './WorkflowWizard';
import StatusStrip from './StatusStrip';
import { FeedbackContainer, feedbackManager } from './ActionFeedback';
import SessionRecoveryBanner from './SessionContinuity';
import { apiClient } from '../services/api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('tasks');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [systemRunning, setSystemRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // New UX state
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  const [showGuidedTour, setShowGuidedTour] = useState(false);
  const [showDailyWorkflow, setShowDailyWorkflow] = useState(false);
  const [showTaskWizard, setShowTaskWizard] = useState(false);
  const [showWorkflowWizard, setShowWorkflowWizard] = useState(false);
  const [currentScenario, setCurrentScenario] = useState('healthy');
  const [hasSeenWelcome, setHasSeenWelcome] = useState(false);
  const [showSessionBanner, setShowSessionBanner] = useState(false);

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

    // Check if user has seen welcome modal before
    const welcomed = localStorage.getItem('hasSeenWelcome');
    if (!welcomed) {
      setTimeout(() => setShowWelcomeModal(true), 1000);
    } else {
      setHasSeenWelcome(true);
    }

    // Check for session recovery
    setTimeout(() => {
      setShowSessionBanner(true);
    }, 500);

    return () => clearInterval(interval);
  }, []);

  // Welcome modal handlers
  const handleWelcomeClose = () => {
    setShowWelcomeModal(false);
    setHasSeenWelcome(true);
    localStorage.setItem('hasSeenWelcome', 'true');
  };

  const handleStartTour = () => {
    setShowWelcomeModal(false);
    setShowGuidedTour(true);
    setHasSeenWelcome(true);
    localStorage.setItem('hasSeenWelcome', 'true');
  };

  const handleUseDemoData = () => {
    setShowWelcomeModal(false);
    setCurrentScenario('backlog_spike');
    setHasSeenWelcome(true);
    localStorage.setItem('hasSeenWelcome', 'true');
    toast.success('Demo scenario loaded! Explore the interface with realistic data.');
  };

  const handleExploreManually = () => {
    setShowWelcomeModal(false);
    setHasSeenWelcome(true);
    localStorage.setItem('hasSeenWelcome', 'true');
  };

  // Tour handlers
  const handleTourClose = () => {
    setShowGuidedTour(false);
  };

  const handleTourStepChange = (tabId) => {
    if (tabId) {
      setActiveTab(tabId);
    }
  };

  // Scenario simulator handlers
  const handleScenarioChange = (scenarioId) => {
    setCurrentScenario(scenarioId);
    feedbackManager.show({
      type: 'info',
      title: 'Scenario Changed',
      message: `Switched to "${scenarioId.replace('_', ' ')}" scenario for realistic testing`,
      autoHide: true,
      duration: 3000
    });
  };

  // Session recovery handlers
  const handleSessionRestore = (draft) => {
    if (draft.type === 'task') {
      // Restore task draft
      setShowTaskWizard(true);
      // TODO: Pass draft data to TaskWizard
      feedbackManager.show({
        type: 'info',
        title: 'Session Restored',
        message: `Restored your ${draft.title} from ${new Date(draft.timestamp).toLocaleString()}`,
        autoHide: true,
        duration: 3000
      });
    } else if (draft.type === 'workflow') {
      // Restore workflow draft
      setShowWorkflowWizard(true);
      // TODO: Pass draft data to WorkflowWizard
      feedbackManager.show({
        type: 'info',
        title: 'Session Restored',
        message: `Restored your ${draft.title} from ${new Date(draft.timestamp).toLocaleString()}`,
        autoHide: true,
        duration: 3000
      });
    }
  };

  // Wizard handlers
  const handleCreateTask = async (taskData) => {
    try {
      const response = await apiClient.createDeviceBoundTask(taskData);
      
      // Enhanced feedback
      feedbackManager.show({
        type: 'success',
        title: 'Task Created Successfully',
        message: `Mock task for @${taskData.target_username || 'user'} has been created and queued for device ${taskData.device_id}`,
        autoHide: true,
        duration: 4000
      });
      
      fetchDashboardStats();
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'Task Creation Failed',
        message: 'There was an error creating the task. Please try again.',
        autoHide: true,
        duration: 5000
      });
    }
  };

  const handleCreateWorkflow = async (templateData, selectedDevices) => {
    try {
      // First create the template
      const templateResponse = await apiClient.createWorkflowTemplate(templateData);
      
      if (templateResponse.success && selectedDevices.length > 0) {
        // Then deploy to selected devices
        const deployResponse = await apiClient.deployWorkflowToDevices(
          templateResponse.template_id,
          { device_ids: selectedDevices }
        );
        
        if (deployResponse.success) {
          feedbackManager.show({
            type: 'success',
            title: 'Workflow Deployed Successfully',
            message: `"${templateData.name}" workflow has been deployed to ${selectedDevices.length} device${selectedDevices.length > 1 ? 's' : ''}`,
            autoHide: true,
            duration: 4000
          });
        }
      } else {
        feedbackManager.show({
          type: 'success',
          title: 'Workflow Template Created',
          message: `"${templateData.name}" workflow template has been saved`,
          autoHide: true,
          duration: 3000
        });
      }
      
      fetchDashboardStats();
    } catch (error) {
      feedbackManager.show({
        type: 'error',
        title: 'Workflow Creation Failed',
        message: 'There was an error creating the workflow. Please try again.',
        autoHide: true,
        duration: 5000
      });
    }
  };

  const handleSystemToggle = async () => {
    try {
      if (systemRunning) {
        await apiClient.stopSystem();
        feedbackManager.show({
          type: 'info',
          title: 'System Stopped',
          message: 'All automation tasks have been paused',
          autoHide: true,
          duration: 3000
        });
      } else {
        await apiClient.startSystem();
        feedbackManager.show({
          type: 'success',
          title: 'System Started',
          message: 'Automation system is now active and processing tasks',
          autoHide: true,
          duration: 3000
        });
      }
      fetchDashboardStats();
    } catch (error) {
      console.error('Failed to toggle system:', error);
      feedbackManager.show({
        type: 'error',
        title: 'System Toggle Failed',
        message: `Failed to ${systemRunning ? 'stop' : 'start'} the automation system`,
        autoHide: true,
        duration: 4000
      });
    }
  };

  const tabs = [
    { id: 'tasks', name: 'Task Management', icon: QueueListIcon },
    { id: 'workflows', name: 'Workflows', icon: RocketLaunchIcon },
    { id: 'engagement', name: 'Engagement Crawler', icon: ChatBubbleLeftRightIcon },
    { id: 'devices', name: 'Devices', icon: DevicePhoneMobileIcon },
    { id: 'monitoring', name: 'System Monitor', icon: ChartBarIcon },
    { id: 'history', name: 'Task History', icon: ClockIcon },
    { id: 'interactions', name: 'Interaction Logs', icon: DocumentTextIcon },
    { id: 'settings', name: 'Settings', icon: CogIcon },
    { id: 'license', name: 'License', icon: KeyIcon },
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
              {/* Help Menu */}
              <button
                onClick={() => setShowGuidedTour(true)}
                className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                title="Start guided tour"
              >
                <QuestionMarkCircleIcon className="h-4 w-4 mr-2" />
                Help
              </button>

              {/* Scenario Simulator */}
              <ScenarioSimulator 
                currentScenario={currentScenario}
                onScenarioChange={handleScenarioChange}
              />

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

      {/* Enhanced Quick Actions & KPI Dashboard */}
      {dashboardStats && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Quick Actions */}
              <div className="lg:col-span-1">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Actions</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => setShowDailyWorkflow(true)}
                      className="w-full flex items-center px-3 py-2 text-sm text-left text-gray-700 bg-white rounded-md hover:bg-gray-100 transition-colors shadow-sm"
                    >
                      <StarIcon className="h-4 w-4 mr-2 text-yellow-500" />
                      Start My Day
                    </button>
                    <button
                      onClick={() => setShowTaskWizard(true)}
                      className="w-full flex items-center px-3 py-2 text-sm text-left text-gray-700 bg-white rounded-md hover:bg-gray-100 transition-colors shadow-sm"
                    >
                      <PlayIcon className="h-4 w-4 mr-2 text-green-500" />
                      Create Task
                    </button>
                    <button
                      onClick={() => setShowWorkflowWizard(true)}
                      className="w-full flex items-center px-3 py-2 text-sm text-left text-gray-700 bg-white rounded-md hover:bg-gray-100 transition-colors shadow-sm"
                    >
                      <RocketLaunchIcon className="h-4 w-4 mr-2 text-purple-500" />
                      Create Workflow
                    </button>
                  </div>
                </div>
              </div>

              {/* KPI Dashboard */}
              <div className="lg:col-span-2">
                <KPIChips dashboardStats={dashboardStats} />
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
              onOpenTaskWizard={() => setShowTaskWizard(true)}
            />
          )}
          {activeTab === 'workflows' && (
            <WorkflowPanel 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
              onOpenWorkflowWizard={() => setShowWorkflowWizard(true)}
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
          {activeTab === 'interactions' && (
            <InteractionsLog 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'settings' && (
            <SettingsPanel 
              dashboardStats={dashboardStats} 
              onRefresh={fetchDashboardStats}
            />
          )}
          {activeTab === 'license' && (
            <LicensePanel />
          )}
        </div>
      </div>

      {/* Welcome Modal */}
      <WelcomeModal
        isOpen={showWelcomeModal}
        onClose={handleWelcomeClose}
        onStartTour={handleStartTour}
        onUseDemoData={handleUseDemoData}
        onExploreManually={handleExploreManually}
      />

      {/* Guided Tour */}
      <GuidedTour
        isActive={showGuidedTour}
        onClose={handleTourClose}
        onStepChange={handleTourStepChange}
        currentTab={activeTab}
      />

      {/* Daily Workflow Modal */}
      {showDailyWorkflow && (
        <DailyWorkflow
          onClose={() => setShowDailyWorkflow(false)}
          dashboardStats={dashboardStats}
        />
      )}

      {/* Task Wizard */}
      <TaskWizard
        isOpen={showTaskWizard}
        onClose={() => setShowTaskWizard(false)}
        onCreateTask={handleCreateTask}
        dashboardStats={dashboardStats}
      />

      {/* Workflow Wizard */}
      <WorkflowWizard
        isOpen={showWorkflowWizard}
        onClose={() => setShowWorkflowWizard(false)}
        onCreateWorkflow={handleCreateWorkflow}
        dashboardStats={dashboardStats}
      />
    </div>
  );
};

export default Dashboard;
import React, { useState } from 'react';
import { 
  PlayIcon,
  CheckIcon,
  ClockIcon,
  DevicePhoneMobileIcon,
  DocumentArrowDownIcon,
  RocketLaunchIcon,
  PlusIcon,
  ArrowPathIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { StarIcon } from '@heroicons/react/24/solid';

const DailyWorkflow = ({ onClose, dashboardStats }) => {
  const [completedTasks, setCompletedTasks] = useState(new Set());

  const dailyTasks = [
    {
      id: 'review_overnight',
      title: 'Review Overnight Tasks',
      description: 'Check completed tasks and any issues from overnight automation',
      icon: ClockIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      estimated: '2 min',
      priority: 'high'
    },
    {
      id: 'check_device_health',
      title: 'Check Device Health',
      description: 'Ensure all devices are connected and ready for automation',
      icon: DevicePhoneMobileIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      estimated: '1 min',
      priority: 'high'
    },
    {
      id: 'deploy_workflow',
      title: 'Deploy Today\'s Workflow',
      description: 'Create or deploy automation workflows for today\'s targets',
      icon: RocketLaunchIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      estimated: '3 min',
      priority: 'medium'
    },
    {
      id: 'monitor_queues',
      title: 'Monitor Task Queues',
      description: 'Review queue status and adjust priorities if needed',
      icon: ChartBarIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      estimated: '2 min',
      priority: 'medium'
    },
    {
      id: 'export_report',
      title: 'Export Daily Report',
      description: 'Generate summary report for yesterday\'s activities',
      icon: DocumentArrowDownIcon,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      estimated: '1 min',
      priority: 'low'
    }
  ];

  const quickActions = [
    {
      id: 'deploy_3_devices',
      title: 'Deploy Workflow to 3 Devices',
      description: 'Quick deployment of your main workflow template',
      action: 'Deploy Now',
      color: 'bg-green-600 hover:bg-green-700'
    },
    {
      id: 'add_5_tasks',
      title: 'Add 5 High-Priority Tasks',
      description: 'Bulk create tasks for immediate execution',
      action: 'Add Tasks',
      color: 'bg-blue-600 hover:bg-blue-700'
    },
    {
      id: 'refresh_all',
      title: 'Refresh All Queues',
      description: 'Update device status and queue information',
      action: 'Refresh',
      color: 'bg-purple-600 hover:bg-purple-700'
    }
  ];

  const handleTaskToggle = (taskId) => {
    const newCompleted = new Set(completedTasks);
    if (newCompleted.has(taskId)) {
      newCompleted.delete(taskId);
    } else {
      newCompleted.add(taskId);
    }
    setCompletedTasks(newCompleted);
  };

  const completedCount = completedTasks.size;
  const totalTasks = dailyTasks.length;
  const progressPercentage = (completedCount / totalTasks) * 100;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-10 h-10 bg-white rounded-full flex items-center justify-center">
                  <StarIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">
                    Start My Day
                  </h3>
                  <p className="text-indigo-100 text-sm">
                    Complete your daily automation checklist ({completedCount}/{totalTasks})
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-indigo-100 hover:text-white transition-colors"
              >
                ×
              </button>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <div className="bg-indigo-400 bg-opacity-30 rounded-full h-2">
                <div 
                  className="bg-white rounded-full h-2 transition-all duration-500"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
              <div className="flex justify-between text-indigo-100 text-xs mt-1">
                <span>Progress</span>
                <span>{Math.round(progressPercentage)}% complete</span>
              </div>
            </div>
          </div>

          <div className="bg-white px-6 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Daily Tasks Checklist */}
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-4">Daily Checklist</h4>
                <div className="space-y-3">
                  {dailyTasks.map((task) => {
                    const isCompleted = completedTasks.has(task.id);
                    const IconComponent = task.icon;
                    
                    return (
                      <div
                        key={task.id}
                        className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                          isCompleted 
                            ? 'border-green-200 bg-green-50' 
                            : `${task.borderColor} ${task.bgColor}`
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <button
                            onClick={() => handleTaskToggle(task.id)}
                            className={`flex-shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                              isCompleted 
                                ? 'border-green-600 bg-green-600' 
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                          >
                            {isCompleted && <CheckIcon className="h-4 w-4 text-white" />}
                          </button>
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <IconComponent className={`h-5 w-5 ${isCompleted ? 'text-green-600' : task.color}`} />
                              <h5 className={`font-medium ${isCompleted ? 'text-green-800 line-through' : 'text-gray-900'}`}>
                                {task.title}
                              </h5>
                              <div className="flex items-center space-x-2">
                                <span className={`text-xs px-2 py-1 rounded-full ${
                                  task.priority === 'high' 
                                    ? 'bg-red-100 text-red-800' 
                                    : task.priority === 'medium'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {task.priority}
                                </span>
                                <span className="text-xs text-gray-500">{task.estimated}</span>
                              </div>
                            </div>
                            <p className={`text-sm mt-1 ${isCompleted ? 'text-green-700' : 'text-gray-600'}`}>
                              {task.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Quick Actions */}
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h4>
                <div className="space-y-4">
                  {quickActions.map((action) => (
                    <div key={action.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="font-medium text-gray-900">{action.title}</h5>
                        <button className={`px-3 py-1 rounded-md text-sm font-medium text-white transition-colors ${action.color}`}>
                          {action.action}
                        </button>
                      </div>
                      <p className="text-sm text-gray-600">{action.description}</p>
                    </div>
                  ))}
                </div>

                {/* System Status Summary */}
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-3">System Status</h5>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {dashboardStats?.device_status?.ready_devices || 0}
                      </div>
                      <div className="text-xs text-gray-500">Ready Devices</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {dashboardStats?.queue_status?.total_tasks || 0}
                      </div>
                      <div className="text-xs text-gray-500">Queued Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {dashboardStats?.active_tasks?.count || 0}
                      </div>
                      <div className="text-xs text-gray-500">Active Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">
                        {dashboardStats?.system_stats?.active_workers || 0}
                      </div>
                      <div className="text-xs text-gray-500">Workers</div>
                    </div>
                  </div>
                  
                  <div className="mt-3 text-center">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      🛡️ Safe Mode Active - Perfect for Testing
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-gray-200 text-center">
              {completedCount === totalTasks ? (
                <div className="text-center">
                  <div className="text-4xl mb-2">🎉</div>
                  <p className="text-lg font-medium text-green-600 mb-2">
                    Great job! You've completed your daily checklist.
                  </p>
                  <p className="text-sm text-gray-600">
                    Your automation system is ready for another productive day!
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  Complete the remaining {totalTasks - completedCount} task{totalTasks - completedCount !== 1 ? 's' : ''} to finish your daily setup
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyWorkflow;
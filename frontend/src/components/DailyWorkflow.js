import React, { useState, useEffect } from 'react';
import { 
  PlayIcon,
  CheckIcon,
  ClockIcon,
  DevicePhoneMobileIcon,
  DocumentArrowDownIcon,
  RocketLaunchIcon,
  PlusIcon,
  ArrowPathIcon,
  ChartBarIcon,
  ListBulletIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { StarIcon } from '@heroicons/react/24/solid';
import { useAutoSave } from './SessionContinuity';

const DailyWorkflow = ({ onClose, dashboardStats, onCreateTask, onCreateWorkflow, onRefresh }) => {
  const [completedTasks, setCompletedTasks] = useState(new Set());
  const [currentPhase, setCurrentPhase] = useState('planning'); // planning, executing, reviewing
  
  // Auto-save progress
  useAutoSave({ 
    completedTasks: Array.from(completedTasks),
    currentPhase,
    timestamp: new Date().toISOString()
  }, 'dailyWorkflow');

  const workflowPhases = {
    planning: {
      title: 'Planning Phase',
      description: 'Set up your automation strategy for today',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    executing: {
      title: 'Execution Phase', 
      description: 'Deploy and monitor your automation tasks',
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    reviewing: {
      title: 'Review Phase',
      description: 'Analyze results and plan for tomorrow',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  };

  const dailyTasks = [
    {
      id: 'review_overnight',
      title: 'Review Overnight Performance',
      description: 'Check completed tasks and success rates from overnight automation',
      icon: ClockIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      estimated: '3 min',
      priority: 'high',
      phase: 'planning',
      action: 'review'
    },
    {
      id: 'check_device_health',
      title: 'Verify Device Readiness',
      description: 'Ensure all devices are connected, charged, and ready for automation',
      icon: DevicePhoneMobileIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      estimated: '2 min',
      priority: 'high',
      phase: 'planning',
      action: 'check'
    },
    {
      id: 'create_daily_workflow',
      title: 'Create Today\'s Workflow',
      description: 'Design and configure automation workflows for today\'s targets',
      icon: RocketLaunchIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      estimated: '5 min',
      priority: 'high',
      phase: 'planning',
      action: 'create_workflow'
    },
    {
      id: 'deploy_tasks',
      title: 'Deploy to Devices',
      description: 'Deploy workflows to selected devices and start automation',
      icon: PlayIcon,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      estimated: '3 min',
      priority: 'high',
      phase: 'executing',
      action: 'deploy'
    },
    {
      id: 'monitor_progress',
      title: 'Monitor Active Tasks',
      description: 'Check task progress, queue status, and handle any issues',
      icon: ChartBarIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      estimated: '4 min',
      priority: 'medium',
      phase: 'executing',
      action: 'monitor'
    },
    {
      id: 'optimize_queues',
      title: 'Optimize Queue Distribution',
      description: 'Balance task distribution across devices for optimal performance',
      icon: ArrowPathIcon,
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
      borderColor: 'border-teal-200',
      estimated: '2 min',
      priority: 'medium',
      phase: 'executing',
      action: 'optimize'
    },
    {
      id: 'review_results',
      title: 'Analyze Performance',
      description: 'Review completion rates, engagement metrics, and success patterns',
      icon: ChartBarIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      estimated: '4 min',
      priority: 'medium',
      phase: 'reviewing',
      action: 'analyze'
    },
    {
      id: 'export_reports',
      title: 'Generate Reports',
      description: 'Export daily performance data and prepare insights for stakeholders',
      icon: DocumentArrowDownIcon,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      estimated: '2 min',
      priority: 'low',
      phase: 'reviewing',
      action: 'export'
    }
  ];

  const quickActions = [
    {
      id: 'create_engagement_workflow',
      title: 'Create Engagement Workflow',
      description: 'Quick setup for targeting users from specific posts',
      action: 'Create Workflow',
      color: 'bg-purple-600 hover:bg-purple-700',
      onClick: () => onCreateWorkflow?.()
    },
    {
      id: 'add_priority_tasks',
      title: 'Add High-Priority Tasks',
      description: 'Quick task creation for immediate execution',
      action: 'Add Tasks',
      color: 'bg-green-600 hover:bg-green-700',
      onClick: () => onCreateTask?.()
    },
    {
      id: 'refresh_system',
      title: 'Refresh System Status',
      description: 'Update device status and queue information',
      action: 'Refresh All',
      color: 'bg-blue-600 hover:bg-blue-700',
      onClick: () => onRefresh?.()
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

    // Auto-advance phases based on task completion
    const task = dailyTasks.find(t => t.id === taskId);
    if (task && newCompleted.has(taskId)) {
      autoAdvancePhase(task.phase, newCompleted);
    }
  };

  const autoAdvancePhase = (taskPhase, completed) => {
    const phaseTasks = dailyTasks.filter(t => t.phase === taskPhase);
    const completedInPhase = phaseTasks.filter(t => completed.has(t.id)).length;
    const totalInPhase = phaseTasks.length;
    
    // Advance phase when 80% of phase tasks are complete
    if (completedInPhase / totalInPhase >= 0.8) {
      if (taskPhase === 'planning' && currentPhase === 'planning') {
        setCurrentPhase('executing');
      } else if (taskPhase === 'executing' && currentPhase === 'executing') {
        setCurrentPhase('reviewing');
      }
    }
  };

  const handleTaskAction = (task) => {
    switch (task.action) {
      case 'create_workflow':
        onCreateWorkflow?.();
        break;
      case 'deploy':
        // Could open deployment modal
        break;
      case 'monitor':
        // Could switch to monitoring tab
        break;
      case 'analyze':
        // Could open analytics view
        break;
      case 'export':
        // Could trigger export modal
        break;
      default:
        // Just mark as completed
        break;
    }
    
    // Auto-complete the task
    setTimeout(() => {
      handleTaskToggle(task.id);
    }, 500);
  };

  const getPhaseProgress = (phase) => {
    const phaseTasks = dailyTasks.filter(t => t.phase === phase);
    const completedInPhase = phaseTasks.filter(t => completedTasks.has(t.id)).length;
    return Math.round((completedInPhase / phaseTasks.length) * 100);
  };

  const getCurrentPhaseTasks = () => {
    return dailyTasks.filter(t => t.phase === currentPhase);
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

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-10 h-10 bg-white rounded-full flex items-center justify-center">
                  <StarIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">
                    Daily Automation Workflow
                  </h3>
                  <p className="text-indigo-100 text-sm">
                    {workflowPhases[currentPhase].title} • {completedCount}/{totalTasks} tasks complete
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
                <span>{workflowPhases[currentPhase].description}</span>
                <span>{Math.round(progressPercentage)}% complete</span>
              </div>
            </div>

            {/* Phase Navigation */}
            <div className="mt-4 flex items-center justify-between">
              {Object.entries(workflowPhases).map(([phase, config]) => (
                <button
                  key={phase}
                  onClick={() => setCurrentPhase(phase)}
                  className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    currentPhase === phase 
                      ? 'bg-white text-indigo-600' 
                      : 'text-indigo-200 hover:text-white'
                  }`}
                >
                  <span>{config.title}</span>
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                    currentPhase === phase ? 'bg-indigo-600 text-white' : 'bg-indigo-400 text-indigo-100'
                  }`}>
                    {getPhaseProgress(phase)}%
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="bg-white px-6 py-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Current Phase Tasks */}
              <div className="lg:col-span-2">
                <div className="flex items-center space-x-2 mb-4">
                  <h4 className="text-lg font-medium text-gray-900">
                    {workflowPhases[currentPhase].title}
                  </h4>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${workflowPhases[currentPhase].bgColor} ${workflowPhases[currentPhase].color}`}>
                    {getCurrentPhaseTasks().filter(t => completedTasks.has(t.id)).length}/{getCurrentPhaseTasks().length} complete
                  </span>
                </div>
                
                <div className="space-y-3">
                  {getCurrentPhaseTasks().map((task) => {
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
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <IconComponent className={`h-5 w-5 ${isCompleted ? 'text-green-600' : task.color}`} />
                                <h5 className={`font-medium ${isCompleted ? 'text-green-800 line-through' : 'text-gray-900'}`}>
                                  {task.title}
                                </h5>
                              </div>
                              
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

                            {task.action && !isCompleted && (
                              <button
                                onClick={() => handleTaskAction(task)}
                                className={`mt-2 inline-flex items-center px-3 py-1 rounded-md text-xs font-medium text-white transition-colors ${
                                  task.color.includes('blue') ? 'bg-blue-600 hover:bg-blue-700' :
                                  task.color.includes('green') ? 'bg-green-600 hover:bg-green-700' :
                                  task.color.includes('purple') ? 'bg-purple-600 hover:bg-purple-700' :
                                  'bg-indigo-600 hover:bg-indigo-700'
                                }`}
                              >
                                <PlayIcon className="h-3 w-3 mr-1" />
                                Start Task
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Sidebar */}
              <div className="space-y-6">
                {/* Quick Actions */}
                <div>
                  <h4 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h4>
                  <div className="space-y-3">
                    {quickActions.map((action) => (
                      <button
                        key={action.id}
                        onClick={action.onClick}
                        className={`w-full p-3 rounded-lg border border-gray-200 hover:shadow-sm transition-all text-left ${action.color}`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <h5 className="font-medium text-white text-sm">{action.title}</h5>
                        </div>
                        <p className="text-xs text-white opacity-90">{action.description}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* System Status Summary */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                    <CheckCircleIcon className="h-4 w-4 mr-2 text-green-600" />
                    System Status
                  </h5>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center">
                      <div className="text-xl font-bold text-green-600">
                        {dashboardStats?.device_status?.ready_devices || 0}
                      </div>
                      <div className="text-xs text-gray-500">Ready Devices</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-blue-600">
                        {dashboardStats?.queue_status?.total_tasks || 0}
                      </div>
                      <div className="text-xs text-gray-500">Queued Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-purple-600">
                        {dashboardStats?.active_tasks?.count || 0}
                      </div>
                      <div className="text-xs text-gray-500">Active Tasks</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-yellow-600">
                        {dashboardStats?.system_stats?.active_workers || 0}
                      </div>
                      <div className="text-xs text-gray-500">Workers</div>
                    </div>
                  </div>
                  
                  <div className="mt-3 text-center">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      🛡️ Safe Mode Active - Perfect for Planning
                    </span>
                  </div>
                </div>

                {/* All Phases Overview */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-medium text-gray-900 mb-3 flex items-center">
                    <ListBulletIcon className="h-4 w-4 mr-2 text-gray-600" />
                    Overall Progress
                  </h5>
                  <div className="space-y-3">
                    {Object.entries(workflowPhases).map(([phase, config]) => (
                      <div key={phase} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            phase === currentPhase ? 'bg-indigo-600' : 'bg-gray-300'
                          }`} />
                          <span className="text-sm text-gray-700">{config.title}</span>
                        </div>
                        <span className="text-sm font-medium text-gray-900">
                          {getPhaseProgress(phase)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              {completedCount === totalTasks ? (
                <div className="text-center">
                  <div className="text-6xl mb-4">🎉</div>
                  <h3 className="text-xl font-medium text-green-600 mb-2">
                    Daily Workflow Complete!
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Excellent work! Your automation system is optimized and running smoothly.
                  </p>
                  <div className="flex justify-center space-x-3">
                    <button
                      onClick={onClose}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                    >
                      Continue to Dashboard
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-3">
                    Complete the remaining {totalTasks - completedCount} task{totalTasks - completedCount !== 1 ? 's' : ''} in the {workflowPhases[currentPhase].title.toLowerCase()} to optimize your automation system.
                  </p>
                  <div className="flex justify-center space-x-3">
                    <button
                      onClick={() => {
                        // Auto-complete current phase
                        const phaseTasks = getCurrentPhaseTasks();
                        const newCompleted = new Set(completedTasks);
                        phaseTasks.forEach(task => newCompleted.add(task.id));
                        setCompletedTasks(newCompleted);
                      }}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                    >
                      Complete Current Phase
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyWorkflow;
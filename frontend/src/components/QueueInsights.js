import React, { useState, useEffect } from 'react';
import { 
  ClockIcon,
  PlayIcon,
  PauseIcon,
  ChartBarIcon,
  DevicePhoneMobileIcon,
  QueueListIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow, addMinutes, addHours } from 'date-fns';

const QueueInsights = ({ deviceId, queueData, pacingRules, className = '' }) => {
  const [nextActionETA, setNextActionETA] = useState(null);
  const [queueAnalysis, setQueueAnalysis] = useState({});

  useEffect(() => {
    if (queueData && pacingRules) {
      calculateQueueInsights();
    }
  }, [queueData, pacingRules]);

  const calculateQueueInsights = () => {
    const analysis = performQueueAnalysis(queueData, pacingRules);
    setQueueAnalysis(analysis);
    setNextActionETA(analysis.nextActionETA);
  };

  const performQueueAnalysis = (queue, pacing) => {
    const now = new Date();
    const queueLength = queue?.queue_length || 0;
    const currentTask = queue?.current_task;
    const pacingStats = queue?.pacing_stats || {};
    
    // Calculate next action ETA based on pacing rules
    let nextETA = now;
    
    if (currentTask) {
      // Device is busy - add estimated completion time
      const avgTaskDuration = pacing.avgTaskDuration || 120; // 2 minutes default
      nextETA = addMinutes(now, avgTaskDuration / 60);
    } else if (pacingStats.in_rest_window) {
      // Device is in rest window
      nextETA = new Date(pacingStats.cooldown_until || now);
    } else if (pacingStats.actions_this_hour >= pacingStats.rate_limits?.actions_per_hour) {
      // Hit rate limit - wait until next hour
      const nextHour = new Date(now);
      nextHour.setHours(now.getHours() + 1, 0, 0, 0);
      nextETA = nextHour;
    } else {
      // Device is available - can start immediately or with minimal delay
      nextETA = addMinutes(now, Math.random() * 2 + 1); // 1-3 minute delay
    }

    // Calculate total queue completion time
    const avgTaskDuration = pacing.avgTaskDuration || 120;
    const actionsPerHour = pacingStats.rate_limits?.actions_per_hour || 60;
    const maxConcurrent = pacingStats.max_concurrent || 1;
    
    const totalCompletionTime = calculateTotalQueueTime(queueLength, avgTaskDuration, actionsPerHour);
    const queueCompletionETA = addMinutes(nextETA, totalCompletionTime);

    // Determine queue health
    const queueHealth = getQueueHealth(queueLength, pacingStats, pacing);

    return {
      nextActionETA: nextETA,
      queueCompletionETA,
      estimatedWaitTime: Math.round((nextETA - now) / 60000), // minutes
      totalCompletionTime: Math.round(totalCompletionTime),
      queueHealth,
      throughputPerHour: actionsPerHour,
      utilizationRate: calculateUtilizationRate(pacingStats, actionsPerHour),
      pacingStatus: getPacingStatus(pacingStats, pacing)
    };
  };

  const calculateTotalQueueTime = (queueLength, avgTaskDuration, actionsPerHour) => {
    if (queueLength === 0) return 0;
    
    const tasksPerMinute = actionsPerHour / 60;
    const totalMinutes = queueLength / tasksPerMinute;
    
    return Math.max(totalMinutes, queueLength * (avgTaskDuration / 60)); // Take the longer time
  };

  const calculateUtilizationRate = (pacingStats, maxActionsPerHour) => {
    const currentRate = pacingStats.actions_this_hour || 0;
    return Math.min((currentRate / maxActionsPerHour) * 100, 100);
  };

  const getQueueHealth = (queueLength, pacingStats, pacing) => {
    if (queueLength === 0) return 'idle';
    if (queueLength <= 5) return 'healthy';
    if (queueLength <= 15) return 'busy';
    if (queueLength <= 30) return 'high';
    return 'overloaded';
  };

  const getPacingStatus = (pacingStats, pacing) => {
    if (pacingStats.in_rest_window) return 'resting';
    if (pacingStats.actions_this_hour >= pacingStats.rate_limits?.actions_per_hour) return 'rate_limited';
    if (pacingStats.current_task) return 'active';
    return 'ready';
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'idle': return 'text-gray-500 bg-gray-50 border-gray-200';
      case 'healthy': return 'text-green-600 bg-green-50 border-green-200';
      case 'busy': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'overloaded': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-500 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <PlayIcon className="h-4 w-4 text-green-600" />;
      case 'resting': return <PauseIcon className="h-4 w-4 text-yellow-600" />;
      case 'rate_limited': return <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />;
      case 'ready': return <ClockIcon className="h-4 w-4 text-blue-600" />;
      default: return <ClockIcon className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatETA = (eta) => {
    if (!eta) return 'Unknown';
    
    const now = new Date();
    const diffMinutes = Math.round((eta - now) / 60000);
    
    if (diffMinutes <= 0) return 'Now';
    if (diffMinutes === 1) return '1 minute';
    if (diffMinutes < 60) return `${diffMinutes} minutes`;
    
    const hours = Math.floor(diffMinutes / 60);
    const mins = diffMinutes % 60;
    return `${hours}h ${mins}m`;
  };

  if (!queueData) return null;

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-900 flex items-center">
          <QueueListIcon className="h-4 w-4 mr-2" />
          Queue Insights
        </h3>
        
        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${
          getHealthColor(queueAnalysis.queueHealth)
        }`}>
          {queueAnalysis.queueHealth}
        </div>
      </div>

      {/* Primary Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {formatETA(nextActionETA)}
          </div>
          <div className="text-xs text-gray-500">Next Action ETA</div>
        </div>
        
        <div className="text-center">
          <div className="text-lg font-semibold text-gray-900">
            {queueData.queue_length || 0}
          </div>
          <div className="text-xs text-gray-500">Queued Tasks</div>
        </div>
      </div>

      {/* Status Information */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Status</span>
          <div className="flex items-center space-x-1">
            {getStatusIcon(queueAnalysis.pacingStatus)}
            <span className="font-medium capitalize">{queueAnalysis.pacingStatus?.replace('_', ' ')}</span>
          </div>
        </div>
        
        {queueData.current_task && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Current Task</span>
            <span className="font-mono text-xs">
              {queueData.current_task.task_id?.substring(0, 8)}...
            </span>
          </div>
        )}
        
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Queue Completion</span>
          <span className="font-medium">
            {formatETA(queueAnalysis.queueCompletionETA)}
          </span>
        </div>
      </div>

      {/* Pacing Information */}
      <div className="border-t border-gray-100 pt-3">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
          <span>Pacing Utilization</span>
          <span>{Math.round(queueAnalysis.utilizationRate || 0)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              queueAnalysis.utilizationRate > 80 ? 'bg-red-500' :
              queueAnalysis.utilizationRate > 60 ? 'bg-yellow-500' :
              'bg-green-500'
            }`}
            style={{ width: `${queueAnalysis.utilizationRate || 0}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
          <span>
            {queueData.pacing_stats?.actions_this_hour || 0}/{queueData.pacing_stats?.rate_limits?.actions_per_hour || 60} actions/hour
          </span>
          <span>
            {queueAnalysis.throughputPerHour || 0}/hr throughput
          </span>
        </div>
      </div>

      {/* Warnings or Recommendations */}
      {queueAnalysis.queueHealth === 'overloaded' && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
            <span className="text-xs font-medium text-red-800">
              Queue Overloaded
            </span>
          </div>
          <p className="text-xs text-red-700 mt-1">
            Consider deploying this workflow to additional devices to improve throughput.
          </p>
        </div>
      )}

      {queueAnalysis.pacingStatus === 'rate_limited' && (
        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-center space-x-2">
            <ClockIcon className="h-4 w-4 text-yellow-500" />
            <span className="text-xs font-medium text-yellow-800">
              Rate Limited
            </span>
          </div>
          <p className="text-xs text-yellow-700 mt-1">
            Device has reached hourly rate limit. Next tasks will resume at {
              queueData.pacing_stats?.rate_window_start ? 
              formatDistanceToNow(addHours(new Date(queueData.pacing_stats.rate_window_start), 1), { addSuffix: true }) :
              'top of next hour'
            }.
          </p>
        </div>
      )}
    </div>
  );
};

export default QueueInsights;
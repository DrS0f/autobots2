import React from 'react';
import { 
  QueueListIcon,
  CheckCircleIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ClockIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  DevicePhoneMobileIcon
} from '@heroicons/react/24/outline';
import { InfoTooltip } from './Tooltip';

const KPIChips = ({ 
  dashboardStats = {}, 
  className = '',
  showMockData = true 
}) => {
  // Generate mock KPI data for demonstration
  const getMockKPIs = () => {
    return {
      actions_queued: Math.floor(Math.random() * 50) + 10,
      actions_completed: Math.floor(Math.random() * 200) + 150,
      success_rate: (Math.random() * 0.2 + 0.8).toFixed(1), // 80-100%
      duplicates_prevented: Math.floor(Math.random() * 30) + 5,
      active_devices: Math.floor(Math.random() * 3) + 1,
      avg_response_time: Math.floor(Math.random() * 1000) + 500,
      tasks_this_hour: Math.floor(Math.random() * 20) + 5,
      uptime_percentage: (Math.random() * 5 + 95).toFixed(1) // 95-100%
    };
  };

  const mockKPIs = showMockData ? getMockKPIs() : {};
  
  const kpis = [
    {
      id: 'actions_queued',
      label: 'Actions Queued',
      value: mockKPIs.actions_queued || dashboardStats.queue_status?.total_tasks || 0,
      icon: QueueListIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      tooltip: 'Total automation actions waiting in device queues'
    },
    {
      id: 'actions_completed',
      label: 'Completed Today',
      value: mockKPIs.actions_completed || 0,
      icon: CheckCircleIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      tooltip: 'Successfully completed actions in the last 24 hours'
    },
    {
      id: 'success_rate',
      label: 'Success Rate',
      value: `${mockKPIs.success_rate || '95.0'}%`,
      icon: ChartBarIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      tooltip: 'Percentage of successful automation actions'
    },
    {
      id: 'duplicates_prevented',
      label: 'Duplicates Blocked',
      value: mockKPIs.duplicates_prevented || 0,
      icon: ShieldCheckIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      tooltip: 'Duplicate interactions prevented by smart filtering'
    },
    {
      id: 'active_devices',
      label: 'Active Devices',
      value: mockKPIs.active_devices || dashboardStats.device_status?.ready_devices || 0,
      icon: DevicePhoneMobileIcon,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      tooltip: 'Number of connected and active iOS devices'
    },
    {
      id: 'avg_response',
      label: 'Avg Response',
      value: `${mockKPIs.avg_response_time || 750}ms`,
      icon: ClockIcon,
      color: 'text-teal-600',
      bgColor: 'bg-teal-50',
      borderColor: 'border-teal-200',
      tooltip: 'Average response time for automation actions'
    },
    {
      id: 'tasks_hourly',
      label: 'Tasks/Hour',
      value: mockKPIs.tasks_this_hour || 0,
      icon: ArrowTrendingUpIcon,
      color: 'text-rose-600',
      bgColor: 'bg-rose-50',
      borderColor: 'border-rose-200',
      tooltip: 'Tasks completed in the current hour'
    },
    {
      id: 'system_uptime',
      label: 'System Uptime',
      value: `${mockKPIs.uptime_percentage || '99.2'}%`,
      icon: CheckCircleIcon,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      borderColor: 'border-emerald-200',
      tooltip: 'System availability and uptime percentage'
    }
  ];

  return (
    <div className={`grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8 gap-3 ${className}`}>
      {kpis.map((kpi) => {
        const IconComponent = kpi.icon;
        
        return (
          <div
            key={kpi.id}
            className={`relative p-3 rounded-lg border ${kpi.borderColor} ${kpi.bgColor} hover:shadow-sm transition-shadow duration-200`}
          >
            <div className="flex items-center justify-between mb-2">
              <IconComponent className={`h-4 w-4 ${kpi.color}`} />
              <InfoTooltip 
                content={kpi.tooltip}
                position="top"
                className="ml-1"
              />
            </div>
            
            <div className="space-y-1">
              <div className={`text-lg font-semibold ${kpi.color}`}>
                {kpi.value}
              </div>
              <div className="text-xs text-gray-600 leading-tight">
                {kpi.label}
              </div>
            </div>

            {/* Safe Mode Indicator for mock data */}
            {showMockData && (
              <div className="absolute top-1 right-1">
                <div className="w-2 h-2 bg-yellow-400 rounded-full" 
                     title="Mock data - Safe Mode active" />
              </div>
            )}
          </div>
        );
      })}

      {/* Safe Mode Notice */}
      {showMockData && (
        <div className="col-span-full">
          <div className="flex items-center justify-center space-x-2 text-xs text-yellow-700 bg-yellow-50 rounded-lg p-2 border border-yellow-200">
            <span>🛡️</span>
            <span>Displaying mock KPI data - Safe Mode active</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default KPIChips;
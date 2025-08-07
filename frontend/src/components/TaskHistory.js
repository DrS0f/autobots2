import React, { useState, useMemo } from 'react';
import { 
  ClockIcon, 
  MagnifyingGlassIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  PlayCircleIcon
} from '@heroicons/react/24/outline';
import { format, formatDistanceToNow } from 'date-fns';

const TaskHistory = ({ dashboardStats, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('completed_at');
  const [sortDirection, setSortDirection] = useState('desc');

  // Mock task history data - in real implementation, this would come from API
  const taskHistory = useMemo(() => {
    const mockTasks = [
      {
        task_id: 'task-1',
        target_username: 'luxurylifestylemag',
        task_type: 'follow_and_like',
        status: 'completed',
        priority: 'normal',
        started_at: new Date(Date.now() - 3600000), // 1 hour ago
        completed_at: new Date(Date.now() - 3300000), // 55 minutes ago
        duration: 300,
        device_name: 'iPhone 13 Pro',
        actions_completed: 5,
        likes_given: 3,
        followed: 1,
        error_message: null
      },
      {
        task_id: 'task-2',
        target_username: 'techstartups',
        task_type: 'like_only',
        status: 'failed',
        priority: 'high',
        started_at: new Date(Date.now() - 7200000), // 2 hours ago
        completed_at: new Date(Date.now() - 6900000), // 1h 55m ago
        duration: 180,
        device_name: 'iPhone 14',
        actions_completed: 2,
        likes_given: 0,
        followed: 0,
        error_message: 'Failed to find user profile'
      },
      {
        task_id: 'task-3',
        target_username: 'foodblogger',
        task_type: 'follow_and_like',
        status: 'completed',
        priority: 'low',
        started_at: new Date(Date.now() - 10800000), // 3 hours ago
        completed_at: new Date(Date.now() - 10200000), // 2h 50m ago
        duration: 420,
        device_name: 'iPhone 12',
        actions_completed: 6,
        likes_given: 5,
        followed: 1,
        error_message: null
      },
      {
        task_id: 'task-4',
        target_username: 'travelphotographer',
        task_type: 'like_only',
        status: 'cancelled',
        priority: 'normal',
        started_at: new Date(Date.now() - 14400000), // 4 hours ago
        completed_at: new Date(Date.now() - 14200000), // 3h 57m ago
        duration: 60,
        device_name: 'iPhone 13',
        actions_completed: 1,
        likes_given: 0,
        followed: 0,
        error_message: null
      }
    ];
    
    // Add recent results from dashboard stats if available
    if (dashboardStats?.recent_results) {
      const recentTasks = dashboardStats.recent_results.map(result => ({
        task_id: result.task_id,
        target_username: 'unknown',
        task_type: 'automation',
        status: result.success ? 'completed' : 'failed',
        priority: 'normal',
        started_at: new Date(result.completed_at * 1000 - result.duration * 1000),
        completed_at: new Date(result.completed_at * 1000),
        duration: result.duration,
        device_name: 'Unknown Device',
        actions_completed: 0,
        likes_given: 0,
        followed: 0,
        error_message: result.error
      }));
      return [...recentTasks, ...mockTasks];
    }
    
    return mockTasks;
  }, [dashboardStats]);

  // Filter and sort tasks
  const filteredAndSortedTasks = useMemo(() => {
    let filtered = taskHistory;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(task =>
        task.target_username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        task.task_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(task => task.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (sortField.includes('_at')) {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [taskHistory, searchTerm, statusFilter, sortField, sortDirection]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'cancelled':
        return <XCircleIcon className="h-5 w-5 text-gray-500" />;
      default:
        return <PlayCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-blue-100 text-blue-800`;
    }
  };

  const getPriorityBadge = (priority) => {
    const baseClasses = "inline-flex items-center px-2 py-1 rounded text-xs font-medium";
    switch (priority) {
      case 'urgent':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'high':
        return `${baseClasses} bg-orange-100 text-orange-800`;
      case 'normal':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'low':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) {
      return <ChevronUpIcon className="h-4 w-4 text-gray-400" />;
    }
    return sortDirection === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4 text-gray-900" />
      : <ChevronDownIcon className="h-4 w-4 text-gray-900" />;
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Task History</h2>
          <p className="text-sm text-gray-500">View and analyze completed automation tasks</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1">
          <div className="relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by username or task ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {taskHistory.filter(t => t.status === 'completed').length}
          </div>
          <div className="text-sm text-green-800">Completed</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-red-600">
            {taskHistory.filter(t => t.status === 'failed').length}
          </div>
          <div className="text-sm text-red-800">Failed</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-gray-600">
            {taskHistory.filter(t => t.status === 'cancelled').length}
          </div>
          <div className="text-sm text-gray-800">Cancelled</div>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">
            {Math.round(taskHistory.reduce((acc, task) => acc + task.duration, 0) / taskHistory.length) || 0}s
          </div>
          <div className="text-sm text-blue-800">Avg Duration</div>
        </div>
      </div>

      {/* Task Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('target_username')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Username</span>
                    <SortIcon field="target_username" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Task Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Priority
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('started_at')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Started</span>
                    <SortIcon field="started_at" />
                  </div>
                </th>
                <th 
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('duration')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Duration</span>
                    <SortIcon field="duration" />
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Results
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedTasks.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-12 text-center text-gray-500">
                    <ClockIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>No task history found</p>
                    <p className="text-sm">Tasks will appear here after completion</p>
                  </td>
                </tr>
              ) : (
                filteredAndSortedTasks.map((task) => (
                  <tr key={task.task_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(task.status)}
                        <span className={`ml-2 ${getStatusBadge(task.status)}`}>
                          {task.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">@{task.target_username}</div>
                      <div className="text-sm text-gray-500">{task.task_id.substring(0, 8)}...</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {task.task_type.replace('_', ' & ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={getPriorityBadge(task.priority)}>
                        {task.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div>{format(task.started_at, 'MMM dd, HH:mm')}</div>
                      <div className="text-xs text-gray-500">
                        {formatDistanceToNow(task.started_at, { addSuffix: true })}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {Math.round(task.duration)}s
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {task.status === 'completed' ? (
                        <div>
                          <div>❤️ {task.likes_given} likes</div>
                          <div>👥 {task.followed} follows</div>
                        </div>
                      ) : task.error_message ? (
                        <div className="text-red-600 text-xs">{task.error_message}</div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {task.device_name}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TaskHistory;
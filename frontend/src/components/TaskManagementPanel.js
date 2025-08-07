import React, { useState } from 'react';
import { 
  PlusIcon, 
  XMarkIcon, 
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  QueueListIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiClient } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

const TaskManagementPanel = ({ dashboardStats, onRefresh }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    target_username: '',
    actions: ['search_user', 'view_profile', 'like_post', 'follow_user', 'navigate_home'],
    max_likes: 3,
    max_follows: 1,
    priority: 'normal'
  });
  const [creating, setCraving] = useState(false);

  const handleCreateTask = async (e) => {
    e.preventDefault();
    if (!formData.target_username.trim()) {
      toast.error('Please enter a valid Instagram username');
      return;
    }

    setCraving(true);
    try {
      const result = await apiClient.createTask({
        ...formData,
        target_username: formData.target_username.replace('@', '') // Remove @ if present
      });
      
      toast.success(`Task created for @${formData.target_username}`);
      setShowCreateForm(false);
      setFormData({
        target_username: '',
        actions: ['search_user', 'view_profile', 'like_post', 'follow_user', 'navigate_home'],
        max_likes: 3,
        max_follows: 1,
        priority: 'normal'
      });
      onRefresh();
    } catch (error) {
      toast.error('Failed to create task');
      console.error('Task creation error:', error);
    } finally {
      setCraving(false);
    }
  };

  const handleCancelTask = async (taskId) => {
    try {
      await apiClient.cancelTask(taskId);
      toast.success('Task cancelled');
      onRefresh();
    } catch (error) {
      toast.error('Failed to cancel task');
      console.error('Task cancellation error:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
      case 'queued':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'running':
        return <PlayIcon className="h-5 w-5 text-blue-500 animate-pulse" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
      case 'cancelled':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (status) {
      case 'pending':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'queued':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'running':
        return `${baseClasses} bg-indigo-100 text-indigo-800`;
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'cancelled':
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-medium text-gray-900">Task Management</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Task
        </button>
      </div>

      {/* Create Task Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <form onSubmit={handleCreateTask}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Create New Task</h3>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Instagram Username
                      </label>
                      <input
                        type="text"
                        value={formData.target_username}
                        onChange={(e) => setFormData({...formData, target_username: e.target.value})}
                        placeholder="luxurylifestylemag"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Task Priority
                      </label>
                      <select
                        value={formData.priority}
                        onChange={(e) => setFormData({...formData, priority: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="low">Low</option>
                        <option value="normal">Normal</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                      </select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Max Likes
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          value={formData.max_likes}
                          onChange={(e) => setFormData({...formData, max_likes: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Follow User
                        </label>
                        <select
                          value={formData.max_follows}
                          onChange={(e) => setFormData({...formData, max_follows: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value={0}>No</option>
                          <option value={1}>Yes</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Actions to Perform
                      </label>
                      <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
                        <ul className="list-disc list-inside space-y-1">
                          <li>Search for user</li>
                          <li>View profile</li>
                          <li>Like up to {formData.max_likes} posts</li>
                          {formData.max_follows === 1 && <li>Follow user</li>}
                          <li>Return to home screen</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    disabled={creating}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creating ? 'Creating...' : 'Create Task'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Task Queue */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Task Queue ({dashboardStats?.queue_status?.total_tasks || 0})</h3>
        
        {dashboardStats?.queue_status?.tasks?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <QueueListIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
            <p>No tasks in queue</p>
            <p className="text-sm">Create a new task to get started</p>
          </div>
        ) : (
          <div className="space-y-3">
            {dashboardStats?.queue_status?.tasks?.map((task) => (
              <div key={task.task_id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(task.status)}
                    <div>
                      <div className="font-medium text-gray-900">@{task.target_username}</div>
                      <div className="text-sm text-gray-500">
                        Priority: {task.priority} • 
                        Created {formatDistanceToNow(new Date(task.created_at * 1000), { addSuffix: true })}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className={getStatusBadge(task.status)}>
                      {task.status}
                    </span>
                    {(task.status === 'pending' || task.status === 'queued') && (
                      <button
                        onClick={() => handleCancelTask(task.task_id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Active Tasks */}
        {dashboardStats?.active_tasks?.tasks?.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Currently Running ({dashboardStats.active_tasks.count})</h3>
            <div className="space-y-3">
              {dashboardStats.active_tasks.tasks.map((task) => (
                <div key={task.task_id} className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <PlayIcon className="h-5 w-5 text-blue-500 animate-pulse" />
                      <div>
                        <div className="font-medium text-gray-900">@{task.target_username}</div>
                        <div className="text-sm text-gray-600">
                          Running for {formatDistanceToNow(new Date(task.started_at * 1000), { addSuffix: true })} • 
                          Device: {task.device_name}
                        </div>
                      </div>
                    </div>
                    
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Running
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tasks Waiting for Account Availability */}
        {dashboardStats?.waiting_tasks?.total_waiting > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Waiting on Account Availability ({dashboardStats.waiting_tasks.total_waiting})
            </h3>
            <div className="space-y-3">
              {Object.entries(dashboardStats.waiting_tasks.by_account || {}).map(([accountId, taskIds]) => (
                <div key={accountId} className="border border-amber-200 rounded-lg p-4 bg-amber-50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <ClockIcon className="h-5 w-5 text-amber-500" />
                      <div>
                        <div className="font-medium text-gray-900">
                          Account: {accountId.length > 20 ? `${accountId.substring(0, 20)}...` : accountId}
                        </div>
                        <div className="text-sm text-amber-700">
                          {taskIds.length} task{taskIds.length !== 1 ? 's' : ''} waiting
                        </div>
                      </div>
                    </div>
                    
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                      Waiting on Account
                    </span>
                  </div>
                  
                  {/* Show waiting task IDs (limited to first 3) */}
                  <div className="text-xs text-gray-600 mt-2">
                    Tasks: {taskIds.slice(0, 3).join(', ')}
                    {taskIds.length > 3 && ` (+${taskIds.length - 3} more)`}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-blue-50 rounded-md">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-4 w-4 text-blue-400" />
                </div>
                <div className="ml-2 text-xs text-blue-700">
                  <strong>Note:</strong> These tasks are waiting because their assigned account is currently 
                  running another task or is in cooldown. They will automatically start when the account becomes available.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskManagementPanel;
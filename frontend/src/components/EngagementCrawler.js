import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  XMarkIcon, 
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  HeartIcon,
  ChatBubbleLeftIcon,
  UserPlusIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiClient } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

const EngagementCrawler = ({ dashboardStats, onRefresh }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [engagementStats, setEngagementStats] = useState(null);
  const [engagementHistory, setEngagementHistory] = useState(null);
  const [formData, setFormData] = useState({
    target_pages: [''],
    comment_list: ['Great post! 🔥', 'Love this content! 💯', 'Amazing! 👏', 'So inspiring! ✨', 'Awesome work! 🙌'],
    actions: {
      follow: true,
      like: true,
      comment: true
    },
    max_users_per_page: 20,
    profile_validation: {
      public_only: true,
      min_posts: 2
    },
    skip_rate: 0.15,
    priority: 'normal'
  });
  const [creating, setCreating] = useState(false);

  // Fetch engagement data
  useEffect(() => {
    fetchEngagementData();
  }, []);

  const fetchEngagementData = async () => {
    try {
      const [stats, history] = await Promise.all([
        apiClient.getEngagementDashboardStats(),
        apiClient.getEngagementHistory()
      ]);
      setEngagementStats(stats);
      setEngagementHistory(history);
    } catch (error) {
      console.error('Failed to fetch engagement data:', error);
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    
    // Validate form
    const validTargetPages = formData.target_pages.filter(page => page.trim());
    const validComments = formData.comment_list.filter(comment => comment.trim());
    
    if (validTargetPages.length === 0) {
      toast.error('Please add at least one target page');
      return;
    }
    
    if (validComments.length === 0) {
      toast.error('Please add at least one comment');
      return;
    }

    setCreating(true);
    try {
      const result = await apiClient.createEngagementTask({
        ...formData,
        target_pages: validTargetPages,
        comment_list: validComments
      });
      
      toast.success('Engagement task created successfully!');
      setShowCreateForm(false);
      resetForm();
      fetchEngagementData();
      onRefresh();
    } catch (error) {
      toast.error('Failed to create engagement task');
      console.error('Engagement task creation error:', error);
    } finally {
      setCreating(false);
    }
  };

  const resetForm = () => {
    setFormData({
      target_pages: [''],
      comment_list: ['Great post! 🔥', 'Love this content! 💯', 'Amazing! 👏', 'So inspiring! ✨', 'Awesome work! 🙌'],
      actions: {
        follow: true,
        like: true,
        comment: true
      },
      max_users_per_page: 20,
      profile_validation: {
        public_only: true,
        min_posts: 2
      },
      skip_rate: 0.15,
      priority: 'normal'
    });
  };

  const handleTargetPageChange = (index, value) => {
    const newPages = [...formData.target_pages];
    newPages[index] = value;
    setFormData({...formData, target_pages: newPages});
  };

  const addTargetPage = () => {
    setFormData({
      ...formData,
      target_pages: [...formData.target_pages, '']
    });
  };

  const removeTargetPage = (index) => {
    const newPages = formData.target_pages.filter((_, i) => i !== index);
    setFormData({...formData, target_pages: newPages});
  };

  const handleCommentChange = (index, value) => {
    const newComments = [...formData.comment_list];
    newComments[index] = value;
    setFormData({...formData, comment_list: newComments});
  };

  const addComment = () => {
    setFormData({
      ...formData,
      comment_list: [...formData.comment_list, '']
    });
  };

  const removeComment = (index) => {
    const newComments = formData.comment_list.filter((_, i) => i !== index);
    setFormData({...formData, comment_list: newComments});
  };

  const handleActionToggle = (action) => {
    setFormData({
      ...formData,
      actions: {
        ...formData.actions,
        [action]: !formData.actions[action]
      }
    });
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
        <div>
          <h2 className="text-lg font-medium text-gray-900">Engagement Crawler</h2>
          <p className="text-sm text-gray-500">Crawl users from target posts and perform engagement actions</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Engagement Task
        </button>
      </div>

      {/* Engagement Statistics */}
      {engagementStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center">
              <EyeIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-800">Users Engaged</p>
                <p className="text-2xl font-bold text-blue-900">
                  {engagementStats.engagement_stats?.total_users_engaged || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <UserPlusIcon className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">Follows Made</p>
                <p className="text-2xl font-bold text-green-900">
                  {engagementStats.engagement_stats?.total_follows_made || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <HeartIcon className="h-8 w-8 text-red-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">Likes Given</p>
                <p className="text-2xl font-bold text-red-900">
                  {engagementStats.engagement_stats?.total_likes_given || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center">
              <ChatBubbleLeftIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-purple-800">Comments Posted</p>
                <p className="text-2xl font-bold text-purple-900">
                  {engagementStats.engagement_stats?.total_comments_posted || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
              <form onSubmit={handleCreateTask}>
                <div className="bg-white px-6 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Create Engagement Task</h3>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  <div className="space-y-6">
                    {/* Target Pages */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Target Pages (Instagram usernames to crawl from)
                      </label>
                      <div className="space-y-2">
                        {formData.target_pages.map((page, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={page}
                              onChange={(e) => handleTargetPageChange(index, e.target.value)}
                              placeholder="luxurylifestylemag"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            />
                            {formData.target_pages.length > 1 && (
                              <button
                                type="button"
                                onClick={() => removeTargetPage(index)}
                                className="text-red-500 hover:text-red-700"
                              >
                                <XMarkIcon className="h-5 w-5" />
                              </button>
                            )}
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={addTargetPage}
                          className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                        >
                          + Add another target page
                        </button>
                      </div>
                    </div>

                    {/* Actions */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Actions to Perform
                      </label>
                      <div className="space-y-2">
                        {Object.entries(formData.actions).map(([action, enabled]) => (
                          <label key={action} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={enabled}
                              onChange={() => handleActionToggle(action)}
                              className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="ml-2 text-sm text-gray-700 capitalize">
                              {action === 'follow' && '👥 Follow users'}
                              {action === 'like' && '❤️ Like their latest post'}
                              {action === 'comment' && '💬 Comment on their post'}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Comment List */}
                    {formData.actions.comment && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Comment List (Random comments to use)
                        </label>
                        <div className="space-y-2">
                          {formData.comment_list.map((comment, index) => (
                            <div key={index} className="flex items-center space-x-2">
                              <input
                                type="text"
                                value={comment}
                                onChange={(e) => handleCommentChange(index, e.target.value)}
                                placeholder="Great post! 🔥"
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              />
                              {formData.comment_list.length > 1 && (
                                <button
                                  type="button"
                                  onClick={() => removeComment(index)}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  <XMarkIcon className="h-5 w-5" />
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            type="button"
                            onClick={addComment}
                            className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                          >
                            + Add another comment
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Settings */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Max Users per Page
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="50"
                          value={formData.max_users_per_page}
                          onChange={(e) => setFormData({...formData, max_users_per_page: parseInt(e.target.value)})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Skip Rate (% to skip for realism)
                        </label>
                        <select
                          value={formData.skip_rate}
                          onChange={(e) => setFormData({...formData, skip_rate: parseFloat(e.target.value)})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value={0.05}>5%</option>
                          <option value={0.1}>10%</option>
                          <option value={0.15}>15%</option>
                          <option value={0.2}>20%</option>
                          <option value={0.25}>25%</option>
                        </select>
                      </div>
                    </div>

                    {/* Profile Validation */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Profile Validation
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={formData.profile_validation.public_only}
                            onChange={(e) => setFormData({
                              ...formData,
                              profile_validation: {
                                ...formData.profile_validation,
                                public_only: e.target.checked
                              }
                            })}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="ml-2 text-sm text-gray-700">Only engage with public accounts</span>
                        </label>
                        
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={formData.profile_validation.min_posts > 0}
                            onChange={(e) => setFormData({
                              ...formData,
                              profile_validation: {
                                ...formData.profile_validation,
                                min_posts: e.target.checked ? 2 : 0
                              }
                            })}
                            className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm text-gray-700">Minimum</span>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            value={formData.profile_validation.min_posts}
                            onChange={(e) => setFormData({
                              ...formData,
                              profile_validation: {
                                ...formData.profile_validation,
                                min_posts: parseInt(e.target.value)
                              }
                            })}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            disabled={formData.profile_validation.min_posts === 0}
                          />
                          <span className="text-sm text-gray-700">posts</span>
                        </div>
                      </div>
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
                  </div>
                </div>

                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    disabled={creating}
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {creating ? 'Creating...' : 'Create Engagement Task'}
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

      {/* Active Tasks & Queue */}
      <div className="space-y-6">
        {/* Active Engagement Tasks */}
        {engagementStats?.active_engagement_tasks?.tasks?.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Active Engagement Tasks ({engagementStats.active_engagement_tasks.count})
            </h3>
            <div className="space-y-3">
              {engagementStats.active_engagement_tasks.tasks.map((task) => (
                <div key={task.task_id} className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <PlayIcon className="h-5 w-5 text-blue-500 animate-pulse" />
                      <div>
                        <div className="font-medium text-gray-900">
                          {task.target_pages.map(page => `@${page}`).join(', ')}
                        </div>
                        <div className="text-sm text-gray-600">
                          Running for {formatDistanceToNow(new Date(task.started_at * 1000), { addSuffix: true })} • 
                          Device: {task.device_name} • 
                          Users processed: {task.users_processed}
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

        {/* Engagement Queue */}
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">
            Engagement Queue ({engagementStats?.engagement_queue?.total_tasks || 0})
          </h3>
          
          {!engagementStats?.engagement_queue?.tasks?.length ? (
            <div className="text-center py-8 text-gray-500">
              <ChatBubbleLeftIcon className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p>No engagement tasks in queue</p>
              <p className="text-sm">Create an engagement task to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {engagementStats.engagement_queue.tasks.map((task) => (
                <div key={task.task_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(task.status)}
                      <div>
                        <div className="font-medium text-gray-900">
                          {task.target_pages ? task.target_pages.map(page => `@${page}`).join(', ') : 'Engagement Task'}
                        </div>
                        <div className="text-sm text-gray-500">
                          Priority: {task.priority} • 
                          Created {formatDistanceToNow(new Date(task.created_at * 1000), { addSuffix: true })}
                        </div>
                      </div>
                    </div>
                    
                    <span className={getStatusBadge(task.status)}>
                      {task.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EngagementCrawler;
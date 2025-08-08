import React, { useState, useEffect } from 'react';
import { 
  PlusIcon,
  DocumentTextIcon,
  PlayIcon,
  TrashIcon,
  PencilIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DevicePhoneMobileIcon,
  UsersIcon,
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  ClipboardDocumentListIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { apiClient } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

const WorkflowPanel = ({ dashboardStats, onRefresh, onOpenWorkflowWizard }) => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [devices, setDevices] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_type: 'engagement',
    target_pages: [],
    target_username: '',
    comment_list: [],
    actions: { follow: true, like: true, comment: false },
    max_users_per_page: 20,
    max_likes: 3,
    max_follows: 1,
    priority: 'normal'
  });
  const [deployData, setDeployData] = useState({
    device_ids: [],
    overrides: {}
  });

  useEffect(() => {
    loadWorkflows();
    loadDevices();
    const interval = setInterval(loadWorkflows, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await apiClient.getWorkflowTemplates();
      if (response.success) {
        setWorkflows(response.templates);
      }
    } catch (error) {
      console.error('Error loading workflows:', error);
      toast.error('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  const loadDevices = async () => {
    try {
      const deviceStatus = dashboardStats?.device_status?.devices || [];
      setDevices(deviceStatus);
    } catch (error) {
      console.error('Error loading devices:', error);
    }
  };

  const handleCreateWorkflow = async (e) => {
    e.preventDefault();
    
    try {
      // Convert target_pages and comment_list strings to arrays
      const templateData = {
        ...formData,
        target_pages: typeof formData.target_pages === 'string' 
          ? formData.target_pages.split(',').map(s => s.trim()).filter(s => s)
          : formData.target_pages,
        comment_list: typeof formData.comment_list === 'string'
          ? formData.comment_list.split('\n').map(s => s.trim()).filter(s => s)
          : formData.comment_list
      };

      const response = await apiClient.createWorkflowTemplate(templateData);
      if (response.success) {
        toast.success(`Workflow "${formData.name}" created successfully`);
        setShowCreateForm(false);
        resetForm();
        loadWorkflows();
      }
    } catch (error) {
      console.error('Error creating workflow:', error);
      toast.error('Failed to create workflow');
    }
  };

  const handleDeployWorkflow = async () => {
    if (!selectedTemplate || deployData.device_ids.length === 0) {
      toast.error('Please select devices to deploy to');
      return;
    }

    try {
      const response = await apiClient.deployWorkflowToDevices(
        selectedTemplate.template_id, 
        deployData
      );
      
      if (response.success) {
        const { deployment_summary } = response;
        toast.success(
          `Deployed "${selectedTemplate.name}" to ${deployment_summary.successful_deployments}/${deployment_summary.total_devices} devices`
        );
        setShowDeployModal(false);
        setSelectedTemplate(null);
        setDeployData({ device_ids: [], overrides: {} });
        onRefresh();
      } else {
        toast.error(`Deployment failed: ${response.error}`);
      }
    } catch (error) {
      console.error('Error deploying workflow:', error);
      toast.error('Failed to deploy workflow');
    }
  };

  const handleDeleteWorkflow = async (templateId, templateName) => {
    if (!confirm(`Are you sure you want to delete workflow "${templateName}"?`)) {
      return;
    }

    try {
      const response = await apiClient.deleteWorkflowTemplate(templateId);
      if (response.success) {
        toast.success(`Workflow "${templateName}" deleted`);
        loadWorkflows();
      }
    } catch (error) {
      console.error('Error deleting workflow:', error);
      toast.error('Failed to delete workflow');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      template_type: 'engagement',
      target_pages: [],
      target_username: '',
      comment_list: [],
      actions: { follow: true, like: true, comment: false },
      max_users_per_page: 20,
      max_likes: 3,
      max_follows: 1,
      priority: 'normal'
    });
  };

  const openDeployModal = (template) => {
    setSelectedTemplate(template);
    setShowDeployModal(true);
    setDeployData({ device_ids: [], overrides: {} });
  };

  const getTemplateTypeIcon = (type) => {
    switch (type) {
      case 'engagement':
        return <UsersIcon className="h-5 w-5 text-blue-500" />;
      case 'single_user':
        return <ChatBubbleLeftRightIcon className="h-5 w-5 text-green-500" />;
      default:
        return <DocumentTextIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getTemplateTypeBadge = (type) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (type) {
      case 'engagement':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      case 'single_user':
        return `${baseClasses} bg-green-100 text-green-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-medium text-gray-900">Workflow Templates</h2>
          <p className="text-sm text-gray-500">Create and deploy automation workflows to multiple devices</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Create Workflow
        </button>
      </div>

      {/* Workflows List */}
      {workflows.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <ClipboardDocumentListIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Workflows Created</h3>
          <p className="text-gray-500 mb-4">
            Create workflow templates to deploy automation tasks to multiple devices simultaneously.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Create Your First Workflow
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((template) => (
            <div key={template.template_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  {getTemplateTypeIcon(template.template_type)}
                  <h3 className="font-medium text-gray-900 truncate">{template.name}</h3>
                </div>
                <span className={getTemplateTypeBadge(template.template_type)}>
                  {template.template_type}
                </span>
              </div>

              {template.description && (
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{template.description}</p>
              )}

              <div className="space-y-2 mb-4 text-xs text-gray-500">
                <div className="flex justify-between">
                  <span>Created:</span>
                  <span>{formatDistanceToNow(new Date(template.created_at), { addSuffix: true })}</span>
                </div>
                <div className="flex justify-between">
                  <span>Priority:</span>
                  <span className="capitalize">{template.priority}</span>
                </div>
                
                {/* Configuration Summary */}
                {template.config_summary && (
                  <div className="mt-2 pt-2 border-t border-gray-100">
                    {template.template_type === 'engagement' && (
                      <>
                        <div className="flex justify-between">
                          <span>Target Pages:</span>
                          <span>{template.config_summary.target_pages_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Comments:</span>
                          <span>{template.config_summary.comment_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Max Users/Page:</span>
                          <span>{template.config_summary.max_users_per_page}</span>
                        </div>
                      </>
                    )}
                    {template.template_type === 'single_user' && (
                      <>
                        <div className="flex justify-between">
                          <span>Target:</span>
                          <span>@{template.config_summary.target_username}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Max Likes:</span>
                          <span>{template.config_summary.max_likes}</span>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => openDeployModal(template)}
                  className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                >
                  <RocketLaunchIcon className="h-3 w-3 mr-1" />
                  Deploy
                </button>
                <button
                  className="px-3 py-2 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                  title="Edit (Coming Soon)"
                  disabled
                >
                  <PencilIcon className="h-3 w-3" />
                </button>
                <button
                  onClick={() => handleDeleteWorkflow(template.template_id, template.name)}
                  className="px-3 py-2 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50"
                >
                  <TrashIcon className="h-3 w-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Workflow Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
              <form onSubmit={handleCreateWorkflow}>
                <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Create Workflow Template</h3>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <XMarkIcon className="h-6 w-6" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Workflow Name *
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => setFormData({...formData, name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Template Type
                        </label>
                        <select
                          value={formData.template_type}
                          onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                          <option value="engagement">Engagement Crawler</option>
                          <option value="single_user">Single User</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData({...formData, description: e.target.value})}
                        rows={2}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    {formData.template_type === 'engagement' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Target Instagram Pages (comma-separated) *
                          </label>
                          <input
                            type="text"
                            value={Array.isArray(formData.target_pages) ? formData.target_pages.join(', ') : formData.target_pages}
                            onChange={(e) => setFormData({...formData, target_pages: e.target.value})}
                            placeholder="luxurylifestylemag, fashionista, techcrunch"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Comments (one per line) *
                          </label>
                          <textarea
                            value={Array.isArray(formData.comment_list) ? formData.comment_list.join('\n') : formData.comment_list}
                            onChange={(e) => setFormData({...formData, comment_list: e.target.value})}
                            rows={3}
                            placeholder="Love this post! 😍&#10;Amazing content! 👏&#10;Great work! 💯"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Max Users Per Page
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={formData.max_users_per_page}
                            onChange={(e) => setFormData({...formData, max_users_per_page: parseInt(e.target.value)})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          />
                        </div>
                      </>
                    )}

                    {formData.template_type === 'single_user' && (
                      <>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Target Username *
                          </label>
                          <input
                            type="text"
                            value={formData.target_username}
                            onChange={(e) => setFormData({...formData, target_username: e.target.value})}
                            placeholder="luxurylifestylemag"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            required
                          />
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
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Follow User
                            </label>
                            <select
                              value={formData.max_follows}
                              onChange={(e) => setFormData({...formData, max_follows: parseInt(e.target.value)})}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                              <option value={0}>No</option>
                              <option value={1}>Yes</option>
                            </select>
                          </div>
                        </div>
                      </>
                    )}

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Priority
                        </label>
                        <select
                          value={formData.priority}
                          onChange={(e) => setFormData({...formData, priority: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                          <option value="low">Low</option>
                          <option value="normal">Normal</option>
                          <option value="high">High</option>
                          <option value="urgent">Urgent</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Actions
                        </label>
                        <div className="space-y-1">
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={formData.actions.follow}
                              onChange={(e) => setFormData({
                                ...formData, 
                                actions: {...formData.actions, follow: e.target.checked}
                              })}
                              className="mr-2"
                            />
                            Follow Users
                          </label>
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={formData.actions.like}
                              onChange={(e) => setFormData({
                                ...formData, 
                                actions: {...formData.actions, like: e.target.checked}
                              })}
                              className="mr-2"
                            />
                            Like Posts
                          </label>
                          <label className="flex items-center text-sm">
                            <input
                              type="checkbox"
                              checked={formData.actions.comment}
                              onChange={(e) => setFormData({
                                ...formData, 
                                actions: {...formData.actions, comment: e.target.checked}
                              })}
                              className="mr-2"
                            />
                            Comment on Posts
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
                  >
                    Create Workflow
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

      {/* Deploy Modal */}
      {showDeployModal && selectedTemplate && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>

            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Deploy Workflow</h3>
                  <button
                    onClick={() => setShowDeployModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="mb-4">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      {getTemplateTypeIcon(selectedTemplate.template_type)}
                      <span className="font-medium">{selectedTemplate.name}</span>
                      <span className={getTemplateTypeBadge(selectedTemplate.template_type)}>
                        {selectedTemplate.template_type}
                      </span>
                    </div>
                    {selectedTemplate.description && (
                      <p className="text-sm text-gray-600">{selectedTemplate.description}</p>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Devices to Deploy To *
                  </label>
                  <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md">
                    {devices.filter(device => device.status === 'ready').length === 0 ? (
                      <div className="p-3 text-center text-sm text-gray-500">
                        <DevicePhoneMobileIcon className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                        No ready devices available
                      </div>
                    ) : (
                      <div className="p-2 space-y-2">
                        {devices.filter(device => device.status === 'ready').map(device => (
                          <label key={device.udid} className="flex items-center p-2 hover:bg-gray-50 rounded">
                            <input
                              type="checkbox"
                              checked={deployData.device_ids.includes(device.udid)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setDeployData({
                                    ...deployData,
                                    device_ids: [...deployData.device_ids, device.udid]
                                  });
                                } else {
                                  setDeployData({
                                    ...deployData,
                                    device_ids: deployData.device_ids.filter(id => id !== device.udid)
                                  });
                                }
                              }}
                              className="mr-3"
                            />
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <DevicePhoneMobileIcon className="h-4 w-4 text-green-500" />
                                <span className="text-sm font-medium">{device.name}</span>
                              </div>
                              <div className="text-xs text-gray-500">
                                iOS {device.ios_version} • Port {device.connection_port}
                              </div>
                            </div>
                          </label>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Selected: {deployData.device_ids.length} device{deployData.device_ids.length !== 1 ? 's' : ''}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  onClick={handleDeployWorkflow}
                  disabled={deployData.device_ids.length === 0}
                  className="w-full inline-flex justify-center items-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <RocketLaunchIcon className="h-4 w-4 mr-2" />
                  Deploy to {deployData.device_ids.length} Device{deployData.device_ids.length !== 1 ? 's' : ''}
                </button>
                <button
                  onClick={() => setShowDeployModal(false)}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowPanel;
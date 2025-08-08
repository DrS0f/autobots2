import React, { useState } from 'react';
import { 
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckIcon,
  UserIcon,
  HeartIcon,
  EyeIcon,
  UserPlusIcon,
  DevicePhoneMobileIcon,
  ClockIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { InfoTooltip } from './Tooltip';

const TaskWizard = ({ isOpen, onClose, onCreateTask, dashboardStats }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    target_username: '',
    actions: {
      view_profile: true,
      like_posts: true,
      follow_user: true,
      comment: false
    },
    max_likes: 3,
    max_follows: 1,
    device_id: '',
    priority: 'normal'
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const steps = [
    {
      id: 1,
      title: 'Target & Actions',
      description: 'Who to target and what actions to perform'
    },
    {
      id: 2,
      title: 'Device & Settings',
      description: 'Choose device and configure pacing'
    }
  ];

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (!formData.target_username.trim()) {
      alert('Please enter a target username');
      return;
    }
    if (!formData.device_id) {
      alert('Please select a device');
      return;
    }

    setIsSubmitting(true);
    try {
      // Convert actions to array format expected by API
      const actions = [];
      if (formData.actions.view_profile) {
        actions.push('search_user', 'view_profile');
      }
      if (formData.actions.like_posts) {
        actions.push('like_post');
      }
      if (formData.actions.follow_user) {
        actions.push('follow_user');
      }
      if (formData.actions.comment) {
        actions.push('comment_post');
      }
      actions.push('navigate_home');

      const taskData = {
        target_username: formData.target_username.replace('@', ''),
        device_id: formData.device_id,
        actions,
        max_likes: formData.max_likes,
        max_follows: formData.max_follows,
        priority: formData.priority
      };

      await onCreateTask(taskData);
      onClose();
      resetForm();
    } catch (error) {
      console.error('Error creating task:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      target_username: '',
      actions: {
        view_profile: true,
        like_posts: true,
        follow_user: true,
        comment: false
      },
      max_likes: 3,
      max_follows: 1,
      device_id: '',
      priority: 'normal'
    });
    setCurrentStep(1);
  };

  const readyDevices = dashboardStats?.device_status?.devices?.filter(device => device.status === 'ready') || [];

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Create New Task</h3>
                <p className="text-sm text-gray-500">Step {currentStep} of 2: {steps[currentStep - 1].description}</p>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Progress Indicator */}
            <div className="mt-4">
              <div className="flex items-center space-x-4">
                {steps.map((step, index) => (
                  <div key={step.id} className="flex items-center">
                    <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${
                      step.id === currentStep 
                        ? 'border-indigo-600 bg-indigo-600 text-white' 
                        : step.id < currentStep 
                        ? 'border-green-600 bg-green-600 text-white'
                        : 'border-gray-300 text-gray-400'
                    }`}>
                      {step.id < currentStep ? (
                        <CheckIcon className="h-4 w-4" />
                      ) : (
                        <span className="text-sm font-medium">{step.id}</span>
                      )}
                    </div>
                    <div className="ml-3">
                      <p className={`text-sm font-medium ${
                        step.id === currentStep ? 'text-indigo-600' : 'text-gray-500'
                      }`}>
                        {step.title}
                      </p>
                    </div>
                    {index < steps.length - 1 && (
                      <div className="flex-1 h-px bg-gray-300 mx-4 min-w-12" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Step Content */}
          <div className="bg-white px-6 py-6">
            {currentStep === 1 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <UserIcon className="h-12 w-12 text-indigo-600 mx-auto mb-2" />
                  <h4 className="text-lg font-medium text-gray-900">Target & Actions</h4>
                  <p className="text-sm text-gray-600">Specify who to target and what actions to perform</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Instagram Username *
                  </label>
                  <input
                    type="text"
                    value={formData.target_username}
                    onChange={(e) => setFormData({...formData, target_username: e.target.value})}
                    placeholder="luxurylifestylemag"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Enter username without the @ symbol
                  </p>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <label className="text-sm font-medium text-gray-700">
                      Actions to Perform
                    </label>
                    <InfoTooltip 
                      title="What actions will be performed"
                      content="Select which interactions you want to perform on the target profile. Each action is performed with human-like delays for safety."
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.view_profile}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, view_profile: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <EyeIcon className="h-5 w-5 text-gray-500 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">View Profile</div>
                        <div className="text-xs text-gray-500">Visit and browse profile</div>
                      </div>
                    </label>

                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.like_posts}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, like_posts: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <HeartIcon className="h-5 w-5 text-gray-500 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">Like Posts</div>
                        <div className="text-xs text-gray-500">Like recent posts</div>
                      </div>
                    </label>

                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.follow_user}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, follow_user: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <UserPlusIcon className="h-5 w-5 text-gray-500 mr-2" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">Follow User</div>
                        <div className="text-xs text-gray-500">Follow the account</div>
                      </div>
                    </label>

                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.comment}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, comment: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <div className="h-5 w-5 text-gray-500 mr-2 flex items-center justify-center">
                        💬
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">Comment</div>
                        <div className="text-xs text-gray-500">Leave comments (coming soon)</div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Likes per Profile
                    </label>
                    <select
                      value={formData.max_likes}
                      onChange={(e) => setFormData({...formData, max_likes: parseInt(e.target.value)})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {[1,2,3,4,5].map(num => (
                        <option key={num} value={num}>{num} like{num !== 1 ? 's' : ''}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority Level
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({...formData, priority: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="low">Low - Process when available</option>
                      <option value="normal">Normal - Standard priority</option>
                      <option value="high">High - Process quickly</option>
                      <option value="urgent">Urgent - Process immediately</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <DevicePhoneMobileIcon className="h-12 w-12 text-indigo-600 mx-auto mb-2" />
                  <h4 className="text-lg font-medium text-gray-900">Device & Settings</h4>
                  <p className="text-sm text-gray-600">Choose device and review pacing settings</p>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <label className="text-sm font-medium text-gray-700">
                      Target Device *
                    </label>
                    <InfoTooltip 
                      title="Device Assignment"
                      content="Each task is assigned to a specific device. The device must be ready and connected to execute the task."
                    />
                  </div>
                  
                  {readyDevices.length === 0 ? (
                    <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                      <p className="text-sm text-red-800">
                        No ready devices available. Please initialize devices in the Devices tab first.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {readyDevices.map((device) => (
                        <label
                          key={device.udid}
                          className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                            formData.device_id === device.udid
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="radio"
                            name="device"
                            value={device.udid}
                            checked={formData.device_id === device.udid}
                            onChange={(e) => setFormData({...formData, device_id: e.target.value})}
                            className="sr-only"
                          />
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <DevicePhoneMobileIcon className="h-6 w-6 text-green-500" />
                              <div>
                                <div className="font-medium text-gray-900">{device.name}</div>
                                <div className="text-sm text-gray-500">
                                  iOS {device.ios_version} • Port {device.connection_port}
                                </div>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-medium text-green-600">Ready</div>
                              <div className="text-xs text-gray-500">Queue: 0 tasks</div>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  )}
                </div>

                {formData.device_id && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2 mb-2">
                      <ShieldCheckIcon className="h-5 w-5 text-yellow-600" />
                      <span className="text-sm font-medium text-yellow-800">Safe Mode Active</span>
                    </div>
                    <div className="text-sm text-yellow-700">
                      <p>This task will run in simulation mode:</p>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>No actual Instagram interactions will be performed</li>
                        <li>Mock execution will complete in ~2 seconds</li>
                        <li>Perfect for testing and learning the system</li>
                      </ul>
                    </div>
                  </div>
                )}

                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Task Summary</h5>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Target:</strong> @{formData.target_username}</p>
                    <p><strong>Actions:</strong> {Object.entries(formData.actions).filter(([_, enabled]) => enabled).map(([action, _]) => action.replace('_', ' ')).join(', ')}</p>
                    <p><strong>Max Likes:</strong> {formData.max_likes}</p>
                    <p><strong>Priority:</strong> {formData.priority}</p>
                    {formData.device_id && <p><strong>Device:</strong> {readyDevices.find(d => d.udid === formData.device_id)?.name}</p>}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-3 flex items-center justify-between">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeftIcon className="h-4 w-4 mr-2" />
              Previous
            </button>

            <div className="text-sm text-gray-500">
              Step {currentStep} of 2
            </div>

            {currentStep < 2 ? (
              <button
                onClick={handleNext}
                disabled={currentStep === 1 && !formData.target_username.trim()}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRightIcon className="h-4 w-4 ml-2" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!formData.device_id || isSubmitting}
                className="inline-flex items-center px-6 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Creating...' : 'Create Mock Task'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskWizard;
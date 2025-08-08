import React, { useState } from 'react';
import { 
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckIcon,
  DocumentTextIcon,
  CogIcon,
  RocketLaunchIcon,
  DevicePhoneMobileIcon,
  ClockIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { InfoTooltip } from './Tooltip';

const WorkflowWizard = ({ isOpen, onClose, onCreateWorkflow, dashboardStats }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_type: 'engagement',
    target_pages: [],
    target_username: '',
    comment_list: [],
    actions: {
      follow: true,
      like: true,
      comment: false
    },
    max_users_per_page: 20,
    max_likes: 3,
    max_follows: 1,
    priority: 'normal',
    delays: {
      action_delay: [2, 5],
      page_delay: [3, 8]
    },
    limits: {
      actions_per_hour: 50,
      actions_per_session: 20
    },
    selectedDevices: []
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const steps = [
    {
      id: 1,
      title: 'Name & Intent',
      description: 'Describe your workflow purpose'
    },
    {
      id: 2,
      title: 'Actions & Delays',
      description: 'Configure automation behavior'
    },
    {
      id: 3,
      title: 'Deploy',
      description: 'Select devices and deploy'
    }
  ];

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      alert('Please enter a workflow name');
      return;
    }

    setIsSubmitting(true);
    try {
      // Create workflow template first
      const templateData = {
        name: formData.name,
        description: formData.description,
        template_type: formData.template_type,
        target_pages: formData.target_pages,
        target_username: formData.target_username,
        comment_list: formData.comment_list,
        actions: formData.actions,
        max_users_per_page: formData.max_users_per_page,
        max_likes: formData.max_likes,
        max_follows: formData.max_follows,
        priority: formData.priority,
        delays: formData.delays,
        limits: formData.limits
      };

      await onCreateWorkflow(templateData, formData.selectedDevices);
      onClose();
      resetForm();
    } catch (error) {
      console.error('Error creating workflow:', error);
    } finally {
      setIsSubmitting(false);
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
      actions: {
        follow: true,
        like: true,
        comment: false
      },
      max_users_per_page: 20,
      max_likes: 3,
      max_follows: 1,
      priority: 'normal',
      delays: {
        action_delay: [2, 5],
        page_delay: [3, 8]
      },
      limits: {
        actions_per_hour: 50,
        actions_per_session: 20
      },
      selectedDevices: []
    });
    setCurrentStep(1);
  };

  const readyDevices = dashboardStats?.device_status?.devices?.filter(device => device.status === 'ready') || [];

  const handleDeviceToggle = (deviceId) => {
    setFormData(prev => ({
      ...prev,
      selectedDevices: prev.selectedDevices.includes(deviceId)
        ? prev.selectedDevices.filter(id => id !== deviceId)
        : [...prev.selectedDevices, deviceId]
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full max-h-[90vh] overflow-y-auto">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200 sticky top-0 z-10">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Create Workflow Template</h3>
                <p className="text-sm text-gray-500">Step {currentStep} of 3: {steps[currentStep - 1].description}</p>
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
                  <DocumentTextIcon className="h-12 w-12 text-indigo-600 mx-auto mb-2" />
                  <h4 className="text-lg font-medium text-gray-900">Name & Intent</h4>
                  <p className="text-sm text-gray-600">Give your workflow a clear name and purpose</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Workflow Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="Daily Engagement Campaign"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Describe what this workflow will accomplish..."
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <label className="text-sm font-medium text-gray-700">
                      Workflow Type
                    </label>
                    <InfoTooltip 
                      title="Workflow Types"
                      content="Engagement: Target users from specific Instagram posts/pages. Single User: Focus on one specific account."
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <label className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      formData.template_type === 'engagement' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                    }`}>
                      <input
                        type="radio"
                        name="template_type"
                        value="engagement"
                        checked={formData.template_type === 'engagement'}
                        onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                        className="sr-only"
                      />
                      <div className="text-center w-full">
                        <div className="text-2xl mb-2">🎯</div>
                        <div className="font-medium text-gray-900">Engagement Crawler</div>
                        <div className="text-sm text-gray-500">Target users from posts</div>
                      </div>
                    </label>

                    <label className={`flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      formData.template_type === 'single_user' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                    }`}>
                      <input
                        type="radio"
                        name="template_type"
                        value="single_user"
                        checked={formData.template_type === 'single_user'}
                        onChange={(e) => setFormData({...formData, template_type: e.target.value})}
                        className="sr-only"
                      />
                      <div className="text-center w-full">
                        <div className="text-2xl mb-2">👤</div>
                        <div className="font-medium text-gray-900">Single User</div>
                        <div className="text-sm text-gray-500">Focus on one account</div>
                      </div>
                    </label>
                  </div>
                </div>

                {formData.template_type === 'engagement' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Target Instagram Pages *
                      </label>
                      <input
                        type="text"
                        value={formData.target_pages.join(', ')}
                        onChange={(e) => setFormData({
                          ...formData, 
                          target_pages: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                        })}
                        placeholder="luxurylifestylemag, fashionista, techcrunch"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Separate multiple pages with commas
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Comments to Use *
                      </label>
                      <textarea
                        value={formData.comment_list.join('\n')}
                        onChange={(e) => setFormData({
                          ...formData,
                          comment_list: e.target.value.split('\n').map(s => s.trim()).filter(s => s)
                        })}
                        placeholder="Great post! 😍&#10;Love this content! 👏&#10;Amazing work! 💯"
                        rows={4}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        One comment per line
                      </p>
                    </div>
                  </>
                )}

                {formData.template_type === 'single_user' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Target Username *
                    </label>
                    <input
                      type="text"
                      value={formData.target_username}
                      onChange={(e) => setFormData({...formData, target_username: e.target.value})}
                      placeholder="luxurylifestylemag"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                )}
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <CogIcon className="h-12 w-12 text-indigo-600 mx-auto mb-2" />
                  <h4 className="text-lg font-medium text-gray-900">Actions & Delays</h4>
                  <p className="text-sm text-gray-600">Configure what actions to perform and timing</p>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <label className="text-sm font-medium text-gray-700">
                      Actions to Perform
                    </label>
                    <InfoTooltip 
                      title="Automation Actions"
                      content="Select which actions your workflow will perform. All actions use human-like delays for safety."
                    />
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.follow}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, follow: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <div className="text-center">
                        <div className="text-lg">👥</div>
                        <div className="text-sm font-medium">Follow</div>
                      </div>
                    </label>

                    <label className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.actions.like}
                        onChange={(e) => setFormData({
                          ...formData,
                          actions: {...formData.actions, like: e.target.checked}
                        })}
                        className="mr-3 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <div className="text-center">
                        <div className="text-lg">❤️</div>
                        <div className="text-sm font-medium">Like</div>
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
                      <div className="text-center">
                        <div className="text-lg">💬</div>
                        <div className="text-sm font-medium">Comment</div>
                      </div>
                    </label>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {formData.template_type === 'engagement' ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Max Users Per Page
                      </label>
                      <select
                        value={formData.max_users_per_page}
                        onChange={(e) => setFormData({...formData, max_users_per_page: parseInt(e.target.value)})}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        {[10, 15, 20, 25, 30].map(num => (
                          <option key={num} value={num}>{num} users</option>
                        ))}
                      </select>
                    </div>
                  ) : (
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
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Priority Level
                    </label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({...formData, priority: e.target.value})}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option value="low">Low - Conservative</option>
                      <option value="normal">Normal - Balanced</option>
                      <option value="high">High - Aggressive</option>
                      <option value="urgent">Urgent - Maximum</option>
                    </select>
                  </div>
                </div>

                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <ClockIcon className="h-5 w-5 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">Humanized Timing (Read-only in Safe Mode)</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm text-blue-700">
                    <div>
                      <strong>Action Delays:</strong> 2-5 seconds between actions
                    </div>
                    <div>
                      <strong>Page Delays:</strong> 3-8 seconds between pages
                    </div>
                    <div>
                      <strong>Rate Limits:</strong> 50 actions/hour, 20 per session
                    </div>
                    <div>
                      <strong>Rest Windows:</strong> Sleep hours respected
                    </div>
                  </div>
                </div>
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <RocketLaunchIcon className="h-12 w-12 text-indigo-600 mx-auto mb-2" />
                  <h4 className="text-lg font-medium text-gray-900">Deploy Workflow</h4>
                  <p className="text-sm text-gray-600">Select devices and deploy your workflow</p>
                </div>

                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <label className="text-sm font-medium text-gray-700">
                      Select Devices for Deployment
                    </label>
                    <InfoTooltip 
                      title="Device Selection"
                      content="Choose which devices will execute this workflow. Each device will get its own copy of the workflow tasks."
                    />
                  </div>
                  
                  {readyDevices.length === 0 ? (
                    <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                      <div className="flex items-center space-x-2">
                        <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                        <p className="text-sm text-red-800">
                          No ready devices available. Please initialize devices in the Devices tab first.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {readyDevices.map((device) => (
                        <label
                          key={device.udid}
                          className={`block p-4 border-2 rounded-lg cursor-pointer transition-all ${
                            formData.selectedDevices.includes(device.udid)
                              ? 'border-indigo-500 bg-indigo-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={formData.selectedDevices.includes(device.udid)}
                            onChange={() => handleDeviceToggle(device.udid)}
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

                  <div className="mt-3 text-sm text-gray-600">
                    Selected: {formData.selectedDevices.length} device{formData.selectedDevices.length !== 1 ? 's' : ''}
                  </div>
                </div>

                {formData.selectedDevices.length > 0 && (
                  <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center space-x-2 mb-2">
                      <ShieldCheckIcon className="h-5 w-5 text-yellow-600" />
                      <span className="text-sm font-medium text-yellow-800">Safe Mode Deployment</span>
                    </div>
                    <div className="text-sm text-yellow-700">
                      <p>This workflow will deploy in simulation mode:</p>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        <li>Creates {formData.selectedDevices.length} mock task{formData.selectedDevices.length !== 1 ? 's' : ''} (one per device)</li>
                        <li>Each task will complete in ~2 seconds</li>
                        <li>No actual Instagram automation will occur</li>
                        <li>Perfect for testing workflow logic</li>
                      </ul>
                    </div>
                  </div>
                )}

                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Deployment Summary</h5>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p><strong>Workflow:</strong> {formData.name}</p>
                    <p><strong>Type:</strong> {formData.template_type === 'engagement' ? 'Engagement Crawler' : 'Single User'}</p>
                    {formData.template_type === 'engagement' ? (
                      <>
                        <p><strong>Target Pages:</strong> {formData.target_pages.length} page{formData.target_pages.length !== 1 ? 's' : ''}</p>
                        <p><strong>Comments:</strong> {formData.comment_list.length} option{formData.comment_list.length !== 1 ? 's' : ''}</p>
                      </>
                    ) : (
                      <p><strong>Target:</strong> @{formData.target_username}</p>
                    )}
                    <p><strong>Actions:</strong> {Object.entries(formData.actions).filter(([_, enabled]) => enabled).map(([action, _]) => action).join(', ')}</p>
                    <p><strong>Priority:</strong> {formData.priority}</p>
                    <p><strong>Devices:</strong> {formData.selectedDevices.length} selected</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-3 flex items-center justify-between sticky bottom-0">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeftIcon className="h-4 w-4 mr-2" />
              Previous
            </button>

            <div className="text-sm text-gray-500">
              Step {currentStep} of 3
            </div>

            {currentStep < 3 ? (
              <button
                onClick={handleNext}
                disabled={
                  (currentStep === 1 && !formData.name.trim()) ||
                  (currentStep === 1 && formData.template_type === 'engagement' && (formData.target_pages.length === 0 || formData.comment_list.length === 0)) ||
                  (currentStep === 1 && formData.template_type === 'single_user' && !formData.target_username.trim())
                }
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
                <ChevronRightIcon className="h-4 w-4 ml-2" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={formData.selectedDevices.length === 0 || isSubmitting}
                className="inline-flex items-center px-6 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? 'Deploying...' : `Deploy Mock Workflow (${formData.selectedDevices.length} devices)`}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorkflowWizard;
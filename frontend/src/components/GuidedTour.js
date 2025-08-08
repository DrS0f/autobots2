import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlayIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const GuidedTour = ({ isActive, onClose, onStepChange, currentTab }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  const tourSteps = [
    {
      id: 'welcome',
      title: 'Welcome to Your Automation Hub!',
      content: 'This dashboard gives you complete control over your Instagram automation. Let\'s take a quick tour to get you familiar with everything.',
      targetTab: null,
      position: 'center',
      icon: '👋'
    },
    {
      id: 'dashboard',
      title: 'Dashboard Overview',
      content: 'Here you can see your system status at a glance - ready devices, queued tasks, active operations, and workers. The quick stats give you instant insights.',
      targetTab: 'tasks',
      position: 'bottom-left',
      icon: '📊'
    },
    {
      id: 'devices',
      title: 'Device Management',
      content: 'Connect and manage your iOS devices here. Each device gets its own queue and pacing controls for maximum safety and performance.',
      targetTab: 'devices',
      position: 'top-right',
      icon: '📱'
    },
    {
      id: 'workflows',
      title: 'Workflow Templates',
      content: 'Create reusable automation templates that you can deploy to multiple devices at once. Perfect for scaling your operations efficiently.',
      targetTab: 'workflows',
      position: 'top-center',
      icon: '🔄'
    },
    {
      id: 'tasks',
      title: 'Task Management',
      content: 'Create individual tasks or deploy workflows here. Each task is assigned to a specific device and shows its queue position.',
      targetTab: 'tasks',
      position: 'bottom-right',
      icon: '✅'
    },
    {
      id: 'engagement',
      title: 'Engagement Crawler',
      content: 'Advanced automation that finds users from specific posts and engages with them intelligently. Great for targeted growth strategies.',
      targetTab: 'engagement',
      position: 'top-left',
      icon: '🎯'
    },
    {
      id: 'history',
      title: 'Task History & Analytics',
      content: 'Monitor your completed tasks, success rates, and performance over time. Export data for deeper analysis.',
      targetTab: 'history',
      position: 'bottom-center',
      icon: '📈'
    },
    {
      id: 'settings',
      title: 'Settings & Safety',
      content: 'Configure pacing, rate limits, and safety features. Currently in Safe Mode - perfect for learning without any real automation.',
      targetTab: 'settings',
      position: 'center',
      icon: '⚙️'
    },
    {
      id: 'complete',
      title: 'You\'re All Set!',
      content: 'That\'s the complete tour! Remember, you\'re in Safe Mode so you can explore and test everything safely. Ready to start automating?',
      targetTab: null,
      position: 'center',
      icon: '🎉'
    }
  ];

  const currentStepData = tourSteps[currentStep];

  useEffect(() => {
    if (isActive) {
      setIsVisible(true);
      // Auto-switch tabs based on tour step
      if (currentStepData.targetTab && onStepChange) {
        onStepChange(currentStepData.targetTab);
      }
    } else {
      setIsVisible(false);
    }
  }, [isActive, currentStep, currentStepData.targetTab, onStepChange]);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleClose = () => {
    setIsVisible(false);
    onClose();
    setCurrentStep(0);
  };

  const handleStepJump = (stepIndex) => {
    setCurrentStep(stepIndex);
  };

  if (!isVisible) return null;

  const getPositionClasses = (position) => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'top-right':
        return 'top-4 right-4';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2';
      case 'center':
      default:
        return 'top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2';
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-40" />
      
      {/* Tour Modal */}
      <div className={`fixed z-50 ${getPositionClasses(currentStepData.position)}`}>
        <div className="bg-white rounded-lg shadow-xl max-w-md mx-4 border border-gray-200">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{currentStepData.icon}</span>
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {currentStepData.title}
                </h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-sm text-gray-500">
                    Step {currentStep + 1} of {tourSteps.length}
                  </span>
                  <div className="flex space-x-1">
                    {tourSteps.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => handleStepJump(index)}
                        className={`w-2 h-2 rounded-full transition-colors ${
                          index === currentStep 
                            ? 'bg-indigo-600' 
                            : index < currentStep 
                            ? 'bg-green-400' 
                            : 'bg-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            <p className="text-gray-700 leading-relaxed">
              {currentStepData.content}
            </p>

            {/* Safe Mode Indicator for relevant steps */}
            {['devices', 'workflows', 'tasks', 'engagement'].includes(currentStepData.id) && (
              <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-600 text-sm">🛡️</span>
                  <span className="text-xs text-yellow-800">
                    Safe to explore - all actions are simulated in Safe Mode
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeftIcon className="h-4 w-4 mr-1" />
              Previous
            </button>

            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">
                {Math.round(((currentStep + 1) / tourSteps.length) * 100)}% complete
              </span>
            </div>

            <button
              onClick={handleNext}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
            >
              {currentStep === tourSteps.length - 1 ? (
                <>
                  <CheckIcon className="h-4 w-4 mr-1" />
                  Finish Tour
                </>
              ) : (
                <>
                  Next
                  <ChevronRightIcon className="h-4 w-4 ml-1" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Pointer/Arrow for positioned modals */}
        {currentStepData.position !== 'center' && (
          <div className={`absolute w-0 h-0 ${
            currentStepData.position.includes('top') 
              ? 'border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-white -bottom-2 left-1/2 transform -translate-x-1/2'
              : currentStepData.position.includes('bottom')
              ? 'border-l-8 border-r-8 border-b-8 border-l-transparent border-r-transparent border-b-white -top-2 left-1/2 transform -translate-x-1/2'
              : ''
          }`} />
        )}
      </div>
    </>
  );
};

export default GuidedTour;
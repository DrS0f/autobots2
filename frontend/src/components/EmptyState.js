import React from 'react';
import { 
  PlusIcon,
  RocketLaunchIcon,
  DevicePhoneMobileIcon,
  DocumentTextIcon,
  ClockIcon,
  CogIcon,
  ChartBarIcon,
  UsersIcon
} from '@heroicons/react/24/outline';

const EmptyState = ({ 
  type, 
  title, 
  description, 
  actionText, 
  onAction, 
  icon: CustomIcon,
  className = ''
}) => {
  const getDefaultIcon = () => {
    switch (type) {
      case 'tasks':
        return DocumentTextIcon;
      case 'workflows':
        return RocketLaunchIcon;
      case 'devices':
        return DevicePhoneMobileIcon;
      case 'history':
        return ClockIcon;
      case 'settings':
        return CogIcon;
      case 'monitoring':
        return ChartBarIcon;
      case 'engagement':
        return UsersIcon;
      default:
        return DocumentTextIcon;
    }
  };

  const IconComponent = CustomIcon || getDefaultIcon();

  const getDefaultContent = () => {
    switch (type) {
      case 'tasks':
        return {
          title: 'No Tasks Created Yet',
          description: 'Create your first automation task to get started. Tasks are assigned to specific devices and executed safely.',
          actionText: 'Create First Task'
        };
      case 'workflows':
        return {
          title: 'No Workflow Templates',
          description: 'Create workflow templates to deploy automation to multiple devices simultaneously. Perfect for scaling your operations.',
          actionText: 'Create First Workflow'
        };
      case 'devices':
        return {
          title: 'No Devices Connected',
          description: 'Connect your iOS devices to start automating Instagram interactions. Each device operates independently.',
          actionText: 'Discover Devices'
        };
      case 'history':
        return {
          title: 'No Task History',
          description: 'Complete some tasks to see your automation history and performance analytics here.',
          actionText: 'View Dashboard'
        };
      case 'engagement':
        return {
          title: 'No Engagement Campaigns',
          description: 'Create targeted engagement campaigns to find and interact with users from specific Instagram posts.',
          actionText: 'Start Campaign'
        };
      case 'monitoring':
        return {
          title: 'System Monitoring',
          description: 'Monitor your automation system health, performance metrics, and real-time status information.',
          actionText: 'Refresh Status'
        };
      default:
        return {
          title: title || 'No Data Available',
          description: description || 'Get started by taking an action.',
          actionText: actionText || 'Get Started'
        };
    }
  };

  const defaultContent = getDefaultContent();
  const finalTitle = title || defaultContent.title;
  const finalDescription = description || defaultContent.description;
  const finalActionText = actionText || defaultContent.actionText;

  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="mx-auto max-w-md">
        <IconComponent className="h-16 w-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {finalTitle}
        </h3>
        <p className="text-gray-500 mb-6 leading-relaxed">
          {finalDescription}
        </p>
        
        {/* Safe Mode Indicator */}
        <div className="mb-6">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            🛡️ Safe Mode Active - Perfect for Learning
          </span>
        </div>

        {onAction && (
          <button
            onClick={onAction}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors duration-200"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            {finalActionText}
          </button>
        )}

        {/* Additional helpful links based on type */}
        {type === 'devices' && (
          <div className="mt-4 text-sm text-gray-500">
            <p className="mb-2">Requirements for iOS device connection:</p>
            <ul className="text-left space-y-1 max-w-xs mx-auto">
              <li>• iOS device with Instagram app installed</li>
              <li>• Device connected via USB or WiFi</li>
              <li>• Developer tools enabled</li>
            </ul>
          </div>
        )}

        {type === 'workflows' && (
          <div className="mt-4 text-sm text-gray-500">
            <p>💡 <strong>Pro tip:</strong> Start with a simple engagement workflow to learn the basics</p>
          </div>
        )}

        {type === 'tasks' && (
          <div className="mt-4 text-sm text-gray-500">
            <p>💡 <strong>Getting started:</strong> Try creating a single-user task first to see how automation works</p>
          </div>
        )}
      </div>
    </div>
  );
};

export const ErrorState = ({ 
  title = "Something went wrong",
  description = "We encountered an issue loading this content.",
  error,
  onRetry,
  className = ''
}) => {
  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="mx-auto max-w-md">
        <div className="h-16 w-16 mx-auto mb-4 text-red-300 flex items-center justify-center">
          <span className="text-4xl">⚠️</span>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {title}
        </h3>
        <p className="text-gray-500 mb-4 leading-relaxed">
          {description}
        </p>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-left">
            <p className="text-sm text-red-600 font-mono">
              {error.message || error.toString()}
            </p>
          </div>
        )}

        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 transition-colors duration-200"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};

export const LoadingState = ({ 
  title = "Loading...",
  description = "Please wait while we fetch your data.",
  className = ''
}) => {
  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="mx-auto max-w-md">
        <div className="h-16 w-16 mx-auto mb-4 animate-spin">
          <div className="h-16 w-16 border-4 border-indigo-200 border-t-indigo-600 rounded-full"></div>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          {title}
        </h3>
        <p className="text-gray-500 leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  );
};

export default EmptyState;
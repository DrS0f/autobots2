import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const ActionFeedback = ({ 
  show, 
  type = 'success', 
  title, 
  message, 
  action,
  onAction,
  onDismiss, 
  autoHide = true,
  duration = 5000,
  position = 'top-right'
}) => {
  const [isVisible, setIsVisible] = useState(show);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      setIsAnimating(true);
      
      if (autoHide) {
        const timer = setTimeout(() => {
          handleDismiss();
        }, duration);
        return () => clearTimeout(timer);
      }
    }
  }, [show, autoHide, duration]);

  const handleDismiss = () => {
    setIsAnimating(false);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, 300);
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />;
      case 'info':
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />;
    }
  };

  const getStyles = () => {
    const baseStyles = 'rounded-lg shadow-lg border max-w-sm';
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-50 border-green-200`;
      case 'error':
        return `${baseStyles} bg-red-50 border-red-200`;
      case 'warning':
        return `${baseStyles} bg-yellow-50 border-yellow-200`;
      case 'info':
      default:
        return `${baseStyles} bg-blue-50 border-blue-200`;
    }
  };

  const getPositionStyles = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2';
      case 'top-right':
        return 'top-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'bottom-center':
        return 'bottom-4 left-1/2 transform -translate-x-1/2';
      case 'bottom-right':
        return 'bottom-4 right-4';
      default:
        return 'top-4 right-4';
    }
  };

  if (!isVisible) return null;

  return (
    <div className={`fixed z-50 ${getPositionStyles()}`}>
      <div 
        className={`${getStyles()} transition-all duration-300 ${
          isAnimating ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform -translate-y-2'
        }`}
      >
        <div className="p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {getIcon()}
            </div>
            
            <div className="flex-1 min-w-0">
              {title && (
                <h3 className="text-sm font-medium text-gray-900 mb-1">
                  {title}
                </h3>
              )}
              
              {message && (
                <p className="text-sm text-gray-600 leading-relaxed">
                  {message}
                </p>
              )}
              
              {action && onAction && (
                <div className="mt-2">
                  <button
                    onClick={onAction}
                    className="text-sm font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
                  >
                    {action}
                  </button>
                </div>
              )}
            </div>
            
            <button
              onClick={handleDismiss}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
        
        {/* Progress bar for auto-hide */}
        {autoHide && (
          <div className="h-1 bg-gray-200 rounded-b-lg overflow-hidden">
            <div 
              className="h-full bg-indigo-600 transition-all ease-linear"
              style={{
                animation: `shrink ${duration}ms linear`,
                width: '100%'
              }}
            />
          </div>
        )}
      </div>
      
      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
};

// Enhanced Feedback Manager for multiple notifications
class FeedbackManager {
  constructor() {
    this.notifications = [];
    this.listeners = [];
  }

  show(notification) {
    const id = Date.now() + Math.random();
    const newNotification = { ...notification, id, show: true };
    
    this.notifications.push(newNotification);
    this.notify();
    
    return id;
  }

  hide(id) {
    this.notifications = this.notifications.map(notification =>
      notification.id === id ? { ...notification, show: false } : notification
    );
    this.notify();
    
    setTimeout(() => {
      this.notifications = this.notifications.filter(notification => notification.id !== id);
      this.notify();
    }, 300);
  }

  clear() {
    this.notifications = [];
    this.notify();
  }

  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== callback);
    };
  }

  notify() {
    this.listeners.forEach(listener => listener(this.notifications));
  }
}

export const feedbackManager = new FeedbackManager();

export const FeedbackContainer = () => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    const unsubscribe = feedbackManager.subscribe(setNotifications);
    return unsubscribe;
  }, []);

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {notifications.map((notification, index) => (
        <div
          key={notification.id}
          className="pointer-events-auto"
          style={{
            position: 'absolute',
            top: `${16 + index * 80}px`,
            right: '16px'
          }}
        >
          <ActionFeedback
            {...notification}
            onDismiss={() => feedbackManager.hide(notification.id)}
          />
        </div>
      ))}
    </div>
  );
};

export default ActionFeedback;
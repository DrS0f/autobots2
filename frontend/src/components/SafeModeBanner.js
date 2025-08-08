import React, { useState, useEffect } from 'react';
import { 
  ExclamationTriangleIcon,
  XMarkIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../services/api';

const SafeModeBanner = () => {
  const [safeModeStatus, setSafeModeStatus] = useState(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSafeModeStatus();
    const interval = setInterval(loadSafeModeStatus, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSafeModeStatus = async () => {
    try {
      const response = await apiClient.getSafeModeStatus();
      if (response.success) {
        setSafeModeStatus(response.safe_mode_status);
      }
    } catch (error) {
      console.error('Error loading safe mode status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
  };

  // Don't show banner if dismissed, loading, or safe mode is off
  if (loading || dismissed || !safeModeStatus?.safe_mode) {
    return null;
  }

  return (
    <div className="bg-yellow-50 border-l-4 border-yellow-400">
      <div className="flex">
        <div className="flex-shrink-0">
          <ShieldCheckIcon className="h-5 w-5 text-yellow-400" />
        </div>
        <div className="ml-3">
          <div className="flex items-center">
            <p className="text-sm text-yellow-700">
              <span className="font-medium">SAFE MODE ACTIVE:</span> {safeModeStatus.message}
            </p>
            <div className="ml-auto flex items-center space-x-4">
              <div className="text-xs text-yellow-600">
                Mock Tasks Completed: {safeModeStatus.total_mock_tasks_completed}
              </div>
              <button
                onClick={handleDismiss}
                className="flex-shrink-0 text-yellow-400 hover:text-yellow-600"
                aria-label="Dismiss"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="mt-1">
            <div className="text-xs text-yellow-600">
              All tasks will run in simulation mode. No actual Instagram interactions will be performed. 
              Mock execution duration: {safeModeStatus.mock_execution_duration}s per task.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SafeModeBanner;
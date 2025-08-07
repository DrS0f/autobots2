import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';
import {
  CogIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const SettingsPanel = () => {
  const [settings, setSettings] = useState({
    reengagement_days: 30,
    rate_limit_steps: [60, 120, 300, 600],
    cooldown_after_consecutive: 3,
    cooldown_minutes: 45
  });
  const [originalSettings, setOriginalSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    // Check if settings have changed
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasChanges(changed);
  }, [settings, originalSettings]);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getSettings();
      if (response.success) {
        setSettings(response.settings);
        setOriginalSettings(response.settings);
      } else {
        toast.error('Failed to load settings');
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Error loading settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    setLoading(true);
    try {
      const response = await apiClient.updateSettings(settings);
      if (response.success) {
        setOriginalSettings(settings);
        setLastSaved(new Date());
        toast.success('Settings saved successfully');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Error saving settings');
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    setSettings(originalSettings);
  };

  const handleRateLimitStepsChange = (index, value) => {
    const newSteps = [...settings.rate_limit_steps];
    newSteps[index] = parseInt(value) || 0;
    setSettings({
      ...settings,
      rate_limit_steps: newSteps
    });
  };

  const addRateLimitStep = () => {
    setSettings({
      ...settings,
      rate_limit_steps: [...settings.rate_limit_steps, 60]
    });
  };

  const removeRateLimitStep = (index) => {
    if (settings.rate_limit_steps.length > 1) {
      const newSteps = settings.rate_limit_steps.filter((_, i) => i !== index);
      setSettings({
        ...settings,
        rate_limit_steps: newSteps
      });
    }
  };

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <CogIcon className="h-6 w-6 text-gray-400" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Phase 4 System Settings
            </h3>
          </div>
          
          {lastSaved && (
            <div className="flex items-center text-sm text-gray-500">
              <CheckCircleIcon className="h-4 w-4 mr-1 text-green-500" />
              Last saved: {lastSaved.toLocaleTimeString()}
            </div>
          )}
        </div>

        {loading && (
          <div className="mb-4 p-4 bg-blue-50 rounded-md">
            <div className="flex items-center">
              <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full mr-2"></div>
              <p className="text-blue-700">Loading settings...</p>
            </div>
          </div>
        )}

        <div className="space-y-8">
          {/* Deduplication Settings */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">
              Deduplication Control
            </h4>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label htmlFor="reengagement_days" className="block text-sm font-medium text-gray-700 mb-2">
                  Re-engagement Window (days)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    id="reengagement_days"
                    min="1"
                    max="365"
                    value={settings.reengagement_days}
                    onChange={(e) => setSettings({
                      ...settings,
                      reengagement_days: parseInt(e.target.value) || 30
                    })}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                  <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                    <ClockIcon className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
                <p className="mt-1 text-sm text-gray-500">
                  Days before the same user can be engaged again
                </p>
              </div>
            </div>
          </div>

          {/* Rate Limiting Settings */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">
              Rate Limit Backoff Steps
            </h4>
            <div className="space-y-3">
              {(settings.rate_limit_steps || []).map((step, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <span className="text-sm text-gray-500 w-12">
                    Step {index + 1}:
                  </span>
                  <div className="flex-1 relative">
                    <input
                      type="number"
                      min="1"
                      max="3600"
                      value={step}
                      onChange={(e) => handleRateLimitStepsChange(index, e.target.value)}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                    />
                    <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                      <span className="text-xs text-gray-400">
                        {formatDuration(step)}
                      </span>
                    </div>
                  </div>
                  {(settings.rate_limit_steps || []).length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRateLimitStep(index)}
                      className="p-1 text-red-600 hover:text-red-800"
                      title="Remove step"
                    >
                      <XCircleIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
              
              <button
                type="button"
                onClick={addRateLimitStep}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                + Add Backoff Step
              </button>
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Exponential backoff delays when rate limited (in seconds)
            </p>
          </div>

          {/* Cooldown Settings */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-4">
              Account Cooldown Settings
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="cooldown_after_consecutive" className="block text-sm font-medium text-gray-700 mb-2">
                  Consecutive Errors Threshold
                </label>
                <input
                  type="number"
                  id="cooldown_after_consecutive"
                  min="1"
                  max="10"
                  value={settings.cooldown_after_consecutive}
                  onChange={(e) => setSettings({
                    ...settings,
                    cooldown_after_consecutive: parseInt(e.target.value) || 3
                  })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Errors before account cooldown
                </p>
              </div>

              <div>
                <label htmlFor="cooldown_minutes" className="block text-sm font-medium text-gray-700 mb-2">
                  Cooldown Duration (minutes)
                </label>
                <input
                  type="number"
                  id="cooldown_minutes"
                  min="1"
                  max="1440"
                  value={settings.cooldown_minutes}
                  onChange={(e) => setSettings({
                    ...settings,
                    cooldown_minutes: parseInt(e.target.value) || 45
                  })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
                <p className="mt-1 text-sm text-gray-500">
                  How long account stays in cooldown
                </p>
              </div>
            </div>
          </div>

          {/* Configuration Summary */}
          <div className="bg-gray-50 p-4 rounded-md">
            <h5 className="text-sm font-medium text-gray-900 mb-2">Configuration Summary</h5>
            <div className="text-sm text-gray-600 space-y-1">
              <p>• Users can be re-engaged after <strong>{settings.reengagement_days} days</strong></p>
              <p>• Rate limit backoff: <strong>{settings.rate_limit_steps.map(s => formatDuration(s)).join(' → ')}</strong></p>
              <p>• Account cooldown after <strong>{settings.cooldown_after_consecutive} consecutive errors</strong></p>
              <p>• Cooldown duration: <strong>{formatDuration(settings.cooldown_minutes * 60)}</strong></p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-gray-200">
          <div className="flex items-center space-x-4">
            {hasChanges && (
              <div className="flex items-center text-amber-600">
                <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                <span className="text-sm">Unsaved changes</span>
              </div>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={resetSettings}
              disabled={!hasChanges || loading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Reset
            </button>
            <button
              type="button"
              onClick={saveSettings}
              disabled={!hasChanges || loading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
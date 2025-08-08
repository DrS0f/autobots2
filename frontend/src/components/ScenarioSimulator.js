import React, { useState, useEffect } from 'react';
import { 
  ChevronDownIcon,
  ArrowPathIcon,
  BeakerIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  WifiIcon,
  KeyIcon,
  QueueListIcon
} from '@heroicons/react/24/outline';

const ScenarioSimulator = ({ onScenarioChange, currentScenario = 'healthy' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const scenarios = [
    {
      id: 'healthy',
      name: 'Healthy Day',
      icon: '✅',
      description: 'Everything running smoothly',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      details: 'All devices ready, queues normal, no rate limits'
    },
    {
      id: 'rate_limited',
      name: 'Rate Limited Device',
      icon: '⏱️',
      description: 'One device in rest mode',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      details: 'Device will be available in +15 minutes'
    },
    {
      id: 'device_offline',
      name: 'Device Offline',
      icon: '📴',
      description: 'One device disconnected',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      details: 'Device dropped mid-task, needs reconnection'
    },
    {
      id: 'license_expiring',
      name: 'License Expiring',
      icon: '🔑',
      description: '3 days until expiration',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
      details: 'License renewal required soon'
    },
    {
      id: 'backlog_spike',
      name: 'Backlog Spike',
      icon: '📈',
      description: 'High queue volume',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
      details: '20-50 tasks queued across devices'
    }
  ];

  const currentScenarioData = scenarios.find(s => s.id === currentScenario) || scenarios[0];

  const handleScenarioSelect = (scenarioId) => {
    setIsOpen(false);
    onScenarioChange(scenarioId);
  };

  const handleReset = async () => {
    setIsResetting(true);
    await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate reset
    onScenarioChange('healthy');
    setIsResetting(false);
  };

  return (
    <div className="relative">
      {/* Main Button */}
      <div className="flex items-center space-x-2">
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`inline-flex items-center px-3 py-2 border ${currentScenarioData.borderColor} rounded-md ${currentScenarioData.bgColor} hover:opacity-80 transition-colors`}
          >
            <BeakerIcon className="h-4 w-4 mr-2 text-gray-500" />
            <span className="text-xs font-medium text-gray-700">Scenario:</span>
            <span className="ml-1 text-xs font-medium mr-2">{currentScenarioData.icon}</span>
            <span className={`text-xs font-medium ${currentScenarioData.color}`}>
              {currentScenarioData.name}
            </span>
            <ChevronDownIcon className="ml-2 h-3 w-3 text-gray-400" />
          </button>

          {/* Dropdown */}
          {isOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg border border-gray-200 z-50">
              <div className="p-3 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-900">Demo Scenarios</h3>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                    Safe Mode
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">
                  Switch between realistic scenarios to test the UI
                </p>
              </div>

              <div className="max-h-64 overflow-y-auto">
                {scenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    onClick={() => handleScenarioSelect(scenario.id)}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 border-l-4 transition-colors ${
                      currentScenario === scenario.id 
                        ? `${scenario.borderColor} bg-gray-50` 
                        : 'border-transparent'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-lg">{scenario.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <p className="text-sm font-medium text-gray-900">
                            {scenario.name}
                          </p>
                          {currentScenario === scenario.id && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                              Active
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                          {scenario.description}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {scenario.details}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>

              <div className="p-3 border-t border-gray-100 bg-gray-50">
                <button
                  onClick={handleReset}
                  disabled={isResetting}
                  className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 rounded-md bg-white text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  <ArrowPathIcon className={`h-4 w-4 mr-2 ${isResetting ? 'animate-spin' : ''}`} />
                  {isResetting ? 'Resetting...' : 'Reset to Healthy Day'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default ScenarioSimulator;
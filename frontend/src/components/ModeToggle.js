import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  CogIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { 
  toggleSafeMode, 
  toggleFeature, 
  isSafeModeActive, 
  isFeatureEnabled,
  prepareForModeSwitch,
  DATA_SOURCE_CONFIG 
} from '../services/dataSourceConfig';

const ModeToggle = ({ className = '', onModeChange }) => {
  const [safeMode, setSafeMode] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [features, setFeatures] = useState({});

  useEffect(() => {
    // Initialize state from configuration
    setSafeMode(isSafeModeActive());
    setFeatures(DATA_SOURCE_CONFIG.FEATURES);

    // Listen for mode changes from other sources
    const handleModeChange = (event) => {
      setSafeMode(event.detail.safeMode);
    };

    window.addEventListener('safeModeChanged', handleModeChange);
    return () => window.removeEventListener('safeModeChanged', handleModeChange);
  }, []);

  const handleModeToggle = async () => {
    if (isTransitioning) return;

    const newMode = !safeMode;
    
    // Show confirmation for switching to Live Mode
    if (!newMode) { // Switching to Live Mode
      const confirmed = await showLiveModeConfirmation();
      if (!confirmed) return;
    }

    setIsTransitioning(true);

    try {
      // Prepare for mode switch
      prepareForModeSwitch(newMode ? 'safe' : 'live');
      
      // Toggle mode
      toggleSafeMode(newMode);
      setSafeMode(newMode);

      // Notify parent component
      if (onModeChange) {
        onModeChange(newMode ? 'safe' : 'live');
      }

      // Show success notification
      const modeName = newMode ? 'Safe Mode' : 'Live Mode';
      window.dispatchEvent(new CustomEvent('showNotification', {
        detail: {
          type: 'success',
          title: `Switched to ${modeName}`,
          message: newMode 
            ? 'All operations are now simulated with mock data'
            : 'System is now connected to real devices - use with caution!'
        }
      }));

    } catch (error) {
      console.error('Failed to switch mode:', error);
      
      window.dispatchEvent(new CustomEvent('showNotification', {
        detail: {
          type: 'error',
          title: 'Mode Switch Failed',
          message: 'Failed to switch operation mode. Please try again.'
        }
      }));
    } finally {
      setIsTransitioning(false);
    }
  };

  const handleFeatureToggle = (featureName) => {
    const newValue = !features[featureName];
    toggleFeature(featureName, newValue);
    setFeatures(prev => ({
      ...prev,
      [featureName]: newValue
    }));
  };

  const showLiveModeConfirmation = () => {
    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.innerHTML = `
        <div class="fixed inset-0 z-50 overflow-y-auto" style="background: rgba(0,0,0,0.7)">
          <div class="flex items-center justify-center min-h-screen px-4">
            <div class="bg-white rounded-lg p-6 max-w-lg w-full">
              <div class="flex items-center mb-4">
                <div class="flex-shrink-0 w-10 h-10 bg-red-100 rounded-full flex items-center justify-center mr-3">
                  <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900">⚠️ Switch to Live Mode</h3>
              </div>
              
              <div class="mb-6">
                <p class="text-gray-600 mb-4">
                  You are about to switch to <strong>Live Mode</strong> which will:
                </p>
                <ul class="text-sm text-gray-700 space-y-2 mb-4">
                  <li class="flex items-start">
                    <span class="w-2 h-2 bg-red-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    Connect to real iOS devices and perform actual Instagram interactions
                  </li>
                  <li class="flex items-start">
                    <span class="w-2 h-2 bg-red-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    Execute tasks on live Instagram accounts (likes, follows, comments)
                  </li>
                  <li class="flex items-start">
                    <span class="w-2 h-2 bg-red-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    Risk account limitations or suspensions if not used carefully
                  </li>
                  <li class="flex items-start">
                    <span class="w-2 h-2 bg-red-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                    Require explicit confirmation for all operations
                  </li>
                </ul>
                <div class="bg-yellow-50 border border-yellow-200 rounded-md p-3">
                  <p class="text-sm text-yellow-800">
                    <strong>Recommendation:</strong> Only switch to Live Mode when you're ready for production use 
                    and have properly configured your devices and Instagram accounts.
                  </p>
                </div>
              </div>
              
              <div class="flex space-x-3">
                <button id="confirm-live" class="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 font-medium">
                  Yes, Switch to Live Mode
                </button>
                <button id="cancel-live" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 font-medium">
                  Stay in Safe Mode
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      document.getElementById('confirm-live').onclick = () => {
        document.body.removeChild(modal);
        resolve(true);
      };

      document.getElementById('cancel-live').onclick = () => {
        document.body.removeChild(modal);
        resolve(false);
      };
    });
  };

  const getModeIcon = () => {
    if (isTransitioning) {
      return <div className="w-5 h-5 animate-spin border-2 border-gray-400 border-t-transparent rounded-full" />;
    }
    return safeMode ? (
      <ShieldCheckIcon className="w-5 h-5" />
    ) : (
      <BoltIcon className="w-5 h-5" />
    );
  };

  const getModeColor = () => {
    if (isTransitioning) return 'bg-gray-100 text-gray-600';
    return safeMode 
      ? 'bg-yellow-100 text-yellow-800 border-yellow-200' 
      : 'bg-red-100 text-red-800 border-red-200';
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Main Mode Toggle */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`inline-flex items-center px-3 py-2 rounded-full text-sm font-medium border ${getModeColor()}`}>
              {getModeIcon()}
              <span className="ml-2">
                {isTransitioning ? 'Switching...' : safeMode ? 'Safe Mode' : 'Live Mode'}
              </span>
            </div>
            
            <div className="text-sm text-gray-600">
              {safeMode ? 'Mock data & simulation' : 'Real device automation'}
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              title="Advanced settings"
            >
              <CogIcon className="w-5 h-5" />
            </button>
            
            <button
              onClick={handleModeToggle}
              disabled={isTransitioning}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                safeMode ? 'bg-yellow-500' : 'bg-red-500'
              } ${isTransitioning ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  safeMode ? 'translate-x-1' : 'translate-x-6'
                }`}
              />
            </button>
          </div>
        </div>
        
        {/* Mode Description */}
        <div className="mt-3 text-sm text-gray-500">
          {safeMode ? (
            <div className="flex items-start space-x-2">
              <InformationCircleIcon className="w-4 h-4 mt-0.5 text-blue-500" />
              <span>
                Safe Mode simulates all automation with mock data. Perfect for testing workflows and UI without affecting real accounts.
              </span>
            </div>
          ) : (
            <div className="flex items-start space-x-2">
              <ExclamationTriangleIcon className="w-4 h-4 mt-0.5 text-red-500" />
              <span>
                Live Mode connects to real devices and performs actual Instagram interactions. Use with caution and proper account management.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Advanced Features */}
      {showAdvanced && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Feature Flags</h4>
          
          <div className="space-y-3">
            {Object.entries(features).map(([featureName, enabled]) => (
              <div key={featureName} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-700">
                    {featureName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-xs text-gray-500">
                    {getFeatureDescription(featureName)}
                  </div>
                </div>
                
                <button
                  onClick={() => handleFeatureToggle(featureName)}
                  disabled={safeMode && featureName.startsWith('LIVE_')}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                    enabled ? 'bg-indigo-500' : 'bg-gray-300'
                  } ${safeMode && featureName.startsWith('LIVE_') ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span
                    className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                      enabled ? 'translate-x-5' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
          
          <div className="mt-4 p-3 bg-gray-50 rounded-md">
            <p className="text-xs text-gray-600">
              💡 <strong>Tip:</strong> Feature flags allow gradual rollout of new capabilities. 
              Live features are automatically disabled in Safe Mode for safety.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

const getFeatureDescription = (featureName) => {
  const descriptions = {
    'LIVE_DEVICE_STATUS': 'Real-time device status monitoring',
    'LIVE_QUEUE_MANAGEMENT': 'Live task queue management',
    'LIVE_TASK_EXECUTION': 'Execute tasks on real devices',
    'LIVE_WORKFLOW_DEPLOYMENT': 'Deploy workflows to live devices',
    'REAL_TIME_UPDATES': 'Real-time data updates',
    'AUTO_FALLBACK': 'Automatic fallback to Safe Mode on errors',
    'USER_CONFIRMATION': 'Require confirmation for live operations'
  };
  
  return descriptions[featureName] || 'Feature configuration';
};

export default ModeToggle;
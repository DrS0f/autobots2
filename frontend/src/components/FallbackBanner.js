import React, { useState, useEffect } from 'react';
import {
  ExclamationTriangleIcon,
  XMarkIcon,
  ArrowPathIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const FallbackBanner = ({ className = '' }) => {
  const [fallbackDevices, setFallbackDevices] = useState([]);
  const [showDetails, setShowDetails] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Listen for fallback events
    const handleDeviceFallback = (event) => {
      const { deviceId, reason } = event.detail;
      
      setFallbackDevices(prev => {
        // Check if device already in fallback list
        const existingIndex = prev.findIndex(d => d.deviceId === deviceId);
        
        if (existingIndex >= 0) {
          // Update existing entry
          const updated = [...prev];
          updated[existingIndex] = {
            ...updated[existingIndex],
            reason,
            timestamp: new Date().toISOString()
          };
          return updated;
        } else {
          // Add new fallback device
          return [...prev, {
            deviceId,
            reason,
            timestamp: new Date().toISOString()
          }];
        }
      });
      
      setDismissed(false); // Show banner when new fallback occurs
    };

    // Listen for device recovery
    const handleDeviceRecovery = (event) => {
      const { deviceId } = event.detail;
      
      setFallbackDevices(prev => 
        prev.filter(d => d.deviceId !== deviceId)
      );
    };

    window.addEventListener('deviceFallbackTriggered', handleDeviceFallback);
    window.addEventListener('deviceRecovered', handleDeviceRecovery);

    // Initial check for existing fallback devices
    checkExistingFallbacks();

    return () => {
      window.removeEventListener('deviceFallbackTriggered', handleDeviceFallback);
      window.removeEventListener('deviceRecovered', handleDeviceRecovery);
    };
  }, []);

  const checkExistingFallbacks = async () => {
    try {
      // This would call the API to check for existing fallback devices
      // For now, we'll simulate this check
      const response = await fetch('/api/devices/fallback');
      if (response.ok) {
        const data = await response.json();
        if (data.fallback_devices && data.fallback_devices.length > 0) {
          setFallbackDevices(data.fallback_devices.map(device => ({
            deviceId: device.device_udid,
            reason: device.reason,
            timestamp: device.fallback_time
          })));
        }
      }
    } catch (error) {
      // Silently handle error - fallback checking is not critical
      console.warn('Failed to check existing fallback devices:', error);
    }
  };

  const handleClearFallback = async (deviceId) => {
    try {
      const response = await fetch(`/api/devices/${deviceId}/clear-fallback`, {
        method: 'POST'
      });

      if (response.ok) {
        setFallbackDevices(prev => prev.filter(d => d.deviceId !== deviceId));
        
        // Emit recovery event
        window.dispatchEvent(new CustomEvent('deviceRecovered', {
          detail: { deviceId }
        }));

        // Show success notification
        window.dispatchEvent(new CustomEvent('showNotification', {
          detail: {
            type: 'success',
            title: 'Fallback Cleared',
            message: `Device ${deviceId.slice(-8)} has been restored to live mode`
          }
        }));
      } else {
        throw new Error('Failed to clear fallback');
      }
    } catch (error) {
      console.error('Failed to clear fallback:', error);
      
      window.dispatchEvent(new CustomEvent('showNotification', {
        detail: {
          type: 'error',
          title: 'Clear Fallback Failed',
          message: 'Failed to restore device to live mode. Please try again.'
        }
      }));
    }
  };

  const handleRetryAll = async () => {
    for (const device of fallbackDevices) {
      await handleClearFallback(device.deviceId);
      // Add small delay between retries
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  // Don't render if no fallback devices or banner is dismissed
  if (fallbackDevices.length === 0 || dismissed) {
    return null;
  }

  return (
    <div className={`bg-yellow-50 border-l-4 border-yellow-400 ${className}`}>
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
          </div>
          
          <div className="ml-3 flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-yellow-800">
                  Device Fallback Active
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  {fallbackDevices.length} device{fallbackDevices.length > 1 ? 's have' : ' has'} been 
                  switched to Safe Mode simulation due to connectivity issues.
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowDetails(!showDetails)}
                  className="text-yellow-700 hover:text-yellow-900 text-sm font-medium underline"
                >
                  {showDetails ? 'Hide Details' : 'Show Details'}
                </button>
                
                <button
                  onClick={handleRetryAll}
                  className="inline-flex items-center px-3 py-1.5 border border-yellow-300 text-sm font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200 transition-colors"
                  title="Retry all devices"
                >
                  <ArrowPathIcon className="w-4 h-4 mr-1" />
                  Retry All
                </button>
                
                <button
                  onClick={() => setDismissed(true)}
                  className="text-yellow-400 hover:text-yellow-600"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Detailed Fallback Information */}
            {showDetails && (
              <div className="mt-4 bg-yellow-100 rounded-md p-3">
                <div className="space-y-3">
                  {fallbackDevices.map((device, index) => (
                    <div key={device.deviceId} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-yellow-800">
                            Device {device.deviceId.slice(-8)}
                          </span>
                          <span className="text-xs text-yellow-600">
                            {formatTimestamp(device.timestamp)}
                          </span>
                        </div>
                        <div className="text-sm text-yellow-700">
                          <InformationCircleIcon className="w-4 h-4 inline mr-1" />
                          {device.reason}
                        </div>
                      </div>
                      
                      <button
                        onClick={() => handleClearFallback(device.deviceId)}
                        className="ml-3 inline-flex items-center px-2 py-1 border border-yellow-400 text-xs font-medium rounded text-yellow-700 bg-white hover:bg-yellow-50 transition-colors"
                      >
                        <ArrowPathIcon className="w-3 h-3 mr-1" />
                        Retry
                      </button>
                    </div>
                  ))}
                </div>
                
                <div className="mt-3 pt-3 border-t border-yellow-200">
                  <p className="text-xs text-yellow-600">
                    💡 <strong>Auto-Recovery:</strong> Devices in fallback mode continue to simulate tasks using Safe Mode data. 
                    Click "Retry" to attempt reconnection to live devices.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FallbackBanner;
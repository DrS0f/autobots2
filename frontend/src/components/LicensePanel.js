import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

const LicensePanel = () => {
  const [licenseStatus, setLicenseStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [licenseKey, setLicenseKey] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Load license status on component mount
  useEffect(() => {
    loadLicenseStatus();
    
    // Refresh status every 30 seconds
    const interval = setInterval(loadLicenseStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadLicenseStatus = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getLicenseStatus();
      setLicenseStatus(response.license_status);
      setLastUpdate(new Date());
      setError('');
    } catch (err) {
      console.error('Failed to load license status:', err);
      setError('Failed to load license status');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyNow = async () => {
    try {
      setVerifying(true);
      setError('');
      const response = await apiClient.verifyLicense();
      setLicenseStatus(response.license_status);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('License verification failed:', err);
      setError('License verification failed');
    } finally {
      setVerifying(false);
    }
  };

  const getStatusBadge = () => {
    if (!licenseStatus) return null;
    
    const { status, licensed, in_grace_period } = licenseStatus;
    
    let badgeClass = 'px-3 py-1 rounded-full text-sm font-medium ';
    let text = '';
    
    if (status === 'no_license_required') {
      badgeClass += 'bg-blue-100 text-blue-800';
      text = 'No License Required';
    } else if (licensed && !in_grace_period) {
      badgeClass += 'bg-green-100 text-green-800';
      text = 'Valid';
    } else if (licensed && in_grace_period) {
      badgeClass += 'bg-yellow-100 text-yellow-800';
      text = 'Grace Period';
    } else {
      badgeClass += 'bg-red-100 text-red-800';
      text = 'Locked';
    }
    
    return <span className={badgeClass}>{text}</span>;
  };

  const getExpiryCountdown = () => {
    if (!licenseStatus || !licenseStatus.time_to_expiry_hours) return null;
    
    const hours = licenseStatus.time_to_expiry_hours;
    if (hours <= 0) return null;
    
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    
    let text = '';
    if (days > 0) {
      text = `${days} days, ${remainingHours} hours`;
    } else {
      text = `${hours} hours`;
    }
    
    const isExpiringSoon = hours <= 24;
    const textClass = isExpiringSoon ? 'text-red-600 font-semibold' : 'text-gray-600';
    
    return (
      <div className={`text-sm ${textClass}`}>
        Expires in: {text}
        {isExpiringSoon && <span className="ml-2">⚠️</span>}
      </div>
    );
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">License Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={loadLicenseStatus}
            disabled={loading}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button
            onClick={handleVerifyNow}
            disabled={verifying}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {verifying ? 'Verifying...' : 'Verify Now'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {licenseStatus && (
        <div className="space-y-4">
          {/* Status Overview */}
          <div className="border rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-lg font-medium">License Status</h3>
              {getStatusBadge()}
            </div>
            
            {licenseStatus.message && (
              <p className="text-gray-600 mb-3">{licenseStatus.message}</p>
            )}
            
            {getExpiryCountdown()}
            
            {licenseStatus.status !== 'no_license_required' && (
              <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                <div>
                  <span className="font-medium">Customer ID:</span>
                  <span className="ml-2">{licenseStatus.customer_id || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-medium">Plan:</span>
                  <span className="ml-2">{licenseStatus.plan || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-medium">Features:</span>
                  <span className="ml-2">{licenseStatus.features?.join(', ') || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-medium">Device ID:</span>
                  <span className="ml-2 font-mono text-xs">
                    {licenseStatus.device_id ? licenseStatus.device_id.substring(0, 8) + '...' : 'N/A'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* License Key Input (for configuration) */}
          {licenseStatus.status === 'no_license_required' && (
            <div className="border rounded-lg p-4">
              <h3 className="text-lg font-medium mb-3">License Key Configuration</h3>
              <p className="text-gray-600 mb-4">
                This system is running without license restrictions. To enable licensing, set the LICENSE_KEY environment variable.
              </p>
              <div className="bg-gray-50 p-3 rounded">
                <code className="text-sm">
                  LICENSE_KEY=your-license-key-here<br/>
                  LICENSE_API_URL=http://localhost:8002
                </code>
              </div>
            </div>
          )}

          {/* Verification History */}
          <div className="border rounded-lg p-4">
            <h3 className="text-lg font-medium mb-3">Verification Info</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Last Verification:</span>
                <span className="ml-2">{formatDate(licenseStatus.last_verification)}</span>
              </div>
              <div>
                <span className="font-medium">Verify Interval:</span>
                <span className="ml-2">{licenseStatus.verify_interval}s</span>
              </div>
              <div>
                <span className="font-medium">Expires At:</span>
                <span className="ml-2">{formatDate(licenseStatus.expires_at)}</span>
              </div>
              <div>
                <span className="font-medium">Grace Days:</span>
                <span className="ml-2">{licenseStatus.grace_days || 0}</span>
              </div>
            </div>
          </div>

          {lastUpdate && (
            <div className="text-xs text-gray-500 text-center">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>
      )}

      {!licenseStatus && !loading && (
        <div className="text-center py-8">
          <p className="text-gray-500">No license information available</p>
          <button
            onClick={loadLicenseStatus}
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Load Status
          </button>
        </div>
      )}
    </div>
  );
};

export default LicensePanel;
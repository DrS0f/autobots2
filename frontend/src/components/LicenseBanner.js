import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';

const LicenseBanner = () => {
  const [licenseStatus, setLicenseStatus] = useState(null);
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    loadLicenseStatus();
    
    // Check status every 60 seconds
    const interval = setInterval(loadLicenseStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const loadLicenseStatus = async () => {
    try {
      const response = await apiClient.getLicenseStatus();
      const status = response.license_status;
      setLicenseStatus(status);
      
      // Show banner if license is expiring, in grace period, or locked
      if (status && status.status !== 'no_license_required') {
        const shouldShow = !status.licensed || 
                          status.in_grace_period || 
                          (status.time_to_expiry_hours && status.time_to_expiry_hours <= 72); // 3 days
        setVisible(shouldShow && !dismissed);
      } else {
        setVisible(false);
      }
    } catch (err) {
      console.error('Failed to load license status for banner:', err);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    setVisible(false);
  };

  const getBannerStyle = () => {
    if (!licenseStatus) return '';
    
    if (!licenseStatus.licensed) {
      // System is locked
      return 'bg-red-600 text-white';
    } else if (licenseStatus.in_grace_period) {
      // In grace period
      return 'bg-yellow-500 text-white';
    } else if (licenseStatus.time_to_expiry_hours && licenseStatus.time_to_expiry_hours <= 24) {
      // Expires within 24 hours
      return 'bg-orange-500 text-white';
    } else {
      // Expires within 72 hours
      return 'bg-blue-500 text-white';
    }
  };

  const getBannerMessage = () => {
    if (!licenseStatus) return '';
    
    if (!licenseStatus.licensed) {
      return '🔒 System Locked: License is invalid or expired. New tasks cannot be created.';
    } else if (licenseStatus.in_grace_period) {
      return `⚠️ Grace Period: License has expired but is still functional. Time remaining: ${getTimeRemaining()}`;
    } else if (licenseStatus.time_to_expiry_hours) {
      const hours = licenseStatus.time_to_expiry_hours;
      if (hours <= 24) {
        return `⏰ License Expires Soon: ${getTimeRemaining()} remaining. Please renew to avoid service interruption.`;
      } else {
        return `📅 License Expires in ${getTimeRemaining()}. Consider renewing soon.`;
      }
    }
    
    return licenseStatus.message || '';
  };

  const getTimeRemaining = () => {
    if (!licenseStatus || !licenseStatus.time_to_expiry_hours) return '';
    
    const hours = licenseStatus.time_to_expiry_hours;
    if (hours <= 0) return '0 hours';
    
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    
    if (days > 0) {
      return `${days} day${days > 1 ? 's' : ''}, ${remainingHours} hour${remainingHours > 1 ? 's' : ''}`;
    } else {
      return `${hours} hour${hours > 1 ? 's' : ''}`;
    }
  };

  if (!visible || !licenseStatus) {
    return null;
  }

  return (
    <div className={`${getBannerStyle()} px-4 py-3 relative`}>
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center">
          <div className="text-sm font-medium">
            {getBannerMessage()}
          </div>
        </div>
        <div className="flex items-center space-x-3">
          {licenseStatus.customer_id && (
            <div className="text-xs opacity-90">
              ID: {licenseStatus.customer_id}
            </div>
          )}
          <button
            onClick={handleDismiss}
            className="text-white hover:text-gray-200 transition-colors duration-200"
            title="Dismiss banner"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LicenseBanner;
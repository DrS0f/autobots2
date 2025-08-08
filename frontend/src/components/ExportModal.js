import React, { useState } from 'react';
import { 
  XMarkIcon,
  DocumentArrowDownIcon,
  CalendarIcon,
  AdjustmentsHorizontalIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const ExportModal = ({ 
  isOpen, 
  onClose, 
  onExport,
  title = "Export Data",
  dataType = "tasks",
  availableFilters = []
}) => {
  const [exportFormat, setExportFormat] = useState('csv');
  const [dateRange, setDateRange] = useState('last_30_days');
  const [filters, setFilters] = useState({});
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) return null;

  const dateRangeOptions = [
    { value: 'last_7_days', label: 'Last 7 days' },
    { value: 'last_30_days', label: 'Last 30 days' },
    { value: 'last_90_days', label: 'Last 90 days' },
    { value: 'custom', label: 'Custom range' }
  ];

  const handleExport = async () => {
    setIsExporting(true);
    try {
      // Generate mock data based on filters
      const mockData = generateMockData(dataType, exportFormat, dateRange, filters);
      await onExport(mockData, exportFormat);
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const generateMockData = (type, format, range, appliedFilters) => {
    const baseData = getMockDataForType(type, range);
    
    if (format === 'csv') {
      return convertToCSV(baseData);
    } else {
      return JSON.stringify(baseData, null, 2);
    }
  };

  const getMockDataForType = (type, range) => {
    const now = new Date();
    const getRandomDate = (daysAgo) => {
      const date = new Date(now);
      date.setDate(date.getDate() - Math.floor(Math.random() * daysAgo));
      return date.toISOString().split('T')[0];
    };

    const getDaysFromRange = (range) => {
      switch (range) {
        case 'last_7_days': return 7;
        case 'last_30_days': return 30;
        case 'last_90_days': return 90;
        default: return 30;
      }
    };

    const days = getDaysFromRange(range);

    switch (type) {
      case 'tasks':
        return Array.from({ length: Math.floor(Math.random() * 20) + 10 }, (_, i) => ({
          task_id: `task_${i + 1}`,
          target_username: `user_${i + 1}`,
          device_name: `Device ${(i % 3) + 1}`,
          status: ['completed', 'failed', 'completed', 'completed'][i % 4],
          created_at: getRandomDate(days),
          completed_at: getRandomDate(days),
          actions_performed: Math.floor(Math.random() * 5) + 1,
          success_rate: (Math.random() * 0.3 + 0.7).toFixed(2),
          priority: ['low', 'normal', 'high'][i % 3]
        }));

      case 'interactions':
        return Array.from({ length: Math.floor(Math.random() * 50) + 30 }, (_, i) => ({
          interaction_id: `int_${i + 1}`,
          account_id: `acc_${(i % 5) + 1}`,
          target_user: `target_${i + 1}`,
          action: ['like', 'follow', 'view_profile', 'comment'][i % 4],
          result: ['success', 'failed', 'success', 'success', 'success'][i % 5],
          timestamp: getRandomDate(days),
          device_id: `device_${(i % 3) + 1}`,
          response_time: Math.floor(Math.random() * 3000) + 500,
          duplicate_prevented: Math.random() > 0.8
        }));

      case 'workflows':
        return Array.from({ length: Math.floor(Math.random() * 10) + 5 }, (_, i) => ({
          workflow_id: `wf_${i + 1}`,
          name: `Workflow ${i + 1}`,
          type: ['engagement', 'single_user'][i % 2],
          created_at: getRandomDate(days),
          deployments: Math.floor(Math.random() * 10) + 1,
          total_tasks: Math.floor(Math.random() * 100) + 20,
          success_rate: (Math.random() * 0.3 + 0.7).toFixed(2),
          avg_completion_time: Math.floor(Math.random() * 300) + 60
        }));

      default:
        return [];
    }
  };

  const convertToCSV = (data) => {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => 
        JSON.stringify(row[header] || '')
      ).join(','))
    ].join('\n');
    
    return csvContent;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <DocumentArrowDownIcon className="h-6 w-6 text-indigo-600" />
                <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-6 py-6 space-y-6">
            {/* Export Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Export Format
              </label>
              <div className="grid grid-cols-2 gap-3">
                <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                  exportFormat === 'csv' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="format"
                    value="csv"
                    checked={exportFormat === 'csv'}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="sr-only"
                  />
                  <div className="text-center w-full">
                    <div className="text-lg mb-1">📊</div>
                    <div className="font-medium text-gray-900">CSV</div>
                    <div className="text-xs text-gray-500">Excel compatible</div>
                  </div>
                </label>

                <label className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                  exportFormat === 'json' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-gray-300'
                }`}>
                  <input
                    type="radio"
                    name="format"
                    value="json"
                    checked={exportFormat === 'json'}
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="sr-only"
                  />
                  <div className="text-center w-full">
                    <div className="text-lg mb-1">📄</div>
                    <div className="font-medium text-gray-900">JSON</div>
                    <div className="text-xs text-gray-500">Developer friendly</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date Range
              </label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {dateRangeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Available Filters */}
            {availableFilters.length > 0 && (
              <div>
                <div className="flex items-center space-x-2 mb-3">
                  <AdjustmentsHorizontalIcon className="h-4 w-4 text-gray-500" />
                  <label className="text-sm font-medium text-gray-700">
                    Additional Filters
                  </label>
                </div>
                <div className="space-y-2">
                  {availableFilters.map((filter, index) => (
                    <label key={index} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters[filter.key] || false}
                        onChange={(e) => setFilters({
                          ...filters,
                          [filter.key]: e.target.checked
                        })}
                        className="mr-2 h-4 w-4 text-indigo-600 rounded focus:ring-indigo-500"
                      />
                      <span className="text-sm text-gray-700">{filter.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Preview Info */}
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-gray-900">Export Preview</span>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <p>• Format: {exportFormat.toUpperCase()}</p>
                <p>• Date range: {dateRangeOptions.find(opt => opt.value === dateRange)?.label}</p>
                <p>• Data type: {dataType}</p>
                <p>• Estimated rows: {Math.floor(Math.random() * 100) + 50}</p>
              </div>
            </div>

            {/* Safe Mode Notice */}
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <span className="text-yellow-600">🛡️</span>
                <span className="text-sm text-yellow-800">
                  <strong>Safe Mode:</strong> Exporting mock/demo data for testing purposes
                </span>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-3 flex items-center justify-between">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              {isExporting ? 'Exporting...' : `Export ${exportFormat.toUpperCase()}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;
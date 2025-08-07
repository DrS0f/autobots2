import React, { useState, useEffect } from 'react';
import { apiClient } from '../services/api';
import toast from 'react-hot-toast';
import {
  DocumentArrowDownIcon,
  FunnelIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

const InteractionsLog = () => {
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    account_id: '',
    target_username: '',
    action: '',
    status: '',
    from_date: '',
    to_date: '',
    limit: 100,
    skip: 0
  });
  const [metrics, setMetrics] = useState({});
  const [showFilters, setShowFilters] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadInteractions();
    loadMetrics();
  }, []);

  const loadInteractions = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getInteractionEvents(filters);
      if (response.success) {
        setInteractions(response.events);
        setTotalCount(response.count || 0);
      } else {
        toast.error('Failed to load interactions');
      }
    } catch (error) {
      console.error('Error loading interactions:', error);
      toast.error('Error loading interactions');
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await apiClient.getMetrics();
      if (response.success) {
        setMetrics(response.metrics.interactions || {});
      }
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      skip: 0 // Reset pagination when filtering
    }));
  };

  const applyFilters = () => {
    loadInteractions();
  };

  const clearFilters = () => {
    setFilters({
      account_id: '',
      target_username: '',
      action: '',
      status: '',
      from_date: '',
      to_date: '',
      limit: 100,
      skip: 0
    });
  };

  const exportData = async (format) => {
    setExporting(true);
    try {
      const exportFilters = {
        format,
        account_id: filters.account_id || undefined,
        action: filters.action || undefined,
        status: filters.status || undefined,
        from_date: filters.from_date || undefined,
        to_date: filters.to_date || undefined
      };

      const blob = await apiClient.exportInteractionEvents(exportFilters);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `interactions_export.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Interactions exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting interactions:', error);
      toast.error('Error exporting interactions');
    } finally {
      setExporting(false);
    }
  };

  const loadMore = () => {
    setFilters(prev => ({
      ...prev,
      skip: prev.skip + prev.limit
    }));
    // Load more would need to be implemented to append results
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4 text-red-500" />;
      case 'skipped':
        return <InformationCircleIcon className="h-4 w-4 text-blue-500" />;
      case 'dedupe_hit':
        return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />;
      case 'rate_limited':
        return <ClockIcon className="h-4 w-4 text-orange-500" />;
      default:
        return <InformationCircleIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'skipped': return 'bg-blue-100 text-blue-800';
      case 'dedupe_hit': return 'bg-yellow-100 text-yellow-800';
      case 'rate_limited': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'follow': return 'bg-purple-100 text-purple-800';
      case 'like': return 'bg-pink-100 text-pink-800';
      case 'comment': return 'bg-indigo-100 text-indigo-800';
      case 'view': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Interaction Logs
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Track all user interactions and deduplication events
            </p>
          </div>
          
          <div className="mt-4 sm:mt-0 flex space-x-3">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
            </button>
            
            <div className="relative">
              <button
                onClick={() => exportData('csv')}
                disabled={exporting}
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
                {exporting ? 'Exporting...' : 'Export CSV'}
              </button>
            </div>
            
            <button
              onClick={() => exportData('json')}
              disabled={exporting}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              Export JSON
            </button>
          </div>
        </div>

        {/* Metrics Summary */}
        {Object.keys(metrics).length > 0 && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6 mb-6">
            <div className="bg-green-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-green-900">
                {metrics.successful_follows || 0}
              </div>
              <div className="text-sm text-green-600">Follows</div>
            </div>
            <div className="bg-pink-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-pink-900">
                {metrics.successful_likes || 0}
              </div>
              <div className="text-sm text-pink-600">Likes</div>
            </div>
            <div className="bg-indigo-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-indigo-900">
                {metrics.successful_comments || 0}
              </div>
              <div className="text-sm text-indigo-600">Comments</div>
            </div>
            <div className="bg-yellow-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-yellow-900">
                {metrics.dedupe_hits || 0}
              </div>
              <div className="text-sm text-yellow-600">Dedupe Hits</div>
            </div>
            <div className="bg-orange-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-orange-900">
                {metrics.rate_limit_events || 0}
              </div>
              <div className="text-sm text-orange-600">Rate Limits</div>
            </div>
            <div className="bg-red-50 p-3 rounded-lg">
              <div className="text-lg font-semibold text-red-900">
                {metrics.failed_interactions || 0}
              </div>
              <div className="text-sm text-red-600">Failed</div>
            </div>
          </div>
        )}

        {/* Filters */}
        {showFilters && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Account ID
                </label>
                <input
                  type="text"
                  value={filters.account_id}
                  onChange={(e) => handleFilterChange('account_id', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Filter by account..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  value={filters.target_username}
                  onChange={(e) => handleFilterChange('target_username', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Filter by username..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action
                </label>
                <select
                  value={filters.action}
                  onChange={(e) => handleFilterChange('action', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">All Actions</option>
                  <option value="follow">Follow</option>
                  <option value="like">Like</option>
                  <option value="comment">Comment</option>
                  <option value="view">View</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value="">All Status</option>
                  <option value="success">Success</option>
                  <option value="failed">Failed</option>
                  <option value="skipped">Skipped</option>
                  <option value="dedupe_hit">Dedupe Hit</option>
                  <option value="rate_limited">Rate Limited</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  From Date
                </label>
                <input
                  type="datetime-local"
                  value={filters.from_date}
                  onChange={(e) => handleFilterChange('from_date', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To Date
                </label>
                <input
                  type="datetime-local"
                  value={filters.to_date}
                  onChange={(e) => handleFilterChange('to_date', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div className="flex justify-between items-center mt-4">
              <button
                onClick={clearFilters}
                className="text-sm text-gray-600 hover:text-gray-800"
              >
                Clear all filters
              </button>
              <button
                onClick={applyFilters}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Apply Filters
              </button>
            </div>
          </div>
        )}

        {/* Interactions Table */}
        <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <div className="overflow-x-auto">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-500">Loading interactions...</p>
              </div>
            ) : interactions.length === 0 ? (
              <div className="p-8 text-center">
                <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No interactions found</p>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reason
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Latency
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {interactions.map((interaction, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatTimestamp(interaction.ts)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {interaction.account_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        @{interaction.target_username}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(interaction.action)}`}>
                          {interaction.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {getStatusIcon(interaction.status)}
                          <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(interaction.status)}`}>
                            {interaction.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {interaction.reason}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {interaction.latency_ms ? `${interaction.latency_ms}ms` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Pagination Info */}
        {interactions.length > 0 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <p className="text-sm text-gray-700">
                Showing {interactions.length} results
              </p>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{filters.skip + 1}</span> to{' '}
                  <span className="font-medium">{filters.skip + interactions.length}</span> of{' '}
                  <span className="font-medium">{totalCount}</span> results
                </p>
              </div>
              {interactions.length === filters.limit && (
                <button
                  onClick={loadMore}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Load More
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InteractionsLog;
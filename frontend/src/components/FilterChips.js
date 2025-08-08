import React, { useState } from 'react';
import { 
  XMarkIcon,
  FunnelIcon,
  CalendarIcon,
  DevicePhoneMobileIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  UserIcon
} from '@heroicons/react/24/outline';

const FilterChips = ({ 
  onFiltersChange, 
  availableFilters = {},
  className = ''
}) => {
  const [activeFilters, setActiveFilters] = useState({});

  const defaultFilters = {
    status: {
      label: 'Status',
      icon: CheckCircleIcon,
      options: [
        { value: 'completed', label: 'Completed', color: 'green' },
        { value: 'failed', label: 'Failed', color: 'red' },
        { value: 'running', label: 'Running', color: 'blue' },
        { value: 'pending', label: 'Pending', color: 'yellow' }
      ]
    },
    device: {
      label: 'Device',
      icon: DevicePhoneMobileIcon,
      options: [
        { value: 'device_1', label: 'iPhone 12 Pro', color: 'indigo' },
        { value: 'device_2', label: 'iPhone 13 Mini', color: 'indigo' },
        { value: 'device_3', label: 'iPad Pro', color: 'indigo' }
      ]
    },
    action: {
      label: 'Action',
      icon: UserIcon,
      options: [
        { value: 'like', label: 'Like', color: 'pink' },
        { value: 'follow', label: 'Follow', color: 'purple' },
        { value: 'view_profile', label: 'View Profile', color: 'blue' },
        { value: 'comment', label: 'Comment', color: 'teal' }
      ]
    },
    priority: {
      label: 'Priority',
      icon: ClockIcon,
      options: [
        { value: 'urgent', label: 'Urgent', color: 'red' },
        { value: 'high', label: 'High', color: 'orange' },
        { value: 'normal', label: 'Normal', color: 'gray' },
        { value: 'low', label: 'Low', color: 'gray' }
      ]
    },
    date: {
      label: 'Date Range',
      icon: CalendarIcon,
      options: [
        { value: 'today', label: 'Today', color: 'green' },
        { value: 'week', label: 'This Week', color: 'blue' },
        { value: 'month', label: 'This Month', color: 'purple' },
        { value: 'custom', label: 'Custom Range', color: 'gray' }
      ]
    }
  };

  const filters = { ...defaultFilters, ...availableFilters };

  const handleFilterToggle = (filterType, optionValue) => {
    const newFilters = { ...activeFilters };
    
    if (!newFilters[filterType]) {
      newFilters[filterType] = [];
    }

    if (newFilters[filterType].includes(optionValue)) {
      newFilters[filterType] = newFilters[filterType].filter(v => v !== optionValue);
      if (newFilters[filterType].length === 0) {
        delete newFilters[filterType];
      }
    } else {
      newFilters[filterType].push(optionValue);
    }

    setActiveFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  const clearFilter = (filterType) => {
    const newFilters = { ...activeFilters };
    delete newFilters[filterType];
    setActiveFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  const clearAllFilters = () => {
    setActiveFilters({});
    onFiltersChange?.({});
  };

  const getColorClasses = (color) => {
    const colorMap = {
      green: 'bg-green-100 text-green-800 border-green-200',
      red: 'bg-red-100 text-red-800 border-red-200',
      blue: 'bg-blue-100 text-blue-800 border-blue-200',
      yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      purple: 'bg-purple-100 text-purple-800 border-purple-200',
      indigo: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      pink: 'bg-pink-100 text-pink-800 border-pink-200',
      teal: 'bg-teal-100 text-teal-800 border-teal-200',
      orange: 'bg-orange-100 text-orange-800 border-orange-200',
      gray: 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colorMap[color] || colorMap.gray;
  };

  const activeFilterCount = Object.values(activeFilters).reduce(
    (count, filterArray) => count + filterArray.length, 
    0
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Filter Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FunnelIcon className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filters</span>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
              {activeFilterCount} active
            </span>
          )}
        </div>
        
        {activeFilterCount > 0 && (
          <button
            onClick={clearAllFilters}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Available Filter Categories */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {Object.entries(filters).map(([filterType, filterConfig]) => {
          const IconComponent = filterConfig.icon;
          const activeOptions = activeFilters[filterType] || [];
          
          return (
            <div key={filterType} className="space-y-2">
              <div className="flex items-center space-x-2">
                <IconComponent className="h-4 w-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-700">
                  {filterConfig.label}
                </span>
                {activeOptions.length > 0 && (
                  <button
                    onClick={() => clearFilter(filterType)}
                    className="text-xs text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                )}
              </div>
              
              <div className="space-y-1">
                {filterConfig.options.map((option) => {
                  const isActive = activeOptions.includes(option.value);
                  
                  return (
                    <button
                      key={option.value}
                      onClick={() => handleFilterToggle(filterType, option.value)}
                      className={`w-full text-left px-2 py-1 text-xs rounded-md border transition-all ${
                        isActive 
                          ? getColorClasses(option.color)
                          : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Active Filter Chips */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(activeFilters).map(([filterType, values]) =>
            values.map((value) => {
              const filterConfig = filters[filterType];
              const option = filterConfig?.options.find(opt => opt.value === value);
              
              if (!option) return null;
              
              return (
                <div
                  key={`${filterType}-${value}`}
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getColorClasses(option.color)}`}
                >
                  <span className="mr-1">{filterConfig.label}:</span>
                  <span>{option.label}</span>
                  <button
                    onClick={() => handleFilterToggle(filterType, value)}
                    className="ml-1 hover:opacity-75"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Mock Data Notice */}
      <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 rounded-lg p-2">
        <div className="flex items-center space-x-1">
          <span>🛡️</span>
          <span>Safe Mode: Filters will affect mock data display for demonstration</span>
        </div>
      </div>
    </div>
  );
};

export default FilterChips;
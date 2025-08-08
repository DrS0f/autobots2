import React from 'react';

const SkeletonLoader = ({ 
  type = 'text', 
  lines = 3, 
  height = 'h-4', 
  className = '',
  animate = true 
}) => {
  const baseClasses = `bg-gray-300 rounded ${animate ? 'animate-pulse' : ''}`;
  
  const renderSkeletonByType = () => {
    switch (type) {
      case 'text':
        return (
          <div className={`space-y-2 ${className}`}>
            {Array.from({ length: lines }).map((_, index) => (
              <div 
                key={index}
                className={`${baseClasses} ${height} ${
                  index === lines - 1 ? 'w-3/4' : 'w-full'
                }`}
              />
            ))}
          </div>
        );
        
      case 'card':
        return (
          <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
            <div className={`${baseClasses} h-6 w-1/3 mb-3`} />
            <div className={`${baseClasses} h-4 w-full mb-2`} />
            <div className={`${baseClasses} h-4 w-2/3 mb-4`} />
            <div className="flex space-x-2">
              <div className={`${baseClasses} h-8 w-20`} />
              <div className={`${baseClasses} h-8 w-16`} />
            </div>
          </div>
        );
        
      case 'device':
        return (
          <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
            {/* Device header */}
            <div className="flex items-center space-x-3 mb-4">
              <div className={`${baseClasses} w-10 h-10 rounded-full`} />
              <div className="flex-1">
                <div className={`${baseClasses} h-5 w-32 mb-2`} />
                <div className={`${baseClasses} h-3 w-24`} />
              </div>
              <div className={`${baseClasses} h-6 w-16 rounded-full`} />
            </div>
            
            {/* Device stats */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <div className={`${baseClasses} h-8 w-12 mx-auto mb-1`} />
                <div className={`${baseClasses} h-3 w-16 mx-auto`} />
              </div>
              <div className="text-center">
                <div className={`${baseClasses} h-8 w-12 mx-auto mb-1`} />
                <div className={`${baseClasses} h-3 w-16 mx-auto`} />
              </div>
            </div>
            
            {/* Queue info */}
            <div className={`border-t border-gray-100 pt-3`}>
              <div className={`${baseClasses} h-4 w-full mb-2`} />
              <div className={`${baseClasses} h-4 w-3/4`} />
            </div>
          </div>
        );
        
      case 'table':
        return (
          <div className={`bg-white border border-gray-200 rounded-lg ${className}`}>
            {/* Table header */}
            <div className="border-b border-gray-200 p-4">
              <div className="flex space-x-4">
                <div className={`${baseClasses} h-4 w-20`} />
                <div className={`${baseClasses} h-4 w-24`} />
                <div className={`${baseClasses} h-4 w-16`} />
                <div className={`${baseClasses} h-4 w-20`} />
              </div>
            </div>
            
            {/* Table rows */}
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="border-b border-gray-100 p-4">
                <div className="flex space-x-4">
                  <div className={`${baseClasses} h-4 w-20`} />
                  <div className={`${baseClasses} h-4 w-24`} />
                  <div className={`${baseClasses} h-4 w-16`} />
                  <div className={`${baseClasses} h-4 w-20`} />
                </div>
              </div>
            ))}
          </div>
        );
        
      case 'kpi':
        return (
          <div className={`grid grid-cols-2 sm:grid-cols-4 gap-4 ${className}`}>
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-3">
                <div className={`${baseClasses} h-6 w-16 mb-2`} />
                <div className={`${baseClasses} h-3 w-20`} />
              </div>
            ))}
          </div>
        );
        
      case 'workflow':
        return (
          <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
            {/* Workflow header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`${baseClasses} w-8 h-8 rounded`} />
                <div>
                  <div className={`${baseClasses} h-5 w-32 mb-1`} />
                  <div className={`${baseClasses} h-3 w-24`} />
                </div>
              </div>
              <div className={`${baseClasses} h-6 w-20 rounded-full`} />
            </div>
            
            {/* Workflow content */}
            <div className={`${baseClasses} h-4 w-full mb-2`} />
            <div className={`${baseClasses} h-4 w-2/3 mb-4`} />
            
            {/* Action buttons */}
            <div className="flex space-x-2">
              <div className={`${baseClasses} h-8 w-16`} />
              <div className={`${baseClasses} h-8 w-20`} />
            </div>
          </div>
        );
        
      case 'dashboard':
        return (
          <div className={`space-y-6 ${className}`}>
            {/* Header skeleton */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`${baseClasses} w-8 h-8 rounded`} />
                <div>
                  <div className={`${baseClasses} h-6 w-48 mb-1`} />
                  <div className={`${baseClasses} h-4 w-32`} />
                </div>
              </div>
              <div className="flex space-x-2">
                <div className={`${baseClasses} h-8 w-24`} />
                <div className={`${baseClasses} h-8 w-20`} />
              </div>
            </div>
            
            {/* KPI skeleton */}
            <SkeletonLoader type="kpi" animate={animate} />
            
            {/* Content skeleton */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SkeletonLoader type="card" animate={animate} />
              <SkeletonLoader type="card" animate={animate} />
            </div>
          </div>
        );
        
      case 'list':
        return (
          <div className={`space-y-3 ${className}`}>
            {Array.from({ length: lines }).map((_, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className={`${baseClasses} w-10 h-10 rounded-full`} />
                <div className="flex-1">
                  <div className={`${baseClasses} h-4 w-3/4 mb-1`} />
                  <div className={`${baseClasses} h-3 w-1/2`} />
                </div>
                <div className={`${baseClasses} h-6 w-16 rounded-full`} />
              </div>
            ))}
          </div>
        );
        
      default:
        return (
          <div className={`${baseClasses} ${height} w-full ${className}`} />
        );
    }
  };
  
  return renderSkeletonByType();
};

// Specialized skeleton components
export const DashboardSkeleton = ({ className = '' }) => (
  <SkeletonLoader type="dashboard" className={className} />
);

export const DeviceSkeleton = ({ count = 3, className = '' }) => (
  <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
    {Array.from({ length: count }).map((_, index) => (
      <SkeletonLoader key={index} type="device" />
    ))}
  </div>
);

export const WorkflowSkeleton = ({ count = 2, className = '' }) => (
  <div className={`space-y-4 ${className}`}>
    {Array.from({ length: count }).map((_, index) => (
      <SkeletonLoader key={index} type="workflow" />
    ))}
  </div>
);

export const TableSkeleton = ({ className = '' }) => (
  <SkeletonLoader type="table" className={className} />
);

export const KPISkeleton = ({ className = '' }) => (
  <SkeletonLoader type="kpi" className={className} />
);

export const ListSkeleton = ({ count = 5, className = '' }) => (
  <SkeletonLoader type="list" lines={count} className={className} />
);

export default SkeletonLoader;
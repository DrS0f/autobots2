import React, { useState } from 'react';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

const Tooltip = ({ 
  content, 
  title, 
  children, 
  position = 'top',
  className = '',
  maxWidth = 'max-w-xs'
}) => {
  const [isVisible, setIsVisible] = useState(false);

  const getPositionClasses = () => {
    switch (position) {
      case 'top':
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
      case 'bottom':
        return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
      default:
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    }
  };

  const getArrowClasses = () => {
    switch (position) {
      case 'top':
        return 'top-full left-1/2 transform -translate-x-1/2 border-t-gray-800 border-l-transparent border-r-transparent border-b-transparent border-4';
      case 'bottom':
        return 'bottom-full left-1/2 transform -translate-x-1/2 border-b-gray-800 border-l-transparent border-r-transparent border-t-transparent border-4';
      case 'left':
        return 'left-full top-1/2 transform -translate-y-1/2 border-l-gray-800 border-t-transparent border-b-transparent border-r-transparent border-4';
      case 'right':
        return 'right-full top-1/2 transform -translate-y-1/2 border-r-gray-800 border-t-transparent border-b-transparent border-l-transparent border-4';
      default:
        return 'top-full left-1/2 transform -translate-x-1/2 border-t-gray-800 border-l-transparent border-r-transparent border-b-transparent border-4';
    }
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className={className}
      >
        {children}
      </div>
      
      {isVisible && (
        <div className={`absolute z-50 ${getPositionClasses()}`}>
          <div className={`${maxWidth} p-3 bg-gray-800 text-white text-sm rounded-lg shadow-lg`}>
            {title && (
              <div className="font-medium text-white mb-1">{title}</div>
            )}
            <div className="text-gray-200 leading-relaxed">{content}</div>
            <div className={`absolute ${getArrowClasses()}`} />
          </div>
        </div>
      )}
    </div>
  );
};

// Helper component for common info icon tooltip
export const InfoTooltip = ({ content, title, position = 'top', className = '' }) => {
  return (
    <Tooltip content={content} title={title} position={position} className={className}>
      <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 cursor-help transition-colors" />
    </Tooltip>
  );
};

export default Tooltip;
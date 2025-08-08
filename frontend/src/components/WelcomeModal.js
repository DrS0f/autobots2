import React, { useState } from 'react';
import { 
  XMarkIcon,
  PlayIcon,
  BeakerIcon,
  EyeIcon,
  RocketLaunchIcon
} from '@heroicons/react/24/outline';
import { StarIcon } from '@heroicons/react/24/solid';

const WelcomeModal = ({ isOpen, onClose, onStartTour, onUseDemoData, onExploreManually }) => {
  const [selectedOption, setSelectedOption] = useState(null);

  if (!isOpen) return null;

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    setTimeout(() => {
      if (option === 'tour') onStartTour();
      else if (option === 'demo') onUseDemoData();
      else if (option === 'manual') onExploreManually();
      onClose();
    }, 200);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-10 h-10 bg-white rounded-full flex items-center justify-center">
                  <RocketLaunchIcon className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-white">
                    Welcome to iOS Instagram Automation
                  </h3>
                  <p className="text-indigo-100 text-sm">
                    Let's get you started with your automation journey
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-indigo-100 hover:text-white transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white px-6 py-6">
            <div className="text-center mb-6">
              <div className="flex items-center justify-center space-x-1 mb-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <StarIcon key={star} className="h-4 w-4 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-600 text-sm">
                Currently running in <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">Safe Mode</span> - 
                Perfect for learning and testing without any real automation
              </p>
            </div>

            <div className="space-y-4">
              <h4 className="text-lg font-medium text-gray-900 text-center mb-4">
                How would you like to get started?
              </h4>

              {/* Quick Tour Option */}
              <button
                onClick={() => handleOptionSelect('tour')}
                className={`w-full p-4 border-2 rounded-lg transition-all duration-200 ${
                  selectedOption === 'tour' 
                    ? 'border-indigo-500 bg-indigo-50 transform scale-105' 
                    : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                    <PlayIcon className="h-6 w-6 text-indigo-600" />
                  </div>
                  <div className="flex-1 text-left">
                    <h5 className="text-lg font-medium text-gray-900">Quick Tour</h5>
                    <p className="text-gray-600 text-sm">
                      Take a guided 5-minute tour through all features and capabilities
                    </p>
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Recommended for first-time users
                      </span>
                    </div>
                  </div>
                </div>
              </button>

              {/* Use Demo Data Option */}
              <button
                onClick={() => handleOptionSelect('demo')}
                className={`w-full p-4 border-2 rounded-lg transition-all duration-200 ${
                  selectedOption === 'demo' 
                    ? 'border-blue-500 bg-blue-50 transform scale-105' 
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <BeakerIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1 text-left">
                    <h5 className="text-lg font-medium text-gray-900">Use Demo Data</h5>
                    <p className="text-gray-600 text-sm">
                      Start with pre-populated workflows, tasks, and realistic scenarios
                    </p>
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Perfect for demos and testing
                      </span>
                    </div>
                  </div>
                </div>
              </button>

              {/* Explore Manually Option */}
              <button
                onClick={() => handleOptionSelect('manual')}
                className={`w-full p-4 border-2 rounded-lg transition-all duration-200 ${
                  selectedOption === 'manual' 
                    ? 'border-purple-500 bg-purple-50 transform scale-105' 
                    : 'border-gray-200 hover:border-purple-300 hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                    <EyeIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="flex-1 text-left">
                    <h5 className="text-lg font-medium text-gray-900">Explore Manually</h5>
                    <p className="text-gray-600 text-sm">
                      Jump right in and explore the interface at your own pace
                    </p>
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        Best for experienced users
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                <span>💡</span>
                <span>You can always access the tour later from the help menu</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeModal;
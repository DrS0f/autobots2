import React, { useEffect, useState } from 'react';
import { 
  ClockIcon,
  DocumentArrowUpIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

// Session storage keys
const STORAGE_KEYS = {
  DRAFT_TASK: 'instagram_automation_draft_task',
  DRAFT_WORKFLOW: 'instagram_automation_draft_workflow',
  SESSION_STATE: 'instagram_automation_session_state',
  USER_PREFERENCES: 'instagram_automation_user_prefs'
};

// Session Continuity Manager
export class SessionManager {
  static saveDraftTask(taskData) {
    try {
      const draft = {
        data: taskData,
        timestamp: new Date().toISOString(),
        type: 'task',
        step: taskData.currentStep || 1
      };
      localStorage.setItem(STORAGE_KEYS.DRAFT_TASK, JSON.stringify(draft));
      return true;
    } catch (error) {
      console.error('Error saving draft task:', error);
      return false;
    }
  }

  static getDraftTask() {
    try {
      const draft = localStorage.getItem(STORAGE_KEYS.DRAFT_TASK);
      return draft ? JSON.parse(draft) : null;
    } catch (error) {
      console.error('Error loading draft task:', error);
      return null;
    }
  }

  static clearDraftTask() {
    localStorage.removeItem(STORAGE_KEYS.DRAFT_TASK);
  }

  static saveDraftWorkflow(workflowData) {
    try {
      const draft = {
        data: workflowData,
        timestamp: new Date().toISOString(),
        type: 'workflow',
        step: workflowData.currentStep || 1
      };
      localStorage.setItem(STORAGE_KEYS.DRAFT_WORKFLOW, JSON.stringify(draft));
      return true;
    } catch (error) {
      console.error('Error saving draft workflow:', error);
      return false;
    }
  }

  static getDraftWorkflow() {
    try {
      const draft = localStorage.getItem(STORAGE_KEYS.DRAFT_WORKFLOW);
      return draft ? JSON.parse(draft) : null;
    } catch (error) {
      console.error('Error loading draft workflow:', error);
      return null;
    }
  }

  static clearDraftWorkflow() {
    localStorage.removeItem(STORAGE_KEYS.DRAFT_WORKFLOW);
  }

  static saveSessionState(state) {
    try {
      const sessionState = {
        ...state,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem(STORAGE_KEYS.SESSION_STATE, JSON.stringify(sessionState));
      return true;
    } catch (error) {
      console.error('Error saving session state:', error);
      return false;
    }
  }

  static getSessionState() {
    try {
      const state = localStorage.getItem(STORAGE_KEYS.SESSION_STATE);
      return state ? JSON.parse(state) : null;
    } catch (error) {
      console.error('Error loading session state:', error);
      return null;
    }
  }

  static saveUserPreferences(preferences) {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences));
      return true;
    } catch (error) {
      console.error('Error saving user preferences:', error);
      return false;
    }
  }

  static getUserPreferences() {
    try {
      const prefs = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return prefs ? JSON.parse(prefs) : {
        welcomeCompleted: false,
        tourCompleted: false,
        preferredScenario: 'healthy',
        dashboardLayout: 'default'
      };
    } catch (error) {
      console.error('Error loading user preferences:', error);
      return {};
    }
  }

  static clearAllDrafts() {
    localStorage.removeItem(STORAGE_KEYS.DRAFT_TASK);
    localStorage.removeItem(STORAGE_KEYS.DRAFT_WORKFLOW);
  }

  static isSessionExpired(timestamp, maxAgeHours = 24) {
    if (!timestamp) return true;
    
    const now = new Date();
    const sessionTime = new Date(timestamp);
    const diffHours = (now - sessionTime) / (1000 * 60 * 60);
    
    return diffHours > maxAgeHours;
  }
}

// Recovery Banner Component
const SessionRecoveryBanner = ({ onRestore, onDismiss }) => {
  const [drafts, setDrafts] = useState([]);

  useEffect(() => {
    checkForDrafts();
  }, []);

  const checkForDrafts = () => {
    const foundDrafts = [];
    
    const draftTask = SessionManager.getDraftTask();
    if (draftTask && !SessionManager.isSessionExpired(draftTask.timestamp)) {
      foundDrafts.push({
        type: 'task',
        data: draftTask,
        title: `Task: @${draftTask.data.target_username || 'Untitled'}`,
        step: draftTask.step,
        timestamp: draftTask.timestamp
      });
    }

    const draftWorkflow = SessionManager.getDraftWorkflow();
    if (draftWorkflow && !SessionManager.isSessionExpired(draftWorkflow.timestamp)) {
      foundDrafts.push({
        type: 'workflow',
        data: draftWorkflow,
        title: `Workflow: ${draftWorkflow.data.name || 'Untitled'}`,
        step: draftWorkflow.step,
        timestamp: draftWorkflow.timestamp
      });
    }

    setDrafts(foundDrafts);
  };

  const handleRestore = (draft) => {
    onRestore(draft);
    onDismiss();
  };

  const handleDismiss = () => {
    SessionManager.clearAllDrafts();
    onDismiss();
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.round((now - date) / 60000);
    
    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;
    if (diffMinutes < 1440) return `${Math.round(diffMinutes / 60)} hours ago`;
    return `${Math.round(diffMinutes / 1440)} days ago`;
  };

  if (drafts.length === 0) return null;

  return (
    <div className="bg-blue-50 border-b border-blue-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <DocumentArrowUpIcon className="h-5 w-5 text-blue-600" />
            <div>
              <h3 className="text-sm font-medium text-blue-900">
                Restore Previous Session
              </h3>
              <p className="text-sm text-blue-700">
                We found {drafts.length} unfinished item{drafts.length > 1 ? 's' : ''} from your previous session.
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {drafts.map((draft, index) => (
              <button
                key={index}
                onClick={() => handleRestore(draft)}
                className="inline-flex items-center px-3 py-1 border border-blue-300 rounded-md text-sm font-medium text-blue-700 bg-white hover:bg-blue-50 transition-colors"
              >
                <ClockIcon className="h-4 w-4 mr-1" />
                {draft.title}
                <span className="ml-2 text-xs text-blue-500">
                  Step {draft.step} • {formatTimestamp(draft.timestamp)}
                </span>
              </button>
            ))}
            
            <button
              onClick={handleDismiss}
              className="text-blue-500 hover:text-blue-700 transition-colors"
              title="Dismiss and clear drafts"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Auto-save hook for forms
export const useAutoSave = (data, key, delay = 2000) => {
  useEffect(() => {
    if (!data || Object.keys(data).length === 0) return;

    const timeoutId = setTimeout(() => {
      if (key === 'task') {
        SessionManager.saveDraftTask(data);
      } else if (key === 'workflow') {
        SessionManager.saveDraftWorkflow(data);
      }
    }, delay);

    return () => clearTimeout(timeoutId);
  }, [data, key, delay]);
};

// Session state hook
export const useSessionState = (initialState = {}) => {
  const [state, setState] = useState(() => {
    const savedState = SessionManager.getSessionState();
    return savedState && !SessionManager.isSessionExpired(savedState.timestamp) 
      ? { ...initialState, ...savedState } 
      : initialState;
  });

  useEffect(() => {
    SessionManager.saveSessionState(state);
  }, [state]);

  return [state, setState];
};

// User preferences hook
export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState(() => {
    return SessionManager.getUserPreferences();
  });

  const updatePreferences = (newPreferences) => {
    const updated = { ...preferences, ...newPreferences };
    setPreferences(updated);
    SessionManager.saveUserPreferences(updated);
  };

  return [preferences, updatePreferences];
};

export default SessionRecoveryBanner;
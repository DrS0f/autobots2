"""
Advanced Error Handling for Phase 4
Instagram-specific error detection, rate limit handling, and circuit breaker
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    RATE_LIMITED = "rate_limited"
    PRIVATE_ACCOUNT = "private_account"
    TARGET_UNAVAILABLE = "target_unavailable"
    NETWORK_ERROR = "network_error"
    APP_CRASH = "app_crash"
    ELEMENT_NOT_FOUND = "element_not_found"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class AccountState(Enum):
    ACTIVE = "active"
    COOLDOWN = "cooldown"
    SUSPENDED = "suspended"
    ERROR = "error"

@dataclass
class ErrorContext:
    """Context information for an error"""
    error_type: ErrorType
    message: str
    timestamp: datetime
    account_id: str
    device_id: str
    task_id: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AccountStateInfo:
    """Account state tracking information"""
    account_id: str
    state: AccountState
    last_error_time: Optional[datetime] = None
    consecutive_errors: int = 0
    cooldown_until: Optional[datetime] = None
    error_history: List[ErrorContext] = None
    
    def __post_init__(self):
        if self.error_history is None:
            self.error_history = []

class ErrorHandler:
    """Advanced error handling with Instagram-specific detection and recovery"""
    
    def __init__(self):
        # Error patterns for Instagram-specific detection
        self.error_patterns = {
            ErrorType.RATE_LIMITED: [
                "action blocked",
                "try again later", 
                "we limit how often",
                "too many requests",
                "please wait a few minutes"
            ],
            ErrorType.PRIVATE_ACCOUNT: [
                "this account is private",
                "user is private",
                "private profile"
            ],
            ErrorType.TARGET_UNAVAILABLE: [
                "user not found",
                "this page isn't available",
                "account unavailable",
                "user doesn't exist",
                "suspended",
                "deactivated"
            ],
            ErrorType.NETWORK_ERROR: [
                "network error",
                "connection failed",
                "timeout",
                "no internet connection"
            ],
            ErrorType.APP_CRASH: [
                "app crashed",
                "application not responding",
                "instagram has stopped"
            ]
        }
        
        # Configuration from environment
        self.rate_limit_steps = [int(x) for x in os.environ.get('RATE_LIMIT_STEPS', '60,120,300,600').split(',')]
        self.cooldown_after_consecutive = int(os.environ.get('COOLDOWN_AFTER_CONSECUTIVE', '3'))
        self.cooldown_minutes = int(os.environ.get('COOLDOWN_MINUTES', '45'))
        
        # Account state tracking
        self.account_states: Dict[str, AccountStateInfo] = {}
        
        # Backoff tracking per account
        self.backoff_counters: Dict[str, int] = {}
        
        # Circuit breaker settings
        self.circuit_breaker_threshold = 5  # failures in window
        self.circuit_breaker_window = 300   # 5 minutes
        
        # Statistics
        self.error_stats = {
            "total_errors": 0,
            "rate_limit_errors": 0,
            "private_account_errors": 0,
            "target_unavailable_errors": 0,
            "network_errors": 0,
            "accounts_in_cooldown": 0,
            "circuit_breaker_trips": 0
        }

    def detect_error_type(self, error_message: str, element_context: str = "") -> ErrorType:
        """Detect error type from message and context"""
        error_text = (error_message + " " + element_context).lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern.lower() in error_text:
                    return error_type
        
        # Check for timeout-specific indicators
        if "timeout" in error_text or "wait" in error_text:
            return ErrorType.TIMEOUT
            
        # Check for element not found
        if "element" in error_text and ("not found" in error_text or "cannot locate" in error_text):
            return ErrorType.ELEMENT_NOT_FOUND
        
        return ErrorType.UNKNOWN

    async def handle_error(
        self, 
        error_message: str,
        account_id: str,
        device_id: str,
        task_id: str,
        element_context: str = "",
        metadata: Dict = None
    ) -> Tuple[bool, int, str]:
        """
        Handle an error and determine retry strategy
        
        Returns:
            Tuple[bool, int, str]: (should_retry, delay_seconds, reason)
        """
        try:
            # Detect error type
            error_type = self.detect_error_type(error_message, element_context)
            
            # Create error context
            error_context = ErrorContext(
                error_type=error_type,
                message=error_message,
                timestamp=datetime.utcnow(),
                account_id=account_id,
                device_id=device_id,
                task_id=task_id,
                metadata=metadata or {}
            )
            
            # Update statistics
            self.error_stats["total_errors"] += 1
            if error_type == ErrorType.RATE_LIMITED:
                self.error_stats["rate_limit_errors"] += 1
            elif error_type == ErrorType.PRIVATE_ACCOUNT:
                self.error_stats["private_account_errors"] += 1
            elif error_type == ErrorType.TARGET_UNAVAILABLE:
                self.error_stats["target_unavailable_errors"] += 1
            elif error_type == ErrorType.NETWORK_ERROR:
                self.error_stats["network_errors"] += 1
            
            # Get or create account state
            if account_id not in self.account_states:
                self.account_states[account_id] = AccountStateInfo(
                    account_id=account_id,
                    state=AccountState.ACTIVE
                )
            
            account_state = self.account_states[account_id]
            
            # Add to error history
            account_state.error_history.append(error_context)
            
            # Keep only recent errors (last 100)
            if len(account_state.error_history) > 100:
                account_state.error_history = account_state.error_history[-100:]
            
            # Handle different error types
            if error_type == ErrorType.RATE_LIMITED:
                return await self._handle_rate_limit_error(account_state, error_context)
            elif error_type == ErrorType.PRIVATE_ACCOUNT:
                return await self._handle_private_account_error(account_state, error_context)
            elif error_type == ErrorType.TARGET_UNAVAILABLE:
                return await self._handle_target_unavailable_error(account_state, error_context)
            elif error_type == ErrorType.NETWORK_ERROR:
                return await self._handle_network_error(account_state, error_context)
            elif error_type == ErrorType.APP_CRASH:
                return await self._handle_app_crash_error(account_state, error_context)
            else:
                return await self._handle_generic_error(account_state, error_context)
                
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            return False, 60, f"error_handler_failed - {str(e)}"

    async def _handle_rate_limit_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle Instagram rate limiting"""
        account_id = account_state.account_id
        
        # Increment consecutive errors
        account_state.consecutive_errors += 1
        account_state.last_error_time = datetime.utcnow()
        
        # Check if we should trigger cooldown
        if account_state.consecutive_errors >= self.cooldown_after_consecutive:
            cooldown_duration = self.cooldown_minutes * 60  # Convert to seconds
            account_state.state = AccountState.COOLDOWN
            account_state.cooldown_until = datetime.utcnow() + timedelta(seconds=cooldown_duration)
            
            self.error_stats["accounts_in_cooldown"] += 1
            
            logger.warning(f"Account {account_id} entering cooldown for {self.cooldown_minutes} minutes")
            return False, cooldown_duration, f"cooldown_triggered - {account_state.consecutive_errors} consecutive rate limits"
        
        # Apply exponential backoff with jitter
        backoff_step = min(account_state.consecutive_errors - 1, len(self.rate_limit_steps) - 1)
        base_delay = self.rate_limit_steps[backoff_step]
        
        # Add jitter (±25%)
        jitter = random.uniform(-0.25, 0.25)
        delay = int(base_delay * (1 + jitter))
        
        logger.info(f"Rate limited on account {account_id}, backing off for {delay}s (step {backoff_step + 1})")
        return True, delay, f"rate_limit_backoff - step {backoff_step + 1}"

    async def _handle_private_account_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle private account errors"""
        # Private accounts should not be retried
        return False, 0, "private_account - cannot access"

    async def _handle_target_unavailable_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle target unavailable errors"""
        # Target unavailable should not be retried immediately
        return False, 0, "target_unavailable - user not accessible"

    async def _handle_network_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle network errors with retry"""
        # Network errors can be retried with short delay
        return True, 30, "network_error - retrying with short delay"

    async def _handle_app_crash_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle app crash errors"""
        # App crashes need device restart, longer delay
        return True, 120, "app_crash - device needs restart"

    async def _handle_generic_error(self, account_state: AccountStateInfo, error_context: ErrorContext) -> Tuple[bool, int, str]:
        """Handle generic/unknown errors"""
        # Generic errors get limited retries with progressive delay
        if account_state.consecutive_errors < 2:
            account_state.consecutive_errors += 1
            delay = 30 * account_state.consecutive_errors
            return True, delay, f"generic_error - retry {account_state.consecutive_errors}"
        else:
            return False, 0, "generic_error - max retries exceeded"

    async def is_account_available(self, account_id: str) -> Tuple[bool, str]:
        """Check if account is available for new tasks"""
        if account_id not in self.account_states:
            return True, "account_ready"
        
        account_state = self.account_states[account_id]
        
        if account_state.state == AccountState.COOLDOWN:
            if account_state.cooldown_until and datetime.utcnow() < account_state.cooldown_until:
                remaining_seconds = int((account_state.cooldown_until - datetime.utcnow()).total_seconds())
                return False, f"cooldown_active - {remaining_seconds}s remaining"
            else:
                # Cooldown expired, reset state
                account_state.state = AccountState.ACTIVE
                account_state.consecutive_errors = 0
                account_state.cooldown_until = None
                self.error_stats["accounts_in_cooldown"] = max(0, self.error_stats["accounts_in_cooldown"] - 1)
                return True, "cooldown_expired"
        
        return True, "account_ready"

    async def reset_account_errors(self, account_id: str):
        """Reset error count for successful interactions"""
        if account_id in self.account_states:
            account_state = self.account_states[account_id]
            if account_state.consecutive_errors > 0:
                logger.debug(f"Resetting error count for account {account_id}")
                account_state.consecutive_errors = 0
                account_state.last_error_time = None

    def get_account_state(self, account_id: str) -> Optional[AccountStateInfo]:
        """Get current state for an account"""
        return self.account_states.get(account_id)

    def get_all_account_states(self) -> Dict[str, Dict]:
        """Get all account states for dashboard"""
        states = {}
        for account_id, state_info in self.account_states.items():
            states[account_id] = {
                "state": state_info.state.value,
                "consecutive_errors": state_info.consecutive_errors,
                "last_error_time": state_info.last_error_time.isoformat() if state_info.last_error_time else None,
                "cooldown_until": state_info.cooldown_until.isoformat() if state_info.cooldown_until else None,
                "recent_errors": len(state_info.error_history),
                "cooldown_remaining": int((state_info.cooldown_until - datetime.utcnow()).total_seconds()) if state_info.cooldown_until and datetime.utcnow() < state_info.cooldown_until else 0
            }
        return states

    def get_error_stats(self) -> Dict:
        """Get error handling statistics"""
        # Update accounts in cooldown count
        cooldown_count = sum(1 for state in self.account_states.values() 
                           if state.state == AccountState.COOLDOWN and 
                           state.cooldown_until and datetime.utcnow() < state.cooldown_until)
        self.error_stats["accounts_in_cooldown"] = cooldown_count
        
        return self.error_stats.copy()

    async def cleanup_old_states(self, max_age_hours: int = 24):
        """Cleanup old account states and error history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        accounts_to_remove = []
        for account_id, state_info in self.account_states.items():
            # Remove accounts that haven't had errors recently and are not in cooldown
            if (state_info.last_error_time and state_info.last_error_time < cutoff_time and
                state_info.state != AccountState.COOLDOWN):
                accounts_to_remove.append(account_id)
        
        for account_id in accounts_to_remove:
            del self.account_states[account_id]
            logger.debug(f"Cleaned up old state for account {account_id}")
        
        # Clean up error history for remaining accounts
        for state_info in self.account_states.values():
            state_info.error_history = [
                error for error in state_info.error_history
                if error.timestamp > cutoff_time
            ]

# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

# Convenience functions
async def handle_automation_error(
    error_message: str,
    account_id: str,
    device_id: str,
    task_id: str,
    element_context: str = "",
    metadata: Dict = None
) -> Tuple[bool, int, str]:
    """Convenience function to handle automation errors"""
    handler = get_error_handler()
    return await handler.handle_error(
        error_message, account_id, device_id, task_id, element_context, metadata
    )

async def is_account_ready(account_id: str) -> Tuple[bool, str]:
    """Convenience function to check account availability"""
    handler = get_error_handler()
    return await handler.is_account_available(account_id)

async def mark_interaction_success(account_id: str):
    """Convenience function to reset errors on successful interaction"""
    handler = get_error_handler()
    await handler.reset_account_errors(account_id)
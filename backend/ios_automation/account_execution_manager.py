"""
Account Execution State Manager
Handles per-account concurrency control and execution state tracking
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)

class AccountExecutionState(Enum):
    """Account execution states for concurrency control"""
    AVAILABLE = "available"    # Account ready for new tasks
    RUNNING = "running"        # Account currently executing a task
    COOLDOWN = "cooldown"      # Account in error cooldown (from error_handling.py)
    SUSPENDED = "suspended"    # Account suspended/banned

@dataclass
class AccountExecutionInfo:
    """Information about account execution state"""
    account_id: str
    state: AccountExecutionState
    current_task_id: Optional[str] = None
    current_device_id: Optional[str] = None
    task_type: Optional[str] = None  # 'instagram' or 'engagement'
    started_at: Optional[datetime] = None
    waiting_tasks: List[str] = field(default_factory=list)  # Task IDs waiting for this account
    last_completed_task: Optional[str] = None
    last_completed_at: Optional[datetime] = None
    total_tasks_completed: int = 0
    
    def is_available_for_execution(self) -> bool:
        """Check if account is available for new task execution"""
        return self.state in [AccountExecutionState.AVAILABLE]
    
    def get_execution_summary(self) -> Dict:
        """Get summary info for API/dashboard"""
        return {
            "account_id": self.account_id,
            "state": self.state.value,
            "current_task_id": self.current_task_id,
            "current_device_id": self.current_device_id,
            "task_type": self.task_type,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "waiting_tasks_count": len(self.waiting_tasks),
            "waiting_task_ids": self.waiting_tasks,
            "last_completed_task": self.last_completed_task,
            "last_completed_at": self.last_completed_at.isoformat() if self.last_completed_at else None,
            "total_tasks_completed": self.total_tasks_completed,
            "execution_duration": (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else None
        }

class AccountExecutionManager:
    """Manages per-account task execution state and concurrency control"""
    
    def __init__(self):
        self.accounts: Dict[str, AccountExecutionInfo] = {}
        self.lock = threading.RLock()  # Thread-safe access
        self.metrics = {
            "total_accounts_tracked": 0,
            "accounts_running": 0,
            "accounts_waiting": 0,
            "accounts_cooldown": 0,
            "total_concurrency_blocks": 0,
            "total_tasks_queued_waiting": 0
        }
        
    def get_or_create_account_info(self, account_id: str) -> AccountExecutionInfo:
        """Get existing account info or create new one"""
        with self.lock:
            if account_id not in self.accounts:
                self.accounts[account_id] = AccountExecutionInfo(
                    account_id=account_id,
                    state=AccountExecutionState.AVAILABLE
                )
                self.metrics["total_accounts_tracked"] += 1
                logger.debug(f"Created account execution info for {account_id}")
            
            return self.accounts[account_id]
    
    def can_execute_task(self, account_id: str, task_id: str) -> Tuple[bool, str]:
        """
        Check if a task can be executed for the given account
        
        Returns:
            Tuple[bool, str]: (can_execute, reason)
        """
        with self.lock:
            account_info = self.get_or_create_account_info(account_id)
            
            if account_info.is_available_for_execution():
                return True, "account_available"
            elif account_info.state == AccountExecutionState.RUNNING:
                return False, f"account_running_task_{account_info.current_task_id}"
            elif account_info.state == AccountExecutionState.COOLDOWN:
                return False, "account_in_cooldown"
            elif account_info.state == AccountExecutionState.SUSPENDED:
                return False, "account_suspended"
            else:
                return False, f"account_state_{account_info.state.value}"
    
    def start_task_execution(
        self, 
        account_id: str, 
        task_id: str, 
        device_id: str, 
        task_type: str = "instagram"
    ) -> bool:
        """
        Mark account as running a task
        
        Returns:
            bool: True if successfully started, False if account unavailable
        """
        with self.lock:
            can_execute, reason = self.can_execute_task(account_id, task_id)
            
            if not can_execute:
                logger.warning(f"Cannot start task {task_id} for account {account_id}: {reason}")
                # Add task to waiting queue
                account_info = self.get_or_create_account_info(account_id)
                if task_id not in account_info.waiting_tasks:
                    account_info.waiting_tasks.append(task_id)
                    self.metrics["total_tasks_queued_waiting"] += 1
                return False
            
            # Start execution
            account_info = self.get_or_create_account_info(account_id)
            account_info.state = AccountExecutionState.RUNNING
            account_info.current_task_id = task_id
            account_info.current_device_id = device_id
            account_info.task_type = task_type
            account_info.started_at = datetime.utcnow()
            
            # Remove from waiting queue if it was there
            if task_id in account_info.waiting_tasks:
                account_info.waiting_tasks.remove(task_id)
                self.metrics["total_tasks_queued_waiting"] = max(0, self.metrics["total_tasks_queued_waiting"] - 1)
            
            self.metrics["accounts_running"] += 1
            self.metrics["accounts_waiting"] = self._count_accounts_with_waiting_tasks()
            
            logger.info(f"Started task execution: {task_id} for account {account_id} on device {device_id}")
            return True
    
    def complete_task_execution(
        self, 
        account_id: str, 
        task_id: str, 
        success: bool = True,
        next_available_in_seconds: int = 0
    ) -> Optional[str]:
        """
        Mark task as completed and make account available
        
        Returns:
            Optional[str]: Next waiting task ID if any
        """
        with self.lock:
            if account_id not in self.accounts:
                logger.warning(f"Attempted to complete task for unknown account: {account_id}")
                return None
            
            account_info = self.accounts[account_id]
            
            # Verify this is the current task
            if account_info.current_task_id != task_id:
                logger.warning(
                    f"Task completion mismatch: expected {account_info.current_task_id}, got {task_id}"
                )
                return None
            
            # Update completion info
            account_info.last_completed_task = task_id
            account_info.last_completed_at = datetime.utcnow()
            account_info.total_tasks_completed += 1
            
            # Clear current execution info
            account_info.current_task_id = None
            account_info.current_device_id = None
            account_info.task_type = None
            account_info.started_at = None
            
            # Set availability state
            if next_available_in_seconds > 0:
                account_info.state = AccountExecutionState.COOLDOWN
                # Note: Actual cooldown management is handled by error_handling.py
            else:
                account_info.state = AccountExecutionState.AVAILABLE
            
            self.metrics["accounts_running"] = max(0, self.metrics["accounts_running"] - 1)
            
            # Check for waiting tasks
            next_task_id = None
            if account_info.waiting_tasks and account_info.state == AccountExecutionState.AVAILABLE:
                next_task_id = account_info.waiting_tasks[0]  # FIFO
                logger.info(f"Account {account_id} has waiting task: {next_task_id}")
            
            self.metrics["accounts_waiting"] = self._count_accounts_with_waiting_tasks()
            
            logger.info(f"Completed task {task_id} for account {account_id} (success: {success})")
            
            return next_task_id
    
    def add_waiting_task(self, account_id: str, task_id: str) -> int:
        """
        Add a task to the waiting queue for an account
        
        Returns:
            int: Position in waiting queue (0-based)
        """
        with self.lock:
            account_info = self.get_or_create_account_info(account_id)
            
            if task_id not in account_info.waiting_tasks:
                account_info.waiting_tasks.append(task_id)
                self.metrics["total_tasks_queued_waiting"] += 1
                self.metrics["accounts_waiting"] = self._count_accounts_with_waiting_tasks()
                
                position = len(account_info.waiting_tasks) - 1
                logger.info(f"Added task {task_id} to waiting queue for account {account_id} (position: {position})")
                return position
            
            return account_info.waiting_tasks.index(task_id)
    
    def remove_waiting_task(self, account_id: str, task_id: str) -> bool:
        """Remove a task from waiting queue (e.g., if task is cancelled)"""
        with self.lock:
            if account_id in self.accounts:
                account_info = self.accounts[account_id]
                if task_id in account_info.waiting_tasks:
                    account_info.waiting_tasks.remove(task_id)
                    self.metrics["total_tasks_queued_waiting"] = max(0, self.metrics["total_tasks_queued_waiting"] - 1)
                    self.metrics["accounts_waiting"] = self._count_accounts_with_waiting_tasks()
                    logger.info(f"Removed waiting task {task_id} from account {account_id}")
                    return True
            return False
    
    def update_account_cooldown_state(self, account_id: str, in_cooldown: bool):
        """Update account cooldown state (called by error_handling.py)"""
        with self.lock:
            if account_id in self.accounts:
                account_info = self.accounts[account_id]
                if in_cooldown and account_info.state != AccountExecutionState.RUNNING:
                    account_info.state = AccountExecutionState.COOLDOWN
                elif not in_cooldown and account_info.state == AccountExecutionState.COOLDOWN:
                    account_info.state = AccountExecutionState.AVAILABLE
                
                self._update_cooldown_metrics()
    
    def get_account_execution_state(self, account_id: str) -> Optional[Dict]:
        """Get execution state for specific account"""
        with self.lock:
            if account_id in self.accounts:
                return self.accounts[account_id].get_execution_summary()
            return None
    
    def get_all_account_states(self) -> Dict[str, Dict]:
        """Get execution states for all accounts"""
        with self.lock:
            return {
                account_id: account_info.get_execution_summary()
                for account_id, account_info in self.accounts.items()
            }
    
    def get_waiting_tasks_by_account(self) -> Dict[str, List[str]]:
        """Get all waiting tasks grouped by account"""
        with self.lock:
            return {
                account_id: account_info.waiting_tasks.copy()
                for account_id, account_info in self.accounts.items()
                if account_info.waiting_tasks
            }
    
    def get_metrics(self) -> Dict:
        """Get concurrency control metrics"""
        with self.lock:
            self._update_all_metrics()
            return self.metrics.copy()
    
    def _count_accounts_with_waiting_tasks(self) -> int:
        """Count accounts that have waiting tasks"""
        return sum(1 for info in self.accounts.values() if info.waiting_tasks)
    
    def _update_cooldown_metrics(self):
        """Update cooldown-related metrics"""
        self.metrics["accounts_cooldown"] = sum(
            1 for info in self.accounts.values() 
            if info.state == AccountExecutionState.COOLDOWN
        )
    
    def _update_all_metrics(self):
        """Update all metrics"""
        self.metrics["total_accounts_tracked"] = len(self.accounts)
        self.metrics["accounts_running"] = sum(
            1 for info in self.accounts.values() 
            if info.state == AccountExecutionState.RUNNING
        )
        self.metrics["accounts_waiting"] = self._count_accounts_with_waiting_tasks()
        self.metrics["accounts_cooldown"] = sum(
            1 for info in self.accounts.values() 
            if info.state == AccountExecutionState.COOLDOWN
        )
        total_waiting_tasks = sum(len(info.waiting_tasks) for info in self.accounts.values())
        self.metrics["total_tasks_queued_waiting"] = total_waiting_tasks
    
    def cleanup_old_accounts(self, max_age_hours: int = 24):
        """Cleanup old account tracking info"""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            accounts_to_remove = []
            for account_id, account_info in self.accounts.items():
                # Remove accounts that haven't been active recently and have no waiting tasks
                if (account_info.state == AccountExecutionState.AVAILABLE and
                    not account_info.waiting_tasks and
                    account_info.last_completed_at and
                    account_info.last_completed_at < cutoff_time):
                    accounts_to_remove.append(account_id)
            
            for account_id in accounts_to_remove:
                del self.accounts[account_id]
                logger.debug(f"Cleaned up old account execution info: {account_id}")
            
            self.metrics["total_accounts_tracked"] = len(self.accounts)

# Global execution manager instance
_execution_manager = None

def get_execution_manager() -> AccountExecutionManager:
    """Get global account execution manager instance"""
    global _execution_manager
    if _execution_manager is None:
        _execution_manager = AccountExecutionManager()
    return _execution_manager
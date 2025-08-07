"""
Unit tests for per-account concurrency control
Tests that only one task runs per account at any time
"""

import asyncio
import pytest
import time
import uuid
from unittest.mock import MagicMock, AsyncMock

# Import modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ios_automation.account_execution_manager import (
    AccountExecutionManager, 
    AccountExecutionState, 
    AccountExecutionInfo
)
from ios_automation.task_manager import TaskManager, InstagramTask, InstagramAction
from ios_automation.device_manager import IOSDeviceManager, IOSDevice


class TestAccountExecutionManager:
    """Test the account execution manager"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.execution_manager = AccountExecutionManager()
        
    def test_can_execute_task_available_account(self):
        """Test that available account can execute task"""
        account_id = "test_account_1"
        task_id = "task_1"
        
        can_execute, reason = self.execution_manager.can_execute_task(account_id, task_id)
        
        assert can_execute == True
        assert reason == "account_available"
        
    def test_start_task_execution_success(self):
        """Test starting task execution on available account"""
        account_id = "test_account_1"
        task_id = "task_1"
        device_id = "device_1"
        
        success = self.execution_manager.start_task_execution(
            account_id, task_id, device_id, "instagram"
        )
        
        assert success == True
        
        # Verify account is now running
        account_info = self.execution_manager.accounts[account_id]
        assert account_info.state == AccountExecutionState.RUNNING
        assert account_info.current_task_id == task_id
        assert account_info.current_device_id == device_id
        
    def test_concurrent_task_blocked(self):
        """Test that concurrent tasks on same account are blocked"""
        account_id = "test_account_1"
        task_id_1 = "task_1"
        task_id_2 = "task_2"
        device_id = "device_1"
        
        # Start first task
        success_1 = self.execution_manager.start_task_execution(
            account_id, task_id_1, device_id, "instagram"
        )
        assert success_1 == True
        
        # Try to start second task on same account
        success_2 = self.execution_manager.start_task_execution(
            account_id, task_id_2, device_id, "instagram"
        )
        assert success_2 == False
        
        # Verify second task is in waiting queue
        account_info = self.execution_manager.accounts[account_id]
        assert task_id_2 in account_info.waiting_tasks
        
    def test_task_completion_releases_account(self):
        """Test that completing a task releases the account for next task"""
        account_id = "test_account_1"
        task_id_1 = "task_1"
        task_id_2 = "task_2"
        device_id = "device_1"
        
        # Start first task
        self.execution_manager.start_task_execution(
            account_id, task_id_1, device_id, "instagram"
        )
        
        # Queue second task
        self.execution_manager.start_task_execution(
            account_id, task_id_2, device_id, "instagram"
        )
        
        # Complete first task
        next_task_id = self.execution_manager.complete_task_execution(
            account_id, task_id_1, success=True
        )
        
        # Verify account is available and next task is returned
        account_info = self.execution_manager.accounts[account_id]
        assert account_info.state == AccountExecutionState.AVAILABLE
        assert account_info.current_task_id is None
        assert next_task_id == task_id_2
        
    def test_multiple_accounts_can_run_simultaneously(self):
        """Test that different accounts can run tasks simultaneously"""
        account_id_1 = "test_account_1"
        account_id_2 = "test_account_2"
        task_id_1 = "task_1"
        task_id_2 = "task_2"
        device_id_1 = "device_1"
        device_id_2 = "device_2"
        
        # Start tasks on different accounts
        success_1 = self.execution_manager.start_task_execution(
            account_id_1, task_id_1, device_id_1, "instagram"
        )
        success_2 = self.execution_manager.start_task_execution(
            account_id_2, task_id_2, device_id_2, "instagram"
        )
        
        assert success_1 == True
        assert success_2 == True
        
        # Verify both accounts are running
        account_1 = self.execution_manager.accounts[account_id_1]
        account_2 = self.execution_manager.accounts[account_id_2]
        
        assert account_1.state == AccountExecutionState.RUNNING
        assert account_2.state == AccountExecutionState.RUNNING
        
    def test_waiting_task_queue_fifo(self):
        """Test that waiting tasks are processed in FIFO order"""
        account_id = "test_account_1"
        task_ids = ["task_1", "task_2", "task_3", "task_4"]
        device_id = "device_1"
        
        # Start first task
        self.execution_manager.start_task_execution(
            account_id, task_ids[0], device_id, "instagram"
        )
        
        # Queue remaining tasks
        for task_id in task_ids[1:]:
            self.execution_manager.start_task_execution(
                account_id, task_id, device_id, "instagram"
            )
        
        # Verify waiting queue order
        account_info = self.execution_manager.accounts[account_id]
        assert account_info.waiting_tasks == task_ids[1:]
        
        # Complete tasks and verify FIFO order
        for expected_next_task in task_ids[1:]:
            next_task_id = self.execution_manager.complete_task_execution(
                account_id, account_info.current_task_id, success=True
            )
            assert next_task_id == expected_next_task
            
            # Start the next task to update current_task_id
            if next_task_id:
                self.execution_manager.start_task_execution(
                    account_id, next_task_id, device_id, "instagram"
                )
        
    def test_cooldown_blocks_new_tasks(self):
        """Test that accounts in cooldown block new tasks"""
        account_id = "test_account_1"
        task_id = "task_1"
        
        # Put account in cooldown
        account_info = self.execution_manager.get_or_create_account_info(account_id)
        account_info.state = AccountExecutionState.COOLDOWN
        
        # Try to start task
        can_execute, reason = self.execution_manager.can_execute_task(account_id, task_id)
        
        assert can_execute == False
        assert "cooldown" in reason.lower()
        
    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly"""
        account_id_1 = "test_account_1"
        account_id_2 = "test_account_2"
        
        # Start task on account 1
        self.execution_manager.start_task_execution(
            account_id_1, "task_1", "device_1", "instagram"
        )
        
        # Queue task on account 1 (should go to waiting)
        self.execution_manager.start_task_execution(
            account_id_1, "task_2", "device_1", "instagram"
        )
        
        # Start task on account 2
        self.execution_manager.start_task_execution(
            account_id_2, "task_3", "device_2", "engagement"
        )
        
        metrics = self.execution_manager.get_metrics()
        
        assert metrics["total_accounts_tracked"] == 2
        assert metrics["accounts_running"] == 2
        assert metrics["accounts_waiting"] == 1  # account_1 has waiting tasks
        assert metrics["total_tasks_queued_waiting"] == 1
        
    def test_remove_waiting_task(self):
        """Test removing a task from waiting queue"""
        account_id = "test_account_1"
        task_id_1 = "task_1"
        task_id_2 = "task_2"
        task_id_3 = "task_3"
        device_id = "device_1"
        
        # Start first task
        self.execution_manager.start_task_execution(
            account_id, task_id_1, device_id, "instagram"
        )
        
        # Queue two more tasks
        self.execution_manager.start_task_execution(
            account_id, task_id_2, device_id, "instagram"
        )
        self.execution_manager.start_task_execution(
            account_id, task_id_3, device_id, "instagram"
        )
        
        # Remove middle task
        removed = self.execution_manager.remove_waiting_task(account_id, task_id_2)
        assert removed == True
        
        # Verify queue updated
        account_info = self.execution_manager.accounts[account_id]
        assert account_info.waiting_tasks == [task_id_3]
        
        # Complete first task
        next_task_id = self.execution_manager.complete_task_execution(
            account_id, task_id_1, success=True
        )
        
        # Should get task_3, not task_2
        assert next_task_id == task_id_3


class TestConcurrencyIntegration:
    """Integration tests for concurrency control with task managers"""
    
    @pytest.fixture
    def mock_device_manager(self):
        """Create mock device manager"""
        device_manager = MagicMock(spec=IOSDeviceManager)
        
        # Create mock devices
        device1 = MagicMock(spec=IOSDevice)
        device1.udid = "device_1"
        device1.name = "Test Device 1"
        
        device2 = MagicMock(spec=IOSDevice)
        device2.udid = "device_2" 
        device2.name = "Test Device 2"
        
        device_manager.get_available_device = AsyncMock(side_effect=[device1, device2, None])
        device_manager.release_device = AsyncMock(return_value=True)
        
        return device_manager
        
    @pytest.fixture  
    def mock_task(self):
        """Create mock Instagram task"""
        task = MagicMock(spec=InstagramTask)
        task.task_id = str(uuid.uuid4())
        task.target_username = "test_user"
        task.actions = [InstagramAction.FOLLOW_USER]
        task.status = "pending"
        return task
    
    @pytest.mark.asyncio
    async def test_task_manager_respects_concurrency(self, mock_device_manager):
        """Test that TaskManager respects per-account concurrency limits"""
        task_manager = TaskManager(mock_device_manager)
        execution_manager = task_manager.execution_manager
        
        # Create tasks for same account (same device)
        account_id = "device_1"
        
        # Mock the automator execution
        mock_automator_result = {
            "success": True,
            "completed_actions": [],
            "session_stats": {}
        }
        
        # Start first task execution directly
        task1_started = execution_manager.start_task_execution(
            account_id, "task_1", "device_1", "instagram"
        )
        assert task1_started == True
        
        # Try to start second task on same account
        task2_started = execution_manager.start_task_execution(
            account_id, "task_2", "device_1", "instagram"
        )
        assert task2_started == False
        
        # Verify second task is waiting
        waiting_tasks = execution_manager.get_waiting_tasks_by_account()
        assert "device_1" in waiting_tasks
        assert "task_2" in waiting_tasks["device_1"]
        
        # Complete first task
        next_task = execution_manager.complete_task_execution(
            account_id, "task_1", success=True
        )
        assert next_task == "task_2"
        
    def test_different_accounts_can_run_concurrently(self):
        """Test that tasks on different accounts can run simultaneously"""
        execution_manager = AccountExecutionManager()
        
        # Start tasks on two different accounts
        task1_started = execution_manager.start_task_execution(
            "account_1", "task_1", "device_1", "instagram"
        )
        task2_started = execution_manager.start_task_execution(
            "account_2", "task_2", "device_2", "instagram"
        )
        
        assert task1_started == True
        assert task2_started == True
        
        # Verify both are running
        metrics = execution_manager.get_metrics()
        assert metrics["accounts_running"] == 2
        assert metrics["accounts_waiting"] == 0


def test_suite():
    """Run all concurrency tests"""
    # Create test instance
    test_execution_manager = TestAccountExecutionManager()
    test_integration = TestConcurrencyIntegration()
    
    print("Running per-account concurrency control tests...")
    
    # Test execution manager
    test_methods = [
        test_execution_manager.test_can_execute_task_available_account,
        test_execution_manager.test_start_task_execution_success,
        test_execution_manager.test_concurrent_task_blocked,
        test_execution_manager.test_task_completion_releases_account,
        test_execution_manager.test_multiple_accounts_can_run_simultaneously,
        test_execution_manager.test_waiting_task_queue_fifo,
        test_execution_manager.test_cooldown_blocks_new_tasks,
        test_execution_manager.test_metrics_tracking,
        test_execution_manager.test_remove_waiting_task,
        test_integration.test_different_accounts_can_run_concurrently
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_execution_manager.setup_method()  # Reset state
            test_method()
            print(f"✅ {test_method.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method.__name__}: {e}")
            failed += 1
    
    print(f"\nTest Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = test_suite()
    exit(0 if success else 1)
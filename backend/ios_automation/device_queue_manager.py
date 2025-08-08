"""
Per-Device Queue Manager with Mock Execution for Safe Development
Manages device-specific FIFO queues and pacing controls
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
import uuid

from .workflow_models import DeviceTask, DevicePacingState, get_workflow_db_manager
from .device_manager import IOSDeviceManager, DeviceStatus

logger = logging.getLogger(__name__)

class DeviceQueueManager:
    """Manages per-device FIFO queues with pacing and capacity controls"""
    
    def __init__(self, device_manager: IOSDeviceManager):
        self.device_manager = device_manager
        self.workflow_db = get_workflow_db_manager()
        
        # In-memory device queues (FIFO)
        self.device_queues: Dict[str, deque] = defaultdict(deque)  # device_id -> deque of DeviceTask
        self.device_pacing_states: Dict[str, DevicePacingState] = {}
        
        # Safe mode - prevents actual task execution
        self.safe_mode = True  # Always True for Phases 1-3
        self.mock_execution_duration = 30  # Mock task duration in seconds
        
        # Feature flag for backward compatibility
        self.enable_pooled_assignment = False  # Default to new per-device system
        
        # Mock data for testing
        self._initialize_mock_data()
        
        # Monitoring
        self.queue_stats = {
            "total_tasks_enqueued": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "active_devices": 0,
            "average_queue_length": 0.0
        }
        
        logger.info("DeviceQueueManager initialized in SAFE MODE")
    
    def _initialize_mock_data(self):
        """Initialize with mock data for testing"""
        # Create mock devices if none exist
        mock_devices = [
            {"udid": "mock_device_001", "name": "iPhone 12 Pro", "status": DeviceStatus.READY},
            {"udid": "mock_device_002", "name": "iPhone 13 Mini", "status": DeviceStatus.READY},
            {"udid": "mock_device_003", "name": "iPad Pro", "status": DeviceStatus.READY},
        ]
        
        for mock_device in mock_devices:
            if mock_device["udid"] not in self.device_queues:
                self.device_queues[mock_device["udid"]] = deque()
                
                # Create mock pacing state
                pacing_state = DevicePacingState(
                    device_id=mock_device["udid"],
                    device_name=mock_device["name"],
                    max_concurrent=1,
                    rate_limits={"actions_per_hour": 60, "sessions_per_day": 10},
                    session_limits={"actions_per_session": 25, "max_session_duration": 1800},
                    queue_length=0,
                    next_run_eta=datetime.utcnow() + timedelta(minutes=2)
                )
                self.device_pacing_states[mock_device["udid"]] = pacing_state
        
        logger.info(f"Initialized {len(mock_devices)} mock device queues")
    
    async def enqueue_task_to_device(self, task: DeviceTask) -> bool:
        """Enqueue task to specific device queue"""
        try:
            device_id = task.device_id
            
            if not device_id:
                logger.error("Task must have device_id assigned")
                return False
            
            # Check if device exists (in mock mode, always allow)
            if not self.safe_mode:
                device = self.device_manager.devices.get(device_id)
                if not device:
                    logger.error(f"Device {device_id} not found")
                    return False
            
            # Get/create pacing state for device
            if device_id not in self.device_pacing_states:
                device_name = f"Mock Device {device_id[-3:]}"
                if not self.safe_mode and device_id in self.device_manager.devices:
                    device_name = self.device_manager.devices[device_id].name
                
                pacing_state = DevicePacingState(
                    device_id=device_id,
                    device_name=device_name
                )
                self.device_pacing_states[device_id] = pacing_state
                await self.workflow_db.upsert_device_pacing_state(pacing_state)
            
            # Set task status and queue position
            task.status = "queued"
            task.queue_position = len(self.device_queues[device_id]) + 1
            task.enqueued_at = datetime.utcnow()
            
            # Add to device queue
            self.device_queues[device_id].append(task)
            
            # Update pacing state
            pacing_state = self.device_pacing_states[device_id]
            pacing_state.queue_length = len(self.device_queues[device_id])
            pacing_state.last_updated = datetime.utcnow()
            await self.workflow_db.upsert_device_pacing_state(pacing_state)
            
            # Persist task to database
            await self.workflow_db.create_device_task(task)
            
            # Update stats
            self.queue_stats["total_tasks_enqueued"] += 1
            
            logger.info(f"Enqueued task {task.task_id} to device {device_id} (position {task.queue_position})")
            return True
            
        except Exception as e:
            logger.error(f"Error enqueuing task to device: {e}")
            return False
    
    async def get_device_queue_snapshot(self, device_id: str) -> Dict[str, Any]:
        """Get comprehensive device queue snapshot with pacing stats"""
        try:
            queue = self.device_queues.get(device_id, deque())
            pacing_state = self.device_pacing_states.get(device_id)
            
            if not pacing_state:
                # Create default state
                pacing_state = DevicePacingState(
                    device_id=device_id,
                    device_name=f"Device {device_id[-6:]}"
                )
                self.device_pacing_states[device_id] = pacing_state
            
            # Calculate next run ETA based on pacing
            next_run_eta = None
            if pacing_state.cooldown_until and pacing_state.cooldown_until > datetime.utcnow():
                next_run_eta = pacing_state.cooldown_until
            elif len(queue) > 0:
                # Estimate based on rate limits
                if pacing_state.current_task_id:
                    # Device busy, ETA after current task completes
                    next_run_eta = datetime.utcnow() + timedelta(seconds=self.mock_execution_duration)
                else:
                    # Device available, can start immediately
                    next_run_eta = datetime.utcnow() + timedelta(seconds=5)
            
            # Mock rate window counters
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            if not pacing_state.rate_window_start or pacing_state.rate_window_start < current_hour:
                pacing_state.rate_window_start = current_hour
                pacing_state.rate_window_actions = pacing_state.actions_this_hour
            
            return {
                "device_id": device_id,
                "device_name": pacing_state.device_name,
                "queue_length": len(queue),
                "queue_tasks": [
                    {
                        "task_id": task.task_id,
                        "target_username": task.target_username,
                        "priority": task.priority,
                        "enqueued_at": task.enqueued_at.isoformat(),
                        "queue_position": task.queue_position,
                        "workflow_id": task.workflow_id
                    }
                    for task in list(queue)[:10]  # Show first 10 tasks
                ],
                "current_task": {
                    "task_id": pacing_state.current_task_id,
                    "started_at": pacing_state.session_start_time.isoformat() if pacing_state.session_start_time else None,
                    "estimated_completion": (datetime.utcnow() + timedelta(seconds=self.mock_execution_duration)).isoformat() if pacing_state.current_task_id else None
                } if pacing_state.current_task_id else None,
                "next_run_eta": next_run_eta.isoformat() if next_run_eta else None,
                "pacing_stats": {
                    "max_concurrent": pacing_state.max_concurrent,
                    "rate_limits": pacing_state.rate_limits,
                    "session_limits": pacing_state.session_limits,
                    "actions_this_hour": pacing_state.actions_this_hour,
                    "actions_this_session": pacing_state.actions_this_session,
                    "rate_window_start": pacing_state.rate_window_start.isoformat() if pacing_state.rate_window_start else None,
                    "rate_window_actions": pacing_state.rate_window_actions,
                    "in_rest_window": pacing_state.in_rest_window,
                    "cooldown_until": pacing_state.cooldown_until.isoformat() if pacing_state.cooldown_until else None
                },
                "statistics": {
                    "total_tasks_completed": pacing_state.total_tasks_completed,
                    "total_actions_performed": pacing_state.total_actions_performed,
                    "average_session_duration": pacing_state.average_session_duration
                },
                "safe_mode": self.safe_mode
            }
            
        except Exception as e:
            logger.error(f"Error getting device queue snapshot: {e}")
            return {"error": str(e)}
    
    async def get_all_device_queues(self) -> Dict[str, Dict[str, Any]]:
        """Get snapshots of all device queues"""
        try:
            snapshots = {}
            
            # Include all devices with queues
            all_device_ids = set(self.device_queues.keys())
            all_device_ids.update(self.device_pacing_states.keys())
            
            for device_id in all_device_ids:
                snapshots[device_id] = await self.get_device_queue_snapshot(device_id)
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Error getting all device queues: {e}")
            return {}
    
    async def mock_task_execution(self, task: DeviceTask) -> Dict[str, Any]:
        """Simulate task execution for safe development mode"""
        try:
            device_id = task.device_id
            pacing_state = self.device_pacing_states[device_id]
            
            # Mark task as running
            task.status = "running"
            task.started_at = datetime.utcnow()
            await self.workflow_db.update_task_status(task.task_id, "running", started_at=task.started_at)
            
            # Update pacing state
            pacing_state.current_task_id = task.task_id
            pacing_state.session_start_time = datetime.utcnow()
            await self.workflow_db.upsert_device_pacing_state(pacing_state)
            
            logger.info(f"[MOCK] Started task {task.task_id} on device {device_id}")
            
            # Simulate execution time
            await asyncio.sleep(2)  # Quick mock execution
            
            # Mark as completed with mock results
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.completed_actions = ["search_user", "view_profile", "like_post"] 
            task.session_stats = {
                "actions_performed": 3,
                "duration": self.mock_execution_duration,
                "success_rate": 1.0,
                "mode": "mock"
            }
            
            await self.workflow_db.update_task_status(
                task.task_id, 
                "completed",
                completed_at=task.completed_at,
                completed_actions=task.completed_actions,
                session_stats=task.session_stats
            )
            
            # Update pacing state
            pacing_state.current_task_id = None
            pacing_state.session_start_time = None
            pacing_state.total_tasks_completed += 1
            pacing_state.total_actions_performed += 3
            pacing_state.actions_this_hour += 3
            pacing_state.actions_this_session += 3
            pacing_state.last_action_time = datetime.utcnow()
            
            # Calculate next ETA based on rate limits
            if pacing_state.actions_this_hour >= pacing_state.rate_limits.get("actions_per_hour", 60):
                # Hit hourly limit, cooldown for rest of hour
                next_hour = (datetime.utcnow() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                pacing_state.cooldown_until = next_hour
                pacing_state.actions_this_hour = 0
            else:
                # Normal pacing delay
                pacing_state.next_run_eta = datetime.utcnow() + timedelta(minutes=2)
            
            await self.workflow_db.upsert_device_pacing_state(pacing_state)
            
            # Update stats
            self.queue_stats["total_tasks_completed"] += 1
            
            logger.info(f"[MOCK] Completed task {task.task_id} on device {device_id}")
            
            return {
                "success": True,
                "task_id": task.task_id,
                "duration": 2,
                "completed_actions": task.completed_actions,
                "session_stats": task.session_stats,
                "mode": "mock"
            }
            
        except Exception as e:
            logger.error(f"Error in mock task execution: {e}")
            
            # Mark as failed
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = f"Mock execution error: {str(e)}"
            
            await self.workflow_db.update_task_status(
                task.task_id, 
                "failed",
                completed_at=task.completed_at,
                error_message=task.error_message
            )
            
            # Clear pacing state
            if device_id in self.device_pacing_states:
                pacing_state = self.device_pacing_states[device_id]
                pacing_state.current_task_id = None
                pacing_state.session_start_time = None
                await self.workflow_db.upsert_device_pacing_state(pacing_state)
            
            self.queue_stats["total_tasks_failed"] += 1
            
            return {
                "success": False,
                "task_id": task.task_id,
                "error": str(e),
                "mode": "mock"
            }
    
    async def process_device_queues(self):
        """Process all device queues (mock execution only in safe mode)"""
        """This would be called by a background worker in production"""
        try:
            processed_count = 0
            
            for device_id, queue in self.device_queues.items():
                if len(queue) == 0:
                    continue
                
                pacing_state = self.device_pacing_states.get(device_id)
                if not pacing_state:
                    continue
                
                # Check if device can accept new task
                can_execute = (
                    not pacing_state.current_task_id and  # Not currently running a task
                    not pacing_state.in_rest_window and   # Not in rest window
                    (not pacing_state.cooldown_until or pacing_state.cooldown_until <= datetime.utcnow())  # Not in cooldown
                )
                
                if can_execute:
                    # Get next task from queue
                    task = queue.popleft()
                    
                    # Update queue positions for remaining tasks
                    for i, remaining_task in enumerate(queue):
                        remaining_task.queue_position = i + 1
                    
                    # Update pacing state queue length
                    pacing_state.queue_length = len(queue)
                    await self.workflow_db.upsert_device_pacing_state(pacing_state)
                    
                    # Execute task (mock mode)
                    if self.safe_mode:
                        await self.mock_task_execution(task)
                        processed_count += 1
                    else:
                        # In production, this would call real task execution
                        logger.info(f"Would execute task {task.task_id} on device {device_id}")
            
            if processed_count > 0:
                logger.info(f"[MOCK] Processed {processed_count} tasks across all device queues")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing device queues: {e}")
            return 0
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics"""
        try:
            total_queued = sum(len(queue) for queue in self.device_queues.values())
            active_devices = len([
                pacing for pacing in self.device_pacing_states.values()
                if pacing.current_task_id is not None
            ])
            
            device_queue_lengths = [len(queue) for queue in self.device_queues.values()]
            avg_queue_length = sum(device_queue_lengths) / len(device_queue_lengths) if device_queue_lengths else 0
            
            return {
                "total_devices_tracked": len(self.device_queues),
                "total_tasks_queued": total_queued,
                "active_devices": active_devices,
                "average_queue_length": round(avg_queue_length, 2),
                "device_breakdown": {
                    device_id: {
                        "queue_length": len(queue),
                        "current_task": pacing_state.current_task_id if device_id in self.device_pacing_states else None,
                        "next_run_eta": pacing_state.next_run_eta.isoformat() if device_id in self.device_pacing_states and pacing_state.next_run_eta else None
                    }
                    for device_id, queue in self.device_queues.items()
                    for pacing_state in [self.device_pacing_states.get(device_id, DevicePacingState(device_id=device_id))]
                },
                "cumulative_stats": self.queue_stats,
                "safe_mode": self.safe_mode,
                "feature_flags": {
                    "enable_pooled_assignment": self.enable_pooled_assignment
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting queue statistics: {e}")
            return {"error": str(e)}
    
    def is_pooled_assignment_enabled(self) -> bool:
        """Check if legacy pooled assignment is enabled"""
        return self.enable_pooled_assignment
    
    def get_safe_mode_status(self) -> Dict[str, Any]:
        """Get safe mode status information"""
        return {
            "safe_mode": self.safe_mode,
            "message": "Task execution is disabled - running in simulation mode for development",
            "mock_execution_duration": self.mock_execution_duration,
            "total_mock_tasks_completed": self.queue_stats["total_tasks_completed"]
        }

# Global device queue manager instance
device_queue_manager = None

def get_device_queue_manager(device_manager: IOSDeviceManager = None) -> DeviceQueueManager:
    """Get global device queue manager instance"""
    global device_queue_manager
    if device_queue_manager is None:
        if device_manager is None:
            from .device_manager import IOSDeviceManager
            device_manager = IOSDeviceManager()
        device_queue_manager = DeviceQueueManager(device_manager)
    return device_queue_manager

async def init_device_queue_system(device_manager: IOSDeviceManager):
    """Initialize device queue system"""
    manager = get_device_queue_manager(device_manager)
    await manager.workflow_db.ensure_indexes()
    logger.info("Device queue system initialized successfully")
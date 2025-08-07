"""
Task Management System
Handles task queuing, execution, monitoring, and logging for iOS automation
"""

import asyncio
import logging
import uuid
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json

from .instagram_automator import InstagramAutomator, InstagramTask, InstagramAction
from .device_manager import IOSDeviceManager, IOSDevice, DeviceStatus
from .human_behavior import HumanBehaviorEngine, HumanBehaviorProfile
from .account_execution_manager import get_execution_manager, AccountExecutionState

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class TaskResult:
    task_id: str
    success: bool
    start_time: float
    end_time: float
    duration: float
    completed_actions: List[dict]
    error_message: Optional[str] = None
    session_stats: Optional[dict] = None
    device_udid: Optional[str] = None

class TaskQueue:
    """FIFO task queue with priority support"""
    
    def __init__(self):
        self.tasks: List[InstagramTask] = []
        self.lock = asyncio.Lock()
    
    async def add_task(self, task: InstagramTask, priority: TaskPriority = TaskPriority.NORMAL):
        """Add task to queue with priority"""
        async with self.lock:
            task.priority = priority
            
            # Insert based on priority
            inserted = False
            for i, existing_task in enumerate(self.tasks):
                if priority.value > getattr(existing_task, 'priority', TaskPriority.NORMAL).value:
                    self.tasks.insert(i, task)
                    inserted = True
                    break
            
            if not inserted:
                self.tasks.append(task)
            
            logger.info(f"Added task {task.task_id} to queue (priority: {priority.name})")
    
    async def get_next_task(self) -> Optional[InstagramTask]:
        """Get next task from queue"""
        async with self.lock:
            if self.tasks:
                task = self.tasks.pop(0)
                task.status = "running"
                return task
            return None
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove task from queue"""
        async with self.lock:
            for i, task in enumerate(self.tasks):
                if task.task_id == task_id:
                    self.tasks.pop(i)
                    return True
            return False
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            "total_tasks": len(self.tasks),
            "tasks_by_priority": {
                priority.name: len([t for t in self.tasks 
                                   if getattr(t, 'priority', TaskPriority.NORMAL) == priority])
                for priority in TaskPriority
            },
            "tasks": [
                {
                    "task_id": task.task_id,
                    "target_username": task.target_username,
                    "priority": getattr(task, 'priority', TaskPriority.NORMAL).name,
                    "status": task.status,
                    "created_at": getattr(task, 'created_at', None)
                }
                for task in self.tasks
            ]
        }

class TaskManager:
    """Main task management system"""
    
    def __init__(self, device_manager: IOSDeviceManager):
        self.device_manager = device_manager
        self.execution_manager = get_execution_manager()  # Per-account concurrency control
        self.task_queue = TaskQueue()
        self.instagram_automator = InstagramAutomator()
        
        # Task tracking
        self.active_tasks: Dict[str, InstagramTask] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_logs: Dict[str, List[dict]] = {}
        
        # Worker management
        self.workers: List[asyncio.Task] = []
        self.max_workers = 10
        self.is_running = False
        
        # Statistics
        self.stats = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "average_task_duration": 0,
            "queued_waiting_on_account": 0,  # New metric for concurrency control
            "uptime_start": time.time()
        }
        
        # Event callbacks
        self.task_callbacks: Dict[str, List[Callable]] = {
            "task_started": [],
            "task_completed": [],
            "task_failed": [],
            "worker_error": []
        }

    async def start_workers(self):
        """Start task worker processes"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info(f"Starting {self.max_workers} task workers")
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(self._monitor_loop())
        self.workers.append(monitor_task)

    async def stop_workers(self):
        """Stop all task workers"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping task workers")
        
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

    async def create_task(self, target_username: str, actions: List[str], 
                         max_likes: int = 3, max_follows: int = 1,
                         priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Create a new automation task"""
        task_id = str(uuid.uuid4())
        
        # Convert string actions to enum
        instagram_actions = []
        for action_str in actions:
            try:
                instagram_actions.append(InstagramAction(action_str))
            except ValueError:
                logger.warning(f"Unknown action: {action_str}")
        
        task = InstagramTask(
            task_id=task_id,
            device_udid="",  # Will be assigned when executed
            target_username=target_username,
            actions=instagram_actions,
            max_likes=max_likes,
            max_follows=max_follows,
            status=TaskStatus.PENDING.value
        )
        
        # Add timestamps
        task.created_at = time.time()
        task.completed_actions = []
        
        await self.task_queue.add_task(task, priority)
        
        self.stats["total_tasks_created"] += 1
        self.task_logs[task_id] = []
        
        logger.info(f"Created task {task_id} for user @{target_username}")
        
        # Trigger callbacks
        await self._trigger_callbacks("task_created", task)
        
        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        # Try to remove from queue first
        removed = await self.task_queue.remove_task(task_id)
        
        if removed:
            logger.info(f"Cancelled queued task {task_id}")
            return True
        
        # Check if task is currently running
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = "cancelled"
            logger.info(f"Marked running task {task_id} for cancellation")
            return True
        
        return False

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get current status of a task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status,
                "target_username": task.target_username,
                "device_udid": task.device_udid,
                "started_at": task.started_at,
                "completed_actions": task.completed_actions,
                "error_message": task.error_message
            }
        
        # Check completed tasks
        if task_id in self.task_results:
            result = self.task_results[task_id]
            return asdict(result)
        
        # Check queue
        queue_status = self.task_queue.get_queue_status()
        for task_info in queue_status["tasks"]:
            if task_info["task_id"] == task_id:
                return task_info
        
        return None

    async def get_task_logs(self, task_id: str) -> List[dict]:
        """Get logs for a specific task"""
        return self.task_logs.get(task_id, [])

    async def get_dashboard_stats(self) -> dict:
        """Get comprehensive dashboard statistics"""
        device_status = self.device_manager.get_device_status()
        queue_status = self.task_queue.get_queue_status()
        
        # Calculate average task duration
        if self.task_results:
            durations = [result.duration for result in self.task_results.values()]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        return {
            "system_stats": {
                "uptime": time.time() - self.stats["uptime_start"],
                "is_running": self.is_running,
                "active_workers": len(self.workers),
                "total_tasks_created": self.stats["total_tasks_created"],
                "total_tasks_completed": self.stats["total_tasks_completed"],
                "total_tasks_failed": self.stats["total_tasks_failed"],
                "average_task_duration": avg_duration
            },
            "device_status": device_status,
            "queue_status": queue_status,
            "active_tasks": {
                "count": len(self.active_tasks),
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "target_username": task.target_username,
                        "device_name": self.device_manager.devices.get(task.device_udid, {}).get('name', 'Unknown'),
                        "started_at": task.started_at,
                        "duration": time.time() - task.started_at if task.started_at else 0
                    }
                    for task in self.active_tasks.values()
                ]
            },
            "recent_results": [
                {
                    "task_id": result.task_id,
                    "success": result.success,
                    "duration": result.duration,
                    "completed_at": result.end_time,
                    "error": result.error_message
                }
                for result in list(self.task_results.values())[-10:]  # Last 10 results
            ]
        }

    async def _worker_loop(self, worker_id: str):
        """Main worker loop for processing tasks"""
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get next task from queue
                task = await self.task_queue.get_next_task()
                if not task:
                    await asyncio.sleep(1)  # No tasks available, wait
                    continue
                
                # Get available device
                device = await self.device_manager.get_available_device()
                if not device:
                    # No devices available, put task back in queue
                    task.status = "pending"
                    await self.task_queue.add_task(task)
                    await asyncio.sleep(5)
                    continue
                
                # Assign device to task
                task.device_udid = device.udid
                self.active_tasks[task.task_id] = task
                
                logger.info(f"Worker {worker_id} starting task {task.task_id} on device {device.name}")
                
                # Trigger callbacks
                await self._trigger_callbacks("task_started", task)
                
                # Execute task
                result = await self._execute_task_with_logging(task, device, worker_id)
                
                # Store result
                self.task_results[task.task_id] = result
                
                # Update statistics
                if result.success:
                    self.stats["total_tasks_completed"] += 1
                    await self._trigger_callbacks("task_completed", task, result)
                else:
                    self.stats["total_tasks_failed"] += 1
                    await self._trigger_callbacks("task_failed", task, result)
                
                # Release device
                await self.device_manager.release_device(device.udid)
                
                # Remove from active tasks
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]
                
                logger.info(f"Worker {worker_id} completed task {task.task_id}")
                
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await self._trigger_callbacks("worker_error", worker_id, e)
                await asyncio.sleep(5)  # Prevent rapid error loops

    async def _execute_task_with_logging(self, task: InstagramTask, 
                                       device: IOSDevice, worker_id: str) -> TaskResult:
        """Execute task with comprehensive logging"""
        start_time = time.time()
        
        try:
            # Create behavior engine for this task
            behavior_engine = HumanBehaviorEngine()
            # Use device UDID as account identifier (or could be Instagram username)
            account_id = device.udid
            automator = InstagramAutomator(behavior_engine, account_id)
            
            # Execute task
            result_data = await automator.execute_task(task, device)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Create result object
            result = TaskResult(
                task_id=task.task_id,
                success=result_data["success"],
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                completed_actions=result_data.get("completed_actions", []),
                error_message=result_data.get("error"),
                session_stats=result_data.get("session_stats"),
                device_udid=device.udid
            )
            
            # Log task completion
            self._log_task_event(task.task_id, "task_completed", {
                "success": result.success,
                "duration": duration,
                "actions_completed": len(result.completed_actions),
                "worker_id": worker_id,
                "device_name": device.name
            })
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = TaskResult(
                task_id=task.task_id,
                success=False,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                completed_actions=task.completed_actions or [],
                error_message=str(e),
                device_udid=device.udid
            )
            
            self._log_task_event(task.task_id, "task_failed", {
                "error": str(e),
                "duration": duration,
                "worker_id": worker_id,
                "device_name": device.name
            })
            
            return result

    async def _monitor_loop(self):
        """Monitor system health and perform maintenance"""
        logger.info("Monitor loop started")
        
        while self.is_running:
            try:
                # Device heartbeat check
                await self.device_manager.heartbeat_check()
                
                # Clean up old task results (keep last 1000)
                if len(self.task_results) > 1000:
                    oldest_tasks = sorted(self.task_results.items(), 
                                        key=lambda x: x[1].start_time)[:100]
                    for task_id, _ in oldest_tasks:
                        del self.task_results[task_id]
                        if task_id in self.task_logs:
                            del self.task_logs[task_id]
                
                # Log system stats periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    stats = await self.get_dashboard_stats()
                    logger.info(f"System stats: {json.dumps(stats['system_stats'], indent=2)}")
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                logger.info("Monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(30)

    def _log_task_event(self, task_id: str, event_type: str, data: dict):
        """Log task event with timestamp"""
        if task_id not in self.task_logs:
            self.task_logs[task_id] = []
        
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        
        self.task_logs[task_id].append(log_entry)
        
        # Limit log size per task (keep last 100 entries)
        if len(self.task_logs[task_id]) > 100:
            self.task_logs[task_id] = self.task_logs[task_id][-100:]

    async def _trigger_callbacks(self, event_type: str, *args):
        """Trigger registered callbacks for events"""
        callbacks = self.task_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Callback error for {event_type}: {e}")

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for task events"""
        if event_type not in self.task_callbacks:
            self.task_callbacks[event_type] = []
        self.task_callbacks[event_type].append(callback)
"""
Engagement Task Management System
Handles engagement-based automation tasks with dedicated queue and monitoring
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

from .engagement_automator import EngagementAutomator, EngagementTask, EngagementAction
from .device_manager import IOSDeviceManager, IOSDevice, DeviceStatus
from .human_behavior import HumanBehaviorEngine, HumanBehaviorProfile
from .account_execution_manager import get_execution_manager, AccountExecutionState
from .task_manager import TaskPriority

class EngagementTaskQueue:
    """FIFO task queue specifically for engagement tasks"""
    
    def __init__(self):
        self.tasks: List[EngagementTask] = []
        self.lock = asyncio.Lock()
    
    async def add_task(self, task: EngagementTask, priority: TaskPriority = TaskPriority.NORMAL):
        """Add engagement task to queue with priority"""
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
            
            logger.info(f"Added engagement task {task.task_id} to queue (priority: {priority.name})")
    
    async def get_next_task(self) -> Optional[EngagementTask]:
        """Get next engagement task from queue"""
        async with self.lock:
            if self.tasks:
                task = self.tasks.pop(0)
                task.status = "running"
                return task
            return None
    
    async def remove_task(self, task_id: str) -> bool:
        """Remove engagement task from queue"""
        async with self.lock:
            for i, task in enumerate(self.tasks):
                if task.task_id == task_id:
                    self.tasks.pop(i)
                    return True
            return False
    
    def get_queue_status(self) -> dict:
        """Get current engagement queue status"""
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
                    "target_pages": task.target_pages,
                    "priority": getattr(task, 'priority', TaskPriority.NORMAL).name,
                    "status": task.status,
                    "created_at": getattr(task, 'created_at', None)
                }
                for task in self.tasks
            ]
        }

logger = logging.getLogger(__name__)

@dataclass
class EngagementTaskResult:
    task_id: str
    success: bool
    start_time: float
    end_time: float
    duration: float
    engagement_stats: Dict
    crawled_users_count: int
    completed_actions: List[dict]
    error_message: Optional[str] = None
    session_stats: Optional[dict] = None
    device_udid: Optional[str] = None

class EngagementTaskManager:
    """Dedicated task manager for engagement automation"""
    
    def __init__(self, device_manager: IOSDeviceManager):
        self.device_manager = device_manager
        self.execution_manager = get_execution_manager()  # Per-account concurrency control
        self.engagement_queue = EngagementTaskQueue()
        self.engagement_automator = EngagementAutomator()
        
        # Task tracking
        self.active_engagement_tasks: Dict[str, EngagementTask] = {}
        self.engagement_results: Dict[str, EngagementTaskResult] = {}
        self.engagement_logs: Dict[str, List[dict]] = {}
        
        # Worker management
        self.engagement_workers: List[asyncio.Task] = []
        self.max_engagement_workers = 5  # Lower than regular tasks due to complexity
        self.engagement_running = False
        
        # Statistics
        self.engagement_stats = {
            "total_tasks_created": 0,
            "total_tasks_completed": 0,
            "total_tasks_failed": 0,
            "total_users_engaged": 0,
            "total_follows_made": 0,
            "total_likes_given": 0,
            "total_comments_posted": 0,
            "average_task_duration": 0,
            "queued_waiting_on_account": 0,  # New metric for concurrency control
            "engagement_uptime_start": time.time()
        }
        
        # Event callbacks
        self.engagement_callbacks: Dict[str, List[Callable]] = {
            "engagement_task_started": [],
            "engagement_task_completed": [],
            "engagement_task_failed": [],
            "engagement_worker_error": []
        }

    async def start_engagement_workers(self):
        """Start engagement task worker processes"""
        if self.engagement_running:
            return
        
        self.engagement_running = True
        logger.info(f"Starting {self.max_engagement_workers} engagement task workers")
        
        for i in range(self.max_engagement_workers):
            worker = asyncio.create_task(self._engagement_worker_loop(f"engagement-worker-{i}"))
            self.engagement_workers.append(worker)
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(self._engagement_monitor_loop())
        self.engagement_workers.append(monitor_task)

    async def stop_engagement_workers(self):
        """Stop all engagement task workers"""
        if not self.engagement_running:
            return
        
        self.engagement_running = False
        logger.info("Stopping engagement task workers")
        
        for worker in self.engagement_workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.engagement_workers, return_exceptions=True)
        self.engagement_workers.clear()

    async def create_engagement_task(
        self,
        target_pages: List[str],
        comment_list: List[str],
        actions: Dict[str, bool],
        max_users_per_page: int = 20,
        profile_validation: Dict[str, bool] = None,
        skip_rate: float = 0.15,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """Create a new engagement automation task"""
        task_id = str(uuid.uuid4())
        
        # Clean up target pages (remove @ if present)
        clean_target_pages = [page.lstrip('@') for page in target_pages]
        
        # Default profile validation
        if profile_validation is None:
            profile_validation = {"public_only": True, "min_posts": 2}
        
        task = EngagementTask(
            task_id=task_id,
            device_udid="",  # Will be assigned when executed
            target_pages=clean_target_pages,
            comment_list=comment_list,
            actions=actions,
            max_users_per_page=max_users_per_page,
            profile_validation=profile_validation,
            skip_rate=skip_rate,
            status="pending"
        )
        
        # Add timestamps
        task.created_at = time.time()
        task.completed_actions = []
        
        await self.engagement_queue.add_task(task, priority)
        
        self.engagement_stats["total_tasks_created"] += 1
        self.engagement_logs[task_id] = []
        
        logger.info(f"Created engagement task {task_id} for pages: {clean_target_pages}")
        
        # Trigger callbacks
        await self._trigger_engagement_callbacks("engagement_task_created", task)
        
        return task_id

    async def cancel_engagement_task(self, task_id: str) -> bool:
        """Cancel a pending or running engagement task"""
        # Try to remove from queue first
        removed = await self.engagement_queue.remove_task(task_id)
        
        if removed:
            logger.info(f"Cancelled queued engagement task {task_id}")
            return True
        
        # Check if task is currently running
        if task_id in self.active_engagement_tasks:
            task = self.active_engagement_tasks[task_id]
            task.status = "cancelled"
            logger.info(f"Marked running engagement task {task_id} for cancellation")
            return True
        
        return False

    async def get_engagement_task_status(self, task_id: str) -> Optional[dict]:
        """Get current status of an engagement task"""
        # Check active tasks
        if task_id in self.active_engagement_tasks:
            task = self.active_engagement_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status,
                "target_pages": task.target_pages,
                "device_udid": task.device_udid,
                "started_at": task.started_at,
                "completed_actions": task.completed_actions,
                "engagement_stats": task.engagement_stats,
                "crawled_users_count": len(task.crawled_users) if task.crawled_users else 0,
                "error_message": task.error_message
            }
        
        # Check completed tasks
        if task_id in self.engagement_results:
            result = self.engagement_results[task_id]
            return asdict(result)
        
        # Check queue
        queue_status = self.engagement_queue.get_queue_status()
        for task_info in queue_status["tasks"]:
            if task_info["task_id"] == task_id:
                # Add target_pages for engagement tasks
                if hasattr(self.engagement_queue, 'tasks'):
                    for queue_task in self.engagement_queue.tasks:
                        if queue_task.task_id == task_id:
                            task_info["target_pages"] = getattr(queue_task, 'target_pages', [])
                            break
                return task_info
        
        return None

    async def get_engagement_task_logs(self, task_id: str) -> List[dict]:
        """Get logs for a specific engagement task"""
        return self.engagement_logs.get(task_id, [])

    async def get_engagement_history(self) -> Dict:
        """Get comprehensive engagement task history and analytics"""
        # Calculate statistics
        if self.engagement_results:
            durations = [result.duration for result in self.engagement_results.values()]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        # Recent results with detailed stats
        recent_results = []
        for result in list(self.engagement_results.values())[-20:]:  # Last 20 results
            recent_results.append({
                "task_id": result.task_id,
                "success": result.success,
                "duration": result.duration,
                "completed_at": result.end_time,
                "engagement_stats": result.engagement_stats,
                "crawled_users_count": result.crawled_users_count,
                "error": result.error_message
            })
        
        return {
            "summary_stats": {
                **self.engagement_stats,
                "average_task_duration": avg_duration,
                "uptime": time.time() - self.engagement_stats["engagement_uptime_start"]
            },
            "recent_results": recent_results,
            "queue_status": self.engagement_queue.get_queue_status(),
            "active_tasks_count": len(self.active_engagement_tasks)
        }

    async def get_engagement_dashboard_stats(self) -> Dict:
        """Get comprehensive engagement dashboard statistics"""
        queue_status = self.engagement_queue.get_queue_status()
        
        # Calculate average task duration
        if self.engagement_results:
            durations = [result.duration for result in self.engagement_results.values()]
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 0
        
        return {
            "engagement_stats": {
                "uptime": time.time() - self.engagement_stats["engagement_uptime_start"],
                "is_running": self.engagement_running,
                "active_workers": len(self.engagement_workers),
                "total_tasks_created": self.engagement_stats["total_tasks_created"],
                "total_tasks_completed": self.engagement_stats["total_tasks_completed"],
                "total_tasks_failed": self.engagement_stats["total_tasks_failed"],
                "total_users_engaged": self.engagement_stats["total_users_engaged"],
                "total_follows_made": self.engagement_stats["total_follows_made"],
                "total_likes_given": self.engagement_stats["total_likes_given"],
                "total_comments_posted": self.engagement_stats["total_comments_posted"],
                "average_task_duration": avg_duration
            },
            "engagement_queue": queue_status,
            "active_engagement_tasks": {
                "count": len(self.active_engagement_tasks),
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "target_pages": task.target_pages,
                        "device_name": self.device_manager.devices.get(task.device_udid, {}).get('name', 'Unknown'),
                        "started_at": task.started_at,
                        "duration": time.time() - task.started_at if task.started_at else 0,
                        "users_processed": task.engagement_stats.get("users_crawled", 0) if task.engagement_stats else 0
                    }
                    for task in self.active_engagement_tasks.values()
                ]
            }
        }

    async def _engagement_worker_loop(self, worker_id: str):
        """Main worker loop for processing engagement tasks with per-account concurrency control"""
        logger.info(f"Engagement worker {worker_id} started")
        
        while self.engagement_running:
            try:
                # Get next task from queue
                task = await self.engagement_queue.get_next_task()
                if not task:
                    await asyncio.sleep(2)  # Wait longer for engagement tasks
                    continue
                
                # Get available device
                device = await self.device_manager.get_available_device()
                if not device:
                    # No devices available, put task back in queue
                    task.status = "pending"
                    await self.engagement_queue.add_task(task)
                    await asyncio.sleep(10)  # Wait longer for devices
                    continue
                
                # Use device UDID as account identifier for concurrency control
                account_id = device.udid
                
                # Check if account can execute a new task (per-account concurrency control)
                can_execute = self.execution_manager.start_task_execution(
                    account_id=account_id,
                    task_id=task.task_id,
                    device_id=device.udid,
                    task_type="engagement"
                )
                
                if not can_execute:
                    # Account is busy or in cooldown, put task back and try another
                    task.status = "waiting"
                    await self.engagement_queue.add_task(task)
                    await self.device_manager.release_device(device.udid)
                    
                    # Update waiting metrics
                    self.engagement_stats["queued_waiting_on_account"] = len(
                        self.execution_manager.get_waiting_tasks_by_account()
                    )
                    
                    logger.info(f"Engagement task {task.task_id} waiting for account {account_id} availability")
                    await asyncio.sleep(3)  # Short wait before trying next task
                    continue
                
                # Assign device to task
                task.device_udid = device.udid
                self.active_engagement_tasks[task.task_id] = task
                
                logger.info(f"Engagement worker {worker_id} starting task {task.task_id} on device {device.name} (account: {account_id})")
                
                # Trigger callbacks
                await self._trigger_engagement_callbacks("engagement_task_started", task)
                
                # Execute engagement task
                result = await self._execute_engagement_task_with_logging(task, device, worker_id)
                
                # Complete task execution in execution manager
                next_waiting_task = self.execution_manager.complete_task_execution(
                    account_id=account_id,
                    task_id=task.task_id,
                    success=result.success
                )
                
                # Store result
                self.engagement_results[task.task_id] = result
                
                # Update statistics
                if result.success:
                    self.engagement_stats["total_tasks_completed"] += 1
                    self.engagement_stats["total_users_engaged"] += result.engagement_stats.get("users_crawled", 0)
                    self.engagement_stats["total_follows_made"] += result.engagement_stats.get("users_followed", 0)
                    self.engagement_stats["total_likes_given"] += result.engagement_stats.get("posts_liked", 0)
                    self.engagement_stats["total_comments_posted"] += result.engagement_stats.get("comments_posted", 0)
                    await self._trigger_engagement_callbacks("engagement_task_completed", task, result)
                else:
                    self.engagement_stats["total_tasks_failed"] += 1
                    await self._trigger_engagement_callbacks("engagement_task_failed", task, result)
                
                # Update waiting metrics
                self.engagement_stats["queued_waiting_on_account"] = len(
                    self.execution_manager.get_waiting_tasks_by_account()
                )
                
                # If there's a waiting task for this account, prioritize it
                if next_waiting_task:
                    logger.info(f"Account {account_id} has waiting engagement task {next_waiting_task}, will be prioritized")
                
                # Release device
                await self.device_manager.release_device(device.udid)
                
                # Remove from active tasks
                if task.task_id in self.active_engagement_tasks:
                    del self.active_engagement_tasks[task.task_id]
                
                logger.info(f"Engagement worker {worker_id} completed task {task.task_id} for account {account_id}")
                
            except asyncio.CancelledError:
                logger.info(f"Engagement worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Engagement worker {worker_id} error: {e}")
                await self._trigger_engagement_callbacks("engagement_worker_error", worker_id, e)
                await asyncio.sleep(5)  # Prevent rapid error loops

    async def _execute_engagement_task_with_logging(
        self, 
        task: EngagementTask, 
        device: IOSDevice, 
        worker_id: str
    ) -> EngagementTaskResult:
        """Execute engagement task with comprehensive logging"""
        start_time = time.time()
        
        try:
            # Create behavior engine for this task
            behavior_engine = HumanBehaviorEngine()
            # Use device UDID as account identifier
            account_id = device.udid
            automator = EngagementAutomator(behavior_engine, account_id)
            
            # Execute engagement task
            result_data = await automator.execute_engagement_task(task, device)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Create result object
            result = EngagementTaskResult(
                task_id=task.task_id,
                success=result_data["success"],
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                engagement_stats=result_data.get("engagement_stats", {}),
                crawled_users_count=result_data.get("crawled_users_count", 0),
                completed_actions=result_data.get("completed_actions", []),
                error_message=result_data.get("error"),
                session_stats=result_data.get("session_stats"),
                device_udid=device.udid
            )
            
            # Log task completion
            self._log_engagement_task_event(task.task_id, "engagement_task_completed", {
                "success": result.success,
                "duration": duration,
                "engagement_stats": result.engagement_stats,
                "crawled_users_count": result.crawled_users_count,
                "worker_id": worker_id,
                "device_name": device.name
            })
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            result = EngagementTaskResult(
                task_id=task.task_id,
                success=False,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                engagement_stats=task.engagement_stats or {},
                crawled_users_count=len(task.crawled_users) if task.crawled_users else 0,
                completed_actions=task.completed_actions or [],
                error_message=str(e),
                device_udid=device.udid
            )
            
            self._log_engagement_task_event(task.task_id, "engagement_task_failed", {
                "error": str(e),
                "duration": duration,
                "worker_id": worker_id,
                "device_name": device.name
            })
            
            return result

    async def _engagement_monitor_loop(self):
        """Monitor engagement system health and perform maintenance"""
        logger.info("Engagement monitor loop started")
        
        while self.engagement_running:
            try:
                # Clean up old results (keep last 500)
                if len(self.engagement_results) > 500:
                    oldest_tasks = sorted(self.engagement_results.items(), 
                                        key=lambda x: x[1].start_time)[:50]
                    for task_id, _ in oldest_tasks:
                        del self.engagement_results[task_id]
                        if task_id in self.engagement_logs:
                            del self.engagement_logs[task_id]
                
                # Log engagement stats periodically
                if int(time.time()) % 600 == 0:  # Every 10 minutes
                    stats = await self.get_engagement_dashboard_stats()
                    logger.info(f"Engagement stats: {json.dumps(stats['engagement_stats'], indent=2)}")
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except asyncio.CancelledError:
                logger.info("Engagement monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Engagement monitor loop error: {e}")
                await asyncio.sleep(60)

    def _log_engagement_task_event(self, task_id: str, event_type: str, data: dict):
        """Log engagement task event with timestamp"""
        if task_id not in self.engagement_logs:
            self.engagement_logs[task_id] = []
        
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        
        self.engagement_logs[task_id].append(log_entry)
        
        # Limit log size per task (keep last 50 entries)
        if len(self.engagement_logs[task_id]) > 50:
            self.engagement_logs[task_id] = self.engagement_logs[task_id][-50:]

    async def _trigger_engagement_callbacks(self, event_type: str, *args):
        """Trigger registered callbacks for engagement events"""
        callbacks = self.engagement_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Engagement callback error for {event_type}: {e}")

    def register_engagement_callback(self, event_type: str, callback: Callable):
        """Register callback for engagement task events"""
        if event_type not in self.engagement_callbacks:
            self.engagement_callbacks[event_type] = []
        self.engagement_callbacks[event_type].append(callback)
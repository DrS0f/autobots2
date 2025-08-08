"""
Workflow Templates and Per-Device Queue Data Models
For Phase 1-3 of Per-Device Task Queues + Workflow Cloning
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid

logger = logging.getLogger(__name__)

@dataclass
class WorkflowTemplate:
    """Workflow template for cloning to multiple devices"""
    template_id: str = ""
    name: str = ""
    description: str = ""
    
    # Workflow configuration
    target_pages: List[str] = None  # For engagement workflows
    target_username: str = ""  # For single-user workflows
    comment_list: List[str] = None
    actions: Dict[str, Any] = None  # {"follow": True, "like": True, "comment": True}
    
    # Task settings
    max_users_per_page: int = 20
    max_likes: int = 3  
    max_follows: int = 1
    profile_validation: Dict[str, Any] = None
    skip_rate: float = 0.15
    priority: str = "normal"
    
    # Timing and pacing
    delays: Dict[str, Any] = None  # Human behavior delays
    limits: Dict[str, Any] = None  # Rate limits per device
    rest_windows: List[Dict[str, Any]] = None  # Cooldown windows
    
    # Metadata
    template_type: str = "engagement"  # engagement|single_user|custom
    created_at: datetime = None
    updated_at: datetime = None
    created_by: str = "system"
    is_active: bool = True
    
    def __post_init__(self):
        if not self.template_id:
            self.template_id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.target_pages is None:
            self.target_pages = []
        if self.comment_list is None:
            self.comment_list = []
        if self.actions is None:
            self.actions = {"follow": True, "like": True, "comment": False}
        if self.profile_validation is None:
            self.profile_validation = {"public_only": True, "min_posts": 2}
        if self.delays is None:
            self.delays = {"action_delay": [2, 5], "page_delay": [3, 8]}
        if self.limits is None:
            self.limits = {"actions_per_hour": 50, "actions_per_session": 20}
        if self.rest_windows is None:
            self.rest_windows = [{"start_hour": 0, "end_hour": 7, "type": "sleep"}]

@dataclass  
class DevicePacingState:
    """Per-device pacing and capacity controls"""
    device_id: str = ""  # UDID
    device_name: str = ""
    
    # Capacity settings
    max_concurrent: int = 1
    rate_limits: Dict[str, int] = None  # {"actions_per_hour": 60, "sessions_per_day": 10}
    session_limits: Dict[str, int] = None  # {"actions_per_session": 25, "max_session_duration": 1800}
    
    # Current state
    current_task_id: Optional[str] = None
    queue_length: int = 0
    actions_this_hour: int = 0
    actions_this_session: int = 0
    session_start_time: Optional[datetime] = None
    
    # Rate window tracking
    rate_window_start: datetime = None
    rate_window_actions: int = 0
    
    # Rest windows and cooldowns
    in_rest_window: bool = False
    cooldown_until: Optional[datetime] = None
    last_action_time: Optional[datetime] = None
    next_run_eta: Optional[datetime] = None
    
    # Statistics
    total_tasks_completed: int = 0
    total_actions_performed: int = 0
    average_session_duration: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if not self.device_id:
            self.device_id = str(uuid.uuid4())
        if self.rate_limits is None:
            self.rate_limits = {"actions_per_hour": 60, "sessions_per_day": 10}
        if self.session_limits is None:
            self.session_limits = {"actions_per_session": 25, "max_session_duration": 1800}
        if self.rate_window_start is None:
            self.rate_window_start = datetime.utcnow()
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()

@dataclass
class DeviceTask:
    """Extended task model with device assignment and workflow reference"""
    task_id: str = ""
    device_id: str = ""  # Required - assigned device UDID
    workflow_id: Optional[str] = None  # Reference to workflow template
    template_snapshot: Optional[Dict[str, Any]] = None  # Frozen template at creation time
    
    # Original task fields
    target_username: str = ""
    target_pages: List[str] = None
    actions: List[str] = None
    comment_list: List[str] = None
    max_likes: int = 3
    max_follows: int = 1
    priority: str = "normal"
    
    # Queue and execution state
    status: str = "pending"  # pending|queued|running|completed|failed|cancelled
    queue_position: int = 0
    enqueued_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    error_message: Optional[str] = None
    completed_actions: List[str] = None
    session_stats: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        if self.target_pages is None:
            self.target_pages = []
        if self.actions is None:
            self.actions = ["search_user", "view_profile", "like_post", "follow_user", "navigate_home"]
        if self.comment_list is None:
            self.comment_list = []
        if self.enqueued_at is None:
            self.enqueued_at = datetime.utcnow()
        if self.completed_actions is None:
            self.completed_actions = []

class WorkflowDatabaseManager:
    """Database manager for workflow templates and device pacing state"""
    
    def __init__(self, db_client: AsyncIOMotorClient = None):
        if db_client is None:
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client[os.environ.get('DB_NAME', 'test_database')]
        else:
            self.client = db_client
            self.db = self.client[os.environ.get('DB_NAME', 'test_database')]
        
        # Collections
        self.workflow_templates = self.db.workflow_templates
        self.device_pacing_state = self.db.device_pacing_state
        self.device_tasks = self.db.device_tasks  # Extended tasks collection
        
        self._indexes_created = False
    
    async def ensure_indexes(self):
        """Create MongoDB indexes for workflow collections"""
        if self._indexes_created:
            return
        
        try:
            # Workflow Templates indexes
            await self.workflow_templates.create_index([
                ("template_id", 1)
            ], unique=True, name="template_id_unique_idx")
            
            await self.workflow_templates.create_index([
                ("name", 1), ("is_active", 1)
            ], name="template_name_active_idx")
            
            await self.workflow_templates.create_index([
                ("template_type", 1), ("is_active", 1)
            ], name="template_type_active_idx")
            
            # Device Pacing State indexes
            await self.device_pacing_state.create_index([
                ("device_id", 1)
            ], unique=True, name="device_pacing_unique_idx")
            
            # Device Tasks indexes  
            await self.device_tasks.create_index([
                ("device_id", 1), ("status", 1), ("enqueued_at", 1)
            ], name="device_queue_idx")
            
            await self.device_tasks.create_index([
                ("workflow_id", 1)
            ], name="workflow_tasks_idx")
            
            await self.device_tasks.create_index([
                ("task_id", 1)
            ], unique=True, name="task_id_unique_idx")
            
            self._indexes_created = True
            logger.info("Workflow database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating workflow database indexes: {e}")
            raise
    
    # Workflow Template methods
    async def create_workflow_template(self, template: WorkflowTemplate) -> bool:
        """Create a new workflow template"""
        try:
            await self.ensure_indexes()
            
            template_dict = asdict(template)
            result = await self.workflow_templates.insert_one(template_dict)
            
            if result.inserted_id:
                logger.info(f"Created workflow template: {template.name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error creating workflow template: {e}")
            return False
    
    async def get_workflow_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template by ID"""
        try:
            await self.ensure_indexes()
            
            result = await self.workflow_templates.find_one({
                "template_id": template_id,
                "is_active": True
            })
            
            if result:
                result.pop('_id', None)
                return WorkflowTemplate(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting workflow template {template_id}: {e}")
            return None
    
    async def list_workflow_templates(self, template_type: Optional[str] = None) -> List[WorkflowTemplate]:
        """List all active workflow templates"""
        try:
            await self.ensure_indexes()
            
            query = {"is_active": True}
            if template_type:
                query["template_type"] = template_type
            
            cursor = self.workflow_templates.find(query).sort("created_at", -1)
            results = await cursor.to_list(None)
            
            templates = []
            for result in results:
                result.pop('_id', None)
                templates.append(WorkflowTemplate(**result))
            
            return templates
            
        except Exception as e:
            logger.error(f"Error listing workflow templates: {e}")
            return []
    
    async def update_workflow_template(self, template: WorkflowTemplate) -> bool:
        """Update workflow template"""
        try:
            await self.ensure_indexes()
            
            template.updated_at = datetime.utcnow()
            template_dict = asdict(template)
            
            result = await self.workflow_templates.replace_one(
                {"template_id": template.template_id},
                template_dict
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating workflow template: {e}")
            return False
    
    async def delete_workflow_template(self, template_id: str) -> bool:
        """Soft delete workflow template"""
        try:
            result = await self.workflow_templates.update_one(
                {"template_id": template_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting workflow template: {e}")
            return False
    
    # Device Pacing State methods
    async def upsert_device_pacing_state(self, pacing_state: DevicePacingState) -> bool:
        """Create or update device pacing state"""
        try:
            await self.ensure_indexes()
            
            pacing_state.last_updated = datetime.utcnow()
            pacing_dict = asdict(pacing_state)
            
            result = await self.device_pacing_state.replace_one(
                {"device_id": pacing_state.device_id},
                pacing_dict,
                upsert=True
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting device pacing state: {e}")
            return False
    
    async def get_device_pacing_state(self, device_id: str) -> Optional[DevicePacingState]:
        """Get device pacing state"""
        try:
            await self.ensure_indexes()
            
            result = await self.device_pacing_state.find_one({"device_id": device_id})
            
            if result:
                result.pop('_id', None)
                return DevicePacingState(**result)
            
            # Return default state if not found
            default_state = DevicePacingState(device_id=device_id)
            await self.upsert_device_pacing_state(default_state)
            return default_state
            
        except Exception as e:
            logger.error(f"Error getting device pacing state: {e}")
            return None
    
    async def get_all_device_pacing_states(self) -> Dict[str, DevicePacingState]:
        """Get all device pacing states"""
        try:
            await self.ensure_indexes()
            
            cursor = self.device_pacing_state.find({})
            results = await cursor.to_list(None)
            
            states = {}
            for result in results:
                result.pop('_id', None)
                state = DevicePacingState(**result)
                states[state.device_id] = state
            
            return states
            
        except Exception as e:
            logger.error(f"Error getting all device pacing states: {e}")
            return {}
    
    # Device Task methods
    async def create_device_task(self, task: DeviceTask) -> bool:
        """Create a new device-bound task"""
        try:
            await self.ensure_indexes()
            
            task_dict = asdict(task)
            result = await self.device_tasks.insert_one(task_dict)
            
            if result.inserted_id:
                logger.info(f"Created device task {task.task_id} for device {task.device_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error creating device task: {e}")
            return False
    
    async def get_device_queue(self, device_id: str) -> List[DeviceTask]:
        """Get queued tasks for a specific device"""
        try:
            await self.ensure_indexes()
            
            cursor = self.device_tasks.find({
                "device_id": device_id,
                "status": {"$in": ["pending", "queued"]}
            }).sort("enqueued_at", 1)
            
            results = await cursor.to_list(None)
            
            tasks = []
            for i, result in enumerate(results):
                result.pop('_id', None)
                task = DeviceTask(**result)
                task.queue_position = i + 1
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error getting device queue for {device_id}: {e}")
            return []
    
    async def get_device_task(self, task_id: str) -> Optional[DeviceTask]:
        """Get device task by ID"""
        try:
            result = await self.device_tasks.find_one({"task_id": task_id})
            
            if result:
                result.pop('_id', None)
                return DeviceTask(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting device task {task_id}: {e}")
            return None
    
    async def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """Update task status and optional fields"""
        try:
            update_fields = {"status": status}
            
            if status == "running":
                update_fields["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                update_fields["completed_at"] = datetime.utcnow()
            
            # Add any additional fields
            update_fields.update(kwargs)
            
            result = await self.device_tasks.update_one(
                {"task_id": task_id},
                {"$set": update_fields}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return False
    
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Workflow database connection closed")

# Global workflow database manager instance
workflow_db_manager = None

def get_workflow_db_manager() -> WorkflowDatabaseManager:
    """Get global workflow database manager instance"""
    global workflow_db_manager
    if workflow_db_manager is None:
        workflow_db_manager = WorkflowDatabaseManager()
    return workflow_db_manager

async def init_workflow_database():
    """Initialize workflow database with indexes"""
    manager = get_workflow_db_manager()
    await manager.ensure_indexes()
    logger.info("Workflow database initialized successfully")
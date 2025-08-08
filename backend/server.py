from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import asyncio
import json
import csv
import io

# Import iOS automation modules
from ios_automation.device_manager import IOSDeviceManager, DeviceStatus
from ios_automation.task_manager import TaskManager, TaskPriority
from ios_automation.human_behavior import HumanBehaviorProfile
from ios_automation.engagement_task_manager import EngagementTaskManager

# Import Phase 4 modules
from ios_automation.database_models import DatabaseManager, get_db_manager, init_database
from ios_automation.deduplication_service import get_deduplication_service
from ios_automation.error_handling import get_error_handler
from ios_automation.account_execution_manager import get_execution_manager

# Import Per-Device Queue modules (Phase 1-3)
from ios_automation.workflow_models import get_workflow_db_manager, init_workflow_database
from ios_automation.device_queue_manager import get_device_queue_manager, init_device_queue_system
from ios_automation.workflow_manager import get_workflow_manager, init_workflow_manager

# Load environment first
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import license client after environment is loaded
from license_client import license_client

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="iOS Instagram Automation API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global automation manager instances
device_manager = IOSDeviceManager()
task_manager = TaskManager(device_manager)
engagement_task_manager = EngagementTaskManager(device_manager)

# Phase 1-3: Per-Device Queue System  
device_queue_manager = None  # Will be initialized after device_manager
workflow_manager = None      # Will be initialized after database

# Pydantic Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class TaskCreateRequest(BaseModel):
    target_username: str = Field(..., description="Instagram username to target (without @)")
    actions: List[str] = Field(default=["search_user", "view_profile", "like_post", "follow_user", "navigate_home"], 
                              description="List of actions to perform")
    max_likes: int = Field(default=3, ge=1, le=10, description="Maximum number of posts to like")
    max_follows: int = Field(default=1, ge=0, le=1, description="Whether to follow the user (0 or 1)")
    priority: str = Field(default="normal", description="Task priority: low, normal, high, urgent")

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class EngagementTaskCreateRequest(BaseModel):
    target_pages: List[str] = Field(..., description="List of Instagram usernames to crawl from")
    comment_list: List[str] = Field(..., description="List of possible comments to use")
    actions: Dict[str, bool] = Field(default={"follow": True, "like": True, "comment": True}, 
                                   description="Actions to perform: follow, like, comment")
    max_users_per_page: int = Field(default=20, ge=1, le=50, description="Maximum users to process per target page")
    profile_validation: Dict[str, Any] = Field(default={"public_only": True, "min_posts": 2}, 
                                              description="Profile validation criteria")
    skip_rate: float = Field(default=0.15, ge=0.0, le=0.5, description="Rate of users to skip for realism (0.1 = 10%)")
    priority: str = Field(default="normal", description="Task priority: low, normal, high, urgent")

class DeviceInfo(BaseModel):
    udid: str
    name: str
    ios_version: str
    status: str
    connection_port: int
    session_id: Optional[str] = None
    error_message: Optional[str] = None

class SystemStats(BaseModel):
    system_stats: Dict[str, Any]
    device_status: Dict[str, Any]
    queue_status: Dict[str, Any]
    active_tasks: Dict[str, Any]
    recent_results: List[Dict[str, Any]]
    license_status: Optional[Dict[str, Any]] = None
    safe_mode_status: Optional[Dict[str, Any]] = None  # New: Safe mode information

# Phase 4 Models
class SystemSettingsUpdate(BaseModel):
    reengagement_days: Optional[int] = Field(None, ge=1, le=365, description="Days before re-engagement allowed")
    rate_limit_steps: Optional[List[int]] = Field(None, description="Backoff steps in seconds for rate limits")
    cooldown_after_consecutive: Optional[int] = Field(None, ge=1, le=10, description="Consecutive errors before cooldown")
    cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Cooldown duration in minutes")

class InteractionEventQuery(BaseModel):
    account_id: Optional[str] = None
    target_username: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    skip: int = Field(0, ge=0)

class ExportRequest(BaseModel):
    format: str = Field("csv", description="Export format: csv or json")
    account_id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

# Per-Device Queue Models
class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., description="Workflow template name")
    description: str = Field("", description="Optional description")
    template_type: str = Field("engagement", description="Template type: engagement, single_user, custom")
    
    # Engagement workflow fields
    target_pages: List[str] = Field(default=[], description="Target Instagram pages for engagement")
    comment_list: List[str] = Field(default=[], description="List of comments to use")
    actions: Dict[str, bool] = Field(default={"follow": True, "like": True, "comment": False}, description="Actions to enable")
    max_users_per_page: int = Field(default=20, ge=1, le=50, description="Max users to process per page")
    profile_validation: Dict[str, Any] = Field(default={"public_only": True, "min_posts": 2}, description="Profile validation criteria")
    skip_rate: float = Field(default=0.15, ge=0.0, le=0.5, description="Skip rate for realism")
    
    # Single user workflow fields  
    target_username: str = Field("", description="Target username for single-user workflows")
    max_likes: int = Field(default=3, ge=1, le=10, description="Max posts to like")
    max_follows: int = Field(default=1, ge=0, le=1, description="Whether to follow user")
    
    # Common fields
    priority: str = Field(default="normal", description="Task priority")
    delays: Dict[str, Any] = Field(default={}, description="Human behavior delays")
    limits: Dict[str, Any] = Field(default={}, description="Rate limits")
    rest_windows: List[Dict[str, Any]] = Field(default=[], description="Rest/cooldown windows")

class WorkflowDeployRequest(BaseModel):
    device_ids: List[str] = Field(..., description="List of device UDIDs to deploy to")
    overrides: Optional[Dict[str, Any]] = Field(None, description="Optional configuration overrides")

class DeviceTaskCreate(BaseModel):
    device_id: str = Field(..., description="Required device UDID for task assignment")
    target_username: str = Field(..., description="Instagram username to target")
    actions: List[str] = Field(default=["search_user", "view_profile", "like_post", "follow_user", "navigate_home"], description="Actions to perform")
    max_likes: int = Field(default=3, ge=1, le=10, description="Max posts to like")
    max_follows: int = Field(default=1, ge=0, le=1, description="Whether to follow user")
    priority: str = Field(default="normal", description="Task priority")

# Basic API endpoints
@api_router.get("/")
async def root():
    return {"message": "iOS Instagram Automation API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Device Management Endpoints
@api_router.get("/devices/discover")
async def discover_devices():
    """Discover connected iOS devices"""
    try:
        devices = await device_manager.discover_devices()
        return {
            "success": True,
            "devices_found": len(devices),
            "devices": [
                {
                    "udid": device.udid,
                    "name": device.name,
                    "ios_version": device.ios_version,
                    "status": device.status.value,
                    "connection_port": device.connection_port
                }
                for device in devices
            ]
        }
    except Exception as e:
        logger.error(f"Device discovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Device discovery failed: {str(e)}")

@api_router.post("/devices/{udid}/initialize")
async def initialize_device(udid: str):
    """Initialize Appium connection for a device"""
    try:
        success = await device_manager.initialize_device(udid)
        if success:
            return {"success": True, "message": f"Device {udid} initialized successfully"}
        else:
            device = device_manager.devices.get(udid)
            error_msg = device.error_message if device else "Device not found"
            raise HTTPException(status_code=400, detail=f"Failed to initialize device: {error_msg}")
    except Exception as e:
        logger.error(f"Device initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Device initialization failed: {str(e)}")

@api_router.get("/devices/status")
async def get_devices_status():
    """Get status of all devices"""
    return device_manager.get_device_status()

@api_router.delete("/devices/{udid}/cleanup")
async def cleanup_device(udid: str):
    """Cleanup device connection"""
    try:
        await device_manager.cleanup_device(udid)
        return {"success": True, "message": f"Device {udid} cleaned up successfully"}
    except Exception as e:
        logger.error(f"Device cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Device cleanup failed: {str(e)}")

# Task Management Endpoints
@api_router.post("/tasks/create", response_model=TaskResponse)
async def create_automation_task(request: TaskCreateRequest):
    """Create a new Instagram automation task"""
    # Check license first
    if not license_client.is_licensed():
        raise HTTPException(status_code=403, detail="License required: System is locked due to invalid or expired license")
    
    try:
        # Validate priority
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        
        priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)
        
        # Create task
        task_id = await task_manager.create_task(
            target_username=request.target_username,
            actions=request.actions,
            max_likes=request.max_likes,
            max_follows=request.max_follows,
            priority=priority
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"Task created for @{request.target_username}"
        )
        
    except Exception as e:
        logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")

@api_router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    status = await task_manager.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@api_router.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """Get logs for a specific task"""
    logs = await task_manager.get_task_logs(task_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "logs": logs}

@api_router.delete("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a pending or running task"""
    success = await task_manager.cancel_task(task_id)
    if success:
        return {"success": True, "message": f"Task {task_id} cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

@api_router.get("/tasks/queue/status")
async def get_queue_status():
    """Get current task queue status"""
    return task_manager.task_queue.get_queue_status()

# Engagement Task Management Endpoints
@api_router.post("/engagement-task", response_model=TaskResponse)
async def create_engagement_task(request: EngagementTaskCreateRequest):
    """Create a new engagement automation task"""
    # Check license first
    if not license_client.is_licensed():
        raise HTTPException(status_code=403, detail="License required: System is locked due to invalid or expired license")
    
    try:
        # Validate priority
        priority_map = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.NORMAL,
            "high": TaskPriority.HIGH,
            "urgent": TaskPriority.URGENT
        }
        
        priority = priority_map.get(request.priority.lower(), TaskPriority.NORMAL)
        
        # Validate comment list
        if not request.comment_list:
            raise HTTPException(status_code=400, detail="Comment list cannot be empty")
        
        # Validate target pages
        if not request.target_pages:
            raise HTTPException(status_code=400, detail="Target pages list cannot be empty")
        
        # Create engagement task
        task_id = await engagement_task_manager.create_engagement_task(
            target_pages=request.target_pages,
            comment_list=request.comment_list,
            actions=request.actions,
            max_users_per_page=request.max_users_per_page,
            profile_validation=request.profile_validation,
            skip_rate=request.skip_rate,
            priority=priority
        )
        
        return TaskResponse(
            task_id=task_id,
            status="created",
            message=f"Engagement task created for {len(request.target_pages)} target pages"
        )
        
    except Exception as e:
        logger.error(f"Engagement task creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Engagement task creation failed: {str(e)}")

@api_router.get("/engagement-status/{task_id}")
async def get_engagement_task_status(task_id: str):
    """Get status of a specific engagement task"""
    status = await engagement_task_manager.get_engagement_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Engagement task not found")
    return status

@api_router.get("/engagement-status")
async def get_engagement_dashboard_stats():
    """Get comprehensive engagement dashboard statistics"""
    try:
        stats = await engagement_task_manager.get_engagement_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get engagement dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement dashboard stats: {str(e)}")

@api_router.get("/engagement-history")
async def get_engagement_history():
    """Get engagement task history and analytics"""
    try:
        history = await engagement_task_manager.get_engagement_history()
        return history
    except Exception as e:
        logger.error(f"Failed to get engagement history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement history: {str(e)}")

@api_router.get("/engagement-task/{task_id}/logs")
async def get_engagement_task_logs(task_id: str):
    """Get logs for a specific engagement task"""
    logs = await engagement_task_manager.get_engagement_task_logs(task_id)
    if logs is None:
        raise HTTPException(status_code=404, detail="Engagement task not found")
    return {"task_id": task_id, "logs": logs}

@api_router.delete("/engagement-task/{task_id}/cancel")
async def cancel_engagement_task(task_id: str):
    """Cancel a pending or running engagement task"""
    success = await engagement_task_manager.cancel_engagement_task(task_id)
    if success:
        return {"success": True, "message": f"Engagement task {task_id} cancelled"}
    else:
        raise HTTPException(status_code=404, detail="Engagement task not found or cannot be cancelled")

@api_router.post("/engagement/start")
async def start_engagement_system():
    """Start the engagement automation workers"""
    try:
        await engagement_task_manager.start_engagement_workers()
        return {"success": True, "message": "Engagement automation system started"}
    except Exception as e:
        logger.error(f"Failed to start engagement system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start engagement system: {str(e)}")

@api_router.post("/engagement/stop")
async def stop_engagement_system():
    """Stop the engagement automation workers"""
    try:
        await engagement_task_manager.stop_engagement_workers()
        return {"success": True, "message": "Engagement automation system stopped"}
    except Exception as e:
        logger.error(f"Failed to stop engagement system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop engagement system: {str(e)}")

# Dashboard and Monitoring Endpoints
@api_router.get("/dashboard/stats", response_model=SystemStats)
async def get_dashboard_stats():
    """Get comprehensive system statistics for dashboard"""
    try:
        stats = await task_manager.get_dashboard_stats()
        
        # Add license status to dashboard stats
        try:
            license_status = license_client.get_status()
            stats["license_status"] = license_status
        except Exception as e:
            logger.warning(f"Failed to get license status for dashboard: {e}")
            stats["license_status"] = None
        
        # Add safe mode status
        try:
            if device_queue_manager:
                safe_mode_status = device_queue_manager.get_safe_mode_status()
                stats["safe_mode_status"] = safe_mode_status
        except Exception as e:
            logger.warning(f"Failed to get safe mode status for dashboard: {e}")
            stats["safe_mode_status"] = None
        
        return SystemStats(**stats)
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@api_router.post("/system/start")
async def start_automation_system():
    """Start the automation task workers"""
    try:
        await task_manager.start_workers()
        return {"success": True, "message": "Automation system started"}
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start system: {str(e)}")

@api_router.post("/system/stop")
async def stop_automation_system():
    """Stop the automation task workers"""
    try:
        await task_manager.stop_workers()
        return {"success": True, "message": "Automation system stopped"}
    except Exception as e:
        logger.error(f"Failed to stop system: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop system: {str(e)}")

@api_router.get("/system/health")
async def get_system_health():
    """Get system health check"""
    device_status = device_manager.get_device_status()
    queue_status = task_manager.task_queue.get_queue_status()
    
    health_status = "healthy"
    issues = []
    
    if device_status["total_devices"] == 0:
        health_status = "warning"
        issues.append("No devices connected")
    
    if device_status["error_devices"] > 0:
        health_status = "warning"
        issues.append(f"{device_status['error_devices']} devices in error state")
    
    if not task_manager.is_running:
        health_status = "warning"
        issues.append("Task workers not running")
    
    return {
        "status": health_status,
        "issues": issues,
        "uptime": task_manager.stats.get("uptime_start", 0),
        "workers_active": len(task_manager.workers),
        "devices_ready": device_status["ready_devices"],
        "queue_size": queue_status["total_tasks"]
    }

# Phase 4 API Endpoints

@api_router.get("/settings")
async def get_settings():
    """Get current system settings"""
    try:
        db_manager = get_db_manager()
        settings = await db_manager.get_settings()
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@api_router.put("/settings")
async def update_settings(settings_update: SystemSettingsUpdate):
    """Update system settings"""
    try:
        db_manager = get_db_manager()
        
        # Convert to dict and filter None values
        settings_dict = {k: v for k, v in settings_update.dict().items() if v is not None}
        
        success = await db_manager.update_settings(settings_dict)
        if success:
            return {"success": True, "message": "Settings updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update settings")
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@api_router.get("/interactions/latest")
async def get_latest_interactions(
    account_id: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None)
):
    """Get latest interaction records for deduplication checking"""
    try:
        db_manager = get_db_manager()
        
        # If specific parameters provided, check that interaction
        if account_id and username and action:
            interaction = await db_manager.check_interaction_exists(account_id, username, action)
            if interaction:
                return {
                    "success": True,
                    "interaction": {
                        "account_id": interaction.account_id,
                        "target_username": interaction.target_username,
                        "action": interaction.action,
                        "last_status": interaction.last_status,
                        "last_ts": interaction.last_ts.isoformat(),
                        "expires_at": interaction.expires_at.isoformat() if interaction.expires_at else None
                    }
                }
            else:
                return {"success": True, "interaction": None}
        else:
            # Return summary of all latest interactions
            # This would require a new method in database_models.py
            return {"success": True, "message": "Use specific account_id, username, and action parameters"}
            
    except Exception as e:
        logger.error(f"Error getting latest interactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest interactions: {str(e)}")

@api_router.get("/interactions/events")
async def get_interaction_events(
    account_id: Optional[str] = Query(None),
    target_username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0)
):
    """Get interaction events with filters and pagination"""
    try:
        db_manager = get_db_manager()
        
        events = await db_manager.get_interaction_events(
            account_id=account_id,
            target_username=target_username,
            action=action,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            skip=skip
        )
        
        # Convert datetime objects to ISO strings for JSON serialization
        for event in events:
            if '_id' in event:
                del event['_id']  # Remove MongoDB ObjectId
            if 'ts' in event and isinstance(event['ts'], datetime):
                event['ts'] = event['ts'].isoformat()
        
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error getting interaction events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get interaction events: {str(e)}")

@api_router.get("/interactions/export")
async def export_interaction_events(
    format: str = Query("csv", description="Export format: csv or json"),
    account_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None)
):
    """Export interaction events as CSV or JSON"""
    try:
        db_manager = get_db_manager()
        
        # Get all matching events (no pagination for export)
        events = await db_manager.get_interaction_events(
            account_id=account_id,
            action=action,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=10000  # Large limit for export
        )
        
        if format.lower() == "csv":
            # Create CSV
            output = io.StringIO()
            if events:
                fieldnames = ['platform', 'account_id', 'target_username', 'action', 'status', 
                            'reason', 'task_id', 'device_id', 'latency_ms', 'ts']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for event in events:
                    # Remove ObjectId and convert datetime to string for CSV
                    if '_id' in event:
                        del event['_id']  # Remove MongoDB ObjectId
                    if 'ts' in event and isinstance(event['ts'], datetime):
                        event['ts'] = event['ts'].isoformat()
                    writer.writerow({k: event.get(k, '') for k in fieldnames})
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=interactions_export.csv"}
            )
        
        elif format.lower() == "json":
            # Convert datetime objects for JSON and remove ObjectIds
            for event in events:
                if '_id' in event:
                    del event['_id']  # Remove MongoDB ObjectId
                if 'ts' in event and isinstance(event['ts'], datetime):
                    event['ts'] = event['ts'].isoformat()
            
            json_content = json.dumps({
                "exported_at": datetime.utcnow().isoformat(),
                "total_events": len(events),
                "filters": {
                    "account_id": account_id,
                    "action": action,
                    "status": status,
                    "from_date": from_date.isoformat() if from_date else None,
                    "to_date": to_date.isoformat() if to_date else None
                },
                "events": events
            }, indent=2)
            
            return Response(
                content=json_content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=interactions_export.json"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
            
    except Exception as e:
        logger.error(f"Error exporting interaction events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export interaction events: {str(e)}")

@api_router.get("/metrics")
async def get_metrics():
    """Get comprehensive metrics for dashboard"""
    try:
        db_manager = get_db_manager()
        dedup_service = get_deduplication_service()
        error_handler = get_error_handler()
        
        # Get interaction metrics
        interaction_metrics = await db_manager.get_interaction_metrics()
        
        # Get deduplication stats
        dedup_stats = dedup_service.get_stats()
        
        # Get error handling stats
        error_stats = error_handler.get_error_stats()
        
        # Get account states
        account_states = error_handler.get_all_account_states()
        
        return {
            "success": True,
            "metrics": {
                "interactions": interaction_metrics,
                "deduplication": dedup_stats,
                "error_handling": error_stats,
                "account_states": account_states,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

@api_router.post("/interactions/cleanup")
async def cleanup_expired_interactions():
    """Manually trigger cleanup of expired interaction records"""
    try:
        db_manager = get_db_manager()
        cleaned_count = await db_manager.cleanup_expired_interactions()
        
        # Also cleanup old account execution states
        execution_manager = get_execution_manager()
        execution_manager.cleanup_old_accounts()
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired interaction records and old account states"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up interactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup interactions: {str(e)}")

@api_router.get("/accounts/execution-states")
async def get_account_execution_states():
    """Get current execution state of all accounts"""
    try:
        execution_manager = get_execution_manager()
        account_states = execution_manager.get_all_account_states()
        
        return {
            "success": True,
            "account_states": account_states,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting account execution states: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account execution states: {str(e)}")

@api_router.get("/accounts/execution-states/{account_id}")
async def get_account_execution_state(account_id: str):
    """Get execution state for a specific account"""
    try:
        execution_manager = get_execution_manager()
        account_state = execution_manager.get_account_execution_state(account_id)
        
        if account_state:
            return {
                "success": True,
                "account_state": account_state,
                "updated_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Account {account_id} not found or not tracked"
            }
        
    except Exception as e:
        logger.error(f"Error getting account execution state for {account_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account execution state: {str(e)}")

@api_router.get("/accounts/waiting-tasks")
async def get_waiting_tasks():
    """Get all tasks waiting for account availability"""
    try:
        execution_manager = get_execution_manager()
        waiting_tasks = execution_manager.get_waiting_tasks_by_account()
        
        return {
            "success": True,
            "waiting_tasks_by_account": waiting_tasks,
            "total_waiting_tasks": sum(len(tasks) for tasks in waiting_tasks.values()),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting waiting tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get waiting tasks: {str(e)}")

@api_router.get("/metrics/concurrency")
async def get_concurrency_metrics():
    """Get detailed concurrency control metrics"""
    try:
        execution_manager = get_execution_manager()
        concurrency_metrics = execution_manager.get_metrics()
        
        return {
            "success": True,
            "concurrency_metrics": concurrency_metrics,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting concurrency metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get concurrency metrics: {str(e)}")

@api_router.get("/accounts/states")
async def get_account_states():
    """Get current state of all accounts (active, cooldown, etc.)"""
    try:
        error_handler = get_error_handler()
        execution_manager = get_execution_manager()
        
        # Get both error states and execution states
        error_states = error_handler.get_all_account_states()
        execution_states = execution_manager.get_all_account_states()
        
        # Merge the information
        combined_states = {}
        
        # Start with execution states
        for account_id, exec_state in execution_states.items():
            combined_states[account_id] = {
                **exec_state,
                "error_state": error_states.get(account_id, {})
            }
        
        # Add error states that don't have execution states
        for account_id, error_state in error_states.items():
            if account_id not in combined_states:
                combined_states[account_id] = {
                    "account_id": account_id,
                    "state": "available",  # Default execution state
                    "current_task_id": None,
                    "waiting_tasks_count": 0,
                    "error_state": error_state
                }
        
        return {
            "success": True,
            "account_states": combined_states,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting account states: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get account states: {str(e)}")

# License Management Endpoints
@api_router.get("/license/status")
async def get_license_status():
    """Get current license status"""
    try:
        status = license_client.get_status()
        return {
            "success": True,
            "license_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting license status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get license status: {str(e)}")

@api_router.post("/license/verify")
async def verify_license_now():
    """Force immediate license verification"""
    try:
        status = await license_client.verify_immediately()
        return {
            "success": True,
            "license_status": status,
            "message": "License verification completed",
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error during license verification: {e}")
        raise HTTPException(status_code=500, detail=f"License verification failed: {str(e)}")

# Per-Device Queue & Workflow Management Endpoints

@api_router.get("/settings")
async def get_settings():
    """Get current system settings including feature flags"""
    try:
        db_manager = get_db_manager()
        settings = await db_manager.get_settings()
        
        # Add feature flags
        settings["feature_flags"] = {
            "ENABLE_POOLED_ASSIGNMENT": device_queue_manager.is_pooled_assignment_enabled() if device_queue_manager else False,
            "SAFE_MODE": device_queue_manager.safe_mode if device_queue_manager else True
        }
        
        return {"success": True, "settings": settings}
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@api_router.get("/workflows")
async def get_workflow_templates(template_type: Optional[str] = Query(None, description="Filter by template type")):
    """Get all workflow templates"""
    try:
        templates = await workflow_manager.list_workflow_templates(template_type)
        return {
            "success": True,
            "templates": templates,
            "total_count": len(templates)
        }
    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow templates: {str(e)}")

@api_router.get("/workflows/{template_id}")
async def get_workflow_template(template_id: str):
    """Get specific workflow template"""
    try:
        template = await workflow_manager.get_workflow_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Workflow template not found")
        
        # Convert to dict for response
        template_dict = {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "template_type": template.template_type,
            "target_pages": template.target_pages,
            "target_username": template.target_username,
            "comment_list": template.comment_list,
            "actions": template.actions,
            "max_users_per_page": template.max_users_per_page,
            "max_likes": template.max_likes,
            "max_follows": template.max_follows,
            "profile_validation": template.profile_validation,
            "skip_rate": template.skip_rate,
            "priority": template.priority,
            "delays": template.delays,
            "limits": template.limits,
            "rest_windows": template.rest_windows,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "created_by": template.created_by,
            "is_active": template.is_active
        }
        
        return {
            "success": True,
            "template": template_dict
        }
    except Exception as e:
        logger.error(f"Error getting workflow template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow template: {str(e)}")

@api_router.post("/workflows")
async def create_workflow_template(template_data: WorkflowTemplateCreate):
    """Create new workflow template"""
    try:
        template_config = template_data.dict()
        name = template_config.pop("name")
        description = template_config.pop("description", "")
        template_type = template_config.pop("template_type", "engagement")
        
        template_id = await workflow_manager.create_workflow_template(
            name=name,
            description=description,
            template_type=template_type,
            **template_config
        )
        
        if template_id:
            return {
                "success": True,
                "template_id": template_id,
                "message": f"Workflow template '{name}' created successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create workflow template")
            
    except Exception as e:
        logger.error(f"Error creating workflow template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow template: {str(e)}")

@api_router.post("/workflows/{template_id}/deploy")
async def deploy_workflow_to_devices(template_id: str, deploy_data: WorkflowDeployRequest):
    """Deploy workflow template to multiple devices"""
    try:
        result = await workflow_manager.deploy_workflow_to_devices(
            template_id=template_id,
            device_ids=deploy_data.device_ids,
            overrides=deploy_data.overrides
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error deploying workflow to devices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy workflow: {str(e)}")

@api_router.put("/workflows/{template_id}")
async def update_workflow_template(template_id: str, updates: Dict[str, Any]):
    """Update existing workflow template"""
    try:
        success = await workflow_manager.update_workflow_template(template_id, updates)
        if success:
            return {"success": True, "message": "Workflow template updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Workflow template not found")
            
    except Exception as e:
        logger.error(f"Error updating workflow template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update workflow template: {str(e)}")

@api_router.delete("/workflows/{template_id}")
async def delete_workflow_template(template_id: str):
    """Delete workflow template"""
    try:
        success = await workflow_manager.delete_workflow_template(template_id)
        if success:
            return {"success": True, "message": "Workflow template deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Workflow template not found")
            
    except Exception as e:
        logger.error(f"Error deleting workflow template: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow template: {str(e)}")

@api_router.post("/workflows/save-from-engagement")
async def save_engagement_as_workflow(
    name: str = Query(..., description="Workflow name"),
    description: str = Query("", description="Optional description"),
    crawler_config: Dict[str, Any] = Body(..., description="Engagement crawler configuration")
):
    """Save engagement crawler configuration as workflow template"""
    try:
        template_id = await workflow_manager.save_engagement_crawler_as_workflow(
            crawler_config=crawler_config,
            name=name,
            description=description
        )
        
        if template_id:
            return {
                "success": True,
                "template_id": template_id,
                "message": f"Engagement configuration saved as workflow '{name}'"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to save engagement as workflow")
            
    except Exception as e:
        logger.error(f"Error saving engagement as workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save engagement as workflow: {str(e)}")

@api_router.get("/devices/{udid}/queue")
async def get_device_queue(udid: str):
    """Get device-specific queue snapshot with pacing stats"""
    try:
        queue_snapshot = await device_queue_manager.get_device_queue_snapshot(udid)
        return {
            "success": True,
            "queue_snapshot": queue_snapshot
        }
    except Exception as e:
        logger.error(f"Error getting device queue: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device queue: {str(e)}")

@api_router.get("/devices/queues/all")
async def get_all_device_queues():
    """Get queue snapshots for all devices"""
    try:
        all_queues = await device_queue_manager.get_all_device_queues()
        return {
            "success": True,
            "device_queues": all_queues,
            "statistics": device_queue_manager.get_queue_statistics()
        }
    except Exception as e:
        logger.error(f"Error getting all device queues: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device queues: {str(e)}")

@api_router.post("/tasks/create-device-bound")
async def create_device_bound_task(task_data: DeviceTaskCreate):
    """Create device-bound task (new per-device system)"""
    try:
        # Check license first
        if not license_client.is_licensed():
            raise HTTPException(status_code=403, detail="License required: System is locked due to invalid or expired license")
        
        from ios_automation.workflow_models import DeviceTask
        
        # Create device task
        task = DeviceTask(
            device_id=task_data.device_id,
            target_username=task_data.target_username,
            actions=task_data.actions,
            max_likes=task_data.max_likes,
            max_follows=task_data.max_follows,
            priority=task_data.priority
        )
        
        # Enqueue to device
        success = await device_queue_manager.enqueue_task_to_device(task)
        if success:
            return {
                "success": True,
                "task_id": task.task_id,
                "device_id": task.device_id,
                "queue_position": task.queue_position,
                "message": f"Task created for @{task.target_username} on device {task.device_id}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to enqueue task to device")
            
    except Exception as e:
        logger.error(f"Error creating device-bound task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create device-bound task: {str(e)}")

@api_router.get("/system/safe-mode")
async def get_safe_mode_status():
    """Get safe mode status and information"""
    try:
        safe_mode_status = device_queue_manager.get_safe_mode_status()
        return {
            "success": True,
            "safe_mode_status": safe_mode_status
        }
    except Exception as e:
        logger.error(f"Error getting safe mode status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get safe mode status: {str(e)}")

# Background task to auto-start system
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global device_queue_manager, workflow_manager
    
    logger.info("Starting iOS Instagram Automation API")
    
    try:
        # Start license client first
        await license_client.start()
        logger.info("License client initialized")
        
        # Initialize Phase 4 database
        await init_database()
        logger.info("Phase 4 database initialized")
        
        # Initialize Phase 1-3 workflow database
        await init_workflow_database()
        logger.info("Workflow database initialized")
        
        # Initialize device queue system
        device_queue_manager = get_device_queue_manager(device_manager)
        await init_device_queue_system(device_manager)
        logger.info("Device queue system initialized")
        
        # Initialize workflow manager
        workflow_manager = get_workflow_manager()
        await init_workflow_manager()
        logger.info("Workflow manager initialized")
        
        # Discover devices on startup
        devices = await device_manager.discover_devices()
        logger.info(f"Discovered {len(devices)} iOS devices")
        
        # Initialize discovered devices
        for device in devices:
            success = await device_manager.initialize_device(device.udid)
            if success:
                logger.info(f"Initialized device: {device.name}")
            else:
                logger.warning(f"Failed to initialize device: {device.name}")
        
        # Start task workers
        await task_manager.start_workers()
        logger.info("Task workers started")
        
        # Start engagement workers
        await engagement_task_manager.start_engagement_workers()
        logger.info("Engagement workers started")
        
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down iOS Instagram Automation API")
    
    try:
        # Stop task workers
        await task_manager.stop_workers()
        
        # Stop engagement workers
        await engagement_task_manager.stop_engagement_workers()
        
        # Cleanup all devices
        for udid in device_manager.devices.keys():
            await device_manager.cleanup_device(udid)
        
        # Cleanup Phase 4 services
        dedup_service = get_deduplication_service()
        await dedup_service.cleanup_service()
        
        error_handler = get_error_handler()
        await error_handler.cleanup_old_states()
        
        # Stop license client
        await license_client.stop()
        logger.info("License client stopped")
        
        # Close database connection
        db_manager = get_db_manager()
        await db_manager.close()
        
        # Close workflow database connection
        workflow_db_manager = get_workflow_db_manager()
        await workflow_db_manager.close()
        
        client.close()
        
    except Exception as e:
        logger.error(f"Shutdown cleanup failed: {e}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

# Import iOS automation modules
from ios_automation.device_manager import IOSDeviceManager, DeviceStatus
from ios_automation.task_manager import TaskManager, TaskPriority
from ios_automation.human_behavior import HumanBehaviorProfile
from ios_automation.engagement_task_manager import EngagementTaskManager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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
    profile_validation: Dict[str, bool] = Field(default={"public_only": True, "min_posts": 2}, 
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

# Dashboard and Monitoring Endpoints
@api_router.get("/dashboard/stats", response_model=SystemStats)
async def get_dashboard_stats():
    """Get comprehensive system statistics for dashboard"""
    try:
        stats = await task_manager.get_dashboard_stats()
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

# Background task to auto-start system
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting iOS Instagram Automation API")
    
    # Discover devices on startup
    try:
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
        
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down iOS Instagram Automation API")
    
    try:
        # Stop task workers
        await task_manager.stop_workers()
        
        # Cleanup all devices
        for udid in device_manager.devices.keys():
            await device_manager.cleanup_device(udid)
        
        # Close database connection
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
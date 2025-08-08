"""
Workflow Template Manager
Handles workflow creation, management, and cloning to multiple devices
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import uuid
import copy

from .workflow_models import WorkflowTemplate, DeviceTask, get_workflow_db_manager
from .device_queue_manager import get_device_queue_manager

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Manages workflow templates and deployment to devices"""
    
    def __init__(self):
        self.workflow_db = get_workflow_db_manager()
        self.device_queue_manager = get_device_queue_manager()
        
        # Template validation rules
        self.max_target_pages = 10
        self.max_comment_list_size = 50
        self.max_devices_per_deployment = 20
        
        logger.info("WorkflowManager initialized")
    
    async def create_workflow_template(
        self, 
        name: str,
        description: str = "",
        template_type: str = "engagement",
        **template_config
    ) -> Optional[str]:
        """Create a new workflow template"""
        try:
            # Validate template configuration
            validation_result = self._validate_template_config(template_type, template_config)
            if not validation_result["valid"]:
                logger.error(f"Template validation failed: {validation_result['error']}")
                return None
            
            # Create template
            template = WorkflowTemplate(
                name=name,
                description=description,
                template_type=template_type,
                **template_config
            )
            
            success = await self.workflow_db.create_workflow_template(template)
            if success:
                logger.info(f"Created workflow template: {template.name} ({template.template_id})")
                return template.template_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating workflow template: {e}")
            return None
    
    def _validate_template_config(self, template_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate template configuration"""
        try:
            errors = []
            
            # Common validations
            if template_type == "engagement":
                target_pages = config.get("target_pages", [])
                if not target_pages:
                    errors.append("Engagement workflows require at least one target page")
                elif len(target_pages) > self.max_target_pages:
                    errors.append(f"Too many target pages (max: {self.max_target_pages})")
                
                comment_list = config.get("comment_list", [])
                if not comment_list:
                    errors.append("Engagement workflows require at least one comment")
                elif len(comment_list) > self.max_comment_list_size:
                    errors.append(f"Too many comments (max: {self.max_comment_list_size})")
            
            elif template_type == "single_user":
                target_username = config.get("target_username", "")
                if not target_username:
                    errors.append("Single user workflows require a target username")
            
            # Validate actions
            actions = config.get("actions", {})
            if isinstance(actions, dict):
                valid_actions = {"follow", "like", "comment", "view"}
                invalid_actions = set(actions.keys()) - valid_actions
                if invalid_actions:
                    errors.append(f"Invalid actions: {invalid_actions}")
            
            # Validate limits
            limits = config.get("limits", {})
            if limits:
                actions_per_hour = limits.get("actions_per_hour", 0)
                if actions_per_hour > 100:
                    errors.append("Actions per hour too high (max: 100)")
            
            if errors:
                return {"valid": False, "error": "; ".join(errors)}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def get_workflow_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get workflow template by ID"""
        return await self.workflow_db.get_workflow_template(template_id)
    
    async def list_workflow_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List workflow templates with metadata"""
        try:
            templates = await self.workflow_db.list_workflow_templates(template_type)
            
            # Add deployment statistics
            result = []
            for template in templates:
                template_dict = {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "template_type": template.template_type,
                    "created_at": template.created_at.isoformat(),
                    "updated_at": template.updated_at.isoformat(),
                    "created_by": template.created_by,
                    "is_active": template.is_active,
                    
                    # Configuration summary
                    "config_summary": self._get_template_config_summary(template),
                    
                    # Deployment stats (would be calculated from database in production)
                    "deployment_stats": await self._get_template_deployment_stats(template.template_id)
                }
                result.append(template_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing workflow templates: {e}")
            return []
    
    def _get_template_config_summary(self, template: WorkflowTemplate) -> Dict[str, Any]:
        """Get configuration summary for template"""
        summary = {
            "template_type": template.template_type,
            "priority": template.priority
        }
        
        if template.template_type == "engagement":
            summary.update({
                "target_pages_count": len(template.target_pages),
                "target_pages": template.target_pages[:3],  # Show first 3
                "comment_count": len(template.comment_list),
                "max_users_per_page": template.max_users_per_page,
                "actions_enabled": template.actions,
                "skip_rate": template.skip_rate
            })
        elif template.template_type == "single_user":
            summary.update({
                "target_username": template.target_username,
                "max_likes": template.max_likes,
                "max_follows": template.max_follows,
                "actions_enabled": template.actions
            })
        
        # Rate limits
        if template.limits:
            summary["rate_limits"] = template.limits
        
        return summary
    
    async def _get_template_deployment_stats(self, template_id: str) -> Dict[str, Any]:
        """Get deployment statistics for template (mock data for now)"""
        # In production, this would query the database for actual deployment stats
        return {
            "total_deployments": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "success_rate": 0.0,
            "last_deployed": None
        }
    
    async def deploy_workflow_to_devices(
        self,
        template_id: str,
        device_ids: List[str],
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Deploy workflow template to multiple devices"""
        try:
            # Get template
            template = await self.workflow_db.get_workflow_template(template_id)
            if not template:
                return {"success": False, "error": "Template not found"}
            
            # Validate device count
            if len(device_ids) > self.max_devices_per_deployment:
                return {"success": False, "error": f"Too many devices (max: {self.max_devices_per_deployment})"}
            
            # Create tasks for each device
            created_tasks = []
            failed_devices = []
            
            for device_id in device_ids:
                try:
                    # Create device-bound task from template
                    task = await self._create_task_from_template(template, device_id, overrides)
                    
                    # Enqueue to device
                    success = await self.device_queue_manager.enqueue_task_to_device(task)
                    if success:
                        created_tasks.append({
                            "task_id": task.task_id,
                            "device_id": device_id,
                            "queue_position": task.queue_position,
                            "enqueued_at": task.enqueued_at.isoformat()
                        })
                    else:
                        failed_devices.append({"device_id": device_id, "error": "Failed to enqueue"})
                        
                except Exception as e:
                    failed_devices.append({"device_id": device_id, "error": str(e)})
            
            # Prepare deployment summary
            deployment_summary = {
                "template_id": template_id,
                "template_name": template.name,
                "total_devices": len(device_ids),
                "successful_deployments": len(created_tasks),
                "failed_deployments": len(failed_devices),
                "deployment_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Deployed workflow {template.name} to {len(created_tasks)}/{len(device_ids)} devices")
            
            return {
                "success": True,
                "deployment_summary": deployment_summary,
                "created_tasks": created_tasks,
                "failed_devices": failed_devices,
                "pacing_summary": await self._get_deployment_pacing_summary(device_ids)
            }
            
        except Exception as e:
            logger.error(f"Error deploying workflow to devices: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_task_from_template(
        self,
        template: WorkflowTemplate,
        device_id: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> DeviceTask:
        """Create a device task from workflow template"""
        try:
            # Create template snapshot
            template_snapshot = {
                "template_id": template.template_id,
                "template_name": template.name,
                "template_type": template.template_type,
                "snapshot_time": datetime.utcnow().isoformat(),
                "original_config": {
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
                    "rest_windows": template.rest_windows
                }
            }
            
            # Apply overrides
            config = copy.deepcopy(template_snapshot["original_config"])
            if overrides:
                config.update(overrides)
            
            # Create device task
            task = DeviceTask(
                device_id=device_id,
                workflow_id=template.template_id,
                template_snapshot=template_snapshot,
                
                # Task configuration from template
                target_username=config.get("target_username", template.target_username),
                target_pages=config.get("target_pages", template.target_pages),
                comment_list=config.get("comment_list", template.comment_list),
                max_likes=config.get("max_likes", template.max_likes),
                max_follows=config.get("max_follows", template.max_follows),
                priority=config.get("priority", template.priority),
                
                # Convert actions dict to list for compatibility
                actions=self._actions_dict_to_list(config.get("actions", template.actions))
            )
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating task from template: {e}")
            raise
    
    def _actions_dict_to_list(self, actions: Any) -> List[str]:
        """Convert actions configuration to list format"""
        if isinstance(actions, list):
            return actions
        elif isinstance(actions, dict):
            action_list = []
            if actions.get("view", True):
                action_list.extend(["search_user", "view_profile"])
            if actions.get("like", True):
                action_list.append("like_post")
            if actions.get("follow", True):
                action_list.append("follow_user")
            if actions.get("comment", False):
                action_list.append("comment_post")
            action_list.append("navigate_home")
            return action_list
        else:
            # Default actions
            return ["search_user", "view_profile", "like_post", "follow_user", "navigate_home"]
    
    async def _get_deployment_pacing_summary(self, device_ids: List[str]) -> Dict[str, Any]:
        """Get pacing summary for deployment confirmation"""
        try:
            device_summaries = []
            
            for device_id in device_ids:
                queue_snapshot = await self.device_queue_manager.get_device_queue_snapshot(device_id)
                
                device_summaries.append({
                    "device_id": device_id,
                    "device_name": queue_snapshot.get("device_name", f"Device {device_id[-6:]}"),
                    "current_queue_length": queue_snapshot.get("queue_length", 0),
                    "estimated_start_time": queue_snapshot.get("next_run_eta"),
                    "rate_limits": queue_snapshot.get("pacing_stats", {}).get("rate_limits", {}),
                    "current_task": queue_snapshot.get("current_task", {}).get("task_id")
                })
            
            return {
                "total_devices": len(device_ids),
                "devices_busy": len([d for d in device_summaries if d["current_task"]]),
                "average_queue_length": sum(d["current_queue_length"] for d in device_summaries) / len(device_summaries) if device_summaries else 0,
                "device_details": device_summaries
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment pacing summary: {e}")
            return {"error": str(e)}
    
    async def update_workflow_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing workflow template"""
        try:
            template = await self.workflow_db.get_workflow_template(template_id)
            if not template:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            # Validate updated configuration
            template_config = {
                "target_pages": template.target_pages,
                "target_username": template.target_username,
                "comment_list": template.comment_list,
                "actions": template.actions,
                "limits": template.limits
            }
            validation_result = self._validate_template_config(template.template_type, template_config)
            if not validation_result["valid"]:
                logger.error(f"Updated template validation failed: {validation_result['error']}")
                return False
            
            template.updated_at = datetime.utcnow()
            success = await self.workflow_db.update_workflow_template(template)
            
            if success:
                logger.info(f"Updated workflow template: {template.name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating workflow template: {e}")
            return False
    
    async def delete_workflow_template(self, template_id: str) -> bool:
        """Soft delete workflow template"""
        try:
            success = await self.workflow_db.delete_workflow_template(template_id)
            if success:
                logger.info(f"Deleted workflow template: {template_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting workflow template: {e}")
            return False
    
    async def save_engagement_crawler_as_workflow(
        self,
        crawler_config: Dict[str, Any],
        name: str,
        description: str = ""
    ) -> Optional[str]:
        """Save engagement crawler configuration as workflow template"""
        try:
            # Convert engagement crawler config to workflow template format
            template_config = {
                "target_pages": crawler_config.get("target_pages", []),
                "comment_list": crawler_config.get("comment_list", []),
                "actions": crawler_config.get("actions", {"follow": True, "like": True, "comment": True}),
                "max_users_per_page": crawler_config.get("max_users_per_page", 20),
                "profile_validation": crawler_config.get("profile_validation", {"public_only": True, "min_posts": 2}),
                "skip_rate": crawler_config.get("skip_rate", 0.15),
                "priority": crawler_config.get("priority", "normal"),
                
                # Add default pacing for engagement workflows
                "delays": {"action_delay": [3, 7], "page_delay": [5, 10]},
                "limits": {"actions_per_hour": 40, "actions_per_session": 15},
                "rest_windows": [
                    {"start_hour": 0, "end_hour": 7, "type": "sleep"},
                    {"start_hour": 12, "end_hour": 13, "type": "lunch"}
                ]
            }
            
            template_id = await self.create_workflow_template(
                name=name,
                description=description or f"Saved from Engagement Crawler - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                template_type="engagement",
                **template_config
            )
            
            if template_id:
                logger.info(f"Saved engagement crawler as workflow template: {name}")
            
            return template_id
            
        except Exception as e:
            logger.error(f"Error saving engagement crawler as workflow: {e}")
            return None

# Global workflow manager instance
workflow_manager = None

def get_workflow_manager() -> WorkflowManager:
    """Get global workflow manager instance"""
    global workflow_manager
    if workflow_manager is None:
        workflow_manager = WorkflowManager()
    return workflow_manager

async def init_workflow_manager():
    """Initialize workflow manager"""
    manager = get_workflow_manager()
    await manager.workflow_db.ensure_indexes()
    logger.info("Workflow manager initialized successfully")
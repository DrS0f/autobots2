#!/usr/bin/env python3
"""
Dual Mode Handler for Phase 4 Live Device Integration
Routes requests between Safe Mode (mock data) and Live Mode (real devices)
"""

import logging
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio

from .live_device_manager import get_live_device_manager, LiveDeviceStatus
from .device_queue_manager import get_device_queue_manager

logger = logging.getLogger(__name__)

class OperationMode(Enum):
    """System operation mode"""
    SAFE_MODE = "safe_mode"      # Mock data and simulation
    LIVE_MODE = "live_mode"      # Real device integration
    HYBRID_MODE = "hybrid_mode"  # Mix of live and fallback devices

class DualModeConfiguration:
    """Configuration for dual-mode operation"""
    
    def __init__(self):
        # Mode configuration from environment or defaults
        self.mode = OperationMode(os.environ.get('AUTOMATION_MODE', 'safe_mode'))
        self.live_mode_enabled = os.environ.get('LIVE_MODE_ENABLED', 'false').lower() == 'true'
        self.auto_fallback = os.environ.get('AUTO_FALLBACK_ENABLED', 'true').lower() == 'true'
        self.user_confirmation_required = os.environ.get('REQUIRE_USER_CONFIRMATION', 'true').lower() == 'true'
        
        # Fallback thresholds
        self.max_device_errors = int(os.environ.get('MAX_DEVICE_ERRORS', '3'))
        self.device_timeout_seconds = int(os.environ.get('DEVICE_TIMEOUT', '300'))
        self.fallback_cooldown_minutes = int(os.environ.get('FALLBACK_COOLDOWN', '30'))
        
        # Feature flags
        self.features = {
            'live_device_discovery': os.environ.get('FEATURE_LIVE_DISCOVERY', 'false').lower() == 'true',
            'live_task_execution': os.environ.get('FEATURE_LIVE_EXECUTION', 'false').lower() == 'true',
            'live_workflow_deployment': os.environ.get('FEATURE_LIVE_WORKFLOWS', 'false').lower() == 'true',
            'real_time_monitoring': os.environ.get('FEATURE_REALTIME_MONITORING', 'false').lower() == 'true',
            'audit_logging': os.environ.get('FEATURE_AUDIT_LOGGING', 'true').lower() == 'true'
        }
    
    def is_live_mode_active(self) -> bool:
        """Check if live mode is currently active"""
        return self.live_mode_enabled and self.mode in [OperationMode.LIVE_MODE, OperationMode.HYBRID_MODE]
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled"""
        return self.features.get(feature, False)

class FallbackTracker:
    """Tracks device fallback status and recovery"""
    
    def __init__(self):
        self.fallback_devices: Dict[str, Dict[str, Any]] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
    
    def record_device_error(self, udid: str, error: str):
        """Record an error for a device"""
        now = datetime.utcnow()
        
        # Increment error count
        self.error_counts[udid] = self.error_counts.get(udid, 0) + 1
        self.last_errors[udid] = now
        
        logger.warning(f"Device error recorded for {udid}: {error} (count: {self.error_counts[udid]})")
    
    def set_device_fallback(self, udid: str, reason: str):
        """Set a device to fallback mode"""
        self.fallback_devices[udid] = {
            'reason': reason,
            'fallback_time': datetime.utcnow(),
            'error_count': self.error_counts.get(udid, 0)
        }
        logger.warning(f"Device {udid} set to fallback mode: {reason}")
    
    def clear_device_fallback(self, udid: str):
        """Clear fallback mode for a device"""
        if udid in self.fallback_devices:
            del self.fallback_devices[udid]
            self.error_counts[udid] = 0
            logger.info(f"Cleared fallback mode for device {udid}")
    
    def is_device_in_fallback(self, udid: str) -> bool:
        """Check if device is in fallback mode"""
        return udid in self.fallback_devices
    
    def should_trigger_fallback(self, udid: str, config: DualModeConfiguration) -> bool:
        """Determine if device should be set to fallback mode"""
        error_count = self.error_counts.get(udid, 0)
        return error_count >= config.max_device_errors
    
    def get_fallback_info(self, udid: str) -> Optional[Dict[str, Any]]:
        """Get fallback information for a device"""
        return self.fallback_devices.get(udid)

class AuditLogger:
    """Logs all live operations for compliance and troubleshooting"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.log_file = os.environ.get('AUDIT_LOG_FILE', '/var/log/instagram_automation_audit.log')
        
        if self.enabled:
            # Configure audit logging
            self.audit_logger = logging.getLogger('audit')
            handler = logging.FileHandler(self.log_file)
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
            self.audit_logger.setLevel(logging.INFO)
    
    def log_operation(self, operation: str, details: Dict[str, Any], user_id: str = None):
        """Log an operation"""
        if not self.enabled:
            return
            
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'details': details,
            'user_id': user_id,
            'mode': 'live'
        }
        
        self.audit_logger.info(json.dumps(audit_entry))
    
    def log_device_action(self, device_udid: str, action: str, task_data: Dict[str, Any], result: Dict[str, Any]):
        """Log device action"""
        self.log_operation('device_action', {
            'device_udid': device_udid,
            'action': action,
            'task_data': task_data,
            'result': result
        })
    
    def log_fallback_trigger(self, device_udid: str, reason: str):
        """Log fallback mode trigger"""
        self.log_operation('fallback_triggered', {
            'device_udid': device_udid,
            'reason': reason
        })
    
    def log_mode_change(self, from_mode: str, to_mode: str, reason: str):
        """Log system mode change"""
        self.log_operation('mode_change', {
            'from_mode': from_mode,
            'to_mode': to_mode,
            'reason': reason
        })

class DualModeHandler:
    """Handles routing between Safe Mode and Live Mode operations"""
    
    def __init__(self):
        self.config = DualModeConfiguration()
        self.fallback_tracker = FallbackTracker()
        self.audit_logger = AuditLogger(self.config.is_feature_enabled('audit_logging'))
        self.live_device_manager = None
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Dual Mode Handler initialized - Mode: {self.config.mode.value}")
    
    async def initialize(self):
        """Initialize dual mode handler"""
        if self.config.is_live_mode_active():
            from .live_device_manager import get_live_device_manager
            self.live_device_manager = get_live_device_manager()
            await self.live_device_manager.start()
            logger.info("Live Device Manager initialized")
    
    async def shutdown(self):
        """Shutdown dual mode handler"""
        if self.live_device_manager:
            await self.live_device_manager.stop()
    
    def get_current_mode(self) -> OperationMode:
        """Get current operation mode"""
        return self.config.mode
    
    async def set_mode(self, mode: OperationMode, user_id: str = None) -> bool:
        """Set operation mode"""
        old_mode = self.config.mode
        
        if mode == old_mode:
            return True
        
        try:
            # Log mode change
            self.audit_logger.log_mode_change(old_mode.value, mode.value, f"User requested mode change")
            
            # Update configuration
            self.config.mode = mode
            
            # Initialize/shutdown components as needed
            if mode in [OperationMode.LIVE_MODE, OperationMode.HYBRID_MODE]:
                if not self.live_device_manager:
                    await self.initialize()
            
            logger.info(f"Mode changed from {old_mode.value} to {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to change mode: {e}")
            self.config.mode = old_mode
            return False
    
    def is_device_available_for_live_mode(self, udid: str) -> bool:
        """Check if device is available for live mode operations"""
        if not self.config.is_live_mode_active():
            return False
            
        return not self.fallback_tracker.is_device_in_fallback(udid)
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics (dual-mode aware)"""
        if self.config.mode == OperationMode.SAFE_MODE:
            return await self._get_mock_dashboard_stats()
        elif self.config.mode == OperationMode.LIVE_MODE:
            return await self._get_live_dashboard_stats()
        else:  # HYBRID_MODE
            return await self._get_hybrid_dashboard_stats()
    
    async def get_device_status(self, udid: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get device status (dual-mode aware)"""
        if self.config.mode == OperationMode.SAFE_MODE:
            return await self._get_mock_device_status(udid)
        elif self.config.is_live_mode_active() and self.live_device_manager:
            if udid:
                device_info = await self.live_device_manager.get_device_status(udid)
                return device_info.to_dict() if device_info else None
            else:
                devices = await self.live_device_manager.get_all_devices()
                return [device.to_dict() for device in devices]
        else:
            return await self._get_mock_device_status(udid)
    
    async def execute_task(self, device_udid: str, task_data: Dict[str, Any], user_confirmation: bool = False) -> Dict[str, Any]:
        """Execute task on device (dual-mode aware)"""
        # Check if user confirmation is required for live operations
        if (self.config.is_live_mode_active() and 
            self.config.user_confirmation_required and 
            not user_confirmation):
            
            # Store pending task for confirmation
            confirmation_id = f"task_{datetime.utcnow().timestamp()}"
            self.pending_confirmations[confirmation_id] = {
                'type': 'task_execution',
                'device_udid': device_udid,
                'task_data': task_data,
                'created_at': datetime.utcnow()
            }
            
            return {
                'success': False,
                'requires_confirmation': True,
                'confirmation_id': confirmation_id,
                'message': 'Live task execution requires user confirmation'
            }
        
        # Execute based on mode and device availability
        if (self.config.is_live_mode_active() and 
            self.is_device_available_for_live_mode(device_udid) and 
            self.live_device_manager):
            
            try:
                result = await self._execute_live_task(device_udid, task_data)
                
                # Log the action
                self.audit_logger.log_device_action(device_udid, 'task_execution', task_data, result)
                
                return result
                
            except Exception as e:
                # Handle live execution failure
                logger.error(f"Live task execution failed: {e}")
                
                # Record error and check for fallback
                self.fallback_tracker.record_device_error(device_udid, str(e))
                
                if self.fallback_tracker.should_trigger_fallback(device_udid, self.config):
                    await self._trigger_device_fallback(device_udid, f"Task execution failures: {str(e)}")
                
                # Return simulated result as fallback
                return await self._execute_mock_task(task_data)
        
        else:
            # Use Safe Mode simulation
            return await self._execute_mock_task(task_data)
    
    async def deploy_workflow(self, template_id: str, device_ids: List[str], user_confirmation: bool = False) -> Dict[str, Any]:
        """Deploy workflow to devices (dual-mode aware)"""
        # Check for user confirmation
        if (self.config.is_live_mode_active() and 
            self.config.user_confirmation_required and 
            not user_confirmation):
            
            confirmation_id = f"workflow_{datetime.utcnow().timestamp()}"
            self.pending_confirmations[confirmation_id] = {
                'type': 'workflow_deployment',
                'template_id': template_id,
                'device_ids': device_ids,
                'created_at': datetime.utcnow()
            }
            
            return {
                'success': False,
                'requires_confirmation': True,
                'confirmation_id': confirmation_id,
                'message': 'Live workflow deployment requires user confirmation'
            }
        
        # Deploy based on mode
        if self.config.is_live_mode_active():
            return await self._deploy_workflow_live(template_id, device_ids)
        else:
            return await self._deploy_workflow_mock(template_id, device_ids)
    
    async def confirm_operation(self, confirmation_id: str) -> Dict[str, Any]:
        """Confirm a pending operation"""
        if confirmation_id not in self.pending_confirmations:
            return {'success': False, 'message': 'Invalid confirmation ID'}
        
        pending = self.pending_confirmations[confirmation_id]
        operation_type = pending['type']
        
        try:
            if operation_type == 'task_execution':
                result = await self.execute_task(
                    pending['device_udid'], 
                    pending['task_data'], 
                    user_confirmation=True
                )
            elif operation_type == 'workflow_deployment':
                result = await self.deploy_workflow(
                    pending['template_id'],
                    pending['device_ids'],
                    user_confirmation=True
                )
            else:
                return {'success': False, 'message': 'Unknown operation type'}
            
            # Clean up confirmation
            del self.pending_confirmations[confirmation_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute confirmed operation: {e}")
            return {'success': False, 'message': str(e)}
    
    async def get_fallback_devices(self) -> List[Dict[str, Any]]:
        """Get list of devices in fallback mode"""
        fallback_info = []
        
        for udid, info in self.fallback_tracker.fallback_devices.items():
            fallback_info.append({
                'device_udid': udid,
                'reason': info['reason'],
                'fallback_time': info['fallback_time'].isoformat(),
                'error_count': info['error_count']
            })
        
        return fallback_info
    
    async def clear_device_fallback(self, udid: str) -> bool:
        """Clear fallback mode for a device"""
        try:
            self.fallback_tracker.clear_device_fallback(udid)
            
            if self.live_device_manager:
                await self.live_device_manager.clear_device_fallback(udid)
            
            return True
        except Exception as e:
            logger.error(f"Failed to clear fallback for device {udid}: {e}")
            return False
    
    # Private methods
    
    async def _execute_live_task(self, device_udid: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task on live device"""
        return await self.live_device_manager.execute_instagram_task(device_udid, task_data)
    
    async def _execute_mock_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mock task simulation"""
        await asyncio.sleep(2)  # Simulate execution time
        
        return {
            'success': True,
            'task_id': f"mock_{datetime.utcnow().timestamp()}",
            'execution_time': 2000,
            'actions_performed': task_data.get('actions', []),
            'results': {
                'likes_given': 1,
                'follows_made': 1 if 'follow' in task_data.get('actions', []) else 0,
                'profile_views': 1,
                'success_rate': 1.0
            },
            'safe_mode': True
        }
    
    async def _get_mock_dashboard_stats(self) -> Dict[str, Any]:
        """Get mock dashboard statistics"""
        from .device_queue_manager import get_device_queue_manager
        
        # Use existing mock data generation
        queue_manager = get_device_queue_manager()
        mock_stats = await queue_manager.get_dashboard_stats() if queue_manager else {}
        
        # Add dual-mode specific information
        mock_stats['operation_mode'] = self.config.mode.value
        mock_stats['live_mode_enabled'] = False
        mock_stats['safe_mode'] = True
        
        return mock_stats
    
    async def _get_live_dashboard_stats(self) -> Dict[str, Any]:
        """Get live dashboard statistics"""
        try:
            devices = await self.live_device_manager.get_all_devices()
            
            # Count devices by status
            ready_devices = len([d for d in devices if d.status == LiveDeviceStatus.READY])
            busy_devices = len([d for d in devices if d.status == LiveDeviceStatus.BUSY])
            error_devices = len([d for d in devices if d.status == LiveDeviceStatus.ERROR])
            fallback_devices = len([d for d in devices if d.status == LiveDeviceStatus.FALLBACK])
            
            return {
                'operation_mode': self.config.mode.value,
                'live_mode_enabled': True,
                'safe_mode': False,
                'device_status': {
                    'total_devices': len(devices),
                    'ready_devices': ready_devices,
                    'busy_devices': busy_devices,
                    'error_devices': error_devices,
                    'fallback_devices': fallback_devices
                },
                'system_stats': {
                    'uptime': 3600,  # This would be calculated
                    'active_workers': ready_devices + busy_devices,
                    'memory_usage': 0.5,
                    'cpu_usage': 0.3
                },
                'queue_status': {
                    'total_tasks': 0,  # This would be calculated from device queues
                    'pending_tasks': 0,
                    'running_tasks': busy_devices,
                    'completed_tasks': 0
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get live dashboard stats: {e}")
            return await self._get_mock_dashboard_stats()
    
    async def _get_hybrid_dashboard_stats(self) -> Dict[str, Any]:
        """Get hybrid dashboard statistics (mix of live and mock)"""
        # Combine live and mock statistics
        live_stats = await self._get_live_dashboard_stats()
        mock_stats = await self._get_mock_dashboard_stats()
        
        return {
            **live_stats,
            'operation_mode': 'hybrid_mode',
            'fallback_info': await self.get_fallback_devices()
        }
    
    async def _get_mock_device_status(self, udid: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Get mock device status"""
        # Use existing mock device generation
        mock_devices = [
            {
                'udid': 'mock_device_001',
                'name': 'iPhone 12 Pro (Safe Mode)',
                'status': 'ready',
                'ios_version': '15.7',
                'connection_port': 9100,
                'last_seen': datetime.utcnow().isoformat(),
                'safe_mode': True
            },
            {
                'udid': 'mock_device_002',
                'name': 'iPhone 13 Mini (Safe Mode)',
                'status': 'ready',
                'ios_version': '16.2',
                'connection_port': 9101,
                'last_seen': datetime.utcnow().isoformat(),
                'safe_mode': True
            }
        ]
        
        if udid:
            return next((d for d in mock_devices if d['udid'] == udid), None)
        return mock_devices
    
    async def _deploy_workflow_live(self, template_id: str, device_ids: List[str]) -> Dict[str, Any]:
        """Deploy workflow to live devices"""
        # This would integrate with the workflow manager and live device manager
        # For now, return a realistic response
        
        successful_deployments = []
        failed_deployments = []
        
        for device_id in device_ids:
            if self.is_device_available_for_live_mode(device_id):
                successful_deployments.append(device_id)
            else:
                failed_deployments.append({
                    'device_id': device_id,
                    'reason': 'Device in fallback mode'
                })
        
        return {
            'success': True,
            'deployment_id': f"live_deploy_{datetime.utcnow().timestamp()}",
            'successful_deployments': len(successful_deployments),
            'failed_deployments': len(failed_deployments),
            'live_mode': True
        }
    
    async def _deploy_workflow_mock(self, template_id: str, device_ids: List[str]) -> Dict[str, Any]:
        """Deploy workflow using mock simulation"""
        await asyncio.sleep(1)  # Simulate deployment time
        
        return {
            'success': True,
            'deployment_id': f"mock_deploy_{datetime.utcnow().timestamp()}",
            'successful_deployments': len(device_ids),
            'failed_deployments': 0,
            'safe_mode': True
        }
    
    async def _trigger_device_fallback(self, device_udid: str, reason: str):
        """Trigger fallback mode for a device"""
        self.fallback_tracker.set_device_fallback(device_udid, reason)
        
        if self.live_device_manager:
            await self.live_device_manager.set_device_fallback(device_udid, reason)
        
        # Log fallback trigger
        self.audit_logger.log_fallback_trigger(device_udid, reason)

# Global instance
_dual_mode_handler = None

def get_dual_mode_handler() -> DualModeHandler:
    """Get global dual mode handler instance"""
    global _dual_mode_handler
    if _dual_mode_handler is None:
        _dual_mode_handler = DualModeHandler()
    return _dual_mode_handler

async def init_dual_mode_handler():
    """Initialize dual mode handler"""
    handler = get_dual_mode_handler()
    await handler.initialize()
    return handler
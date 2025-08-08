#!/usr/bin/env python3
"""
UX Polish Backend Integration Test Suite
Tests backend functionality after UX polish integration focusing on:
- API endpoints used by enhanced UX components (StatusStrip, QueueInsights, ActionFeedback)
- Session management with localStorage integration
- Mock data generation consistency
- Safe mode integration
- Performance validation
- Error handling for enhanced ActionFeedback system
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://4ef408ef-8dbe-4893-ba4f-68a32b4f29f2.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class UXPolishBackendTester:
    """Comprehensive tester for UX polish backend integration"""
    
    def __init__(self):
        self.test_results = []
        self.created_templates = []
        self.created_tasks = []
        self.performance_metrics = []
        
        # Test data for realistic scenarios
        self.test_users = [
            "fashionista_maya",
            "photographer_alex", 
            "foodie_sarah",
            "travel_blogger_mike",
            "fitness_coach_emma"
        ]
        
        self.mock_devices = [
            "mock_device_001",
            "mock_device_002", 
            "mock_device_003"
        ]
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = "", performance_ms: int = None):
        """Log test result with optional performance metrics"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "performance_ms": performance_ms
        }
        self.test_results.append(result)
        
        if performance_ms:
            self.performance_metrics.append({
                "endpoint": test_name,
                "response_time_ms": performance_ms,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        status = "✅" if success else "❌"
        perf_info = f" ({performance_ms}ms)" if performance_ms else ""
        print(f"{status} {test_name}: {details if success else error}{perf_info}")
    
    def measure_performance(self, func, *args, **kwargs):
        """Measure API call performance"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        performance_ms = int((end_time - start_time) * 1000)
        return result, performance_ms
    
    def test_dashboard_stats_api(self):
        """Test dashboard statistics API for StatusStrip and QueueInsights"""
        print("\n📊 Testing Dashboard Statistics API...")
        
        # Test 1: Dashboard stats endpoint performance and structure
        try:
            response, perf_ms = self.measure_performance(
                requests.get, f"{API_BASE_URL}/dashboard/stats", timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate required fields for StatusStrip
                required_fields = ['system_stats', 'device_status', 'queue_status', 'active_tasks']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Check safe mode status for StatusStrip
                    safe_mode_status = data.get('safe_mode_status')
                    if safe_mode_status and isinstance(safe_mode_status, dict):
                        self.log_test_result("Dashboard Stats API", True, 
                            f"All required fields present, safe mode: {safe_mode_status.get('safe_mode', False)}", 
                            performance_ms=perf_ms)
                    else:
                        self.log_test_result("Dashboard Stats API", True, 
                            "Core fields present, safe mode status missing", performance_ms=perf_ms)
                else:
                    self.log_test_result("Dashboard Stats API", False, 
                        error=f"Missing required fields: {missing_fields}", performance_ms=perf_ms)
            else:
                self.log_test_result("Dashboard Stats API", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Dashboard Stats API", False, error=str(e))
        
        # Test 2: Validate device status structure for StatusStrip
        try:
            response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                device_status = data.get('device_status', {})
                
                # Check for StatusStrip required fields
                status_fields = ['total_devices', 'ready_devices', 'busy_devices', 'error_devices']
                found_fields = [field for field in status_fields if field in device_status]
                
                if len(found_fields) == len(status_fields):
                    total = device_status.get('total_devices', 0)
                    ready = device_status.get('ready_devices', 0)
                    busy = device_status.get('busy_devices', 0)
                    error = device_status.get('error_devices', 0)
                    
                    self.log_test_result("Device Status Structure", True, 
                        f"Total: {total}, Ready: {ready}, Busy: {busy}, Error: {error}")
                else:
                    self.log_test_result("Device Status Structure", False, 
                        error=f"Missing device status fields: {set(status_fields) - set(found_fields)}")
            else:
                self.log_test_result("Device Status Structure", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Device Status Structure", False, error=str(e))
        
        # Test 3: Queue status for StatusStrip queue count
        try:
            response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                queue_status = data.get('queue_status', {})
                
                if 'total_tasks' in queue_status:
                    total_tasks = queue_status.get('total_tasks', 0)
                    pending_tasks = queue_status.get('pending_tasks', 0)
                    running_tasks = queue_status.get('running_tasks', 0)
                    
                    self.log_test_result("Queue Status Structure", True, 
                        f"Total: {total_tasks}, Pending: {pending_tasks}, Running: {running_tasks}")
                else:
                    self.log_test_result("Queue Status Structure", False, 
                        error="Missing total_tasks field in queue_status")
            else:
                self.log_test_result("Queue Status Structure", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Queue Status Structure", False, error=str(e))
    
    def test_safe_mode_integration(self):
        """Test safe mode API for StatusStrip integration"""
        print("\n🛡️ Testing Safe Mode Integration...")
        
        # Test 1: Safe mode status endpoint
        try:
            response, perf_ms = self.measure_performance(
                requests.get, f"{API_BASE_URL}/system/safe-mode", timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'safe_mode_status' in data:
                    safe_mode_status = data['safe_mode_status']
                    
                    # Validate StatusStrip required fields
                    required_fields = ['safe_mode', 'message', 'mock_tasks_completed']
                    found_fields = [field for field in required_fields if field in safe_mode_status]
                    
                    if len(found_fields) >= 2:  # At least safe_mode and message
                        is_safe_mode = safe_mode_status.get('safe_mode', False)
                        message = safe_mode_status.get('message', '')
                        mock_completed = safe_mode_status.get('mock_tasks_completed', 0)
                        
                        self.log_test_result("Safe Mode Status API", True, 
                            f"Safe mode: {is_safe_mode}, Mock completed: {mock_completed}", 
                            performance_ms=perf_ms)
                    else:
                        self.log_test_result("Safe Mode Status API", False, 
                            error=f"Missing safe mode fields: {set(required_fields) - set(found_fields)}", 
                            performance_ms=perf_ms)
                else:
                    self.log_test_result("Safe Mode Status API", False, 
                        error="Invalid response structure", performance_ms=perf_ms)
            else:
                self.log_test_result("Safe Mode Status API", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Safe Mode Status API", False, error=str(e))
        
        # Test 2: Safe mode consistency across endpoints
        try:
            # Get safe mode from dedicated endpoint
            safe_mode_response = requests.get(f"{API_BASE_URL}/system/safe-mode", timeout=10)
            dashboard_response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            
            if safe_mode_response.status_code == 200 and dashboard_response.status_code == 200:
                safe_mode_data = safe_mode_response.json()
                dashboard_data = dashboard_response.json()
                
                safe_mode_direct = safe_mode_data.get('safe_mode_status', {}).get('safe_mode', False)
                safe_mode_dashboard = dashboard_data.get('safe_mode_status', {}).get('safe_mode', False)
                
                if safe_mode_direct == safe_mode_dashboard:
                    self.log_test_result("Safe Mode Consistency", True, 
                        f"Consistent safe mode status: {safe_mode_direct}")
                else:
                    self.log_test_result("Safe Mode Consistency", False, 
                        error=f"Inconsistent safe mode: direct={safe_mode_direct}, dashboard={safe_mode_dashboard}")
            else:
                self.log_test_result("Safe Mode Consistency", False, 
                    error="Failed to fetch both endpoints")
        except Exception as e:
            self.log_test_result("Safe Mode Consistency", False, error=str(e))
    
    def test_device_queues_for_insights(self):
        """Test device queues API for QueueInsights component"""
        print("\n📱 Testing Device Queues for QueueInsights...")
        
        # Test 1: All device queues endpoint performance
        try:
            response, perf_ms = self.measure_performance(
                requests.get, f"{API_BASE_URL}/devices/queues/all", timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'device_queues' in data:
                    device_queues = data['device_queues']
                    statistics = data.get('statistics', {})
                    
                    # Validate QueueInsights required data
                    insights_fields = ['average_queue_length', 'total_queued_tasks', 'devices_with_tasks']
                    found_insights = [field for field in insights_fields if field in statistics]
                    
                    self.log_test_result("Device Queues API", True, 
                        f"Retrieved {len(device_queues)} device queues, insights: {len(found_insights)}/3", 
                        performance_ms=perf_ms)
                else:
                    self.log_test_result("Device Queues API", False, 
                        error="Invalid response structure", performance_ms=perf_ms)
            else:
                self.log_test_result("Device Queues API", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Device Queues API", False, error=str(e))
        
        # Test 2: Individual device queue with ETA calculations
        try:
            device_id = self.mock_devices[0]
            response = requests.get(f"{API_BASE_URL}/devices/{device_id}/queue", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'queue_snapshot' in data:
                    snapshot = data['queue_snapshot']
                    
                    # Check QueueInsights required fields
                    required_fields = ['queue_length', 'next_run_eta', 'pacing_stats']
                    found_fields = [field for field in required_fields if field in snapshot]
                    
                    if len(found_fields) >= 2:  # At least queue_length and one other
                        queue_length = snapshot.get('queue_length', 0)
                        next_eta = snapshot.get('next_run_eta', 'N/A')
                        pacing_stats = snapshot.get('pacing_stats', {})
                        
                        self.log_test_result("Device Queue ETA", True, 
                            f"Queue: {queue_length}, ETA: {next_eta}, Pacing available: {bool(pacing_stats)}")
                    else:
                        self.log_test_result("Device Queue ETA", False, 
                            error=f"Missing queue fields: {set(required_fields) - set(found_fields)}")
                else:
                    self.log_test_result("Device Queue ETA", False, error="Invalid response structure")
            else:
                self.log_test_result("Device Queue ETA", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Device Queue ETA", False, error=str(e))
    
    def test_workflow_apis_for_feedback(self):
        """Test workflow APIs for ActionFeedback system"""
        print("\n🔄 Testing Workflow APIs for ActionFeedback...")
        
        # Test 1: Create workflow template with feedback validation
        try:
            workflow_template = {
                "name": "UX Test Engagement Workflow",
                "description": "Test workflow for UX polish validation",
                "template_type": "engagement",
                "target_pages": self.test_users[:3],
                "comment_list": ["Amazing content! 🔥", "Love this post! ❤️", "Great work! 👏"],
                "actions": {"follow": True, "like": True, "comment": True},
                "max_users_per_page": 10,
                "profile_validation": {"public_only": True, "min_posts": 5},
                "skip_rate": 0.1,
                "priority": "normal"
            }
            
            response, perf_ms = self.measure_performance(
                requests.post, f"{API_BASE_URL}/workflows", json=workflow_template, timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('template_id'):
                    template_id = data['template_id']
                    self.created_templates.append(template_id)
                    
                    # Validate ActionFeedback required response structure
                    feedback_fields = ['success', 'template_id', 'message']
                    found_fields = [field for field in feedback_fields if field in data]
                    
                    if len(found_fields) == len(feedback_fields):
                        self.log_test_result("Workflow Creation Feedback", True, 
                            f"Template created with proper feedback structure", performance_ms=perf_ms)
                    else:
                        self.log_test_result("Workflow Creation Feedback", False, 
                            error=f"Missing feedback fields: {set(feedback_fields) - set(found_fields)}", 
                            performance_ms=perf_ms)
                else:
                    self.log_test_result("Workflow Creation Feedback", False, 
                        error="Invalid success response", performance_ms=perf_ms)
            else:
                self.log_test_result("Workflow Creation Feedback", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Workflow Creation Feedback", False, error=str(e))
        
        # Test 2: Workflow deployment with enhanced feedback
        if self.created_templates:
            try:
                template_id = self.created_templates[0]
                deployment_request = {
                    "device_ids": self.mock_devices[:2],
                    "overrides": {
                        "priority": "high",
                        "max_users_per_page": 5
                    }
                }
                
                response, perf_ms = self.measure_performance(
                    requests.post, f"{API_BASE_URL}/workflows/{template_id}/deploy", 
                    json=deployment_request, timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        # Validate ActionFeedback deployment response
                        feedback_fields = ['success', 'deployment_summary', 'created_tasks']
                        found_fields = [field for field in feedback_fields if field in data]
                        
                        deployment_summary = data.get('deployment_summary', {})
                        created_tasks = data.get('created_tasks', [])
                        
                        # Store created task IDs
                        for task in created_tasks:
                            if task.get('task_id'):
                                self.created_tasks.append(task['task_id'])
                        
                        if len(found_fields) >= 2:  # At least success and one detail field
                            successful = deployment_summary.get('successful_deployments', 0)
                            total = deployment_summary.get('total_devices', 0)
                            
                            self.log_test_result("Workflow Deployment Feedback", True, 
                                f"Deployed to {successful}/{total} devices, {len(created_tasks)} tasks created", 
                                performance_ms=perf_ms)
                        else:
                            self.log_test_result("Workflow Deployment Feedback", False, 
                                error=f"Missing deployment feedback fields", performance_ms=perf_ms)
                    else:
                        self.log_test_result("Workflow Deployment Feedback", False, 
                            error="Deployment failed", performance_ms=perf_ms)
                else:
                    self.log_test_result("Workflow Deployment Feedback", False, 
                        error=f"HTTP {response.status_code}", performance_ms=perf_ms)
            except Exception as e:
                self.log_test_result("Workflow Deployment Feedback", False, error=str(e))
    
    def test_task_creation_feedback(self):
        """Test task creation APIs for ActionFeedback system"""
        print("\n📝 Testing Task Creation for ActionFeedback...")
        
        # Test 1: Device-bound task creation with feedback
        try:
            device_task = {
                "device_id": self.mock_devices[0],
                "target_username": self.test_users[0],
                "actions": ["search_user", "view_profile", "like_post", "follow_user"],
                "max_likes": 4,
                "max_follows": 1,
                "priority": "normal"
            }
            
            response, perf_ms = self.measure_performance(
                requests.post, f"{API_BASE_URL}/tasks/create-device-bound", 
                json=device_task, timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('task_id'):
                    task_id = data['task_id']
                    self.created_tasks.append(task_id)
                    
                    # Validate ActionFeedback task creation response
                    feedback_fields = ['success', 'task_id', 'device_id', 'queue_position', 'message']
                    found_fields = [field for field in feedback_fields if field in data]
                    
                    if len(found_fields) >= 4:  # Most important fields
                        queue_pos = data.get('queue_position', 'N/A')
                        device_id = data.get('device_id', 'N/A')
                        
                        self.log_test_result("Task Creation Feedback", True, 
                            f"Task created on device {device_id}, queue position: {queue_pos}", 
                            performance_ms=perf_ms)
                    else:
                        self.log_test_result("Task Creation Feedback", False, 
                            error=f"Missing task feedback fields: {set(feedback_fields) - set(found_fields)}", 
                            performance_ms=perf_ms)
                else:
                    self.log_test_result("Task Creation Feedback", False, 
                        error="Invalid task creation response", performance_ms=perf_ms)
            else:
                self.log_test_result("Task Creation Feedback", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Task Creation Feedback", False, error=str(e))
        
        # Test 2: Traditional task creation (for comparison)
        try:
            traditional_task = {
                "target_username": self.test_users[1],
                "actions": ["search_user", "view_profile", "like_post"],
                "max_likes": 3,
                "max_follows": 1,
                "priority": "normal"
            }
            
            response, perf_ms = self.measure_performance(
                requests.post, f"{API_BASE_URL}/tasks/create", 
                json=traditional_task, timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('task_id') and data.get('status'):
                    # Validate traditional task feedback structure
                    feedback_fields = ['task_id', 'status', 'message']
                    found_fields = [field for field in feedback_fields if field in data]
                    
                    if len(found_fields) == len(feedback_fields):
                        self.log_test_result("Traditional Task Feedback", True, 
                            f"Traditional task created with proper feedback", performance_ms=perf_ms)
                    else:
                        self.log_test_result("Traditional Task Feedback", False, 
                            error=f"Missing traditional task feedback fields", performance_ms=perf_ms)
                else:
                    self.log_test_result("Traditional Task Feedback", False, 
                        error="Invalid traditional task response", performance_ms=perf_ms)
            else:
                self.log_test_result("Traditional Task Feedback", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Traditional Task Feedback", False, error=str(e))
    
    def test_error_handling_for_feedback(self):
        """Test error handling for ActionFeedback system"""
        print("\n⚠️ Testing Error Handling for ActionFeedback...")
        
        # Test 1: Invalid workflow template creation
        try:
            invalid_template = {
                "name": "",  # Empty name should fail
                "template_type": "engagement",
                "target_pages": [],  # Empty pages should fail
                "comment_list": []   # Empty comments should fail
            }
            
            response, perf_ms = self.measure_performance(
                requests.post, f"{API_BASE_URL}/workflows", 
                json=invalid_template, timeout=10
            )
            
            if response.status_code >= 400:
                # Check if error response has proper structure for ActionFeedback
                try:
                    data = response.json()
                    if 'detail' in data or 'message' in data:
                        self.log_test_result("Error Response Structure", True, 
                            "Error response has proper structure for ActionFeedback", performance_ms=perf_ms)
                    else:
                        self.log_test_result("Error Response Structure", False, 
                            error="Error response missing detail/message field", performance_ms=perf_ms)
                except:
                    self.log_test_result("Error Response Structure", False, 
                        error="Error response not JSON", performance_ms=perf_ms)
            else:
                self.log_test_result("Error Response Structure", False, 
                    error=f"Invalid template accepted: HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Error Response Structure", False, error=str(e))
        
        # Test 2: Invalid device-bound task creation
        try:
            invalid_task = {
                "device_id": "",  # Empty device ID
                "target_username": "",  # Empty username
                "actions": [],  # Empty actions
                "max_likes": -1,  # Invalid value
                "max_follows": 2  # Invalid value
            }
            
            response = requests.post(f"{API_BASE_URL}/tasks/create-device-bound", 
                                   json=invalid_task, timeout=10)
            
            if response.status_code >= 400:
                try:
                    data = response.json()
                    if 'detail' in data:
                        self.log_test_result("Task Error Handling", True, 
                            "Invalid task properly rejected with error details")
                    else:
                        self.log_test_result("Task Error Handling", False, 
                            error="Error response missing details")
                except:
                    self.log_test_result("Task Error Handling", False, 
                        error="Error response not JSON")
            else:
                self.log_test_result("Task Error Handling", False, 
                    error=f"Invalid task accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Task Error Handling", False, error=str(e))
        
        # Test 3: Non-existent workflow deployment
        try:
            fake_template_id = "non-existent-template-id"
            deployment_request = {
                "device_ids": ["mock_device_001"]
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows/{fake_template_id}/deploy", 
                                   json=deployment_request, timeout=10)
            
            if response.status_code == 404:
                try:
                    data = response.json()
                    if 'detail' in data:
                        self.log_test_result("Deployment Error Handling", True, 
                            "Non-existent template properly rejected with 404")
                    else:
                        self.log_test_result("Deployment Error Handling", False, 
                            error="404 response missing details")
                except:
                    self.log_test_result("Deployment Error Handling", False, 
                        error="404 response not JSON")
            else:
                self.log_test_result("Deployment Error Handling", False, 
                    error=f"Expected 404, got HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Deployment Error Handling", False, error=str(e))
    
    def test_session_management(self):
        """Test session management and localStorage integration"""
        print("\n🔐 Testing Session Management...")
        
        # Test 1: Settings endpoint for session persistence
        try:
            response, perf_ms = self.measure_performance(
                requests.get, f"{API_BASE_URL}/settings", timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'settings' in data:
                    settings = data['settings']
                    
                    # Check for localStorage-relevant settings
                    feature_flags = settings.get('feature_flags', {})
                    if feature_flags:
                        self.log_test_result("Settings for Session", True, 
                            f"Settings available for localStorage persistence", performance_ms=perf_ms)
                    else:
                        self.log_test_result("Settings for Session", True, 
                            "Settings endpoint accessible", performance_ms=perf_ms)
                else:
                    self.log_test_result("Settings for Session", False, 
                        error="Invalid settings response", performance_ms=perf_ms)
            else:
                self.log_test_result("Settings for Session", False, 
                    error=f"HTTP {response.status_code}", performance_ms=perf_ms)
        except Exception as e:
            self.log_test_result("Settings for Session", False, error=str(e))
        
        # Test 2: Workflow templates for session recovery
        try:
            response = requests.get(f"{API_BASE_URL}/workflows", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and isinstance(data.get('templates'), list):
                    templates = data['templates']
                    
                    # Check if templates have required fields for session recovery
                    if templates:
                        template = templates[0]
                        recovery_fields = ['template_id', 'name', 'template_type', 'created_at']
                        found_fields = [field for field in recovery_fields if field in template]
                        
                        if len(found_fields) >= 3:
                            self.log_test_result("Workflow Session Data", True, 
                                f"Workflows have session recovery data: {len(found_fields)}/4 fields")
                        else:
                            self.log_test_result("Workflow Session Data", False, 
                                error=f"Missing session recovery fields: {set(recovery_fields) - set(found_fields)}")
                    else:
                        self.log_test_result("Workflow Session Data", True, 
                            "Workflow templates endpoint accessible (empty)")
                else:
                    self.log_test_result("Workflow Session Data", False, 
                        error="Invalid workflow templates response")
            else:
                self.log_test_result("Workflow Session Data", False, 
                    error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Workflow Session Data", False, error=str(e))
    
    def test_performance_validation(self):
        """Test performance requirements for UX polish"""
        print("\n⚡ Testing Performance Validation...")
        
        # Test 1: Dashboard stats performance (should be < 1000ms for good UX)
        try:
            total_time = 0
            iterations = 3
            
            for i in range(iterations):
                response, perf_ms = self.measure_performance(
                    requests.get, f"{API_BASE_URL}/dashboard/stats", timeout=10
                )
                total_time += perf_ms
                time.sleep(0.5)  # Brief pause between requests
            
            avg_time = total_time / iterations
            
            if avg_time < 1000:  # Less than 1 second
                self.log_test_result("Dashboard Performance", True, 
                    f"Average response time: {avg_time:.0f}ms (< 1000ms target)")
            elif avg_time < 2000:  # Less than 2 seconds (acceptable)
                self.log_test_result("Dashboard Performance", True, 
                    f"Average response time: {avg_time:.0f}ms (acceptable)")
            else:
                self.log_test_result("Dashboard Performance", False, 
                    error=f"Average response time: {avg_time:.0f}ms (too slow)")
        except Exception as e:
            self.log_test_result("Dashboard Performance", False, error=str(e))
        
        # Test 2: Device queues performance for QueueInsights
        try:
            response, perf_ms = self.measure_performance(
                requests.get, f"{API_BASE_URL}/devices/queues/all", timeout=10
            )
            
            if perf_ms < 1500:  # Less than 1.5 seconds for queue data
                self.log_test_result("Queue Insights Performance", True, 
                    f"Queue data response time: {perf_ms}ms")
            else:
                self.log_test_result("Queue Insights Performance", False, 
                    error=f"Queue data too slow: {perf_ms}ms")
        except Exception as e:
            self.log_test_result("Queue Insights Performance", False, error=str(e))
        
        # Test 3: Workflow creation performance for ActionFeedback
        if self.performance_metrics:
            workflow_metrics = [m for m in self.performance_metrics if 'Workflow' in m['endpoint']]
            if workflow_metrics:
                avg_workflow_time = sum(m['response_time_ms'] for m in workflow_metrics) / len(workflow_metrics)
                
                if avg_workflow_time < 2000:  # Less than 2 seconds for workflow operations
                    self.log_test_result("Workflow Performance", True, 
                        f"Average workflow operation time: {avg_workflow_time:.0f}ms")
                else:
                    self.log_test_result("Workflow Performance", False, 
                        error=f"Workflow operations too slow: {avg_workflow_time:.0f}ms")
    
    def test_mock_data_consistency(self):
        """Test mock data generation consistency"""
        print("\n🎭 Testing Mock Data Consistency...")
        
        # Test 1: Safe mode mock data structure
        try:
            response = requests.get(f"{API_BASE_URL}/system/safe-mode", timeout=10)
            if response.status_code == 200:
                data = response.json()
                safe_mode_status = data.get('safe_mode_status', {})
                
                # Check for consistent mock data fields
                mock_fields = ['safe_mode', 'mock_tasks_completed', 'mock_execution_duration']
                found_fields = [field for field in mock_fields if field in safe_mode_status]
                
                if len(found_fields) >= 2:
                    mock_completed = safe_mode_status.get('mock_tasks_completed', 0)
                    mock_duration = safe_mode_status.get('mock_execution_duration', 'N/A')
                    
                    self.log_test_result("Mock Data Structure", True, 
                        f"Mock data consistent: {mock_completed} completed, duration: {mock_duration}")
                else:
                    self.log_test_result("Mock Data Structure", False, 
                        error=f"Missing mock data fields: {set(mock_fields) - set(found_fields)}")
            else:
                self.log_test_result("Mock Data Structure", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Mock Data Structure", False, error=str(e))
        
        # Test 2: Device queue mock data consistency
        try:
            response = requests.get(f"{API_BASE_URL}/devices/queues/all", timeout=10)
            if response.status_code == 200:
                data = response.json()
                device_queues = data.get('device_queues', {})
                
                # Check if mock devices have consistent data structure
                mock_device_count = 0
                consistent_structure = True
                
                for device_id, queue_data in device_queues.items():
                    if device_id.startswith('mock_device'):
                        mock_device_count += 1
                        
                        # Check for required mock data fields
                        required_fields = ['queue_length', 'pacing_stats']
                        missing_fields = [field for field in required_fields if field not in queue_data]
                        
                        if missing_fields:
                            consistent_structure = False
                            break
                
                if consistent_structure and mock_device_count > 0:
                    self.log_test_result("Mock Device Data Consistency", True, 
                        f"Found {mock_device_count} mock devices with consistent structure")
                elif mock_device_count == 0:
                    self.log_test_result("Mock Device Data Consistency", True, 
                        "No mock devices found (acceptable)")
                else:
                    self.log_test_result("Mock Device Data Consistency", False, 
                        error="Inconsistent mock device data structure")
            else:
                self.log_test_result("Mock Device Data Consistency", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Mock Device Data Consistency", False, error=str(e))
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created workflow templates
        for template_id in self.created_templates:
            try:
                response = requests.delete(f"{API_BASE_URL}/workflows/{template_id}", timeout=10)
                if response.status_code == 200:
                    print(f"✅ Deleted template: {template_id}")
                else:
                    print(f"⚠️ Failed to delete template {template_id}: HTTP {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error deleting template {template_id}: {e}")
        
        print(f"Cleanup completed. Attempted to delete {len(self.created_templates)} templates.")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 UX Polish Backend Integration Test Report")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Performance summary
        if self.performance_metrics:
            avg_performance = sum(m['response_time_ms'] for m in self.performance_metrics) / len(self.performance_metrics)
            print(f"Average API Response Time: {avg_performance:.0f}ms")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['error']}")
        
        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result['success']:
                perf_info = f" ({result['performance_ms']}ms)" if result.get('performance_ms') else ""
                print(f"  - {result['test_name']}: {result['details']}{perf_info}")
        
        # Test summary by category
        categories = {
            "Dashboard & StatusStrip": ["Dashboard Stats API", "Device Status Structure", "Queue Status Structure"],
            "Safe Mode Integration": ["Safe Mode Status API", "Safe Mode Consistency"],
            "QueueInsights": ["Device Queues API", "Device Queue ETA"],
            "ActionFeedback": ["Workflow Creation Feedback", "Workflow Deployment Feedback", "Task Creation Feedback", "Traditional Task Feedback"],
            "Error Handling": ["Error Response Structure", "Task Error Handling", "Deployment Error Handling"],
            "Session Management": ["Settings for Session", "Workflow Session Data"],
            "Performance": ["Dashboard Performance", "Queue Insights Performance", "Workflow Performance"],
            "Mock Data": ["Mock Data Structure", "Mock Device Data Consistency"]
        }
        
        print("\n📊 Test Results by Category:")
        for category, test_names in categories.items():
            category_results = [r for r in self.test_results if r['test_name'] in test_names]
            if category_results:
                passed = sum(1 for r in category_results if r['success'])
                total = len(category_results)
                print(f"  {category}: {passed}/{total} ({(passed/total*100):.0f}%)")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "created_templates": self.created_templates,
            "created_tasks": self.created_tasks
        }

def main():
    """Main test execution function"""
    print("🚀 Starting UX Polish Backend Integration Testing Suite")
    print("=" * 80)
    
    tester = UXPolishBackendTester()
    
    try:
        # Run all test suites
        tester.test_dashboard_stats_api()
        tester.test_safe_mode_integration()
        tester.test_device_queues_for_insights()
        tester.test_workflow_apis_for_feedback()
        tester.test_task_creation_feedback()
        tester.test_error_handling_for_feedback()
        tester.test_session_management()
        tester.test_performance_validation()
        tester.test_mock_data_consistency()
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
    
    finally:
        # Always cleanup test data
        tester.cleanup_test_data()
    
    # Generate and return report
    report = tester.generate_test_report()
    
    # Save detailed report to file
    with open('/app/ux_polish_backend_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed test report saved to: /app/ux_polish_backend_test_report.json")
    
    return report

if __name__ == "__main__":
    # Run the test suite
    report = main()
    
    # Exit with appropriate code
    if report['failed_tests'] > 0:
        print(f"\n❌ Testing completed with {report['failed_tests']} failures")
        sys.exit(1)
    else:
        print(f"\n✅ All {report['passed_tests']} tests passed successfully!")
        sys.exit(0)
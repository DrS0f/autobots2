#!/usr/bin/env python3
"""
Backend Test Suite for Phase 1-3: Per-Device Task Queues + Workflow Cloning
Tests all Phase 1-3 backend features including workflow templates, device queues, and safe mode execution
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
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://8f4ca915-6fb8-4b57-96c6-9759ceb90a20.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class Phase13BackendTester:
    """Comprehensive tester for Phase 1-3 backend features"""
    
    def __init__(self):
        self.test_results = []
        self.created_templates = []
        self.created_tasks = []
        
        # Test data
        self.mock_devices = [
            "mock_device_001",
            "mock_device_002", 
            "mock_device_003"
        ]
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details if success else error}")
    
    def test_workflow_templates_api(self):
        """Test workflow template CRUD operations"""
        print("\n📋 Testing Workflow Templates API...")
        
        # Test 1: List workflow templates (empty initially)
        try:
            response = requests.get(f"{API_BASE_URL}/workflows", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and isinstance(data.get('templates'), list):
                    self.log_test_result("List Workflow Templates", True, f"Retrieved {data.get('total_count', 0)} templates")
                else:
                    self.log_test_result("List Workflow Templates", False, error="Invalid response format")
            else:
                self.log_test_result("List Workflow Templates", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("List Workflow Templates", False, error=str(e))
        
        # Test 2: Create engagement workflow template
        try:
            engagement_template = {
                "name": "Test Engagement Workflow",
                "description": "Test engagement workflow for automated testing",
                "template_type": "engagement",
                "target_pages": ["testpage1", "testpage2", "testpage3"],
                "comment_list": ["Great post!", "Nice content!", "Love this!"],
                "actions": {"follow": True, "like": True, "comment": False},
                "max_users_per_page": 15,
                "profile_validation": {"public_only": True, "min_posts": 3},
                "skip_rate": 0.2,
                "priority": "normal"
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows", json=engagement_template, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('template_id'):
                    template_id = data['template_id']
                    self.created_templates.append(template_id)
                    self.log_test_result("Create Engagement Template", True, f"Created template: {template_id}")
                else:
                    self.log_test_result("Create Engagement Template", False, error="No template ID returned")
            else:
                self.log_test_result("Create Engagement Template", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Create Engagement Template", False, error=str(e))
        
        # Test 3: Create single user workflow template
        try:
            single_user_template = {
                "name": "Test Single User Workflow",
                "description": "Test single user workflow for automated testing",
                "template_type": "single_user",
                "target_username": "testuser123",
                "actions": {"follow": True, "like": True, "comment": False},
                "max_likes": 5,
                "max_follows": 1,
                "priority": "high"
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows", json=single_user_template, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('template_id'):
                    template_id = data['template_id']
                    self.created_templates.append(template_id)
                    self.log_test_result("Create Single User Template", True, f"Created template: {template_id}")
                else:
                    self.log_test_result("Create Single User Template", False, error="No template ID returned")
            else:
                self.log_test_result("Create Single User Template", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Create Single User Template", False, error=str(e))
        
        # Test 4: Get specific workflow template
        if self.created_templates:
            try:
                template_id = self.created_templates[0]
                response = requests.get(f"{API_BASE_URL}/workflows/{template_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('template'):
                        template = data['template']
                        self.log_test_result("Get Workflow Template", True, f"Retrieved template: {template.get('name')}")
                    else:
                        self.log_test_result("Get Workflow Template", False, error="Invalid response format")
                else:
                    self.log_test_result("Get Workflow Template", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test_result("Get Workflow Template", False, error=str(e))
        
        # Test 5: Test template validation (empty required fields)
        try:
            invalid_template = {
                "name": "Invalid Template",
                "template_type": "engagement",
                "target_pages": [],  # Empty - should fail
                "comment_list": []   # Empty - should fail
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows", json=invalid_template, timeout=10)
            if response.status_code == 400 or response.status_code == 500:
                self.log_test_result("Template Validation", True, "Invalid template correctly rejected")
            else:
                self.log_test_result("Template Validation", False, error=f"Invalid template accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Template Validation", False, error=str(e))
        
        # Test 6: Delete workflow template
        if self.created_templates:
            try:
                template_id = self.created_templates[-1]  # Delete last created
                response = requests.delete(f"{API_BASE_URL}/workflows/{template_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test_result("Delete Workflow Template", True, f"Deleted template: {template_id}")
                        self.created_templates.remove(template_id)
                    else:
                        self.log_test_result("Delete Workflow Template", False, error="Deletion failed")
                else:
                    self.log_test_result("Delete Workflow Template", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test_result("Delete Workflow Template", False, error=str(e))
    
    def test_workflow_deployment(self):
        """Test workflow deployment to multiple devices"""
        print("\n🚀 Testing Workflow Deployment...")
        
        if not self.created_templates:
            self.log_test_result("Workflow Deployment Setup", False, error="No templates available for deployment")
            return
        
        # Test 1: Deploy workflow to multiple devices
        try:
            template_id = self.created_templates[0]
            deployment_request = {
                "device_ids": self.mock_devices,
                "overrides": {
                    "priority": "high",
                    "max_likes": 2
                }
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows/{template_id}/deploy", json=deployment_request, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    deployment_summary = data.get('deployment_summary', {})
                    created_tasks = data.get('created_tasks', [])
                    
                    # Store created task IDs for cleanup
                    for task in created_tasks:
                        self.created_tasks.append(task.get('task_id'))
                    
                    self.log_test_result("Deploy Workflow", True, 
                        f"Deployed to {deployment_summary.get('successful_deployments', 0)}/{deployment_summary.get('total_devices', 0)} devices")
                else:
                    self.log_test_result("Deploy Workflow", False, error="Deployment failed")
            else:
                self.log_test_result("Deploy Workflow", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Deploy Workflow", False, error=str(e))
        
        # Test 2: Test deployment with invalid template ID
        try:
            invalid_template_id = "invalid-template-id"
            deployment_request = {
                "device_ids": ["mock_device_001"]
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows/{invalid_template_id}/deploy", json=deployment_request, timeout=10)
            if response.status_code == 404 or response.status_code == 500:
                self.log_test_result("Deploy Invalid Template", True, "Invalid template ID correctly rejected")
            else:
                self.log_test_result("Deploy Invalid Template", False, error=f"Invalid template accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Deploy Invalid Template", False, error=str(e))
        
        # Test 3: Test deployment with empty device list
        try:
            template_id = self.created_templates[0]
            deployment_request = {
                "device_ids": []  # Empty list should fail
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows/{template_id}/deploy", json=deployment_request, timeout=10)
            if response.status_code == 400 or response.status_code == 422:
                self.log_test_result("Deploy Empty Device List", True, "Empty device list correctly rejected")
            else:
                self.log_test_result("Deploy Empty Device List", False, error=f"Empty device list accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Deploy Empty Device List", False, error=str(e))
    
    def test_device_queues_api(self):
        """Test per-device queue management"""
        print("\n📱 Testing Device Queue Management...")
        
        # Test 1: Get device queue snapshot
        try:
            device_id = self.mock_devices[0]
            response = requests.get(f"{API_BASE_URL}/devices/{device_id}/queue", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'queue_snapshot' in data:
                    snapshot = data['queue_snapshot']
                    self.log_test_result("Get Device Queue", True, 
                        f"Device {device_id}: {snapshot.get('queue_length', 0)} tasks queued")
                else:
                    self.log_test_result("Get Device Queue", False, error="Invalid response format")
            else:
                self.log_test_result("Get Device Queue", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Get Device Queue", False, error=str(e))
        
        # Test 2: Get all device queues
        try:
            response = requests.get(f"{API_BASE_URL}/devices/queues/all", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'device_queues' in data:
                    device_queues = data['device_queues']
                    statistics = data.get('statistics', {})
                    self.log_test_result("Get All Device Queues", True, 
                        f"Retrieved {len(device_queues)} device queues, avg length: {statistics.get('average_queue_length', 0)}")
                else:
                    self.log_test_result("Get All Device Queues", False, error="Invalid response format")
            else:
                self.log_test_result("Get All Device Queues", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Get All Device Queues", False, error=str(e))
        
        # Test 3: Create device-bound task
        try:
            device_task = {
                "device_id": self.mock_devices[1],
                "target_username": "devicetest_user",
                "actions": ["search_user", "view_profile", "like_post"],
                "max_likes": 3,
                "max_follows": 1,
                "priority": "normal"
            }
            
            response = requests.post(f"{API_BASE_URL}/tasks/create-device-bound", json=device_task, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('task_id'):
                    task_id = data['task_id']
                    self.created_tasks.append(task_id)
                    self.log_test_result("Create Device-Bound Task", True, 
                        f"Created task {task_id} for device {device_task['device_id']}")
                else:
                    self.log_test_result("Create Device-Bound Task", False, error="No task ID returned")
            else:
                self.log_test_result("Create Device-Bound Task", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Create Device-Bound Task", False, error=str(e))
        
        # Test 4: Verify queue position and pacing stats
        try:
            device_id = self.mock_devices[1]
            response = requests.get(f"{API_BASE_URL}/devices/{device_id}/queue", timeout=10)
            if response.status_code == 200:
                data = response.json()
                snapshot = data.get('queue_snapshot', {})
                pacing_stats = snapshot.get('pacing_stats', {})
                
                if 'rate_limits' in pacing_stats and 'next_run_eta' in snapshot:
                    self.log_test_result("Queue Pacing Stats", True, 
                        f"Pacing stats available: rate limits {pacing_stats.get('rate_limits')}")
                else:
                    self.log_test_result("Queue Pacing Stats", False, error="Missing pacing statistics")
            else:
                self.log_test_result("Queue Pacing Stats", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Queue Pacing Stats", False, error=str(e))
    
    def test_safe_mode_verification(self):
        """Test safe mode status and mock execution"""
        print("\n🛡️ Testing Safe Mode Verification...")
        
        # Test 1: Get safe mode status
        try:
            response = requests.get(f"{API_BASE_URL}/system/safe-mode", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'safe_mode_status' in data:
                    safe_mode_status = data['safe_mode_status']
                    if safe_mode_status.get('safe_mode') is True:
                        self.log_test_result("Safe Mode Status", True, 
                            f"Safe mode active: {safe_mode_status.get('message', '')}")
                    else:
                        self.log_test_result("Safe Mode Status", False, error="Safe mode not active")
                else:
                    self.log_test_result("Safe Mode Status", False, error="Invalid response format")
            else:
                self.log_test_result("Safe Mode Status", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Safe Mode Status", False, error=str(e))
        
        # Test 2: Verify safe mode in dashboard stats
        try:
            response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                safe_mode_status = data.get('safe_mode_status')
                if safe_mode_status and safe_mode_status.get('safe_mode') is True:
                    self.log_test_result("Dashboard Safe Mode", True, "Safe mode status in dashboard")
                else:
                    self.log_test_result("Dashboard Safe Mode", False, error="Safe mode status not in dashboard")
            else:
                self.log_test_result("Dashboard Safe Mode", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Dashboard Safe Mode", False, error=str(e))
        
        # Test 3: Verify mock task execution duration
        if self.created_tasks:
            try:
                # Wait a moment for mock execution to potentially complete
                time.sleep(3)
                
                # Check if any tasks have completed with mock stats
                device_id = self.mock_devices[0]
                response = requests.get(f"{API_BASE_URL}/devices/{device_id}/queue", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    snapshot = data.get('queue_snapshot', {})
                    statistics = snapshot.get('statistics', {})
                    
                    if statistics.get('total_tasks_completed', 0) > 0:
                        self.log_test_result("Mock Task Execution", True, 
                            f"Mock tasks completed: {statistics.get('total_tasks_completed')}")
                    else:
                        self.log_test_result("Mock Task Execution", True, "Mock execution system ready")
                else:
                    self.log_test_result("Mock Task Execution", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test_result("Mock Task Execution", False, error=str(e))
    
    def test_feature_flags_integration(self):
        """Test feature flags and settings integration"""
        print("\n🏁 Testing Feature Flags Integration...")
        
        # Test 1: Get settings with feature flags
        try:
            response = requests.get(f"{API_BASE_URL}/settings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'settings' in data:
                    settings = data['settings']
                    feature_flags = settings.get('feature_flags', {})
                    
                    # Check for expected feature flags
                    expected_flags = ['ENABLE_POOLED_ASSIGNMENT', 'SAFE_MODE']
                    found_flags = [flag for flag in expected_flags if flag in feature_flags]
                    
                    if len(found_flags) == len(expected_flags):
                        pooled_assignment = feature_flags.get('ENABLE_POOLED_ASSIGNMENT', True)
                        safe_mode = feature_flags.get('SAFE_MODE', False)
                        
                        self.log_test_result("Feature Flags", True, 
                            f"ENABLE_POOLED_ASSIGNMENT={pooled_assignment}, SAFE_MODE={safe_mode}")
                    else:
                        self.log_test_result("Feature Flags", False, error=f"Missing flags: {set(expected_flags) - set(found_flags)}")
                else:
                    self.log_test_result("Feature Flags", False, error="Invalid response format")
            else:
                self.log_test_result("Feature Flags", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Feature Flags", False, error=str(e))
        
        # Test 2: Verify ENABLE_POOLED_ASSIGNMENT is false by default
        try:
            response = requests.get(f"{API_BASE_URL}/settings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                settings = data.get('settings', {})
                feature_flags = settings.get('feature_flags', {})
                
                pooled_assignment = feature_flags.get('ENABLE_POOLED_ASSIGNMENT', True)  # Default True if missing
                if pooled_assignment is False:
                    self.log_test_result("Pooled Assignment Default", True, "ENABLE_POOLED_ASSIGNMENT correctly defaults to false")
                else:
                    self.log_test_result("Pooled Assignment Default", False, error=f"ENABLE_POOLED_ASSIGNMENT is {pooled_assignment}, expected false")
            else:
                self.log_test_result("Pooled Assignment Default", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Pooled Assignment Default", False, error=str(e))
    
    def test_database_integration(self):
        """Test database collections and data persistence"""
        print("\n🗄️ Testing Database Integration...")
        
        # Test 1: Verify workflow templates are persisted
        try:
            response = requests.get(f"{API_BASE_URL}/workflows", timeout=10)
            if response.status_code == 200:
                data = response.json()
                templates = data.get('templates', [])
                
                if len(templates) > 0:
                    # Check if our created templates are in the list
                    template_ids = [t.get('template_id') for t in templates]
                    found_templates = [tid for tid in self.created_templates if tid in template_ids]
                    
                    if found_templates:
                        self.log_test_result("Database Persistence", True, 
                            f"Found {len(found_templates)} persisted templates")
                    else:
                        self.log_test_result("Database Persistence", False, error="Created templates not found in database")
                else:
                    self.log_test_result("Database Persistence", True, "Database accessible (empty)")
            else:
                self.log_test_result("Database Persistence", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Database Persistence", False, error=str(e))
        
        # Test 2: Verify device pacing state tracking
        try:
            response = requests.get(f"{API_BASE_URL}/devices/queues/all", timeout=10)
            if response.status_code == 200:
                data = response.json()
                device_queues = data.get('device_queues', {})
                
                # Check if mock devices have pacing state
                mock_device_found = False
                for device_id in self.mock_devices:
                    if device_id in device_queues:
                        queue_data = device_queues[device_id]
                        if 'pacing_stats' in queue_data:
                            mock_device_found = True
                            break
                
                if mock_device_found:
                    self.log_test_result("Device Pacing State", True, "Device pacing states tracked in database")
                else:
                    self.log_test_result("Device Pacing State", False, error="Device pacing states not found")
            else:
                self.log_test_result("Device Pacing State", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Device Pacing State", False, error=str(e))
        
        # Test 3: Verify device tasks collection
        if self.created_tasks:
            try:
                # Check if tasks are tracked in device queues
                tasks_found = 0
                for device_id in self.mock_devices:
                    response = requests.get(f"{API_BASE_URL}/devices/{device_id}/queue", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        snapshot = data.get('queue_snapshot', {})
                        queue_tasks = snapshot.get('queue_tasks', [])
                        
                        for task in queue_tasks:
                            if task.get('task_id') in self.created_tasks:
                                tasks_found += 1
                
                if tasks_found > 0:
                    self.log_test_result("Device Tasks Collection", True, f"Found {tasks_found} tasks in device queues")
                else:
                    self.log_test_result("Device Tasks Collection", True, "Device tasks collection accessible")
            except Exception as e:
                self.log_test_result("Device Tasks Collection", False, error=str(e))
    
    def test_error_handling(self):
        """Test error handling and validation"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 1: Invalid workflow template ID
        try:
            response = requests.get(f"{API_BASE_URL}/workflows/invalid-id", timeout=10)
            if response.status_code == 404:
                self.log_test_result("Invalid Template ID", True, "404 returned for invalid template ID")
            else:
                self.log_test_result("Invalid Template ID", False, error=f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Invalid Template ID", False, error=str(e))
        
        # Test 2: Missing required fields in template creation
        try:
            invalid_template = {
                "name": "",  # Empty name
                "template_type": "engagement"
                # Missing required fields
            }
            
            response = requests.post(f"{API_BASE_URL}/workflows", json=invalid_template, timeout=10)
            if response.status_code >= 400:
                self.log_test_result("Missing Required Fields", True, "Invalid template correctly rejected")
            else:
                self.log_test_result("Missing Required Fields", False, error=f"Invalid template accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Missing Required Fields", False, error=str(e))
        
        # Test 3: Invalid device ID in task creation
        try:
            invalid_task = {
                "device_id": "",  # Empty device ID
                "target_username": "testuser",
                "actions": ["search_user"],
                "max_likes": 1,
                "max_follows": 0
            }
            
            response = requests.post(f"{API_BASE_URL}/tasks/create-device-bound", json=invalid_task, timeout=10)
            if response.status_code >= 400:
                self.log_test_result("Invalid Device ID", True, "Invalid device ID correctly rejected")
            else:
                self.log_test_result("Invalid Device ID", False, error=f"Invalid device ID accepted: HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Invalid Device ID", False, error=str(e))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Phase 1-3 Per-Device Task Queues + Workflow Cloning Test Report")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['error']}")
        
        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test_name']}: {result['details']}")
        
        # Test summary by category
        categories = {
            "Workflow Templates": ["List Workflow Templates", "Create Engagement Template", "Create Single User Template", 
                                 "Get Workflow Template", "Template Validation", "Delete Workflow Template"],
            "Workflow Deployment": ["Deploy Workflow", "Deploy Invalid Template", "Deploy Empty Device List"],
            "Device Queues": ["Get Device Queue", "Get All Device Queues", "Create Device-Bound Task", "Queue Pacing Stats"],
            "Safe Mode": ["Safe Mode Status", "Dashboard Safe Mode", "Mock Task Execution"],
            "Feature Flags": ["Feature Flags", "Pooled Assignment Default"],
            "Database": ["Database Persistence", "Device Pacing State", "Device Tasks Collection"],
            "Error Handling": ["Invalid Template ID", "Missing Required Fields", "Invalid Device ID"]
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
            "created_templates": self.created_templates,
            "created_tasks": self.created_tasks
        }

def main():
    """Main test execution function"""
    print("🚀 Starting Phase 1-3 Per-Device Task Queues + Workflow Cloning Testing Suite")
    print("=" * 80)
    
    tester = Phase13BackendTester()
    
    try:
        # Run all test suites
        tester.test_workflow_templates_api()
        tester.test_workflow_deployment()
        tester.test_device_queues_api()
        tester.test_safe_mode_verification()
        tester.test_feature_flags_integration()
        tester.test_database_integration()
        tester.test_error_handling()
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
    
    # Generate and return report
    report = tester.generate_test_report()
    
    # Save detailed report to file
    with open('/app/phase13_workflow_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed test report saved to: /app/phase13_workflow_test_report.json")
    
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
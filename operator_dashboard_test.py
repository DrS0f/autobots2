#!/usr/bin/env python3
"""
Operator Dashboard + Phase 4 Integration Validation Test
Quick validation test to confirm Operator Dashboard functionality with Phase 4 Live Device Integration
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

class OperatorDashboardTester:
    """Focused tester for Operator Dashboard + Phase 4 Integration"""
    
    def __init__(self):
        self.test_results = []
        self.api_calls_made = 0
        
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
    
    def make_api_call(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make API call and track count"""
        self.api_calls_made += 1
        url = f"{API_BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "data": {},
                "error": str(e),
                "response_time_ms": 0
            }
    
    def test_dashboard_stats_api(self):
        """Test dashboard stats API for operator metrics"""
        print("\n=== Testing Dashboard Stats API ===")
        
        result = self.make_api_call("GET", "/dashboard/stats")
        
        if result["success"]:
            data = result["data"]
            required_fields = [
                "system_stats", "device_status", "queue_status", 
                "active_tasks", "recent_results", "license_status", "safe_mode_status"
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                # Check specific operator dashboard fields
                system_stats = data.get("system_stats", {})
                device_status = data.get("device_status", {})
                queue_status = data.get("queue_status", {})
                safe_mode_status = data.get("safe_mode_status", {})
                
                details = f"Dashboard stats API working. Response time: {result['response_time_ms']:.1f}ms. "
                details += f"System stats: {len(system_stats)} fields, "
                details += f"Device status: {device_status.get('total_devices', 0)} devices, "
                details += f"Queue: {queue_status.get('total_tasks', 0)} tasks, "
                details += f"Safe mode: {safe_mode_status.get('safe_mode', 'unknown')}"
                
                self.log_test_result("Dashboard Stats API", True, details)
                return True
            else:
                self.log_test_result("Dashboard Stats API", False, 
                                   error=f"Missing required fields: {missing_fields}")
                return False
        else:
            self.log_test_result("Dashboard Stats API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_device_status_apis(self):
        """Test device status APIs for device control table"""
        print("\n=== Testing Device Status APIs ===")
        
        # Test regular device status
        result = self.make_api_call("GET", "/devices/status")
        
        if result["success"]:
            data = result["data"]
            device_fields = ["total_devices", "ready_devices", "busy_devices", "error_devices"]
            
            has_required_fields = all(field in data for field in device_fields)
            
            if has_required_fields:
                details = f"Device status API working. "
                details += f"Total: {data.get('total_devices', 0)}, "
                details += f"Ready: {data.get('ready_devices', 0)}, "
                details += f"Busy: {data.get('busy_devices', 0)}, "
                details += f"Error: {data.get('error_devices', 0)}"
                
                self.log_test_result("Device Status API", True, details)
                device_status_success = True
            else:
                self.log_test_result("Device Status API", False, 
                                   error=f"Missing device status fields")
                device_status_success = False
        else:
            self.log_test_result("Device Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            device_status_success = False
        
        # Test live device status (Phase 4)
        result = self.make_api_call("GET", "/devices/status-live")
        
        if result["success"]:
            data = result["data"]
            if "devices" in data:
                devices = data["devices"]
                details = f"Live device status API working. Found {len(devices)} devices"
                self.log_test_result("Live Device Status API", True, details)
                live_status_success = True
            else:
                self.log_test_result("Live Device Status API", False, 
                                   error="Missing 'devices' field in response")
                live_status_success = False
        else:
            self.log_test_result("Live Device Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            live_status_success = False
        
        return device_status_success and live_status_success
    
    def test_task_management_apis(self):
        """Test task management APIs for quick actions"""
        print("\n=== Testing Task Management APIs ===")
        
        # Test queue status
        result = self.make_api_call("GET", "/tasks/queue/status")
        
        if result["success"]:
            data = result["data"]
            queue_fields = ["total_tasks", "pending_tasks", "running_tasks", "completed_tasks"]
            
            has_queue_info = any(field in data for field in queue_fields)
            
            if has_queue_info:
                details = f"Task queue status API working. "
                details += f"Total: {data.get('total_tasks', 0)}, "
                details += f"Pending: {data.get('pending_tasks', 0)}, "
                details += f"Running: {data.get('running_tasks', 0)}"
                
                self.log_test_result("Task Queue Status API", True, details)
                queue_success = True
            else:
                self.log_test_result("Task Queue Status API", False, 
                                   error="No queue information found in response")
                queue_success = False
        else:
            self.log_test_result("Task Queue Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            queue_success = False
        
        # Test device queues (Phase 1-3)
        result = self.make_api_call("GET", "/devices/queues/all")
        
        if result["success"]:
            data = result["data"]
            if "device_queues" in data and "statistics" in data:
                device_queues = data["device_queues"]
                statistics = data["statistics"]
                
                details = f"Device queues API working. "
                details += f"Device queues: {len(device_queues)}, "
                details += f"Statistics fields: {len(statistics)}"
                
                self.log_test_result("Device Queues API", True, details)
                device_queues_success = True
            else:
                self.log_test_result("Device Queues API", False, 
                                   error="Missing device_queues or statistics in response")
                device_queues_success = False
        else:
            self.log_test_result("Device Queues API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            device_queues_success = False
        
        return queue_success and device_queues_success
    
    def test_mode_management_apis(self):
        """Test Phase 4 Dual-Mode System APIs"""
        print("\n=== Testing Mode Management APIs ===")
        
        # Test mode status
        result = self.make_api_call("GET", "/system/mode-status")
        
        if result["success"]:
            data = result["data"]
            required_fields = ["current_mode", "live_mode_enabled", "features", "fallback_devices"]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                details = f"Mode status API working. "
                details += f"Current mode: {data.get('current_mode', 'unknown')}, "
                details += f"Live mode enabled: {data.get('live_mode_enabled', False)}, "
                details += f"Features: {len(data.get('features', {}))}, "
                details += f"Fallback devices: {len(data.get('fallback_devices', []))}"
                
                self.log_test_result("Mode Status API", True, details)
                mode_status_success = True
            else:
                self.log_test_result("Mode Status API", False, 
                                   error=f"Missing required fields: {missing_fields}")
                mode_status_success = False
        else:
            self.log_test_result("Mode Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            mode_status_success = False
        
        # Test safe mode status
        result = self.make_api_call("GET", "/system/safe-mode")
        
        if result["success"]:
            data = result["data"]
            if "safe_mode_status" in data:
                safe_mode_status = data["safe_mode_status"]
                
                details = f"Safe mode status API working. "
                details += f"Safe mode: {safe_mode_status.get('safe_mode', 'unknown')}, "
                details += f"Mock tasks completed: {safe_mode_status.get('mock_tasks_completed', 0)}"
                
                self.log_test_result("Safe Mode Status API", True, details)
                safe_mode_success = True
            else:
                self.log_test_result("Safe Mode Status API", False, 
                                   error="Missing safe_mode_status in response")
                safe_mode_success = False
        else:
            self.log_test_result("Safe Mode Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            safe_mode_success = False
        
        return mode_status_success and safe_mode_success
    
    def test_fallback_system_apis(self):
        """Test Phase 4 Fallback System APIs"""
        print("\n=== Testing Fallback System APIs ===")
        
        # Test fallback devices list
        result = self.make_api_call("GET", "/devices/fallback")
        
        if result["success"]:
            data = result["data"]
            if "fallback_devices" in data:
                fallback_devices = data["fallback_devices"]
                
                details = f"Fallback devices API working. "
                details += f"Fallback devices: {len(fallback_devices)}"
                
                self.log_test_result("Fallback Devices API", True, details)
                return True
            else:
                self.log_test_result("Fallback Devices API", False, 
                                   error="Missing fallback_devices in response")
                return False
        else:
            self.log_test_result("Fallback Devices API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_workflow_management_apis(self):
        """Test workflow management APIs for operator dashboard"""
        print("\n=== Testing Workflow Management APIs ===")
        
        # Test workflow templates list
        result = self.make_api_call("GET", "/workflows")
        
        if result["success"]:
            data = result["data"]
            if "templates" in data and "total_count" in data:
                templates = data["templates"]
                total_count = data["total_count"]
                
                details = f"Workflow templates API working. "
                details += f"Templates: {len(templates)}, Total count: {total_count}"
                
                self.log_test_result("Workflow Templates API", True, details)
                return True
            else:
                self.log_test_result("Workflow Templates API", False, 
                                   error="Missing templates or total_count in response")
                return False
        else:
            self.log_test_result("Workflow Templates API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            return False
    
    def test_settings_and_license_apis(self):
        """Test settings and license APIs for operator dashboard"""
        print("\n=== Testing Settings and License APIs ===")
        
        # Test settings API
        result = self.make_api_call("GET", "/settings")
        
        if result["success"]:
            data = result["data"]
            if "settings" in data:
                settings = data["settings"]
                
                details = f"Settings API working. "
                details += f"Settings fields: {len(settings)}"
                
                if "feature_flags" in settings:
                    feature_flags = settings["feature_flags"]
                    details += f", Feature flags: {len(feature_flags)}"
                
                self.log_test_result("Settings API", True, details)
                settings_success = True
            else:
                self.log_test_result("Settings API", False, 
                                   error="Missing settings in response")
                settings_success = False
        else:
            self.log_test_result("Settings API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            settings_success = False
        
        # Test license status API
        result = self.make_api_call("GET", "/license/status")
        
        if result["success"]:
            data = result["data"]
            if "license_status" in data:
                license_status = data["license_status"]
                
                details = f"License status API working. "
                details += f"Status: {license_status.get('status', 'unknown')}"
                
                self.log_test_result("License Status API", True, details)
                license_success = True
            else:
                self.log_test_result("License Status API", False, 
                                   error="Missing license_status in response")
                license_success = False
        else:
            self.log_test_result("License Status API", False, 
                               error=f"API call failed: {result.get('error', 'Unknown error')}")
            license_success = False
        
        return settings_success and license_success
    
    def run_operator_dashboard_validation(self):
        """Run complete operator dashboard validation"""
        print("🚀 OPERATOR DASHBOARD + PHASE 4 INTEGRATION VALIDATION")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base URL: {API_BASE_URL}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core API Validation
        print("\n📊 CORE API VALIDATION")
        dashboard_stats_success = self.test_dashboard_stats_api()
        device_status_success = self.test_device_status_apis()
        task_management_success = self.test_task_management_apis()
        
        # Operator Dashboard Data Flow
        print("\n🎛️ OPERATOR DASHBOARD DATA FLOW")
        workflow_success = self.test_workflow_management_apis()
        settings_license_success = self.test_settings_and_license_apis()
        
        # Phase 4 Dual-Mode System
        print("\n🔄 PHASE 4 DUAL-MODE SYSTEM")
        mode_management_success = self.test_mode_management_apis()
        fallback_system_success = self.test_fallback_system_apis()
        
        # Calculate results
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 OPERATOR DASHBOARD VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"✅ Tests Passed: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"🕒 Total Duration: {duration:.2f} seconds")
        print(f"🌐 API Calls Made: {self.api_calls_made}")
        print(f"⚡ Average Response Time: {sum(r.get('response_time_ms', 0) for r in [res for res in self.test_results if 'response_time_ms' in res]) / max(1, len([r for r in self.test_results if 'response_time_ms' in r])):.1f}ms")
        
        print("\n📊 COMPONENT STATUS:")
        print(f"  Dashboard Stats API: {'✅' if dashboard_stats_success else '❌'}")
        print(f"  Device Status APIs: {'✅' if device_status_success else '❌'}")
        print(f"  Task Management APIs: {'✅' if task_management_success else '❌'}")
        print(f"  Workflow Management: {'✅' if workflow_success else '❌'}")
        print(f"  Settings & License: {'✅' if settings_license_success else '❌'}")
        print(f"  Mode Management: {'✅' if mode_management_success else '❌'}")
        print(f"  Fallback System: {'✅' if fallback_system_success else '❌'}")
        
        # Detailed results
        print("\n📝 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test_name']}")
            if result["success"] and result["details"]:
                print(f"      {result['details']}")
            elif not result["success"] and result["error"]:
                print(f"      ❌ {result['error']}")
        
        # Overall assessment
        print("\n🎯 OPERATOR DASHBOARD READINESS:")
        if success_rate >= 90:
            print("  🟢 EXCELLENT - Operator Dashboard fully functional")
        elif success_rate >= 75:
            print("  🟡 GOOD - Operator Dashboard mostly functional with minor issues")
        elif success_rate >= 50:
            print("  🟠 FAIR - Operator Dashboard partially functional, needs attention")
        else:
            print("  🔴 POOR - Operator Dashboard has significant issues")
        
        print("\n" + "=" * 60)
        
        return {
            "success_rate": success_rate,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "duration": duration,
            "api_calls": self.api_calls_made,
            "component_status": {
                "dashboard_stats": dashboard_stats_success,
                "device_status": device_status_success,
                "task_management": task_management_success,
                "workflow_management": workflow_success,
                "settings_license": settings_license_success,
                "mode_management": mode_management_success,
                "fallback_system": fallback_system_success
            }
        }

def main():
    """Main test execution"""
    tester = OperatorDashboardTester()
    results = tester.run_operator_dashboard_validation()
    
    # Exit with appropriate code
    if results["success_rate"] >= 75:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
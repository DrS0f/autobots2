#!/usr/bin/env python3
"""
Backend Test Suite for Phase 5: SaaS Licensing & Kill-Switch
Tests all Phase 5 backend features including license server, license client integration, and API endpoints
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import subprocess
import signal

# Add backend to path
sys.path.append('/app/backend')
sys.path.append('/app/licensing')

# Import Phase 5 licensing modules
try:
    from license_client import LicenseClient, LicenseStatus
    from licensing.models import LicenseRequest, LicenseResponse, VerifyRequest, VerifyResponse
    from licensing.license_service import LicenseService
except ImportError as e:
    print(f"Warning: Could not import licensing modules: {e}")
    LicenseClient = None
    LicenseService = None

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://9b89d9f1-548e-4699-8ffa-55b25cb47e22.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"
LICENSE_SERVER_URL = "http://localhost:8002"

class Phase5BackendTester:
    """Comprehensive tester for Phase 5 backend features including licensing"""
    
    def __init__(self):
        self.test_results = []
        self.license_service = None
        self.license_server_process = None
        
        # License test data
        self.test_customer_id = "test_customer_001"
        self.test_license_key = None
        self.admin_token = "admin-token-change-this"
        self.test_device_id = "test_device_123"
        
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
    
    async def setup_license_server(self):
        """Start the license server for testing"""
        print("🔧 Starting license server...")
        
        try:
            # Set environment variables for license server
            env = os.environ.copy()
            env.update({
                'LICENSE_SECRET_KEY': 'test-secret-key-for-testing',
                'ADMIN_TOKEN': self.admin_token,
                'LICENSE_STORAGE_PATH': '/tmp/test_licenses.json'
            })
            
            # Start license server
            self.license_server_process = subprocess.Popen([
                sys.executable, '-m', 'uvicorn', 
                'licensing.server:app',
                '--host', '0.0.0.0',
                '--port', '8002'
            ], env=env, cwd='/app')
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test if server is running
            try:
                response = requests.get(f"{LICENSE_SERVER_URL}/", timeout=5)
                if response.status_code == 200:
                    self.log_test_result("License Server Startup", True, "License server started successfully")
                    return True
                else:
                    self.log_test_result("License Server Startup", False, error=f"Server returned {response.status_code}")
                    return False
            except Exception as e:
                self.log_test_result("License Server Startup", False, error=f"Server not responding: {e}")
                return False
                
        except Exception as e:
            self.log_test_result("License Server Startup", False, error=str(e))
            return False
    
    def cleanup_license_server(self):
        """Stop the license server"""
        if self.license_server_process:
            try:
                self.license_server_process.terminate()
                self.license_server_process.wait(timeout=5)
                print("🧹 License server stopped")
            except subprocess.TimeoutExpired:
                self.license_server_process.kill()
                print("🧹 License server killed")
            except Exception as e:
                print(f"⚠️ Warning: Could not stop license server: {e}")
    
    def test_license_service_core(self):
        """Test core license service functionality"""
        print("\n🔐 Testing License Service Core...")
        
        if not LicenseService:
            self.log_test_result("License Service Import", False, error="Could not import LicenseService")
            return
        
        # Test 1: Initialize license service
        try:
            self.license_service = LicenseService(
                secret_key="test-secret-key-for-testing",
                storage_path="/tmp/test_licenses.json"
            )
            self.log_test_result("License Service Initialization", True, "Service initialized successfully")
        except Exception as e:
            self.log_test_result("License Service Initialization", False, error=str(e))
            return
        
        # Test 2: Issue a license
        try:
            license_response = self.license_service.issue_license(
                customer_id=self.test_customer_id,
                plan="basic",
                features=["basic_automation"],
                device_id=self.test_device_id,
                duration_days=30,
                grace_days=7
            )
            
            if license_response.license_key:
                self.test_license_key = license_response.license_key
                self.log_test_result("Issue License", True, f"License issued for customer {self.test_customer_id}")
            else:
                self.log_test_result("Issue License", False, error="No license key returned")
        except Exception as e:
            self.log_test_result("Issue License", False, error=str(e))
        
        # Test 3: Verify valid license
        if self.test_license_key:
            try:
                verify_response = self.license_service.verify_license(
                    self.test_license_key, 
                    self.test_device_id
                )
                
                if verify_response.valid:
                    self.log_test_result("Verify Valid License", True, f"License valid: {verify_response.message}")
                else:
                    self.log_test_result("Verify Valid License", False, error=f"License invalid: {verify_response.message}")
            except Exception as e:
                self.log_test_result("Verify Valid License", False, error=str(e))
        
        # Test 4: Verify invalid license
        try:
            verify_response = self.license_service.verify_license(
                "invalid.license.key", 
                self.test_device_id
            )
            
            if not verify_response.valid:
                self.log_test_result("Verify Invalid License", True, f"Correctly rejected: {verify_response.message}")
            else:
                self.log_test_result("Verify Invalid License", False, error="Invalid license was accepted")
        except Exception as e:
            self.log_test_result("Verify Invalid License", False, error=str(e))
        
        # Test 5: Device binding check
        if self.test_license_key:
            try:
                verify_response = self.license_service.verify_license(
                    self.test_license_key, 
                    "wrong_device_id"
                )
                
                if not verify_response.valid and "device" in verify_response.message:
                    self.log_test_result("Device Binding Check", True, f"Device binding enforced: {verify_response.message}")
                else:
                    self.log_test_result("Device Binding Check", False, error="Device binding not enforced")
            except Exception as e:
                self.log_test_result("Device Binding Check", False, error=str(e))
        
        # Test 6: List licenses
        try:
            licenses = self.license_service.list_licenses()
            if isinstance(licenses, list) and len(licenses) > 0:
                self.log_test_result("List Licenses", True, f"Found {len(licenses)} licenses")
            else:
                self.log_test_result("List Licenses", False, error="No licenses found")
        except Exception as e:
            self.log_test_result("List Licenses", False, error=str(e))
        
        # Test 7: Revoke license
        if self.test_license_key:
            try:
                revoke_success = self.license_service.revoke_license(
                    self.test_license_key, 
                    "Test revocation"
                )
                
                if revoke_success:
                    self.log_test_result("Revoke License", True, "License revoked successfully")
                    
                    # Verify revoked license is invalid
                    verify_response = self.license_service.verify_license(
                        self.test_license_key, 
                        self.test_device_id
                    )
                    
                    if not verify_response.valid and "revoked" in verify_response.message:
                        self.log_test_result("Verify Revoked License", True, "Revoked license correctly rejected")
                    else:
                        self.log_test_result("Verify Revoked License", False, error="Revoked license still valid")
                else:
                    self.log_test_result("Revoke License", False, error="Failed to revoke license")
            except Exception as e:
                self.log_test_result("Revoke License", False, error=str(e))
    
    def test_license_server_api(self):
        """Test license server API endpoints"""
        print("\n🌐 Testing License Server API...")
        
        # Test 1: Server health check
        try:
            response = requests.get(f"{LICENSE_SERVER_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "License Server" in data.get('service', ''):
                    self.log_test_result("License Server Health", True, "Server is running")
                else:
                    self.log_test_result("License Server Health", False, error="Unexpected response")
            else:
                self.log_test_result("License Server Health", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("License Server Health", False, error=str(e))
        
        # Test 2: Issue license via API (admin endpoint)
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            license_request = {
                "customer_id": "api_test_customer",
                "plan": "premium",
                "features": ["basic_automation", "advanced_features"],
                "device_id": "api_test_device",
                "duration_days": 60,
                "grace_days": 14
            }
            
            response = requests.post(
                f"{LICENSE_SERVER_URL}/auth/issue",
                json=license_request,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('license_key'):
                    self.test_license_key = data['license_key']  # Update for further tests
                    self.log_test_result("API Issue License", True, f"License issued via API for {license_request['customer_id']}")
                else:
                    self.log_test_result("API Issue License", False, error="No license key in response")
            else:
                self.log_test_result("API Issue License", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("API Issue License", False, error=str(e))
        
        # Test 3: Verify license via API (public endpoint)
        if self.test_license_key:
            try:
                params = {
                    "license_key": self.test_license_key,
                    "device_id": "api_test_device"
                }
                
                response = requests.get(
                    f"{LICENSE_SERVER_URL}/auth/verify",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('valid'):
                        self.log_test_result("API Verify License", True, f"License verified: {data.get('message', '')}")
                    else:
                        self.log_test_result("API Verify License", False, error=f"License invalid: {data.get('message', '')}")
                else:
                    self.log_test_result("API Verify License", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test_result("API Verify License", False, error=str(e))
        
        # Test 4: List licenses via API (admin endpoint)
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{LICENSE_SERVER_URL}/admin/licenses",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test_result("API List Licenses", True, f"Retrieved {len(data)} licenses")
                else:
                    self.log_test_result("API List Licenses", False, error="Invalid response format")
            else:
                self.log_test_result("API List Licenses", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("API List Licenses", False, error=str(e))
        
        # Test 5: Revoke license via API (admin endpoint)
        if self.test_license_key:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                revoke_request = {
                    "license_key": self.test_license_key,
                    "reason": "API test revocation"
                }
                
                response = requests.post(
                    f"{LICENSE_SERVER_URL}/auth/revoke",
                    json=revoke_request,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log_test_result("API Revoke License", True, "License revoked via API")
                    else:
                        self.log_test_result("API Revoke License", False, error="Revocation failed")
                else:
                    self.log_test_result("API Revoke License", False, error=f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test_result("API Revoke License", False, error=str(e))
        
        # Test 6: Admin authentication check
        try:
            headers = {"Authorization": "Bearer invalid-token"}
            response = requests.get(
                f"{LICENSE_SERVER_URL}/admin/licenses",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test_result("Admin Auth Check", True, "Invalid token correctly rejected")
            else:
                self.log_test_result("Admin Auth Check", False, error=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Admin Auth Check", False, error=str(e))
    
    async def test_license_client_integration(self):
        """Test license client integration"""
        print("\n🔗 Testing License Client Integration...")
        
        if not LicenseClient:
            self.log_test_result("License Client Import", False, error="Could not import LicenseClient")
            return
        
        # Test 1: License client initialization (no license key)
        try:
            # Test without license key
            os.environ.pop('LICENSE_KEY', None)
            client = LicenseClient()
            
            if client.status == LicenseStatus.OK:
                self.log_test_result("License Client - No Key Required", True, "Client correctly allows operation without license")
            else:
                self.log_test_result("License Client - No Key Required", False, error=f"Wrong status: {client.status}")
        except Exception as e:
            self.log_test_result("License Client - No Key Required", False, error=str(e))
        
        # Test 2: License client with invalid key
        try:
            os.environ['LICENSE_KEY'] = 'invalid.license.key'
            os.environ['LICENSE_API_URL'] = LICENSE_SERVER_URL
            
            client = LicenseClient()
            
            if client.status == LicenseStatus.LOCKED:
                self.log_test_result("License Client - Invalid Key", True, "Client correctly locked with invalid key")
            else:
                self.log_test_result("License Client - Invalid Key", False, error=f"Wrong status: {client.status}")
        except Exception as e:
            self.log_test_result("License Client - Invalid Key", False, error=str(e))
        
        # Test 3: Get license status
        try:
            client = LicenseClient()
            status = client.get_status()
            
            if isinstance(status, dict) and 'status' in status:
                self.log_test_result("License Client - Get Status", True, f"Status: {status['status']}")
            else:
                self.log_test_result("License Client - Get Status", False, error="Invalid status format")
        except Exception as e:
            self.log_test_result("License Client - Get Status", False, error=str(e))
        
        # Test 4: License verification with valid key (if available)
        if self.test_license_key:
            try:
                # Issue a new valid license for testing
                if self.license_service:
                    license_response = self.license_service.issue_license(
                        customer_id="client_test_customer",
                        plan="basic",
                        features=["basic_automation"],
                        device_id="client_test_device",
                        duration_days=1,  # Short duration for testing
                        grace_days=1
                    )
                    
                    os.environ['LICENSE_KEY'] = license_response.license_key
                    client = LicenseClient()
                    
                    # Perform immediate verification
                    await client._verify_now()
                    
                    if client.status == LicenseStatus.OK:
                        self.log_test_result("License Client - Valid Key", True, "Client correctly validated license")
                    else:
                        self.log_test_result("License Client - Valid Key", False, error=f"Wrong status: {client.status}")
            except Exception as e:
                self.log_test_result("License Client - Valid Key", False, error=str(e))
    
    def test_backend_license_integration(self):
        """Test backend integration with license system"""
        print("\n🔧 Testing Backend License Integration...")
        
        # Test 1: License status API endpoint
        try:
            response = requests.get(f"{API_BASE_URL}/license/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'license_status' in data:
                    status = data['license_status']
                    self.log_test_result("Backend License Status API", True, f"License status: {status.get('status', 'unknown')}")
                else:
                    self.log_test_result("Backend License Status API", False, error="Invalid response format")
            else:
                self.log_test_result("Backend License Status API", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Backend License Status API", False, error=str(e))
        
        # Test 2: License verification API endpoint
        try:
            response = requests.post(f"{API_BASE_URL}/license/verify", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'license_status' in data:
                    self.log_test_result("Backend License Verify API", True, "License verification endpoint working")
                else:
                    self.log_test_result("Backend License Verify API", False, error="Invalid response format")
            else:
                self.log_test_result("Backend License Verify API", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Backend License Verify API", False, error=str(e))
        
        # Test 3: Dashboard stats include license information
        try:
            response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'license_status' in data:
                    self.log_test_result("Dashboard License Integration", True, "License status included in dashboard")
                else:
                    self.log_test_result("Dashboard License Integration", False, error="License status not in dashboard")
            else:
                self.log_test_result("Dashboard License Integration", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Dashboard License Integration", False, error=str(e))
    
    def test_task_creation_license_enforcement(self):
        """Test task creation blocking when unlicensed"""
        print("\n🚫 Testing Task Creation License Enforcement...")
        
        # Test 1: Task creation with no license (should work)
        try:
            os.environ.pop('LICENSE_KEY', None)  # Remove license key
            
            task_request = {
                "target_username": "testuser",
                "actions": ["search_user", "view_profile"],
                "max_likes": 1,
                "max_follows": 0,
                "priority": "normal"
            }
            
            response = requests.post(f"{API_BASE_URL}/tasks/create", json=task_request, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('task_id'):
                    self.log_test_result("Task Creation - No License Required", True, f"Task created: {data['task_id']}")
                else:
                    self.log_test_result("Task Creation - No License Required", False, error="No task ID returned")
            else:
                self.log_test_result("Task Creation - No License Required", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Task Creation - No License Required", False, error=str(e))
        
        # Test 2: Task creation with invalid license (should be blocked)
        try:
            os.environ['LICENSE_KEY'] = 'invalid.license.key'
            
            # Wait a moment for license client to update
            time.sleep(2)
            
            response = requests.post(f"{API_BASE_URL}/tasks/create", json=task_request, timeout=10)
            if response.status_code == 403:
                self.log_test_result("Task Creation - Invalid License Block", True, "Task creation correctly blocked")
            else:
                self.log_test_result("Task Creation - Invalid License Block", False, error=f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Task Creation - Invalid License Block", False, error=str(e))
        
        # Test 3: Engagement task creation with invalid license (should be blocked)
        try:
            engagement_request = {
                "target_pages": ["testpage1", "testpage2"],
                "comment_list": ["Nice post!", "Great content!"],
                "actions": {"follow": True, "like": True, "comment": False},
                "max_users_per_page": 5,
                "skip_rate": 0.1,
                "priority": "normal"
            }
            
            response = requests.post(f"{API_BASE_URL}/engagement-task", json=engagement_request, timeout=10)
            if response.status_code == 403:
                self.log_test_result("Engagement Task Creation - Invalid License Block", True, "Engagement task creation correctly blocked")
            else:
                self.log_test_result("Engagement Task Creation - Invalid License Block", False, error=f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Engagement Task Creation - Invalid License Block", False, error=str(e))
    
    def test_license_states_and_grace_period(self):
        """Test different license states and grace period behavior"""
        print("\n⏰ Testing License States and Grace Period...")
        
        if not self.license_service:
            self.log_test_result("License States Test Setup", False, error="License service not available")
            return
        
        # Test 1: Create license with short expiry
        try:
            # Create a license that expires in 1 second
            from datetime import datetime, timezone, timedelta
            import jwt
            
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=1)
            
            payload = {
                "sub": "grace_test_customer",
                "license_id": "grace_test_license",
                "plan": "basic",
                "features": ["basic_automation"],
                "device_id": "grace_test_device",
                "exp": expires_at.timestamp(),
                "iat": now.timestamp(),
                "grace_days": 1
            }
            
            expired_license_key = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")
            
            # Wait for license to expire
            time.sleep(2)
            
            # Verify expired license (should be in grace period)
            verify_response = self.license_service.verify_license(expired_license_key, "grace_test_device")
            
            if verify_response.valid and verify_response.in_grace_period:
                self.log_test_result("Grace Period Test", True, f"License in grace period: {verify_response.message}")
            else:
                self.log_test_result("Grace Period Test", False, error=f"Grace period not working: {verify_response.message}")
                
        except Exception as e:
            self.log_test_result("Grace Period Test", False, error=str(e))
        
        # Test 2: Test completely expired license (past grace period)
        try:
            # Create a license that expired more than grace period ago
            now = datetime.now(timezone.utc)
            expires_at = now - timedelta(days=2)  # Expired 2 days ago
            
            payload = {
                "sub": "expired_test_customer",
                "license_id": "expired_test_license",
                "plan": "basic",
                "features": ["basic_automation"],
                "device_id": "expired_test_device",
                "exp": expires_at.timestamp(),
                "iat": (now - timedelta(days=3)).timestamp(),
                "grace_days": 1  # 1 day grace period
            }
            
            expired_license_key = jwt.encode(payload, "test-secret-key-for-testing", algorithm="HS256")
            
            verify_response = self.license_service.verify_license(expired_license_key, "expired_test_device")
            
            if not verify_response.valid and "expired" in verify_response.message:
                self.log_test_result("Expired License Test", True, f"Expired license correctly rejected: {verify_response.message}")
            else:
                self.log_test_result("Expired License Test", False, error=f"Expired license not rejected: {verify_response.message}")
                
        except Exception as e:
            self.log_test_result("Expired License Test", False, error=str(e))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Phase 5 License System Test Report")
        print("=" * 60)
        
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
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "results": self.test_results
        }

async def main():
    """Main test execution function"""
    print("🚀 Starting Phase 5 SaaS Licensing & Kill-Switch Testing Suite")
    print("=" * 70)
    
    tester = Phase5BackendTester()
    
    try:
        # Setup license server
        if not await tester.setup_license_server():
            print("❌ Failed to setup license server. Some tests will be skipped.")
        
        # Run all test suites
        tester.test_license_service_core()
        tester.test_license_server_api()
        tester.test_license_client_integration()
        tester.test_backend_license_integration()
        tester.test_task_creation_license_enforcement()
        tester.test_license_states_and_grace_period()
        
    finally:
        # Always cleanup
        tester.cleanup_license_server()
    
    # Generate and return report
    report = tester.generate_test_report()
    
    # Save detailed report to file
    with open('/app/phase5_license_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed test report saved to: /app/phase5_license_test_report.json")
    
    return report

if __name__ == "__main__":
    # Run the test suite
    report = asyncio.run(main())
    
    # Exit with appropriate code
    if report['failed_tests'] > 0:
        print(f"\n❌ Testing completed with {report['failed_tests']} failures")
        sys.exit(1)
    else:
        print(f"\n✅ All {report['passed_tests']} tests passed successfully!")
        sys.exit(0)
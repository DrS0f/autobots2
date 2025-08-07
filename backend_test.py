#!/usr/bin/env python3
"""
Backend Test Suite for Phase 4: Session Integrity & Fail-Safe Crawler Behavior
Tests all Phase 4 backend features including database models, deduplication, error handling, and API endpoints
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import pytest
from motor.motor_asyncio import AsyncIOMotorClient

# Add backend to path
sys.path.append('/app/backend')

# Import Phase 4 modules
from ios_automation.database_models import (
    DatabaseManager, InteractionEvent, LatestInteraction, 
    InteractionAction, InteractionStatus, get_db_manager, init_database
)
from ios_automation.deduplication_service import (
    DeduplicationService, get_deduplication_service,
    should_engage_user, record_successful_engagement, record_failed_engagement
)
from ios_automation.error_handling import (
    ErrorHandler, ErrorType, AccountState, get_error_handler,
    handle_automation_error, is_account_ready, mark_interaction_success
)
from ios_automation.account_execution_manager import (
    AccountExecutionManager, AccountExecutionState, AccountExecutionInfo, get_execution_manager
)

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://6c5138b3-5167-4119-a029-29051836ac8d.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class Phase4BackendTester:
    """Comprehensive tester for Phase 4 backend features"""
    
    def __init__(self):
        self.test_results = []
        self.db_manager = None
        self.dedup_service = None
        self.error_handler = None
        self.execution_manager = None
        
        # Test data
        self.test_account_id = "test_account_123"
        self.test_device_id = "test_device_456"
        self.test_task_id = "test_task_789"
        self.test_usernames = ["testuser1", "testuser2", "testuser3"]
        
    async def setup_test_environment(self):
        """Setup test environment and initialize services"""
        print("🔧 Setting up test environment...")
        
        try:
            # Initialize database
            await init_database()
            
            # Get service instances
            self.db_manager = get_db_manager()
            self.dedup_service = get_deduplication_service()
            self.error_handler = get_error_handler()
            
            # Clean up any existing test data
            await self._cleanup_test_data()
            
            print("✅ Test environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return False
    
    async def _cleanup_test_data(self):
        """Clean up test data from previous runs"""
        try:
            # Clean up test interactions
            await self.db_manager.interactions_events.delete_many({
                "account_id": self.test_account_id
            })
            await self.db_manager.interactions_latest.delete_many({
                "account_id": self.test_account_id
            })
            
            # Reset error handler state for test account
            if self.test_account_id in self.error_handler.account_states:
                del self.error_handler.account_states[self.test_account_id]
                
            print("🧹 Test data cleanup complete")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test data: {e}")
    
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
    
    async def test_database_models(self):
        """Test Phase 4 database models and operations"""
        print("\n📊 Testing Database Models...")
        
        # Test 1: Database connection and indexes
        try:
            await self.db_manager.ensure_indexes()
            self.log_test_result("Database Indexes Creation", True, "All indexes created successfully")
        except Exception as e:
            self.log_test_result("Database Indexes Creation", False, error=str(e))
            return
        
        # Test 2: Record interaction event
        try:
            event = InteractionEvent(
                account_id=self.test_account_id,
                target_username="testuser1",
                action="follow",
                status="success",
                reason="test_interaction",
                task_id=self.test_task_id,
                device_id=self.test_device_id,
                latency_ms=150
            )
            
            success = await self.db_manager.record_interaction_event(event)
            if success:
                self.log_test_result("Record Interaction Event", True, "Event recorded successfully")
            else:
                self.log_test_result("Record Interaction Event", False, error="Failed to record event")
        except Exception as e:
            self.log_test_result("Record Interaction Event", False, error=str(e))
        
        # Test 3: Upsert latest interaction
        try:
            latest = LatestInteraction(
                account_id=self.test_account_id,
                target_username="testuser1",
                action="follow",
                last_status="success"
            )
            
            success = await self.db_manager.upsert_latest_interaction(latest)
            if success:
                self.log_test_result("Upsert Latest Interaction", True, "Latest interaction upserted")
            else:
                self.log_test_result("Upsert Latest Interaction", False, error="Failed to upsert")
        except Exception as e:
            self.log_test_result("Upsert Latest Interaction", False, error=str(e))
        
        # Test 4: Check interaction exists
        try:
            existing = await self.db_manager.check_interaction_exists(
                self.test_account_id, "testuser1", "follow"
            )
            if existing:
                self.log_test_result("Check Interaction Exists", True, f"Found interaction: {existing.last_status}")
            else:
                self.log_test_result("Check Interaction Exists", False, error="Expected interaction not found")
        except Exception as e:
            self.log_test_result("Check Interaction Exists", False, error=str(e))
        
        # Test 5: Query interaction events
        try:
            events = await self.db_manager.get_interaction_events(
                account_id=self.test_account_id,
                limit=10
            )
            if events:
                self.log_test_result("Query Interaction Events", True, f"Retrieved {len(events)} events")
            else:
                self.log_test_result("Query Interaction Events", False, error="No events found")
        except Exception as e:
            self.log_test_result("Query Interaction Events", False, error=str(e))
        
        # Test 6: Get interaction metrics
        try:
            metrics = await self.db_manager.get_interaction_metrics(
                account_id=self.test_account_id
            )
            if isinstance(metrics, dict):
                self.log_test_result("Get Interaction Metrics", True, f"Metrics: {metrics.get('total_interactions', 0)} total")
            else:
                self.log_test_result("Get Interaction Metrics", False, error="Invalid metrics format")
        except Exception as e:
            self.log_test_result("Get Interaction Metrics", False, error=str(e))
        
        # Test 7: Settings management
        try:
            # Get default settings
            settings = await self.db_manager.get_settings()
            if settings and 'reengagement_days' in settings:
                self.log_test_result("Get Settings", True, f"Default reengagement: {settings['reengagement_days']} days")
            else:
                self.log_test_result("Get Settings", False, error="Invalid settings format")
            
            # Update settings
            update_success = await self.db_manager.update_settings({
                "reengagement_days": 45,
                "cooldown_minutes": 60
            })
            if update_success:
                self.log_test_result("Update Settings", True, "Settings updated successfully")
            else:
                self.log_test_result("Update Settings", False, error="Failed to update settings")
        except Exception as e:
            self.log_test_result("Settings Management", False, error=str(e))
    
    async def test_deduplication_service(self):
        """Test deduplication service functionality"""
        print("\n🔄 Testing Deduplication Service...")
        
        # Test 1: Should engage check (new user)
        try:
            should_engage, reason = await self.dedup_service.should_engage(
                self.test_account_id, "newuser", "follow", self.test_task_id, self.test_device_id
            )
            if should_engage:
                self.log_test_result("Should Engage - New User", True, f"Allowed: {reason}")
            else:
                self.log_test_result("Should Engage - New User", False, error=f"Unexpected block: {reason}")
        except Exception as e:
            self.log_test_result("Should Engage - New User", False, error=str(e))
        
        # Test 2: Record successful interaction
        try:
            success = await self.dedup_service.record_successful_interaction(
                self.test_account_id, "newuser", "follow", self.test_task_id, self.test_device_id, 200
            )
            if success:
                self.log_test_result("Record Successful Interaction", True, "Interaction recorded")
            else:
                self.log_test_result("Record Successful Interaction", False, error="Failed to record")
        except Exception as e:
            self.log_test_result("Record Successful Interaction", False, error=str(e))
        
        # Test 3: Should engage check (existing user - should be blocked)
        try:
            should_engage, reason = await self.dedup_service.should_engage(
                self.test_account_id, "newuser", "follow", self.test_task_id, self.test_device_id
            )
            if not should_engage and "dedupe_hit" in reason:
                self.log_test_result("Should Engage - Existing User", True, f"Correctly blocked: {reason}")
            else:
                self.log_test_result("Should Engage - Existing User", False, error=f"Should be blocked: {reason}")
        except Exception as e:
            self.log_test_result("Should Engage - Existing User", False, error=str(e))
        
        # Test 4: Record failed interaction
        try:
            success = await self.dedup_service.record_failed_interaction(
                self.test_account_id, "faileduser", "like", InteractionStatus.PRIVATE_ACCOUNT,
                "account_is_private", self.test_task_id, self.test_device_id, 100
            )
            if success:
                self.log_test_result("Record Failed Interaction", True, "Failed interaction recorded")
            else:
                self.log_test_result("Record Failed Interaction", False, error="Failed to record")
        except Exception as e:
            self.log_test_result("Record Failed Interaction", False, error=str(e))
        
        # Test 5: Bulk check users
        try:
            users_and_actions = [
                ("bulkuser1", "follow"),
                ("bulkuser2", "like"),
                ("newuser", "follow")  # This should be blocked
            ]
            
            results = await self.dedup_service.bulk_check_users(
                self.test_account_id, users_and_actions, self.test_task_id
            )
            
            if len(results) == 3:
                blocked_count = sum(1 for should_engage, _ in results.values() if not should_engage)
                self.log_test_result("Bulk Check Users", True, f"Checked 3 users, {blocked_count} blocked")
            else:
                self.log_test_result("Bulk Check Users", False, error=f"Expected 3 results, got {len(results)}")
        except Exception as e:
            self.log_test_result("Bulk Check Users", False, error=str(e))
        
        # Test 6: Get user interaction history
        try:
            history = await self.dedup_service.get_user_interaction_history(
                self.test_account_id, "newuser", limit=5
            )
            if isinstance(history, list):
                self.log_test_result("Get User History", True, f"Retrieved {len(history)} history entries")
            else:
                self.log_test_result("Get User History", False, error="Invalid history format")
        except Exception as e:
            self.log_test_result("Get User History", False, error=str(e))
        
        # Test 7: Service statistics
        try:
            stats = self.dedup_service.get_stats()
            if isinstance(stats, dict) and 'total_checks' in stats:
                self.log_test_result("Get Service Stats", True, f"Total checks: {stats['total_checks']}")
            else:
                self.log_test_result("Get Service Stats", False, error="Invalid stats format")
        except Exception as e:
            self.log_test_result("Get Service Stats", False, error=str(e))
    
    async def test_error_handling(self):
        """Test advanced error handling functionality"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test 1: Error type detection
        try:
            error_type = self.error_handler.detect_error_type("action blocked try again later")
            if error_type == ErrorType.RATE_LIMITED:
                self.log_test_result("Error Type Detection - Rate Limited", True, "Correctly detected rate limit")
            else:
                self.log_test_result("Error Type Detection - Rate Limited", False, error=f"Wrong type: {error_type}")
        except Exception as e:
            self.log_test_result("Error Type Detection - Rate Limited", False, error=str(e))
        
        # Test 2: Private account detection
        try:
            error_type = self.error_handler.detect_error_type("this account is private")
            if error_type == ErrorType.PRIVATE_ACCOUNT:
                self.log_test_result("Error Type Detection - Private Account", True, "Correctly detected private account")
            else:
                self.log_test_result("Error Type Detection - Private Account", False, error=f"Wrong type: {error_type}")
        except Exception as e:
            self.log_test_result("Error Type Detection - Private Account", False, error=str(e))
        
        # Test 3: Handle rate limit error
        try:
            should_retry, delay, reason = await self.error_handler.handle_error(
                "action blocked try again later",
                self.test_account_id, self.test_device_id, self.test_task_id
            )
            if should_retry and delay > 0:
                self.log_test_result("Handle Rate Limit Error", True, f"Retry in {delay}s: {reason}")
            else:
                self.log_test_result("Handle Rate Limit Error", False, error=f"Unexpected response: retry={should_retry}, delay={delay}")
        except Exception as e:
            self.log_test_result("Handle Rate Limit Error", False, error=str(e))
        
        # Test 4: Handle private account error
        try:
            should_retry, delay, reason = await self.error_handler.handle_error(
                "this account is private",
                self.test_account_id, self.test_device_id, self.test_task_id
            )
            if not should_retry:
                self.log_test_result("Handle Private Account Error", True, f"Correctly no retry: {reason}")
            else:
                self.log_test_result("Handle Private Account Error", False, error=f"Should not retry private account")
        except Exception as e:
            self.log_test_result("Handle Private Account Error", False, error=str(e))
        
        # Test 5: Account availability check
        try:
            available, reason = await self.error_handler.is_account_available(self.test_account_id)
            if available:
                self.log_test_result("Account Availability Check", True, f"Account available: {reason}")
            else:
                self.log_test_result("Account Availability Check", False, error=f"Account not available: {reason}")
        except Exception as e:
            self.log_test_result("Account Availability Check", False, error=str(e))
        
        # Test 6: Multiple rate limit errors (trigger cooldown)
        try:
            # Simulate multiple consecutive rate limit errors
            for i in range(4):  # Should trigger cooldown after 3 (default)
                await self.error_handler.handle_error(
                    "action blocked try again later",
                    self.test_account_id, self.test_device_id, f"task_{i}"
                )
            
            # Check if account is now in cooldown
            available, reason = await self.error_handler.is_account_available(self.test_account_id)
            if not available and "cooldown" in reason:
                self.log_test_result("Cooldown Trigger", True, f"Account in cooldown: {reason}")
            else:
                self.log_test_result("Cooldown Trigger", False, error=f"Expected cooldown: {reason}")
        except Exception as e:
            self.log_test_result("Cooldown Trigger", False, error=str(e))
        
        # Test 7: Reset account errors
        try:
            await self.error_handler.reset_account_errors(self.test_account_id)
            account_state = self.error_handler.get_account_state(self.test_account_id)
            if account_state and account_state.consecutive_errors == 0:
                self.log_test_result("Reset Account Errors", True, "Errors reset successfully")
            else:
                self.log_test_result("Reset Account Errors", False, error="Errors not reset")
        except Exception as e:
            self.log_test_result("Reset Account Errors", False, error=str(e))
        
        # Test 8: Get error statistics
        try:
            stats = self.error_handler.get_error_stats()
            if isinstance(stats, dict) and 'total_errors' in stats:
                self.log_test_result("Get Error Stats", True, f"Total errors: {stats['total_errors']}")
            else:
                self.log_test_result("Get Error Stats", False, error="Invalid stats format")
        except Exception as e:
            self.log_test_result("Get Error Stats", False, error=str(e))
    
    def test_api_endpoints(self):
        """Test Phase 4 API endpoints"""
        print("\n🌐 Testing API Endpoints...")
        
        # Test 1: Get settings
        try:
            response = requests.get(f"{API_BASE_URL}/settings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'settings' in data:
                    self.log_test_result("GET /api/settings", True, f"Retrieved settings: {data['settings'].get('reengagement_days')} days")
                else:
                    self.log_test_result("GET /api/settings", False, error="Invalid response format")
            else:
                self.log_test_result("GET /api/settings", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/settings", False, error=str(e))
        
        # Test 2: Update settings
        try:
            settings_update = {
                "reengagement_days": 35,
                "cooldown_minutes": 50
            }
            response = requests.put(f"{API_BASE_URL}/settings", json=settings_update, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test_result("PUT /api/settings", True, "Settings updated successfully")
                else:
                    self.log_test_result("PUT /api/settings", False, error="Update failed")
            else:
                self.log_test_result("PUT /api/settings", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("PUT /api/settings", False, error=str(e))
        
        # Test 3: Get interaction events
        try:
            params = {
                "account_id": self.test_account_id,
                "limit": 10
            }
            response = requests.get(f"{API_BASE_URL}/interactions/events", params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'events' in data:
                    self.log_test_result("GET /api/interactions/events", True, f"Retrieved {data['count']} events")
                else:
                    self.log_test_result("GET /api/interactions/events", False, error="Invalid response format")
            else:
                self.log_test_result("GET /api/interactions/events", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/interactions/events", False, error=str(e))
        
        # Test 4: Export interactions (CSV)
        try:
            params = {
                "format": "csv",
                "account_id": self.test_account_id
            }
            response = requests.get(f"{API_BASE_URL}/interactions/export", params=params, timeout=10)
            if response.status_code == 200:
                if response.headers.get('content-type') == 'text/csv':
                    self.log_test_result("GET /api/interactions/export (CSV)", True, f"CSV export: {len(response.content)} bytes")
                else:
                    self.log_test_result("GET /api/interactions/export (CSV)", False, error="Not CSV format")
            else:
                self.log_test_result("GET /api/interactions/export (CSV)", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/interactions/export (CSV)", False, error=str(e))
        
        # Test 5: Export interactions (JSON)
        try:
            params = {
                "format": "json",
                "account_id": self.test_account_id
            }
            response = requests.get(f"{API_BASE_URL}/interactions/export", params=params, timeout=10)
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/json':
                    data = response.json()
                    if 'events' in data:
                        self.log_test_result("GET /api/interactions/export (JSON)", True, f"JSON export: {data['total_events']} events")
                    else:
                        self.log_test_result("GET /api/interactions/export (JSON)", False, error="Invalid JSON format")
                else:
                    self.log_test_result("GET /api/interactions/export (JSON)", False, error="Not JSON format")
            else:
                self.log_test_result("GET /api/interactions/export (JSON)", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/interactions/export (JSON)", False, error=str(e))
        
        # Test 6: Get metrics
        try:
            response = requests.get(f"{API_BASE_URL}/metrics", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'metrics' in data:
                    metrics = data['metrics']
                    self.log_test_result("GET /api/metrics", True, f"Metrics retrieved: interactions, deduplication, errors")
                else:
                    self.log_test_result("GET /api/metrics", False, error="Invalid response format")
            else:
                self.log_test_result("GET /api/metrics", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/metrics", False, error=str(e))
        
        # Test 7: Get account states
        try:
            response = requests.get(f"{API_BASE_URL}/accounts/states", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'account_states' in data:
                    states = data['account_states']
                    self.log_test_result("GET /api/accounts/states", True, f"Account states: {len(states)} accounts")
                else:
                    self.log_test_result("GET /api/accounts/states", False, error="Invalid response format")
            else:
                self.log_test_result("GET /api/accounts/states", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("GET /api/accounts/states", False, error=str(e))
        
        # Test 8: Cleanup expired interactions
        try:
            response = requests.post(f"{API_BASE_URL}/interactions/cleanup", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test_result("POST /api/interactions/cleanup", True, data.get('message', 'Cleanup completed'))
                else:
                    self.log_test_result("POST /api/interactions/cleanup", False, error="Cleanup failed")
            else:
                self.log_test_result("POST /api/interactions/cleanup", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("POST /api/interactions/cleanup", False, error=str(e))
    
    def test_integration_points(self):
        """Test integration with existing automation system"""
        print("\n🔗 Testing Integration Points...")
        
        # Test 1: Basic API connectivity
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "iOS Instagram Automation API" in data.get('message', ''):
                    self.log_test_result("API Connectivity", True, "API is running and accessible")
                else:
                    self.log_test_result("API Connectivity", False, error="Unexpected API response")
            else:
                self.log_test_result("API Connectivity", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("API Connectivity", False, error=str(e))
        
        # Test 2: System health check
        try:
            response = requests.get(f"{API_BASE_URL}/system/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    self.log_test_result("System Health Check", True, f"System status: {data['status']}")
                else:
                    self.log_test_result("System Health Check", False, error="Invalid health response")
            else:
                self.log_test_result("System Health Check", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("System Health Check", False, error=str(e))
        
        # Test 3: Dashboard stats (existing endpoint)
        try:
            response = requests.get(f"{API_BASE_URL}/dashboard/stats", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'system_stats' in data:
                    self.log_test_result("Dashboard Stats Integration", True, "Dashboard stats accessible")
                else:
                    self.log_test_result("Dashboard Stats Integration", False, error="Invalid dashboard response")
            else:
                self.log_test_result("Dashboard Stats Integration", False, error=f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test_result("Dashboard Stats Integration", False, error=str(e))
    
    async def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        try:
            await self._cleanup_test_data()
            
            # Close database connections
            if self.db_manager:
                await self.db_manager.close()
            
            print("✅ Test environment cleanup complete")
            
        except Exception as e:
            print(f"⚠️ Warning: Cleanup failed: {e}")
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n📋 Test Report Summary")
        print("=" * 50)
        
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
    print("🚀 Starting Phase 4 Backend Testing Suite")
    print("=" * 60)
    
    tester = Phase4BackendTester()
    
    # Setup test environment
    if not await tester.setup_test_environment():
        print("❌ Failed to setup test environment. Exiting.")
        return
    
    try:
        # Run all test suites
        await tester.test_database_models()
        await tester.test_deduplication_service()
        await tester.test_error_handling()
        tester.test_api_endpoints()
        tester.test_integration_points()
        
    finally:
        # Always cleanup
        await tester.cleanup_test_environment()
    
    # Generate and return report
    report = tester.generate_test_report()
    
    # Save detailed report to file
    with open('/app/phase4_test_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed test report saved to: /app/phase4_test_report.json")
    
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
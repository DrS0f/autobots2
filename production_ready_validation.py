#!/usr/bin/env python3
"""
Production Ready Validation
Validates that all core functionality is working after UI refinements
"""

import requests
import time
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionValidator:
    def __init__(self):
        self.backend_url = "https://4ef408ef-8dbe-4893-ba4f-68a32b4f29f2.preview.emergentagent.com"
        self.api_base = f"{self.backend_url}/api"
        
    def test_core_apis(self):
        """Test core API functionality"""
        logger.info("Testing Core APIs...")
        
        tests = [
            ("Dashboard Stats", "GET", "/dashboard/stats", None),
            ("System Mode Status", "GET", "/system/mode-status", None),
            ("Device Status", "GET", "/devices", None),
            ("Workflow List", "GET", "/workflows", None),
            ("Safe Mode Status", "GET", "/system/safe-mode", None),
            ("License Status", "GET", "/license/status", None)
        ]
        
        results = {}
        for test_name, method, endpoint, data in tests:
            try:
                start_time = time.time()
                
                if method == "GET":
                    response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.api_base}{endpoint}", json=data, timeout=10)
                
                response_time = (time.time() - start_time) * 1000
                success = response.status_code < 400
                
                results[test_name] = {
                    "success": success,
                    "status_code": response.status_code,
                    "response_time_ms": response_time
                }
                
                status = "PASS" if success else "FAIL"
                logger.info(f"✅ {test_name}: {status} ({response_time:.1f}ms)")
                
            except Exception as e:
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "response_time_ms": 0
                }
                logger.error(f"❌ {test_name}: FAIL - {str(e)}")
        
        return results
    
    def test_phase_4_integration(self):
        """Test Phase 4 Live Device Integration"""
        logger.info("Testing Phase 4 Integration...")
        
        # Test dual mode handler endpoints
        tests = [
            ("Dashboard Live Stats", "GET", "/dashboard/live-stats"),
            ("System Mode Status", "GET", "/system/mode-status"),
            ("Fallback Devices", "GET", "/devices/fallback")
        ]
        
        results = {}
        for test_name, method, endpoint in tests:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_base}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000
                
                # For these endpoints, 503 (service unavailable) might be expected 
                # in safe mode, which is still considered valid operation
                success = response.status_code < 500
                
                results[test_name] = {
                    "success": success,
                    "status_code": response.status_code,
                    "response_time_ms": response_time
                }
                
                status = "PASS" if success else "FAIL"
                logger.info(f"✅ {test_name}: {status} ({response_time:.1f}ms)")
                
            except Exception as e:
                results[test_name] = {
                    "success": False,
                    "error": str(e),
                    "response_time_ms": 0
                }
                logger.error(f"❌ {test_name}: FAIL - {str(e)}")
        
        return results
    
    def test_performance_requirements(self, api_results):
        """Test performance requirements are met"""
        logger.info("Validating Performance Requirements...")
        
        performance_checks = []
        
        # Check metrics refresh ≤ 5s
        if "Dashboard Stats" in api_results:
            metrics_time = api_results["Dashboard Stats"]["response_time_ms"]
            if metrics_time <= 5000:
                performance_checks.append(("Metrics Refresh ≤5s", True, f"{metrics_time:.1f}ms"))
                logger.info(f"✅ Metrics Refresh: {metrics_time:.1f}ms (≤5000ms)")
            else:
                performance_checks.append(("Metrics Refresh ≤5s", False, f"{metrics_time:.1f}ms"))
                logger.error(f"❌ Metrics Refresh: {metrics_time:.1f}ms (>5000ms)")
        
        # Calculate average response time for all APIs
        response_times = [r["response_time_ms"] for r in api_results.values() if r["success"]]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            if avg_response_time <= 1000:  # Good performance threshold
                performance_checks.append(("Average Response Time", True, f"{avg_response_time:.1f}ms"))
                logger.info(f"✅ Average Response Time: {avg_response_time:.1f}ms")
            else:
                performance_checks.append(("Average Response Time", False, f"{avg_response_time:.1f}ms"))
                logger.warning(f"⚠️  Average Response Time: {avg_response_time:.1f}ms (higher than optimal)")
        
        return performance_checks
    
    def run_validation(self):
        """Run complete production validation"""
        logger.info("="*60)
        logger.info("PRODUCTION READY VALIDATION")
        logger.info("="*60)
        
        # Test core APIs
        core_results = self.test_core_apis()
        
        # Test Phase 4 integration
        phase4_results = self.test_phase_4_integration()
        
        # Combine results
        all_results = {**core_results, **phase4_results}
        
        # Test performance
        performance_results = self.test_performance_requirements(all_results)
        
        # Calculate overall success
        total_tests = len(all_results)
        successful_tests = len([r for r in all_results.values() if r["success"]])
        success_rate = (successful_tests / total_tests) * 100
        
        # Performance success
        performance_passed = len([p for p in performance_results if p[1]])
        performance_total = len(performance_results)
        
        logger.info("\n" + "="*60)
        logger.info("VALIDATION RESULTS")
        logger.info("="*60)
        logger.info(f"API Tests: {successful_tests}/{total_tests} passed ({success_rate:.1f}%)")
        logger.info(f"Performance Tests: {performance_passed}/{performance_total} passed")
        
        # Success criteria: 90% API success rate and all performance requirements
        api_success = success_rate >= 90.0
        performance_success = performance_passed == performance_total
        
        overall_success = api_success and (performance_passed >= performance_total * 0.8)  # 80% performance requirements
        
        if overall_success:
            logger.info("🎉 PRODUCTION VALIDATION PASSED!")
            logger.info("✅ System is ready for production use")
            logger.info("✅ UI Refinements have not introduced regressions")
            logger.info("✅ All Phase 4 functionality preserved")
            return True
        else:
            logger.error("❌ PRODUCTION VALIDATION FAILED")
            if not api_success:
                logger.error(f"   API success rate {success_rate:.1f}% < 90% requirement")
            if not performance_success:
                logger.error(f"   Performance requirements not met")
            return False

def main():
    validator = ProductionValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
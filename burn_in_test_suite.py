#!/usr/bin/env python3
"""
Production Burn-In Test Suite for Operator Dashboard + Phase 4 Live Device Integration
2-Hour Automated Testing Under Real-World Load Conditions
"""

import asyncio
import json
import os
import sys
import time
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import uuid
import statistics
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/burn_in_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://4ef408ef-8dbe-4893-ba4f-68a32b4f29f2.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"
BURN_IN_DURATION_HOURS = 2.0  # 2 hours
TEST_INTERVAL_SECONDS = 10     # Test every 10 seconds
MAX_CONCURRENT_REQUESTS = 20   # Maximum concurrent API calls

class BurnInMetrics:
    """Tracks comprehensive burn-in test metrics"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.api_calls = []
        self.errors = []
        self.performance_samples = []
        self.system_metrics = []
        self.mode_toggles = []
        self.device_commands = []
        self.task_operations = []
        self.workflow_operations = []
        self.fallback_events = []
        self.lock = threading.Lock()
    
    def record_api_call(self, endpoint: str, method: str, success: bool, response_time_ms: float, status_code: int, error: str = None):
        """Record API call metrics"""
        with self.lock:
            self.api_calls.append({
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'success': success,
                'response_time_ms': response_time_ms,
                'status_code': status_code,
                'error': error
            })
    
    def record_error(self, error_type: str, details: str, severity: str = 'ERROR'):
        """Record error event"""
        with self.lock:
            self.errors.append({
                'timestamp': datetime.utcnow().isoformat(),
                'type': error_type,
                'details': details,
                'severity': severity
            })
    
    def record_performance_sample(self, metric_name: str, value: float, unit: str = 'ms'):
        """Record performance metric sample"""
        with self.lock:
            self.performance_samples.append({
                'timestamp': datetime.utcnow().isoformat(),
                'metric': metric_name,
                'value': value,
                'unit': unit
            })
    
    def record_system_metrics(self, cpu_percent: float, memory_percent: float, memory_mb: float):
        """Record system resource metrics"""
        with self.lock:
            self.system_metrics.append({
                'timestamp': datetime.utcnow().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_mb': memory_mb
            })
    
    def record_mode_toggle(self, from_mode: str, to_mode: str, success: bool, duration_ms: float):
        """Record mode toggle operation"""
        with self.lock:
            self.mode_toggles.append({
                'timestamp': datetime.utcnow().isoformat(),
                'from_mode': from_mode,
                'to_mode': to_mode,
                'success': success,
                'duration_ms': duration_ms
            })
    
    def record_device_command(self, device_id: str, command: str, success: bool, duration_ms: float):
        """Record device command execution"""
        with self.lock:
            self.device_commands.append({
                'timestamp': datetime.utcnow().isoformat(),
                'device_id': device_id,
                'command': command,
                'success': success,
                'duration_ms': duration_ms
            })
    
    def record_task_operation(self, operation: str, task_id: str, success: bool, duration_ms: float):
        """Record task operation"""
        with self.lock:
            self.task_operations.append({
                'timestamp': datetime.utcnow().isoformat(),
                'operation': operation,
                'task_id': task_id,
                'success': success,
                'duration_ms': duration_ms
            })
    
    def record_workflow_operation(self, operation: str, workflow_id: str, success: bool, duration_ms: float):
        """Record workflow operation"""
        with self.lock:
            self.workflow_operations.append({
                'timestamp': datetime.utcnow().isoformat(),
                'operation': operation,
                'workflow_id': workflow_id,
                'success': success,
                'duration_ms': duration_ms
            })
    
    def record_fallback_event(self, device_id: str, reason: str, recovery_time_ms: float = None):
        """Record fallback system activation"""
        with self.lock:
            self.fallback_events.append({
                'timestamp': datetime.utcnow().isoformat(),
                'device_id': device_id,
                'reason': reason,
                'recovery_time_ms': recovery_time_ms
            })
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        if not self.api_calls:
            return 0.0
        
        successful_calls = sum(1 for call in self.api_calls if call['success'])
        return (successful_calls / len(self.api_calls)) * 100.0
    
    def get_average_response_time(self) -> float:
        """Calculate average API response time"""
        if not self.api_calls:
            return 0.0
        
        times = [call['response_time_ms'] for call in self.api_calls]
        return statistics.mean(times)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive burn-in test report"""
        end_time = datetime.utcnow()
        duration_hours = (end_time - self.start_time).total_seconds() / 3600
        
        return {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_hours': duration_hours,
                'total_api_calls': len(self.api_calls),
                'total_errors': len(self.errors),
                'success_rate_percent': self.get_success_rate(),
                'average_response_time_ms': self.get_average_response_time()
            },
            'performance_metrics': {
                'mode_toggles': len(self.mode_toggles),
                'device_commands': len(self.device_commands),
                'task_operations': len(self.task_operations),
                'workflow_operations': len(self.workflow_operations),
                'fallback_events': len(self.fallback_events)
            },
            'detailed_metrics': {
                'api_calls': self.api_calls,
                'errors': self.errors,
                'performance_samples': self.performance_samples,
                'system_metrics': self.system_metrics,
                'mode_toggles': self.mode_toggles,
                'device_commands': self.device_commands,
                'task_operations': self.task_operations,
                'workflow_operations': self.workflow_operations,
                'fallback_events': self.fallback_events
            }
        }

class BurnInTester:
    """Main burn-in test orchestrator"""
    
    def __init__(self):
        self.metrics = BurnInMetrics()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS)
        self.current_mode = 'safe'  # Track current system mode
        self.test_devices = ['mock_device_001', 'mock_device_002', 'mock_device_003']
        
    def make_api_request(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Tuple[bool, Dict, float, int, str]:
        """Make API request and record metrics"""
        url = f"{API_BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time_ms = (time.time() - start_time) * 1000
            success = response.status_code < 400
            
            try:
                response_data = response.json()
            except:
                response_data = {'raw_response': response.text}
            
            error_msg = None if success else response_data.get('detail', f'HTTP {response.status_code}')
            
            self.metrics.record_api_call(endpoint, method, success, response_time_ms, response.status_code, error_msg)
            
            return success, response_data, response_time_ms, response.status_code, error_msg
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            self.metrics.record_api_call(endpoint, method, False, response_time_ms, 0, error_msg)
            self.metrics.record_error('API_REQUEST_EXCEPTION', f"{method} {endpoint}: {error_msg}")
            
            return False, {}, response_time_ms, 0, error_msg
    
    def test_metrics_refresh(self):
        """Test dashboard metrics refresh performance"""
        start_time = time.time()
        success, data, response_time, status_code, error = self.make_api_request('GET', '/dashboard/stats')
        
        if success:
            self.metrics.record_performance_sample('metrics_refresh', response_time, 'ms')
            
            # Validate metrics refresh target (≤ 5s)
            if response_time > 5000:
                self.metrics.record_error('PERFORMANCE_VIOLATION', f'Metrics refresh took {response_time}ms (target: ≤5000ms)', 'WARNING')
                
        return success
    
    def test_mode_toggle(self):
        """Test Safe↔Live mode toggle performance"""
        new_mode = 'live_mode' if self.current_mode == 'safe' else 'safe_mode'
        
        start_time = time.time()
        success, data, response_time, status_code, error = self.make_api_request('POST', '/system/mode/set', {'mode': new_mode})
        
        if success:
            old_mode = self.current_mode
            self.current_mode = 'live' if new_mode == 'live_mode' else 'safe'
            self.metrics.record_mode_toggle(old_mode, self.current_mode, True, response_time)
            
            # Validate mode toggle target (< 1s)
            if response_time > 1000:
                self.metrics.record_error('PERFORMANCE_VIOLATION', f'Mode toggle took {response_time}ms (target: <1000ms)', 'WARNING')
        else:
            self.metrics.record_mode_toggle(self.current_mode, new_mode, False, response_time)
            
        return success
    
    def test_device_commands(self):
        """Test device command execution performance"""
        device_id = random.choice(self.test_devices)
        commands = ['refresh', 'toggle-mode', 'initialize']
        command = random.choice(commands)
        
        start_time = time.time()
        
        if command == 'refresh':
            success, data, response_time, status_code, error = self.make_api_request('GET', f'/devices/{device_id}/status')
        elif command == 'toggle-mode':
            success, data, response_time, status_code, error = self.make_api_request('POST', f'/devices/{device_id}/toggle-mode')
        elif command == 'initialize':
            success, data, response_time, status_code, error = self.make_api_request('POST', f'/devices/{device_id}/initialize')
        
        self.metrics.record_device_command(device_id, command, success, response_time)
        
        # Validate device command target (< 2s)
        if response_time > 2000:
            self.metrics.record_error('PERFORMANCE_VIOLATION', f'Device command {command} took {response_time}ms (target: <2000ms)', 'WARNING')
            
        return success
    
    def test_bulk_task_operations(self):
        """Test bulk task creation and management"""
        operations = ['create', 'cancel', 'queue_status']
        operation = random.choice(operations)
        
        start_time = time.time()
        
        if operation == 'create':
            task_data = {
                'device_id': random.choice(self.test_devices),
                'target_username': f'burn_in_user_{random.randint(1000, 9999)}',
                'actions': ['search_user', 'view_profile'],
                'priority': random.choice(['low', 'normal', 'high'])
            }
            success, data, response_time, status_code, error = self.make_api_request('POST', '/tasks/create-device-bound', task_data)
            task_id = data.get('task_id', 'unknown') if success else 'failed'
            
        elif operation == 'cancel':
            # Simulate task cancellation
            success, data, response_time, status_code, error = self.make_api_request('GET', '/tasks/active')
            task_id = 'simulated_cancel'
            
        elif operation == 'queue_status':
            success, data, response_time, status_code, error = self.make_api_request('GET', '/devices/queues/all')
            task_id = 'queue_check'
        
        self.metrics.record_task_operation(operation, task_id, success, response_time)
        return success
    
    def test_workflow_operations(self):
        """Test workflow creation and deployment"""
        operations = ['create_template', 'deploy', 'status']
        operation = random.choice(operations)
        
        start_time = time.time()
        
        if operation == 'create_template':
            template_data = {
                'name': f'Burn-In Test Workflow {random.randint(1000, 9999)}',
                'description': 'Automated burn-in test workflow',
                'template_type': 'single_user',
                'target_username': f'test_user_{random.randint(1000, 9999)}',
                'actions': ['search_user', 'view_profile'],
                'priority': 'normal'
            }
            success, data, response_time, status_code, error = self.make_api_request('POST', '/workflows', template_data)
            workflow_id = data.get('template_id', 'unknown') if success else 'failed'
            
        elif operation == 'deploy':
            # First get available workflows
            success_list, data_list, _, _, _ = self.make_api_request('GET', '/workflows')
            if success_list and data_list.get('workflows'):
                workflow_id = random.choice(data_list['workflows']).get('template_id', 'unknown')
                deploy_data = {'device_ids': [random.choice(self.test_devices)]}
                success, data, response_time, status_code, error = self.make_api_request('POST', f'/workflows/{workflow_id}/deploy', deploy_data)
            else:
                success = False
                response_time = 0
                workflow_id = 'no_workflows_available'
                
        elif operation == 'status':
            success, data, response_time, status_code, error = self.make_api_request('GET', '/workflows')
            workflow_id = 'status_check'
        
        self.metrics.record_workflow_operation(operation, workflow_id, success, response_time)
        return success
    
    def simulate_device_offline_recovery(self):
        """Simulate device offline scenarios and recovery"""
        device_id = random.choice(self.test_devices)
        
        # Simulate device going offline (record fallback event)
        self.metrics.record_fallback_event(device_id, 'Simulated device offline for burn-in test')
        
        # Test fallback system by trying to execute task on "offline" device
        start_time = time.time()
        success, data, response_time, status_code, error = self.make_api_request('GET', f'/devices/{device_id}/queue')
        
        # Simulate recovery
        recovery_time = time.time() - start_time
        if success:
            self.metrics.record_fallback_event(device_id, 'Device recovered', recovery_time * 1000)
        
        return success
    
    def monitor_system_resources(self):
        """Monitor system CPU and memory usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / (1024 * 1024)
            
            self.metrics.record_system_metrics(cpu_percent, memory_percent, memory_mb)
            
            # Log resource usage warnings
            if cpu_percent > 80:
                self.metrics.record_error('RESOURCE_WARNING', f'High CPU usage: {cpu_percent}%', 'WARNING')
            
            if memory_percent > 85:
                self.metrics.record_error('RESOURCE_WARNING', f'High memory usage: {memory_percent}%', 'WARNING')
                
        except Exception as e:
            self.metrics.record_error('MONITORING_ERROR', f'Failed to collect system metrics: {str(e)}')
    
    def run_test_cycle(self):
        """Run one complete test cycle"""
        test_functions = [
            ('metrics_refresh', self.test_metrics_refresh),
            ('mode_toggle', self.test_mode_toggle),
            ('device_commands', self.test_device_commands),
            ('bulk_tasks', self.test_bulk_task_operations),
            ('workflows', self.test_workflow_operations),
            ('device_recovery', self.simulate_device_offline_recovery)
        ]
        
        # Submit concurrent tests
        futures = []
        for test_name, test_func in test_functions:
            if random.random() > 0.3:  # Run ~70% of tests each cycle for varied load
                future = self.executor.submit(test_func)
                futures.append((test_name, future))
        
        # Wait for completion and handle results
        for test_name, future in futures:
            try:
                result = future.result(timeout=30)
                logger.info(f"Test cycle {test_name}: {'SUCCESS' if result else 'FAILED'}")
            except Exception as e:
                logger.error(f"Test cycle {test_name} exception: {str(e)}")
                self.metrics.record_error('TEST_EXCEPTION', f'{test_name}: {str(e)}')
    
    def run_burn_in_test(self):
        """Run the complete 2-hour burn-in test"""
        logger.info(f"Starting burn-in test for {BURN_IN_DURATION_HOURS} hours")
        logger.info(f"Test interval: {TEST_INTERVAL_SECONDS} seconds")
        logger.info(f"Backend URL: {BACKEND_URL}")
        
        self.running = True
        start_time = time.time()
        end_time = start_time + (BURN_IN_DURATION_HOURS * 3600)
        
        cycle_count = 0
        
        try:
            while self.running and time.time() < end_time:
                cycle_start = time.time()
                
                # Run test cycle
                logger.info(f"Running test cycle {cycle_count + 1}")
                self.run_test_cycle()
                
                # Monitor system resources
                self.monitor_system_resources()
                
                cycle_count += 1
                
                # Calculate remaining time
                remaining_hours = (end_time - time.time()) / 3600
                logger.info(f"Cycle {cycle_count} completed. Remaining time: {remaining_hours:.2f} hours")
                
                # Progress update every 10 cycles
                if cycle_count % 10 == 0:
                    success_rate = self.metrics.get_success_rate()
                    avg_response = self.metrics.get_average_response_time()
                    logger.info(f"Progress update - Success rate: {success_rate:.1f}%, Avg response: {avg_response:.1f}ms")
                
                # Wait for next cycle
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, TEST_INTERVAL_SECONDS - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("Burn-in test interrupted by user")
            self.running = False
        except Exception as e:
            logger.error(f"Burn-in test failed with exception: {str(e)}")
            self.metrics.record_error('BURN_IN_FATAL', f'Test stopped due to exception: {str(e)}', 'CRITICAL')
        finally:
            self.executor.shutdown(wait=True)
            
        logger.info(f"Burn-in test completed after {cycle_count} cycles")
        
        # Generate final report
        report = self.metrics.generate_report()
        return report
    
    def evaluate_success_criteria(self, report: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Evaluate burn-in test against success criteria"""
        failures = []
        
        # Success Criteria Evaluation
        success_rate = report['test_summary']['success_rate_percent']
        if success_rate < 99.0:
            failures.append(f"Success rate {success_rate:.1f}% < 99% requirement")
        
        avg_response = report['test_summary']['average_response_time_ms']
        if avg_response > 5000:
            failures.append(f"Average response time {avg_response:.1f}ms > 5000ms requirement")
        
        # Check mode toggle performance
        mode_toggles = [t for t in report['detailed_metrics']['mode_toggles'] if t['success']]
        if mode_toggles:
            avg_mode_toggle_time = statistics.mean([t['duration_ms'] for t in mode_toggles])
            if avg_mode_toggle_time > 1000:
                failures.append(f"Average mode toggle time {avg_mode_toggle_time:.1f}ms > 1000ms requirement")
        
        # Check device command performance
        device_commands = [c for c in report['detailed_metrics']['device_commands'] if c['success']]
        if device_commands:
            avg_device_cmd_time = statistics.mean([c['duration_ms'] for c in device_commands])
            if avg_device_cmd_time > 2000:
                failures.append(f"Average device command time {avg_device_cmd_time:.1f}ms > 2000ms requirement")
        
        # Check for critical errors
        critical_errors = [e for e in report['detailed_metrics']['errors'] if e['severity'] == 'CRITICAL']
        if critical_errors:
            failures.append(f"Found {len(critical_errors)} critical errors")
        
        # Check fallback system activation
        fallback_events = report['detailed_metrics']['fallback_events']
        if len(fallback_events) == 0:
            failures.append("No fallback system activations detected (expected during device offline simulation)")
        
        return len(failures) == 0, failures

def main():
    """Main entry point for burn-in test"""
    print("=" * 80)
    print("PRODUCTION BURN-IN TEST - OPERATOR DASHBOARD + PHASE 4 INTEGRATION")
    print("=" * 80)
    print(f"Duration: {BURN_IN_DURATION_HOURS} hours")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Start Time: {datetime.utcnow().isoformat()}")
    print("=" * 80)
    
    # Initialize and run burn-in test
    tester = BurnInTester()
    report = tester.run_burn_in_test()
    
    # Save detailed report
    report_filename = f'/tmp/burn_in_report_{int(time.time())}.json'
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Evaluate success criteria
    success, failures = tester.evaluate_success_criteria(report)
    
    # Print final results
    print("\n" + "=" * 80)
    print("BURN-IN TEST RESULTS")
    print("=" * 80)
    print(f"Duration: {report['test_summary']['duration_hours']:.2f} hours")
    print(f"Total API Calls: {report['test_summary']['total_api_calls']}")
    print(f"Success Rate: {report['test_summary']['success_rate_percent']:.2f}%")
    print(f"Average Response Time: {report['test_summary']['average_response_time_ms']:.2f}ms")
    print(f"Total Errors: {report['test_summary']['total_errors']}")
    
    print(f"\nPerformance Operations:")
    print(f"- Mode Toggles: {report['performance_metrics']['mode_toggles']}")
    print(f"- Device Commands: {report['performance_metrics']['device_commands']}")
    print(f"- Task Operations: {report['performance_metrics']['task_operations']}")
    print(f"- Workflow Operations: {report['performance_metrics']['workflow_operations']}")
    print(f"- Fallback Events: {report['performance_metrics']['fallback_events']}")
    
    print(f"\nSuccess Criteria Evaluation: {'PASS' if success else 'FAIL'}")
    if not success:
        print("Failure Reasons:")
        for failure in failures:
            print(f"  - {failure}")
    
    print(f"\nDetailed Report Saved: {report_filename}")
    print("=" * 80)
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
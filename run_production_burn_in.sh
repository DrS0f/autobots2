#!/bin/bash

# Production Burn-In Test Runner Script
# Deploys Operator Dashboard and runs comprehensive 2-hour burn-in test

set -e

echo "=============================================================================="
echo "PRODUCTION DEPLOYMENT & BURN-IN TEST - OPERATOR DASHBOARD + PHASE 4"
echo "=============================================================================="
echo "Start Time: $(date)"
echo ""

# Configuration
BURN_IN_DURATION="2 hours"
LOG_FILE="/tmp/production_burn_in_$(date +%Y%m%d_%H%M%S).log"

echo "Configuration:"
echo "- Burn-in Duration: $BURN_IN_DURATION"
echo "- Log File: $LOG_FILE"
echo "- Backend URL: $REACT_APP_BACKEND_URL"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check service status
check_services() {
    log "Checking service status..."
    
    # Check all required services are running
    if ! sudo supervisorctl status | grep -E "(backend|frontend|mongodb)" | grep -q "RUNNING"; then
        log "ERROR: Not all required services are running"
        sudo supervisorctl status
        exit 1
    fi
    
    log "✅ All services are running"
    
    # Check backend API health
    if ! curl -sf "$REACT_APP_BACKEND_URL/api/dashboard/stats" > /dev/null; then
        log "ERROR: Backend API health check failed"
        exit 1
    fi
    
    log "✅ Backend API health check passed"
}

# Function to validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    # Check that OperatorDashboard component is deployed
    if [ ! -f "/app/frontend/src/components/OperatorDashboard.js" ]; then
        log "ERROR: OperatorDashboard.js not found"
        exit 1
    fi
    
    # Check that App.js uses OperatorDashboard
    if ! grep -q "OperatorDashboard" "/app/frontend/src/App.js"; then
        log "ERROR: App.js does not import OperatorDashboard"
        exit 1
    fi
    
    # Check Phase 4 components are present
    if [ ! -f "/app/backend/ios_automation/dual_mode_handler.py" ]; then
        log "ERROR: Phase 4 dual_mode_handler.py not found"
        exit 1
    fi
    
    if [ ! -f "/app/backend/ios_automation/live_device_manager.py" ]; then
        log "ERROR: Phase 4 live_device_manager.py not found"
        exit 1
    fi
    
    log "✅ Deployment validation passed"
}

# Function to run pre-flight checks
pre_flight_checks() {
    log "Running pre-flight checks..."
    
    # Install required Python packages for burn-in test
    pip install psutil > /dev/null 2>&1 || true
    
    # Check system resources
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2+$4}' | cut -d'%' -f1)
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.1f", ($3/$2) * 100.0)}')
    
    log "System Resources:"
    log "- CPU Usage: ${CPU_USAGE}%"
    log "- Memory Usage: ${MEMORY_USAGE}%"
    
    # Check if system is under reasonable load before starting
    if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
        log "WARNING: High CPU usage detected before burn-in test"
    fi
    
    if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
        log "WARNING: High memory usage detected before burn-in test"
    fi
    
    log "✅ Pre-flight checks completed"
}

# Function to restart services if needed
restart_services_if_needed() {
    log "Checking if service restart is needed..."
    
    # Check if services have been running for less than 5 minutes (fresh restart)
    BACKEND_UPTIME=$(sudo supervisorctl status backend | awk '{print $4}' | cut -d',' -f1)
    
    if [[ "$BACKEND_UPTIME" == *"0:00:"* ]] || [[ "$BACKEND_UPTIME" == *"0:01:"* ]] || [[ "$BACKEND_UPTIME" == *"0:02:"* ]] || [[ "$BACKEND_UPTIME" == *"0:03:"* ]] || [[ "$BACKEND_UPTIME" == *"0:04:"* ]]; then
        log "Services recently restarted, proceeding with current instances"
    else
        log "Restarting all services for clean burn-in test..."
        sudo supervisorctl restart all
        
        # Wait for services to stabilize
        sleep 30
        
        check_services
    fi
    
    log "✅ Services are ready for burn-in test"
}

# Function to run the burn-in test
run_burn_in_test() {
    log "Starting burn-in test..."
    log "Expected duration: $BURN_IN_DURATION"
    
    # Make burn-in test script executable
    chmod +x /app/burn_in_test_suite.py
    
    # Run the burn-in test with output logging
    if python3 /app/burn_in_test_suite.py 2>&1 | tee -a "$LOG_FILE"; then
        log "✅ Burn-in test completed successfully"
        return 0
    else
        log "❌ Burn-in test failed"
        return 1
    fi
}

# Function to generate summary report
generate_summary() {
    local test_result=$1
    
    log "Generating burn-in test summary..."
    
    # Find the most recent burn-in report
    LATEST_REPORT=$(ls -t /tmp/burn_in_report_*.json 2>/dev/null | head -n1)
    
    if [ -n "$LATEST_REPORT" ]; then
        log "Burn-in report generated: $LATEST_REPORT"
        
        # Extract key metrics from the report
        SUCCESS_RATE=$(python3 -c "import json; print(json.load(open('$LATEST_REPORT'))['test_summary']['success_rate_percent'])")
        AVG_RESPONSE=$(python3 -c "import json; print(json.load(open('$LATEST_REPORT'))['test_summary']['average_response_time_ms'])")
        TOTAL_CALLS=$(python3 -c "import json; print(json.load(open('$LATEST_REPORT'))['test_summary']['total_api_calls'])")
        TOTAL_ERRORS=$(python3 -c "import json; print(json.load(open('$LATEST_REPORT'))['test_summary']['total_errors'])")
        
        log "Key Metrics:"
        log "- Success Rate: ${SUCCESS_RATE}%"
        log "- Average Response Time: ${AVG_RESPONSE}ms"
        log "- Total API Calls: $TOTAL_CALLS"
        log "- Total Errors: $TOTAL_ERRORS"
    fi
    
    if [ $test_result -eq 0 ]; then
        log "🎉 BURN-IN TEST PASSED - Ready for UI refinement phase"
    else
        log "❌ BURN-IN TEST FAILED - Issues must be resolved before proceeding"
    fi
}

# Main execution
main() {
    log "Starting production deployment and burn-in test sequence"
    
    # Step 1: Validate deployment
    validate_deployment
    
    # Step 2: Check services
    check_services
    
    # Step 3: Run pre-flight checks
    pre_flight_checks
    
    # Step 4: Restart services if needed
    restart_services_if_needed
    
    # Step 5: Run burn-in test
    if run_burn_in_test; then
        TEST_RESULT=0
    else
        TEST_RESULT=1
    fi
    
    # Step 6: Generate summary
    generate_summary $TEST_RESULT
    
    log "Production burn-in test completed"
    log "End Time: $(date)"
    
    exit $TEST_RESULT
}

# Trap to ensure cleanup on script exit
cleanup() {
    log "Cleaning up burn-in test resources..."
    # Kill any remaining background processes
    pkill -f "burn_in_test_suite.py" 2>/dev/null || true
}

trap cleanup EXIT

# Run main function
main "$@"
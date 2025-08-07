# Clean 1-Click Install Test

This document provides step-by-step instructions for testing the 1-click installer on a fresh machine and verifying the SaaS licensing kill-switch functionality.

## Prerequisites

- Fresh Linux/macOS/WSL2 environment
- Internet connection
- Docker & Docker Compose installed

## Fresh Environment Installation Test

### 1. Install Docker & Docker Compose

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose (if not included with Docker)
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

**macOS:**
```bash
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop
# Or use Homebrew:
brew install --cask docker
```

**Verification:**
```bash
docker --version
docker compose version
curl --version
```

### 2. Clone Repository and Navigate to App Directory

```bash
git clone <repository-url>
cd <repository-name>/app
```

### 3. Optional: Clean Previous Docker Installation

```bash
# Only if Docker was used before for testing
make clean
```

### 4. Run 1-Click Installer

```bash
# Method 1: Using Makefile
make install

# Method 2: Direct script execution
./scripts/install.sh
```

**Expected Installer Flow:**
1. ✅ Checks prerequisites (Docker, curl, Docker Compose)
2. ✅ Creates `.env` from `.env.production.example`  
3. ✅ Generates MongoDB credentials automatically
4. ✅ Prompts for LICENSE_KEY (optional)
5. ✅ Builds and starts Docker services
6. ✅ Waits for MongoDB health check
7. ✅ Initializes database indexes and TTLs
8. ✅ Performs backend/frontend health checks
9. ✅ Verifies license status (if configured)
10. ✅ Shows access URLs and management commands

### 5. Verification Steps

#### A. Service Accessibility
```bash
# Frontend accessibility
curl -I http://localhost:8080
# Expected: HTTP/1.1 200 OK

# Backend health check  
curl http://localhost:8000/api/system/health
# Expected: JSON response with system status

# Docker services status
docker compose ps
# Expected: All services running and healthy
```

#### B. Web Interface Access
- **Frontend:** http://localhost:8080 
  - ✅ Dashboard loads without errors
  - ✅ All tabs accessible (Tasks, Devices, License, etc.)
  - ✅ License tab shows current status

- **Backend API:** http://localhost:8000/api
  - ✅ Health endpoint responsive
  - ✅ License status endpoint functional

#### C. License Status Verification

**Development Mode (no LICENSE_KEY):**
```bash
curl -s http://localhost:8000/api/license/status | python3 -m json.tool
```
**Expected Response:**
```json
{
  "success": true,
  "license_status": {
    "status": "no_license_required",
    "message": "Running without license restrictions",
    "licensed": true
  },
  "updated_at": "2024-01-XX..."
}
```

**Production Mode (with LICENSE_KEY):**
```bash
curl -s http://localhost:8000/api/license/status | python3 -m json.tool
```
**Expected Response (if invalid key):**
```json
{
  "success": true,  
  "license_status": {
    "status": "LOCKED",
    "licensed": false,
    "device_id": "uuid-device-id",
    "verify_interval": 900
  },
  "updated_at": "2024-01-XX..."
}
```

## License Kill-Switch Quick Check

This test verifies the remote kill-switch functionality works correctly.

### Prerequisites
- Running license server (see `LICENSED_DISTRIBUTION.md`)
- Valid license key issued and configured

### Test Scenario 1: System Lock via License Revocation

#### Step 1: Setup Valid License
```bash
# Configure valid license in .env
echo "LICENSE_KEY=your-valid-license-key-here" >> .env
sudo supervisorctl restart backend  # If not using Docker
# OR
docker compose restart backend
```

#### Step 2: Verify System Unlocked
```bash
# Check license status
curl -s http://localhost:8000/api/license/status | python3 -m json.tool

# Test task creation (should succeed)
curl -X POST -H "Content-Type: application/json" \
  -d '{"target_username": "test_user", "actions": ["like"], "priority": "normal"}' \
  http://localhost:8000/api/tasks/create
```
**Expected:** HTTP 200, task created successfully

#### Step 3: Revoke License on Server
```bash
cd /app/licensing
./admin_cli.py revoke "your-license-key" --reason "Kill switch test"
```

#### Step 4: Wait for License Verification (≤15 minutes)
```bash
# Check license status every few minutes
while true; do
  echo "Checking license status..."
  curl -s http://localhost:8000/api/license/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
status = data.get('license_status', {})
print(f'Status: {status.get(\"status\")}, Licensed: {status.get(\"licensed\")}')
"
  sleep 60
done
```

#### Step 5: Verify System Locked
```bash
# Test task creation (should fail with 403)
curl -X POST -H "Content-Type: application/json" \
  -d '{"target_username": "test_user", "actions": ["like"], "priority": "normal"}' \
  http://localhost:8000/api/tasks/create
```
**Expected:** HTTP 403 with message "License required: System is locked..."

#### Step 6: Verify UI Shows Locked State
- Open http://localhost:8080
- ✅ Red license banner should appear at top
- ✅ License tab should show "Locked" status with red badge
- ✅ Task creation should be disabled

### Test Scenario 2: System Unlock via License Renewal

#### Step 1: Issue New License
```bash
cd /app/licensing
./admin_cli.py issue customer123 --plan premium --duration 30
# Copy the returned license key
```

#### Step 2: Update License Key
```bash
# Update .env file with new license key
sed -i 's/LICENSE_KEY=.*/LICENSE_KEY=new-license-key-here/' .env
```

#### Step 3: Force License Verification
```bash
curl -X POST http://localhost:8000/api/license/verify
```

#### Step 4: Verify System Unlocked
```bash
# Check license status (should show valid)
curl -s http://localhost:8000/api/license/status | python3 -m json.tool

# Test task creation (should succeed again)
curl -X POST -H "Content-Type: application/json" \
  -d '{"target_username": "test_user", "actions": ["like"], "priority": "normal"}' \
  http://localhost:8000/api/tasks/create
```
**Expected:** HTTP 200, task created successfully

### Test Scenario 3: Grace Period Behavior

#### Step 1: Setup License with Short Duration
```bash
cd /app/licensing
./admin_cli.py issue test-grace --duration 0 --grace 1  # Expires immediately, 1 day grace
```

#### Step 2: Configure and Wait
```bash
# Update LICENSE_KEY in .env
# Restart backend
# Wait 1-2 minutes for verification
```

#### Step 3: Verify Grace Period Active
```bash
curl -s http://localhost:8000/api/license/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
status = data.get('license_status', {})
print(f'Valid: {status.get(\"valid\")}')
print(f'Grace Period: {status.get(\"in_grace_period\")}')  
print(f'Message: {status.get(\"message\")}')
"
```
**Expected:** `valid=true`, `in_grace_period=true`

## Troubleshooting Common Issues

### Installation Fails

**Docker not running:**
```bash
sudo systemctl start docker  # Linux
# Or start Docker Desktop on macOS
```

**Permission denied:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Port conflicts:**
```bash
# Check what's using the ports
sudo netstat -tlnp | grep -E ':80|:8000|:8080|:27017'
# Stop conflicting services or change ports in docker-compose.yml
```

### License Server Issues

**License server not accessible:**
```bash
# Verify license server is running
curl http://localhost:8002/
# Expected: JSON response with service info

# Check if LICENSE_API_URL is correct in .env
grep LICENSE_API_URL .env
```

**Invalid license key:**
```bash
# Verify license key format (should be JWT)
cd /app/licensing
./admin_cli.py verify "your-license-key"
```

### Service Health Issues

**Backend health check fails:**
```bash
# Check backend logs
docker compose logs backend

# Common issues: 
# - MongoDB not ready: Wait longer or check mongo logs
# - Environment variables: Verify .env file
# - Port conflicts: Change backend port
```

**Frontend not accessible:**
```bash
# Check frontend logs  
docker compose logs frontend

# Verify nginx configuration
docker compose exec frontend cat /etc/nginx/conf.d/default.conf
```

## Uninstall

### Complete Cleanup
```bash
# Remove all services, volumes, and images
make clean

# Or manually:
docker compose down -v --remove-orphans
docker system prune -af
```

### Keep Data, Remove Services Only
```bash
# Stop services but keep volumes
docker compose down
```

## Success Criteria

✅ **Installation Completeness:**
- All prerequisites automatically checked
- Environment files created from templates  
- MongoDB credentials auto-generated
- All services start successfully
- Database properly initialized
- Health checks pass

✅ **License Integration:**
- Development mode works without LICENSE_KEY
- Production mode enforces license validation
- Kill-switch locks system within 15 minutes
- License renewal unlocks without restart
- UI reflects license status correctly

✅ **Clean Installation:**
- Works on fresh machine with no prior setup
- No manual configuration required beyond LICENSE_KEY
- All dependencies handled by Docker
- Clear error messages for common issues

✅ **Documentation Quality:**
- Step-by-step instructions are clear
- Expected outputs documented
- Troubleshooting covers common issues  
- Uninstall process documented

This testing protocol ensures the 1-click installer provides a robust, production-ready deployment experience with comprehensive SaaS licensing integration.
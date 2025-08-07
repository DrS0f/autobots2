# Licensed Distribution Guide
## iOS Instagram Automation - SaaS Licensing & Remote Kill-Switch

This document explains how to manage licenses for the iOS Instagram Automation system with remote kill-switch capability.

## Overview

The system implements JWT-based licensing with the following components:
- **License Server**: Issues, verifies, and revokes licenses
- **Client Integration**: Periodic verification with graceful degradation
- **Admin CLI**: Command-line tools for license management
- **Frontend UI**: License status and management interface

## Architecture

### License Server (`/licensing`)
- FastAPI-based service running on port 8002
- JWT (HS256) signed tokens with license claims
- Simple file-based storage for licenses
- Admin-only endpoints for management

### Client Integration (`/backend`)
- Background verification every 15 minutes (configurable)
- Graceful degradation with 2-hour grace period for network issues
- Task blocking when license is invalid/expired
- Device ID binding (optional)

### License Claims (JWT)
```json
{
  "sub": "customer_id",
  "license_id": "uuid",
  "plan": "basic|premium|enterprise",
  "features": ["basic_automation", "analytics", "premium_support"],
  "device_id": "optional-device-binding",
  "exp": 1640995200,
  "iat": 1640908800,
  "grace_days": 7
}
```

## License Server Setup

### 1. Install Dependencies
```bash
cd /app/licensing
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
# Required for production
export LICENSE_SECRET_KEY="your-strong-secret-key-256-bits"
export ADMIN_TOKEN="your-admin-token-change-this"
export LICENSE_STORAGE_PATH="/secure/path/licenses.json"
```

### 3. Start License Server
```bash
cd /app/licensing
python -m uvicorn server:app --host 0.0.0.0 --port 8002
```

Or for production with gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8002
```

## Client Setup

### Environment Variables
Add to `/app/backend/.env`:
```bash
# License configuration
LICENSE_KEY=your-jwt-license-key-here
LICENSE_API_URL=http://your-license-server:8002
LICENSE_VERIFY_INTERVAL=900  # 15 minutes
```

### Restart Backend
```bash
sudo supervisorctl restart backend
# or
cd /app && make restart
```

## Admin CLI Usage

The admin CLI provides command-line access to license management:

### Setup
```bash
export LICENSE_ADMIN_TOKEN="your-admin-token"
cd /app/licensing
chmod +x admin_cli.py
```

### Issue New License
```bash
./admin_cli.py issue customer123 --plan premium --duration 30 --features basic_automation analytics premium_support
```

Output:
```
✅ License issued successfully!
Customer ID: customer123
Plan: premium
Features: basic_automation, analytics, premium_support
Expires: 2024-02-15T10:30:00Z
Grace Days: 7

🔑 License Key:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Verify License
```bash
./admin_cli.py verify "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### List All Licenses
```bash
./admin_cli.py list
```

### Revoke License
```bash
./admin_cli.py revoke "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." --reason "Payment failed"
```

### Extend License
```bash
./admin_cli.py extend "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." 30
```

## License States & Behavior

### 1. No License Required
- `LICENSE_KEY` not set
- System runs normally without restrictions
- Frontend shows "No License Required" status

### 2. Valid License
- Regular verification every 15 minutes
- All features available
- Frontend shows green "Valid" status

### 3. Grace Period
- License expired but within grace_days
- System continues to function
- Frontend shows yellow "Grace Period" warning
- UI displays countdown to hard lock

### 4. Locked State
- License invalid, expired (past grace), or revoked
- New task creation blocked (HTTP 403)
- Existing tasks may complete
- Workers pause automatically
- Frontend shows red "Locked" status

### 5. Network Issues
- License server unreachable
- 2-hour grace period for temporary network issues
- System locks if verification fails for too long

## Grace Period Handling

### Default Grace Period: 7 days
- After license expires, system continues functioning
- Grace period countdown shown in UI
- Admin can extend license during grace period

### Grace Period Behavior
1. **Days 1-7**: Full functionality with warnings
2. **Day 8+**: System locks, tasks blocked
3. **Recovery**: Renew/extend license to unlock immediately

## API Endpoints

### License Server Endpoints
```
POST /auth/issue          # Issue new license (admin only)
GET  /auth/verify         # Verify license (public)
POST /auth/revoke         # Revoke license (admin only)
GET  /admin/licenses      # List all licenses (admin only)
POST /admin/extend        # Extend license (admin only)
```

### Client API Endpoints
```
GET  /api/license/status  # Get current license status
POST /api/license/verify  # Force immediate verification
```

## Frontend Features

### License Panel (`/license` tab)
- Real-time license status display
- Manual verification trigger
- License key configuration guidance
- Expiry countdown with warnings
- Customer/plan/features display

### License Banner (global)
- Automatic display for issues
- Color-coded warnings (blue → orange → red)
- Dismissible notifications
- Expiry countdown

### Dashboard Integration
- License status in system stats
- Real-time updates every 5 seconds
- License warnings in metrics

## Security Features

### JWT Security
- HS256 algorithm with strong secret key
- Standard JWT claims (sub, exp, iat)
- Custom claims for license features

### Device Binding (Optional)
- Bind license to specific device ID
- Prevents license sharing
- Configurable per license

### Admin Authentication
- Bearer token authentication for admin endpoints
- Separate admin token for CLI access

## Deployment Scenarios

### 1. Development/Testing
```bash
# Start license server locally
cd /app/licensing
python server.py

# Configure client
export LICENSE_KEY="test-license-key"
export LICENSE_API_URL="http://localhost:8002"
```

### 2. Production Deployment

#### Option A: Same Server
- Run license server on port 8002
- Configure client to use localhost:8002

#### Option B: Separate License Server
- Deploy license server on dedicated instance
- Configure client with remote URL
- Use HTTPS for production

#### Option C: Private Registry (Future)
- Push Docker images to private registry (GHCR/ECR)
- Expiring pull tokens per customer
- Combines image access control with runtime licensing

## Troubleshooting

### License Server Issues
```bash
# Check server status
curl http://localhost:8002/

# Test verification endpoint
curl "http://localhost:8002/auth/verify?license_key=YOUR_KEY"

# Check logs
tail -f /var/log/license-server.log
```

### Client Issues
```bash
# Check license status via API
curl http://localhost:8001/api/license/status

# Force verification
curl -X POST http://localhost:8001/api/license/verify

# Check backend logs
tail -f /var/log/supervisor/backend.out.log
```

### Common Problems

#### "System Locked" Error
1. Check license key in .env file
2. Verify license server is running
3. Test license with admin CLI
4. Check network connectivity

#### License Server Unreachable
1. Verify LICENSE_API_URL setting
2. Check firewall/network rules
3. Ensure license server is running
4. Check DNS resolution

#### Invalid License Token
1. Verify LICENSE_SECRET_KEY matches server
2. Check license hasn't been revoked
3. Validate JWT format and signature

## Production Checklist

### Security
- [ ] Strong LICENSE_SECRET_KEY (256-bit)
- [ ] Secure ADMIN_TOKEN
- [ ] HTTPS for license server (production)
- [ ] Firewall rules for license server
- [ ] Regular backup of licenses.json

### Monitoring
- [ ] License server health monitoring
- [ ] Client verification success rates
- [ ] License expiry alerts
- [ ] Grace period notifications

### Backup & Recovery
- [ ] Regular backup of license storage
- [ ] Disaster recovery plan
- [ ] License server redundancy (if needed)

## Support & Maintenance

### Regular Tasks
1. **Monitor license expirations** (weekly)
2. **Clean up revoked licenses** (monthly)
3. **Rotate secret keys** (annually)
4. **Review license usage** (quarterly)

### Customer Support
- Use admin CLI for license issues
- Check license status via API
- Review system logs for license-related errors
- Provide grace period for payment issues

## Example Customer Workflow

### New Customer
1. Admin issues license: `./admin_cli.py issue customer123 --duration 30`
2. Customer receives license key
3. Customer sets LICENSE_KEY in environment
4. System automatically validates and unlocks

### License Renewal
1. Admin extends license: `./admin_cli.py extend LICENSE_KEY 30`
2. System automatically detects renewal
3. Grace period warnings disappear
4. Full functionality restored

### Non-Payment/Termination
1. Admin revokes license: `./admin_cli.py revoke LICENSE_KEY`
2. Customer system locks within 15 minutes
3. New tasks blocked, existing tasks complete
4. Customer sees "System Locked" message

This licensing system provides flexible, secure license management with graceful degradation and clear customer communication.
#!/usr/bin/env bash
set -euo pipefail

# iOS Instagram Automation - 1-Click Installer
# Installs and configures the complete stack with licensing support

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Colors and messaging
msg() { echo -e "\033[1;36m==>\033[0m $*"; }
err() { echo -e "\033[1;31mERROR:\033[0m $*" >&2; }
success() { echo -e "\033[1;32m✅\033[0m $*"; }
warn() { echo -e "\033[1;33m⚠️\033[0m $*"; }

# Dependency checker
need() { 
    command -v "$1" >/dev/null 2>&1 || { 
        err "Missing required dependency: $1"
        echo "Please install $1 and try again."
        exit 1
    }
}

# Header
echo
echo "🚀 iOS Instagram Automation - 1-Click Installer"
echo "================================================"
echo

# Check prerequisites
msg "Checking prerequisites..."
need docker
need curl

# Check for docker-compose or docker compose
if ! command -v docker-compose >/dev/null 2>&1; then
    if ! docker compose version >/dev/null 2>&1; then
        err "Missing docker-compose or 'docker compose' plugin"
        echo "Please install Docker Compose and try again."
        exit 1
    else
        DOCKER_COMPOSE="docker compose"
    fi
else
    DOCKER_COMPOSE="docker-compose"
fi

success "All prerequisites found"

# Check if .env.production.example exists
if [ ! -f ".env.production.example" ]; then
    warn ".env.production.example not found, creating basic template..."
    cat > .env.production.example << 'EOF'
# MongoDB Configuration
MONGO_URL=mongodb://gram_mongo:27017/instagram_automation
DB_NAME=instagram_automation

# Phase 4 Settings
REENGAGEMENT_DAYS_DEFAULT=30
RATE_LIMIT_STEPS=60,120,300,600
COOLDOWN_AFTER_CONSECUTIVE=3
COOLDOWN_MINUTES=45

# Phase 5 License Configuration
LICENSE_KEY=
LICENSE_API_URL=http://localhost:8002
LICENSE_VERIFY_INTERVAL=900

# Auto-generated MongoDB credentials (will be set by installer)
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
EOF
fi

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    msg "Creating .env from .env.production.example..."
    cp .env.production.example .env
    success ".env file created"
else
    msg "Using existing .env file"
fi

# Generate MongoDB credentials if not present
if ! grep -q "^MONGO_INITDB_ROOT_USERNAME=" .env || [ -z "$(grep '^MONGO_INITDB_ROOT_USERNAME=' .env | cut -d= -f2-)" ]; then
    msg "Generating MongoDB credentials..."
    # Remove any existing empty credentials
    sed -i '/^MONGO_INITDB_ROOT_USERNAME=$/d' .env
    sed -i '/^MONGO_INITDB_ROOT_PASSWORD=$/d' .env
    
    # Add new credentials
    echo "MONGO_INITDB_ROOT_USERNAME=$(openssl rand -hex 8)" >> .env
    echo "MONGO_INITDB_ROOT_PASSWORD=$(openssl rand -hex 16)" >> .env
    success "MongoDB credentials generated"
fi

# Handle license configuration
LICENSE_KEY_ENV=$(grep -E '^LICENSE_KEY=' .env || true)
if [ -z "$LICENSE_KEY_ENV" ] || [ "$(echo "$LICENSE_KEY_ENV" | cut -d= -f2-)" = "" ]; then
    echo
    msg "License Configuration"
    echo "The system can run in two modes:"
    echo "  1. Development mode (no licensing restrictions)"
    echo "  2. Production mode (with SaaS licensing)"
    echo
    read -p "Enter LICENSE_KEY (leave empty for development mode): " LK || LK=""
    
    # Update or add LICENSE_KEY
    if grep -q '^LICENSE_KEY=' .env; then
        sed -i "s/^LICENSE_KEY=.*/LICENSE_KEY=${LK:-}/" .env
    else
        echo "LICENSE_KEY=${LK:-}" >> .env
    fi
    
    if [ -n "$LK" ]; then
        success "License key configured for production mode"
    else
        success "Configured for development mode (no licensing)"
    fi
fi

# Clean up any previous installation
msg "Cleaning up previous installation..."
$DOCKER_COMPOSE down --remove-orphans >/dev/null 2>&1 || true

# Start Docker services
msg "Starting Docker services (this may take a few minutes)..."
echo "Building and starting: mongo, backend, frontend, init..."
$DOCKER_COMPOSE -f docker-compose.yml up -d --build

# Wait for MongoDB to be healthy
msg "Waiting for MongoDB to be healthy..."
timeout=60
counter=0
until $DOCKER_COMPOSE ps mongo | grep -q "healthy" || [ $counter -eq $timeout ]; do 
    sleep 2
    counter=$((counter + 1))
    if [ $((counter % 10)) -eq 0 ]; then
        echo "  Still waiting for MongoDB... ($counter/${timeout}s)"
    fi
done

if [ $counter -eq $timeout ]; then
    err "MongoDB failed to become healthy within ${timeout} seconds"
    echo "Check logs with: $DOCKER_COMPOSE logs mongo"
    exit 1
fi

success "MongoDB is healthy"

# Initialize database
msg "Initializing database indexes and TTLs..."
if $DOCKER_COMPOSE run --rm init; then
    success "Database initialization complete"
else
    warn "Database initialization had some issues, but continuing..."
fi

# Service URLs
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
FRONTEND_URL=${FRONTEND_URL:-"http://localhost:8080"}

# Health checks
msg "Performing health checks..."

# Wait for backend to be ready
echo "  Checking backend health..."
timeout=30
counter=0
until curl -fsS "$BACKEND_URL/api/system/health" >/dev/null 2>&1 || [ $counter -eq $timeout ]; do
    sleep 2
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    err "Backend health check failed"
    echo "Check logs with: $DOCKER_COMPOSE logs backend"
    exit 1
fi

success "Backend is healthy"

# Check frontend
echo "  Checking frontend..."
timeout=15
counter=0
until curl -fsS "$FRONTEND_URL" >/dev/null 2>&1 || [ $counter -eq $timeout ]; do
    sleep 1
    counter=$((counter + 1))
done

if [ $counter -eq $timeout ]; then
    warn "Frontend health check failed, but backend is working"
    echo "You may need to wait a moment for frontend to fully load"
else
    success "Frontend is healthy"
fi

# License verification
LICENSE_KEY_VALUE=$(grep '^LICENSE_KEY=' .env | cut -d= -f2- || echo "")
if [ -n "$LICENSE_KEY_VALUE" ]; then
    msg "Verifying license status..."
    if LICENSE_RESPONSE=$(curl -fsS "$BACKEND_URL/api/license/status" 2>/dev/null); then
        echo "$LICENSE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('license_status', {})
    licensed = status.get('licensed', False)
    state = status.get('status', 'unknown')
    
    if state == 'no_license_required':
        print('  📋 Running in development mode (no licensing)')
    elif licensed:
        plan = status.get('plan', 'N/A')
        customer = status.get('customer_id', 'N/A')
        print(f'  ✅ License valid - Plan: {plan}, Customer: {customer}')
    else:
        message = status.get('message', 'Unknown error')
        print(f'  ❌ License invalid: {message}')
except:
    print('  ⚠️  Could not parse license status')
"
    else
        warn "Could not verify license status"
    fi
fi

# Installation complete
echo
success "🎉 Installation complete!"
echo
echo "🌐 Access URLs:"
echo "   Frontend:  $FRONTEND_URL"
echo "   Backend:   $BACKEND_URL"
echo
echo "🔧 Management Commands:"
echo "   View status:     $DOCKER_COMPOSE ps"
echo "   View logs:       $DOCKER_COMPOSE logs -f"
echo "   Stop services:   $DOCKER_COMPOSE down"
echo "   Restart:         $DOCKER_COMPOSE restart"
echo
echo "📖 Quick Commands:"
echo "   make up          # Start services"
echo "   make down        # Stop/remove services"  
echo "   make logs        # Stream logs"
echo "   make seed        # Reinitialize database"
echo "   make clean       # Full cleanup"
echo

# Show license information
LICENSE_KEY_VALUE=$(grep '^LICENSE_KEY=' .env | cut -d= -f2- || echo "")
if [ -n "$LICENSE_KEY_VALUE" ]; then
    echo "🔐 License Management:"
    echo "   License status:  curl $BACKEND_URL/api/license/status"
    echo "   Task creation:   curl -X POST $BACKEND_URL/api/tasks/create"
    echo
    echo "📚 For license management, see: ./LICENSED_DISTRIBUTION.md"
else
    echo "🔓 Development Mode:"
    echo "   No licensing restrictions active"
    echo "   To enable licensing, set LICENSE_KEY in .env and restart"
fi

echo
echo "🚀 Your iOS Instagram Automation system is ready!"
echo "   Open $FRONTEND_URL to get started"
echo
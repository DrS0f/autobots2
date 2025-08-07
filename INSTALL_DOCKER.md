# Instagram Automation - Docker Deployment Guide

Complete guide for deploying the iOS Instagram automation system using Docker containers with optional SaaS licensing.

## Prerequisites

### Required Software
- **Docker Engine** 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Make** (usually pre-installed on macOS/Linux)

### System Requirements
- **Minimum**: 2 CPU cores, 4GB RAM, 10GB disk space
- **Recommended**: 4 CPU cores, 8GB RAM, 50GB disk space
- **Operating System**: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows 10+ with WSL2

### Verify Installation
```bash
# Check Docker installation
docker --version
docker-compose --version

# Verify Docker daemon is running
docker info

# Test Docker permissions (Linux users)
docker run hello-world
```

---

## Quick Start (Local Development)

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd instagram-automation

# Create environment file from template
make env-dev
# OR manually: cp .env.example .env

# Review and update environment variables
nano .env  # Update passwords and settings
```

### 2. License Configuration (Optional)
For development, the system runs without license restrictions. For production licensing:

```bash
# Add license configuration to .env
echo "LICENSE_KEY=your-license-key-here" >> .env
echo "LICENSE_API_URL=http://localhost:8002" >> .env
echo "LICENSE_VERIFY_INTERVAL=900" >> .env
```

See [Licensed Distribution Guide](./LICENSED_DISTRIBUTION.md) for complete licensing setup.

### 3. Start Services
```bash
# Start all services (backend + frontend + MongoDB)
make up

# Initialize database with indexes and seed data
make seed

# Check service status
make status
```

### 3. Access Applications
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MongoDB**: mongodb://localhost:27017

### 4. View Logs
```bash
# View all logs
make logs

# View specific service logs
make logs-backend
make logs-frontend
make logs-mongo
```

---

## Production Deployment

### 1. Server Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

### 2. Production Configuration
```bash
# Create production environment file
make env-prod
# OR manually: cp .env.production.example .env.production

# Edit production settings
nano .env.production
```

**Important Production Settings:**
```bash
# Change default passwords!
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=YOUR_SECURE_PASSWORD_HERE
MONGO_APP_PASSWORD=YOUR_APP_PASSWORD_HERE

# Update backend URL with your domain
REACT_APP_BACKEND_URL=https://api.yourdomain.com

# Disable test data
SEED_TEST_DATA=false
NODE_ENV=production
```

### 3. Deploy Production Services
```bash
# Start production services
docker-compose --env-file .env.production up -d

# Initialize database (without test data)
docker-compose --env-file .env.production --profile init run --rm init

# Verify deployment
docker-compose ps
make health
```

### 4. Set Up Reverse Proxy (Nginx)
```nginx
# /etc/nginx/sites-available/instagram-automation
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Set Up SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

---

## Database Operations

### Initialize Database
```bash
# First time setup - create indexes and seed sample data
make seed

# Clean database and re-seed
make clean-seed

# Production initialization (no test data)
SEED_TEST_DATA=false make seed
```

### Backup and Restore
```bash
# Create database backup
make backup-db

# Restore from backup
make restore-db BACKUP_PATH=./backups/mongodb-20241229-120000

# List available backups
ls -la ./backups/
```

### Database Management
```bash
# Access MongoDB shell
make shell-mongo

# View database statistics
make stats

# Monitor database logs
make logs-mongo
```

---

## Monitoring and Maintenance

### Health Checks
```bash
# Check service health
make health

# View resource usage
make stats

# Show running processes
make top
```

### Log Management
```bash
# View logs (last 100 lines, follow mode)
make logs

# View specific service logs
make logs-backend
make logs-frontend
make logs-mongo

# Filter logs by timestamp
docker-compose logs --since="2024-12-29T10:00:00" backend
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Network usage
docker network ls
```

---

## Development Workflow

### Development Mode
```bash
# Start in development mode (with hot reload)
make dev

# Build images from scratch
make build

# Run tests
make test

# Code formatting and linting
make lint
make format
```

### Debugging
```bash
# Access container shells
make shell-backend   # Backend Python shell
make shell-frontend  # Frontend Node.js shell
make shell-mongo     # MongoDB shell

# View container processes
make top

# Inspect service configuration
docker-compose config
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port conflicts
sudo netstat -tulpn | grep -E ':(3000|8000|27017)'

# Check logs for errors
make logs
```

#### Database Connection Issues
```bash
# Verify MongoDB is running
make status

# Test database connectivity
make shell-mongo

# Check MongoDB logs
make logs-mongo

# Restart MongoDB
docker-compose restart mongo
```

#### Permission Errors (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Fix file permissions
sudo chown -R $USER:$USER .

# Restart Docker daemon
sudo systemctl restart docker
```

#### Port Already in Use
```bash
# Find process using port
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :27017

# Kill conflicting process
sudo kill -9 <PID>

# Or use different ports in .env file
```

### Performance Issues
```bash
# Increase Docker resources (Docker Desktop)
# Settings > Resources > Advanced
# RAM: 4GB+ recommended
# CPUs: 2+ recommended

# Clean up Docker system
docker system prune -a
docker volume prune

# Monitor resource usage
make stats
```

### Reset Everything
```bash
# Complete cleanup (DESTROYS ALL DATA!)
make clean

# Restart from scratch
make up
make seed
```

---

## Security Considerations

### Production Security Checklist
- [ ] Change all default passwords
- [ ] Use strong, unique passwords
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (UFW/iptables)
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Access logging
- [ ] Rate limiting

### Firewall Configuration (Ubuntu)
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Block direct access to services (optional)
sudo ufw deny 3000
sudo ufw deny 8000
sudo ufw deny 27017

# Check firewall status
sudo ufw status
```

### Backup Security
```bash
# Encrypt backups
gpg --cipher-algo AES256 --compress-algo 1 --symmetric backup.tar.gz

# Store backups securely (AWS S3, encrypted)
aws s3 cp backup.tar.gz.gpg s3://your-backup-bucket/
```

---

## Advanced Configuration

### Custom Domains
1. Update `REACT_APP_BACKEND_URL` in `.env.production`
2. Configure reverse proxy (Nginx/Apache)
3. Set up SSL certificates
4. Update DNS records

### Scaling
```bash
# Increase backend workers
docker-compose up -d --scale backend=3

# Use external MongoDB
# Update MONGO_URL in .env to point to external database

# Load balancer configuration (example with nginx)
upstream backend {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}
```

### External Services Integration
```bash
# Redis for caching (optional)
docker-compose -f docker-compose.yml -f docker-compose.redis.yml up -d

# Monitoring with Prometheus/Grafana
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

---

## Maintenance Tasks

### Regular Maintenance
```bash
# Weekly tasks
make backup-db
docker system prune -f
make logs > system-logs-$(date +%Y%m%d).txt

# Monthly tasks
sudo apt update && sudo apt upgrade -y
docker-compose pull  # Update base images
make rebuild         # Rebuild with updates
```

### Updates
```bash
# Update application code
git pull origin main

# Rebuild and restart services
make rebuild

# Apply database migrations (if any)
make seed
```

---

## Support and Documentation

### Additional Resources
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MongoDB Documentation](https://docs.mongodb.com/)

### Getting Help
1. Check logs: `make logs`
2. Review this documentation
3. Check GitHub issues
4. Contact support team

---

## Quick Reference

### Essential Commands
```bash
make up           # Start services
make down         # Stop services
make logs         # View logs
make seed         # Initialize database
make health       # Check service health
make clean        # Remove everything
```

### File Locations
- **Configuration**: `.env` or `.env.production`
- **Logs**: `docker-compose logs`
- **Backups**: `./backups/`
- **Volumes**: Docker managed volumes
- **SSL Certs**: `/etc/letsencrypt/live/yourdomain.com/`

---

**🎉 Your Instagram Automation system is now ready for production use!**

For questions or issues, please refer to the troubleshooting section or contact the development team.
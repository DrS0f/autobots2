# Instagram Automation Docker Management
# Usage: make [target]

# Variables
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = instagram-automation
COMPOSE_CMD = docker-compose -f $(COMPOSE_FILE) -p $(PROJECT_NAME)

# Default environment file
ENV_FILE = .env

# Colors for output
BLUE = \033[34m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
NC = \033[0m # No Color

.PHONY: help up down restart logs seed clean test lint build status health dev prod

# Default target
help: ## Show this help message
	@echo "$(BLUE)Instagram Automation - Docker Management$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Core Docker operations
up: ## Start all services in detached mode
	@echo "$(BLUE)🚀 Starting Instagram Automation services...$(NC)"
	$(COMPOSE_CMD) up -d
	@echo "$(GREEN)✅ Services started successfully!$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:3000"
	@echo "$(YELLOW)Backend:$(NC)  http://localhost:8000"
	@echo "$(YELLOW)MongoDB:$(NC)  mongodb://localhost:27017"

down: ## Stop and remove all services
	@echo "$(BLUE)🛑 Stopping Instagram Automation services...$(NC)"
	$(COMPOSE_CMD) down -v
	@echo "$(GREEN)✅ Services stopped and volumes removed$(NC)"

restart: down up ## Restart all services

# Database operations
seed: ## Initialize database with indexes and seed data
	@echo "$(BLUE)🌱 Initializing database...$(NC)"
	$(COMPOSE_CMD) --profile init run --rm init
	@echo "$(GREEN)✅ Database initialized successfully$(NC)"

clean-seed: ## Clean database and re-seed
	@echo "$(BLUE)🧹 Cleaning and re-seeding database...$(NC)"
	$(COMPOSE_CMD) --profile init run --rm -e CLEANUP_TEST_DATA=true -e SEED_TEST_DATA=true init
	@echo "$(GREEN)✅ Database cleaned and re-seeded$(NC)"

# Monitoring and logs
logs: ## Show logs for all services (follow mode)
	@echo "$(BLUE)📋 Following logs (Ctrl+C to stop)...$(NC)"
	$(COMPOSE_CMD) logs -f --tail=100

logs-backend: ## Show backend logs only
	$(COMPOSE_CMD) logs -f --tail=100 backend

logs-frontend: ## Show frontend logs only
	$(COMPOSE_CMD) logs -f --tail=100 frontend

logs-mongo: ## Show MongoDB logs only
	$(COMPOSE_CMD) logs -f --tail=100 mongo

status: ## Show status of all services
	@echo "$(BLUE)📊 Service Status:$(NC)"
	$(COMPOSE_CMD) ps

health: ## Check health of all services
	@echo "$(BLUE)🏥 Health Check Results:$(NC)"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=com.docker.compose.project=$(PROJECT_NAME)"

# Development operations
dev: ## Start services in development mode with file watching
	@echo "$(BLUE)🔧 Starting in development mode...$(NC)"
	$(COMPOSE_CMD) -f docker-compose.yml -f docker-compose.dev.yml up

build: ## Build all images from scratch
	@echo "$(BLUE)🏗️ Building all images...$(NC)"
	$(COMPOSE_CMD) build --no-cache
	@echo "$(GREEN)✅ Build completed$(NC)"

rebuild: ## Force rebuild and restart services
	@echo "$(BLUE)🔄 Rebuilding and restarting...$(NC)"
	$(COMPOSE_CMD) down
	$(COMPOSE_CMD) build --no-cache
	$(COMPOSE_CMD) up -d
	@echo "$(GREEN)✅ Rebuild and restart completed$(NC)"

# Testing and quality
test: ## Run backend tests in container
	@echo "$(BLUE)🧪 Running backend tests...$(NC)"
	$(COMPOSE_CMD) run --rm backend python -m pytest /app/backend/test_concurrency_control.py -v
	@echo "$(GREEN)✅ Tests completed$(NC)"

lint: ## Run linting on backend and frontend code
	@echo "$(BLUE)🔍 Running linters...$(NC)"
	@echo "$(YELLOW)Backend (flake8):$(NC)"
	$(COMPOSE_CMD) run --rm backend flake8 /app/backend --max-line-length=120 --ignore=E203,W503
	@echo "$(YELLOW)Frontend (eslint):$(NC)"
	$(COMPOSE_CMD) run --rm frontend yarn lint
	@echo "$(GREEN)✅ Linting completed$(NC)"

format: ## Format code with black and prettier
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@echo "$(YELLOW)Backend (black):$(NC)"
	$(COMPOSE_CMD) run --rm backend black /app/backend
	@echo "$(YELLOW)Frontend (prettier):$(NC)"
	$(COMPOSE_CMD) run --rm frontend yarn format
	@echo "$(GREEN)✅ Code formatting completed$(NC)"

# Production operations
prod: ## Start services in production mode
	@echo "$(BLUE)🚀 Starting in production mode...$(NC)"
	$(COMPOSE_CMD) --env-file .env.production up -d
	@echo "$(GREEN)✅ Production services started$(NC)"

# Maintenance operations
clean: ## Remove all containers, volumes, and images
	@echo "$(RED)🧹 WARNING: This will remove all data and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		echo "$(BLUE)Cleaning up...$(NC)"; \
		$(COMPOSE_CMD) down -v --rmi all --remove-orphans; \
		docker system prune -f; \
		echo "$(GREEN)✅ Cleanup completed$(NC)"; \
	else \
		echo ""; \
		echo "$(YELLOW)Cleanup cancelled$(NC)"; \
	fi

volumes: ## List all volumes
	@echo "$(BLUE)💾 Docker Volumes:$(NC)"
	@docker volume ls --filter "label=com.docker.compose.project=$(PROJECT_NAME)"

backup-db: ## Backup MongoDB data
	@echo "$(BLUE)💾 Backing up MongoDB...$(NC)"
	@mkdir -p ./backups
	docker exec $(PROJECT_NAME)_mongo_1 mongodump --db instagram_automation --out /tmp/backup
	docker cp $(PROJECT_NAME)_mongo_1:/tmp/backup ./backups/mongodb-$(shell date +%Y%m%d-%H%M%S)
	@echo "$(GREEN)✅ Database backup completed$(NC)"

restore-db: ## Restore MongoDB data (requires BACKUP_PATH)
	@if [ -z "$(BACKUP_PATH)" ]; then \
		echo "$(RED)❌ BACKUP_PATH is required. Usage: make restore-db BACKUP_PATH=./backups/mongodb-20241229-120000$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)📦 Restoring MongoDB from $(BACKUP_PATH)...$(NC)"
	docker cp $(BACKUP_PATH) $(PROJECT_NAME)_mongo_1:/tmp/restore
	docker exec $(PROJECT_NAME)_mongo_1 mongorestore --db instagram_automation --drop /tmp/restore/instagram_automation
	@echo "$(GREEN)✅ Database restore completed$(NC)"

# Environment management
env-dev: ## Copy development environment template
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Development .env file created$(NC)"; \
		echo "$(YELLOW)📝 Please review and update .env file$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ .env file already exists$(NC)"; \
	fi

env-prod: ## Copy production environment template
	@if [ ! -f .env.production ]; then \
		cp .env.production.example .env.production; \
		echo "$(GREEN)✅ Production .env file created$(NC)"; \
		echo "$(YELLOW)📝 Please review and update .env.production file$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ .env.production file already exists$(NC)"; \
	fi

# Quick access commands
shell-backend: ## Access backend container shell
	$(COMPOSE_CMD) exec backend bash

shell-frontend: ## Access frontend container shell
	$(COMPOSE_CMD) exec frontend sh

shell-mongo: ## Access MongoDB shell
	$(COMPOSE_CMD) exec mongo mongosh

# Performance monitoring
stats: ## Show resource usage statistics
	@echo "$(BLUE)📊 Container Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" \
		$(shell $(COMPOSE_CMD) ps -q)

top: ## Show running processes in containers
	@echo "$(BLUE)🔝 Running Processes:$(NC)"
	$(COMPOSE_CMD) top

# Installation verification
check: ## Verify all prerequisites are installed
	@echo "$(BLUE)✅ Checking prerequisites...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker is not installed$(NC)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)❌ Docker Compose is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✅ All prerequisites are installed$(NC)"
	@echo "$(YELLOW)Docker version:$(NC) $$(docker --version)"
	@echo "$(YELLOW)Docker Compose version:$(NC) $$(docker-compose --version)"
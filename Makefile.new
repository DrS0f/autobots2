# Instagram Automation Docker Management
# Usage: make [target]

# Variables
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = instagram-automation
COMPOSE_CMD = docker compose -f $(COMPOSE_FILE)

# Default environment file
ENV_FILE = .env

# Colors for output
BLUE = \033[34m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
NC = \033[0m # No Color

.PHONY: help up down restart logs seed install clean test lint build status health dev

# Default target
help: ## Show this help message
	@echo "$(BLUE)Instagram Automation - Docker Management$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Installation and setup
install: ## 1-click installer for fresh machines
	@echo "$(BLUE)🚀 Running 1-click installer...$(NC)"
	./scripts/install.sh

# Core Docker operations
up: ## Start all services in detached mode
	@echo "$(BLUE)🚀 Starting Instagram Automation services...$(NC)"
	$(COMPOSE_CMD) up -d
	@echo "$(GREEN)✅ Services started successfully!$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:8080"
	@echo "$(YELLOW)Backend:$(NC)  http://localhost:8000"
	@echo "$(YELLOW)MongoDB:$(NC)  mongodb://localhost:27017"

down: ## Stop and remove all services
	@echo "$(BLUE)🛑 Stopping Instagram Automation services...$(NC)"
	$(COMPOSE_CMD) down --remove-orphans
	@echo "$(GREEN)✅ Services stopped$(NC)"

restart: down up ## Restart all services

# Database operations
seed: ## Initialize/reinitialize database with indexes and TTLs
	@echo "$(BLUE)🌱 Initializing database...$(NC)"
	$(COMPOSE_CMD) run --rm init
	@echo "$(GREEN)✅ Database initialized successfully$(NC)"

# Monitoring and logs
logs: ## Show logs for all services (follow mode)
	@echo "$(BLUE)📋 Following logs (Ctrl+C to stop)...$(NC)"
	$(COMPOSE_CMD) logs -f --tail=200

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
	@$(COMPOSE_CMD) ps --format table

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

# Maintenance operations
clean: ## Remove all containers, volumes, and images (full cleanup)
	@echo "$(RED)🧹 Performing full cleanup...$(NC)"
	$(COMPOSE_CMD) down -v --remove-orphans || true
	docker system prune -af || true
	@echo "$(GREEN)✅ Full cleanup completed$(NC)"

# Environment management
env-setup: ## Setup environment files from examples
	@if [ ! -f .env ]; then \
		if [ -f .env.production.example ]; then \
			cp .env.production.example .env; \
			echo "$(GREEN)✅ Environment file created from .env.production.example$(NC)"; \
		elif [ -f .env.example ]; then \
			cp .env.example .env; \
			echo "$(GREEN)✅ Environment file created from .env.example$(NC)"; \
		else \
			echo "$(RED)❌ No environment example file found$(NC)"; \
			exit 1; \
		fi; \
		echo "$(YELLOW)📝 Please review and update .env file before running 'make up'$(NC)"; \
	else \
		echo "$(YELLOW)⚠️ .env file already exists$(NC)"; \
	fi

# Quick access commands
shell-backend: ## Access backend container shell
	$(COMPOSE_CMD) exec backend bash

shell-frontend: ## Access frontend container shell  
	$(COMPOSE_CMD) exec frontend sh

shell-mongo: ## Access MongoDB shell
	$(COMPOSE_CMD) exec mongo mongosh

# License operations (if applicable)
license-status: ## Check license status
	@curl -s http://localhost:8000/api/license/status | python3 -m json.tool 2>/dev/null || echo "$(RED)❌ Could not check license status$(NC)"

# Testing
test: ## Run basic smoke tests
	@echo "$(BLUE)🧪 Running smoke tests...$(NC)"
	@echo "$(YELLOW)Testing backend health...$(NC)"
	@curl -f http://localhost:8000/api/system/health >/dev/null 2>&1 && echo "$(GREEN)✅ Backend: OK$(NC)" || echo "$(RED)❌ Backend: FAIL$(NC)"
	@echo "$(YELLOW)Testing frontend...$(NC)"
	@curl -f http://localhost:8080 >/dev/null 2>&1 && echo "$(GREEN)✅ Frontend: OK$(NC)" || echo "$(RED)❌ Frontend: FAIL$(NC)"

# Installation verification
check: ## Verify all prerequisites are installed
	@echo "$(BLUE)✅ Checking prerequisites...$(NC)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)❌ Docker is not installed$(NC)"; exit 1; }
	@command -v curl >/dev/null 2>&1 || { echo "$(RED)❌ curl is not installed$(NC)"; exit 1; }
	@docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)❌ Docker Compose is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✅ All prerequisites are installed$(NC)"
	@echo "$(YELLOW)Docker version:$(NC) $$(docker --version)"
	@echo "$(YELLOW)Docker Compose:$(NC) Available"
.PHONY: help setup start stop restart destroy status logs shell pentester-shell merge-scenarios validate-scenarios lab-web-shell lab-web-logs

DOCKER_COMPOSE := docker-compose

help:
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║   GitLab Attack Lab - Commands                 ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Complete setup (ONE COMMAND!)"
	@echo "  make merge-scenarios     - Merge scenario configs into a single YAML"
	@echo "  make validate-scenarios  - Validate scenarios for duplicates and references"
	@echo ""
	@echo "Container Management:"
	@echo "  make start              - Start services"
	@echo "  make stop               - Stop services"
	@echo "  make restart            - Restart services"
	@echo "  make destroy            - Stop and remove all data (volumes)"
	@echo "  make shell              - Enter GitLab container"
	@echo "  make pentester-shell    - Enter pentester container"
	@echo "  make lab-web-shell      - Enter lab web app container"
	@echo ""
	@echo "Web App:"
	@echo "  make lab-web-start      - Start only the lab web app"
	@echo "  make lab-web-logs       - Follow lab web app logs"
	@echo ""
	@echo "Information:"
	@echo "  make status             - Show container status"
	@echo "  make logs               - Follow GitLab logs"
	@echo "  make help               - Show this help"
	@echo ""

setup:
	@if [ ! -f .env ]; then \
		echo "[*] Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "[+] .env file created!"; \
	fi
	@bash setup.sh

merge-scenarios:
	@python3 scripts/merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --output /tmp/gitlab-lab-merged.yml
	@echo "[+] Merged config written to /tmp/gitlab-lab-merged.yml"

validate-scenarios:
	@python3 scripts/merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --validate-only
	@echo "[+] Scenario validation passed"

start:
	@echo "[*] Starting services..."
	$(DOCKER_COMPOSE) up -d
	@echo "[+] Services started!"

stop:
	@echo "[*] Stopping services..."
	$(DOCKER_COMPOSE) down
	@echo "[+] Services stopped!"

restart:
	@echo "[*] Restarting services..."
	$(DOCKER_COMPOSE) restart
	@echo "[+] Services restarted!"

destroy:
	@echo "[*] Destroying lab (containers + volumes)..."
	$(DOCKER_COMPOSE) down -v
	@echo "[+] Lab destroyed!"

status:
	@$(DOCKER_COMPOSE) ps

logs:
	@$(DOCKER_COMPOSE) logs -f gitlab

gitlab-shell:
	@$(DOCKER_COMPOSE) exec gitlab /bin/bash

shell:
	@$(DOCKER_COMPOSE) exec pentester /bin/bash

lab-web-shell:
	@$(DOCKER_COMPOSE) exec lab-web /bin/bash

lab-web-start:
	@$(DOCKER_COMPOSE) up -d --build lab-web

lab-web-logs:
	@$(DOCKER_COMPOSE) logs -f lab-web

.DEFAULT_GOAL := help

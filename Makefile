.PHONY: help setup test-ci test-deployment start stop restart destroy status logs shell gitlab-shell merge-scenarios validate-scenarios lab-web-shell lab-web-logs lab-web-restart lab-web-rebuild lab-web-watch

DOCKER_COMPOSE := docker compose
# setup.sh installs test/scenario-tooling dependencies into a project-local venv
# (PEP 668 blocks system-wide pip installs on modern Debian/Ubuntu). Each Makefile
# recipe line runs in its own shell, so that venv's PATH never reaches us here -
# point straight at its python3 when present instead of falling back to the system one.
PYTHON := $(shell [ -x .venv/bin/python3 ] && echo .venv/bin/python3 || echo python3)

help:
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║   GitLab Attack Lab - Commands                 ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup:"
	@echo "  make setup               - Start the full attack lab"
	@echo "  make test-ci             - Run offline CI/unit-style tests"
	@echo "  make test-deployment     - Validate deployed lab state and scenarios"
	@echo "  make merge-scenarios     - Merge scenario configs into a single YAML"
	@echo "  make validate-scenarios  - Validate scenarios for duplicates and references"
	@echo ""
	@echo "Container Management:"
	@echo "  make start              - Start services"
	@echo "  make stop               - Stop services"
	@echo "  make restart            - Restart services"
	@echo "  make destroy            - Stop and remove all data (volumes)"
	@echo "  make gitlab-shell       - Enter GitLab container"
	@echo "  make shell              - Enter pentester container"
	@echo "  make lab-web-shell      - Enter lab web app container"
	@echo ""
	@echo "Web App:"
	@echo "  make lab-web-start      - Start only the lab web app"
	@echo "  make lab-web-restart    - Restart the lab web app"
	@echo "  make lab-web-rebuild    - Rebuild and restart the lab web app"
	@echo "  make lab-web-watch      - Watch sources and auto-update the lab web app"
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
	@$(MAKE) --no-print-directory test-deployment

test-ci:
	@$(PYTHON) -m pytest tests/ci -m ci -v --tb=short

test-deployment:
	@$(PYTHON) -m pytest tests/deployment -m deployment -v --tb=short

merge-scenarios:
	@$(PYTHON) scripts/merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --output /tmp/gitlab-lab-merged.yml
	@echo "[+] Merged config written to /tmp/gitlab-lab-merged.yml"

validate-scenarios:
	@$(PYTHON) scripts/merge-scenarios.py --base lab-config/base.yml --scenarios lab-config/scenarios --validate-only
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
	@RUNNER_CONTAINERS=$$(docker ps -aq --filter "network=lab-network" --filter "name=runner-"); \
	if [ -n "$$RUNNER_CONTAINERS" ]; then \
		echo "[*] Removing runner job/service containers on lab-network..."; \
		docker rm -f $$RUNNER_CONTAINERS >/dev/null; \
	fi
	$(DOCKER_COMPOSE) down --remove-orphans -v
	@RUNNER_VOLUMES=$$(docker volume ls -q --filter "name=runner-"); \
	if [ -n "$$RUNNER_VOLUMES" ]; then \
		echo "[*] Removing runner cache volumes..."; \
		docker volume rm $$RUNNER_VOLUMES >/dev/null 2>&1 || true; \
	fi
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

lab-web-restart:
	@echo "[*] Restarting lab web app..."
	@$(DOCKER_COMPOSE) restart lab-web
	@echo "[+] Lab web app restarted!"

lab-web-rebuild:
	@echo "[*] Rebuilding and restarting lab web app..."
	@$(DOCKER_COMPOSE) up -d --build --force-recreate lab-web
	@echo "[+] Lab web app rebuilt and restarted!"

lab-web-watch:
	@echo "[*] Watching lab web app sources for changes (Ctrl+C to stop)..."
	@$(DOCKER_COMPOSE) watch lab-web

lab-web-logs:
	@$(DOCKER_COMPOSE) logs -f lab-web

.DEFAULT_GOAL := help

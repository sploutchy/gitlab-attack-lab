.PHONY: help setup start stop restart destroy status logs shell pentester-shell

DOCKER_COMPOSE := docker-compose

help:
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║   GitLab Attack Lab - Commands                 ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Complete setup (ONE COMMAND!)"
	@echo ""
	@echo "Container Management:"
	@echo "  make start              - Start services"
	@echo "  make stop               - Stop services"
	@echo "  make restart            - Restart services"
	@echo "  make destroy            - Stop and remove all data (volumes)"
	@echo "  make shell              - Enter GitLab container"
	@echo "  make pentester-shell    - Enter pentester container"
	@echo ""
	@echo "Information:"
	@echo "  make status             - Show container status"
	@echo "  make logs               - Follow GitLab logs"
	@echo "  make help               - Show this help"
	@echo ""

setup:
	@bash setup.sh

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

shell:
	@$(DOCKER_COMPOSE) exec gitlab /bin/bash

pentester-shell:
	@$(DOCKER_COMPOSE) exec pentester /bin/bash

.DEFAULT_GOAL := help

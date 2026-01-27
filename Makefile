# Makefile for Lunaris Civitas simulation engine

PYTHON := .venv/bin/python
PIP := .venv/bin/pip
VENV := .venv

.PHONY: setup install run run-stop resume resume-stop test docs docs-serve docs-stop clean help

help:
	@echo "Available targets:"
	@echo "  make setup    - Create virtual environment and install dependencies"
	@echo "  make install  - Install dependencies (creates venv if needed)"
	@echo "  make run      - Run simulation with dev config in background (starts new, overwrites logs)"
	@echo "  make run-stop - Stop the running simulation"
	@echo "  make resume   - Resume simulation from database (appends to logs, preserves DB)"
	@echo "  make resume-stop - Stop the resumed simulation"
	@echo "  make test     - Run tests"
	@echo "  make docs     - Build documentation"
	@echo "  make docs-serve [PORT=5001] - Serve documentation locally in background (default port: 8000)"
	@echo "  make docs-stop - Stop the documentation server"
	@echo "  make modifier-add - Interactive tool to add modifiers"
	@echo "  make modifier-list - View all modifiers from database"
	@echo "  make world-state-view - Display current world state summary"
	@echo "  make resources-view - Display all resources and their states"
	@echo "  make export-resources - Export resource history to CSV"
	@echo "  make export-entities - Export entity history to CSV"
	@echo "  make clean    - Clean build artifacts"
	@echo "  make help     - Show this help message"

setup: $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Setup complete! Activate with: source .venv/bin/activate"

$(VENV):
	python3 -m venv $(VENV)

install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Creating .venv..."; \
		python3 -m venv $(VENV); \
	fi
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run: $(VENV)
	@mkdir -p _running/logs _running/pids
	@if [ -f _running/pids/simulation.pid ]; then \
		echo "Simulation is already running (PID: $$(cat _running/pids/simulation.pid))"; \
		exit 1; \
	fi
	@if [ -z "$(CONFIG)" ]; then \
		$(PYTHON) -m src --config configs/dev.yml > _running/logs/simulation.log 2>&1 & \
		echo $$! > _running/pids/simulation.pid; \
		echo "Simulation started in background (PID: $$(cat _running/pids/simulation.pid))"; \
		echo "Logs: _running/logs/simulation.log"; \
		echo "Stop with: make run-stop"; \
	else \
		$(PYTHON) -m src --config $(CONFIG) > _running/logs/simulation.log 2>&1 & \
		echo $$! > _running/pids/simulation.pid; \
		echo "Simulation started in background (PID: $$(cat _running/pids/simulation.pid))"; \
		echo "Logs: _running/logs/simulation.log"; \
		echo "Stop with: make run-stop"; \
	fi

run-stop:
	@if [ ! -f _running/pids/simulation.pid ]; then \
		echo "No simulation PID file found. Simulation may not be running."; \
		exit 1; \
	fi
	@PID=$$(cat _running/pids/simulation.pid); \
	if ps -p $$PID > /dev/null 2>&1; then \
		kill $$PID; \
		rm _running/pids/simulation.pid; \
		echo "Simulation stopped (PID: $$PID)"; \
	else \
		echo "Process $$PID not found. Removing stale PID file."; \
		rm _running/pids/simulation.pid; \
	fi

resume: $(VENV)
	@mkdir -p _running/logs _running/pids
	@if [ -f _running/pids/simulation.pid ]; then \
		echo "Simulation is already running (PID: $$(cat _running/pids/simulation.pid))"; \
		exit 1; \
	fi
	@$(PYTHON) -m src --resume >> _running/logs/simulation.log 2>&1 & \
	echo $$! > _running/pids/simulation.pid; \
	echo "Simulation resumed in background (PID: $$(cat _running/pids/simulation.pid))"; \
	echo "Logs: _running/logs/simulation.log (appending)"; \
	echo "Stop with: make resume-stop"

resume-stop:
	@if [ ! -f _running/pids/simulation.pid ]; then \
		echo "No simulation PID file found. Simulation may not be running."; \
		exit 1; \
	fi
	@PID=$$(cat _running/pids/simulation.pid); \
	if ps -p $$PID > /dev/null 2>&1; then \
		kill $$PID; \
		rm _running/pids/simulation.pid; \
		echo "Simulation stopped (PID: $$PID)"; \
	else \
		echo "Process $$PID not found. Removing stale PID file."; \
		rm _running/pids/simulation.pid; \
	fi

test: $(VENV)
	@if ! $(PYTHON) -m pytest --version > /dev/null 2>&1; then \
		echo "pytest not installed. Running: make install"; \
		$(PIP) install -r requirements.txt; \
	fi
	$(PYTHON) -m pytest tests/ -v

docs: $(VENV)
	$(PYTHON) -m mkdocs build

docs-serve: $(VENV)
	@mkdir -p _running/logs _running/pids
	@if [ -f _running/pids/docs.pid ]; then \
		echo "Documentation server is already running (PID: $$(cat _running/pids/docs.pid))"; \
		exit 1; \
	fi
	@if [ -z "$(PORT)" ]; then \
		$(PYTHON) -m mkdocs serve --dev-addr 127.0.0.1:8000 > _running/logs/docs.log 2>&1 & \
		echo $$! > _running/pids/docs.pid; \
		echo "Documentation server started in background (PID: $$(cat _running/pids/docs.pid), Port: 8000)"; \
		echo "Logs: _running/logs/docs.log"; \
		echo "Stop with: make docs-stop"; \
	else \
		$(PYTHON) -m mkdocs serve --dev-addr 127.0.0.1:$(PORT) > _running/logs/docs.log 2>&1 & \
		echo $$! > _running/pids/docs.pid; \
		echo "Documentation server started in background (PID: $$(cat _running/pids/docs.pid), Port: $(PORT))"; \
		echo "Logs: _running/logs/docs.log"; \
		echo "Stop with: make docs-stop"; \
	fi

docs-stop:
	@if [ ! -f _running/pids/docs.pid ]; then \
		echo "No documentation server PID file found. Server may not be running."; \
		exit 1; \
	fi
	@PID=$$(cat _running/pids/docs.pid); \
	if ps -p $$PID > /dev/null 2>&1; then \
		kill $$PID; \
		rm _running/pids/docs.pid; \
		echo "Documentation server stopped (PID: $$PID)"; \
	else \
		echo "Process $$PID not found. Removing stale PID file."; \
		rm _running/pids/docs.pid; \
	fi

modifier-add: $(VENV)
	$(PYTHON) -m src.cli.add_modifier

modifier-list: $(VENV)
	$(PYTHON) -m src.cli.view_modifiers

world-state-view: $(VENV)
	$(PYTHON) -m src.cli.view_world_state

resources-view: $(VENV)
	$(PYTHON) -m src.cli.view_resources

export-resources: $(VENV)
	@mkdir -p _running/exports
	$(PYTHON) -m src.cli.export_resources
	@echo "Resource history exported to _running/exports/"

export-entities: $(VENV)
	@mkdir -p _running/exports
	$(PYTHON) -m src.cli.export_entities
	@echo "Entity history exported to _running/exports/"

clean:
	@rm -rf _running/*.db
	@rm -rf _running/logs/*.log
	@rm -rf _running/pids/*.pid
	@rm -rf _running/exports/*.csv
	@rm -rf site/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned: _running, site, .pytest_cache, .coverage, htmlcov, __pycache__, *.pyc"

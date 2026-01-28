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
		kill $$PID 2>/dev/null || true; \
		COUNT=0; \
		while ps -p $$PID > /dev/null 2>&1 && [ $$COUNT -lt 10 ]; do \
			sleep 0.5; \
			COUNT=$$((COUNT + 1)); \
		done; \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "Process did not terminate, forcing kill..."; \
			kill -9 $$PID 2>/dev/null || true; \
			sleep 0.5; \
		fi; \
		rm -f _running/pids/docs.pid; \
		echo "Documentation server stopped (PID: $$PID)"; \
	else \
		echo "Process $$PID not found. Removing stale PID file."; \
		rm _running/pids/docs.pid; \
	fi

docs-restart: $(VENV)
	@PORT=$$(grep 'Serving on http://127\.0\.0\.1:' _running/logs/docs.log 2>/dev/null | sed -n 's/.*:\([0-9]\+\)\/.*/\1/p' | tail -1); \
	if [ -z "$$PORT" ]; then \
		echo "ERROR: Port not found in logs. Cannot restart."; \
		echo "Check _running/logs/docs.log for details."; \
		exit 1; \
	fi; \
	if [ -f _running/pids/docs.pid ]; then \
		make docs-stop; \
		sleep 1; \
	fi; \
	make docs-serve PORT=$$PORT; \
	sleep 2; \
	echo "Documentation server restarted (PID: $$(cat _running/pids/docs.pid), Port: $$PORT)"; \
	echo "Logs: _running/logs/docs.log"; \
	echo "Stop with: make docs-stop"

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
	@ACTIVE_PIDS=0; \
	KILL_PIDS=""; \
	if [ -f _running/pids/simulation.pid ]; then \
		PID=$$(cat _running/pids/simulation.pid 2>/dev/null); \
		if [ -n "$$PID" ] && ps -p $$PID > /dev/null 2>&1; then \
			ACTIVE_PIDS=$$((ACTIVE_PIDS + 1)); \
			KILL_PIDS="$$KILL_PIDS simulation ($$PID)"; \
		fi; \
	fi; \
	if [ -f _running/pids/docs.pid ]; then \
		PID=$$(cat _running/pids/docs.pid 2>/dev/null); \
		if [ -n "$$PID" ] && ps -p $$PID > /dev/null 2>&1; then \
			ACTIVE_PIDS=$$((ACTIVE_PIDS + 1)); \
			KILL_PIDS="$$KILL_PIDS docs ($$PID)"; \
		fi; \
	fi; \
	if [ $$ACTIVE_PIDS -gt 0 ]; then \
		echo "WARNING: Found $$ACTIVE_PIDS active process(es):$$KILL_PIDS"; \
		echo -n "Kill these processes and clean? (y/N): "; \
		read -r CONFIRM; \
		if [ "$$CONFIRM" != "y" ] && [ "$$CONFIRM" != "Y" ]; then \
			echo "Skipping cleanup of logs, pids, and database files."; \
			rm -rf _running/exports/*.csv; \
			rm -rf site/; \
			rm -rf .pytest_cache/; \
			rm -rf .coverage; \
			rm -rf htmlcov/; \
			find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true; \
			find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
			echo "Cleaned: _running/exports, site, .pytest_cache, .coverage, htmlcov, __pycache__, *.pyc"; \
			exit 0; \
		fi; \
		if [ -f _running/pids/simulation.pid ]; then \
			PID=$$(cat _running/pids/simulation.pid 2>/dev/null); \
			if [ -n "$$PID" ] && ps -p $$PID > /dev/null 2>&1; then \
				kill $$PID 2>/dev/null || true; \
				echo "Killed simulation process (PID: $$PID)"; \
			fi; \
		fi; \
		if [ -f _running/pids/docs.pid ]; then \
			PID=$$(cat _running/pids/docs.pid 2>/dev/null); \
			if [ -n "$$PID" ] && ps -p $$PID > /dev/null 2>&1; then \
				kill $$PID 2>/dev/null || true; \
				echo "Killed docs server process (PID: $$PID)"; \
			fi; \
		fi; \
	fi; \
	rm -rf _running/*.db; \
	rm -rf _running/logs/*.log; \
	rm -rf _running/pids/*.pid; \
	rm -rf _running/exports/*.csv; \
	rm -rf site/; \
	rm -rf .pytest_cache/; \
	rm -rf .coverage; \
	rm -rf htmlcov/; \
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true; \
	find . -type f -name "*.pyc" -delete 2>/dev/null || true; \
	echo "Cleaned: _running, site, .pytest_cache, .coverage, htmlcov, __pycache__, *.pyc"

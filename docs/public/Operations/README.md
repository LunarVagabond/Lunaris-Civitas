# Operations

## Running the Simulation

### Basic Run

```bash
make run
```

### Custom Configuration

```bash
python -m src --config path/to/config.yml
```

### Resume Simulation

**Recommended (appends to logs, preserves database):**
```bash
make resume
```

**Direct command:**
```bash
python -m src --resume
```

The `make resume` command:
- Resumes from the last saved state in the database
- Appends to existing log file (creates if missing)
- Preserves database and logs (doesn't clean anything)
- Runs in background like `make run`

Stop with: `make resume-stop` (or `make run-stop` - both work)

### Command Line Options

- `--config PATH`: Path to configuration file (YAML or JSON)
- `--db PATH`: Path to SQLite database (default: `_running/simulation.db`)
- `--resume`: Resume simulation from database
- `--max-ticks N`: Maximum number of ticks to run
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Make Commands

- `make setup` - Create virtual environment and install dependencies
- `make install` - Install dependencies (requires existing venv)
- `make run` - Run simulation with dev config (starts new, overwrites logs)
- `make run-stop` - Stop the running simulation
- `make resume` - Resume simulation from database (appends to logs, preserves DB)
- `make resume-stop` - Stop the resumed simulation
- `make test` - Run tests
- `make docs` - Build documentation
- `make docs-serve` - Serve documentation locally
- `make clean` - Clean build artifacts

## Database

The simulation uses SQLite for persistence. Database files are stored in `_running/` directory.

## Logging

Logs are written to `_running/simulation.log` by default. Log level can be configured in the config file or via command line.

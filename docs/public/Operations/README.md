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

## Exporting Data

### Export Resource History

Export resource history to CSV for analysis:

```bash
make export-resources
```

This exports all resource history to `_running/exports/resources_YYYYMMDD_HHMMSS.csv`.

**Advanced options:**

```bash
# Export specific resources
python -m src.cli.export_resources --resource-id food --resource-id water

# Export by tick range
python -m src.cli.export_resources --start-tick 100 --end-tick 200

# Export by date range
python -m src.cli.export_resources --start-date 2024-01-01T00:00:00 --end-date 2024-01-31T23:59:59

# Export to specific file
python -m src.cli.export_resources --output path/to/output.csv

# Pivot format (one column per resource)
python -m src.cli.export_resources --pivot
```

**CSV Format:**

Standard format (one row per resource per timestamp):
- `timestamp`: ISO format datetime
- `tick`: Simulation tick number
- `resource_id`: Resource identifier
- `amount`: Resource amount at this timestamp
- `status_id`: Resource status (depleted, at_risk, moderate, sufficient, abundant)
- `utilization_percent`: Utilization percentage (if max_capacity exists)

Pivot format (`--pivot`):
- One row per timestamp
- Columns: `timestamp`, `tick`, `{resource_id}_amount`, `{resource_id}_status`, `{resource_id}_utilization` for each resource

### Export Entity History

Export entity history to CSV for analysis:

```bash
make export-entities
```

This exports all entity history to `_running/exports/entities_YYYYMMDD_HHMMSS.csv`.

**Advanced options:**

```bash
# Export by tick range
python -m src.cli.export_entities --start-tick 100 --end-tick 200

# Export by date range
python -m src.cli.export_entities --start-date 2024-01-01T00:00:00 --end-date 2024-01-31T23:59:59

# Export to specific file
python -m src.cli.export_entities --output path/to/output.csv

# Pivot format (component_counts expanded into columns)
python -m src.cli.export_entities --pivot
```

**CSV Format:**

Standard format (one row per timestamp):
- `timestamp`: ISO format datetime
- `tick`: Simulation tick number
- `total_entities`: Total number of entities
- `component_counts`: JSON string of component_type -> count
- `avg_hunger`, `avg_thirst`, `avg_rest`: Average needs levels (0.0-1.0)
- `avg_pressure_level`: Average pressure level (0.0-1.0)
- `entities_with_pressure`: Count of entities with pressure > 0
- `avg_health`: Average health level (0.0-1.0)
- `entities_at_risk`: Count of entities with health < 0.5
- `avg_age_years`: Average age in years
- `avg_wealth`: Average wealth/money
- `employed_count`: Count of employed entities

Pivot format (`--pivot`):
- One row per timestamp
- Component counts expanded into separate columns: `component_count_{component_type}`
- All other metrics as columns

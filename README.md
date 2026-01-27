# Lunaris Civitas

A deterministic, modular zero-player simulation engine written in Python.

## Overview

Lunaris Civitas is a background simulation kernel designed for:
- Analytics
- Research
- Long-running scenario modeling
- Future human and societal simulations

This is **not** a game UI - it's a deterministic simulation engine focused on analytical reporting and research.

## Key Features

- **Deterministic**: Fully replayable with seeded RNG
- **Modular**: Systems interact only through world state
- **Extensible**: Add new systems without changing the engine
- **Persistent**: SQLite-based state management with resume capability
- **Data-driven**: All behavior driven by configuration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lunaris-civitas
```

2. Set up the virtual environment and install dependencies:
```bash
make setup
```

This will:
- Create a `.venv` virtual environment
- Install all required dependencies from `requirements.txt`

3. Activate the virtual environment (optional, Makefile handles this automatically):
```bash
source .venv/bin/activate
```

## Running the Simulation

### Basic Run

Run the simulation with the default development configuration:
```bash
make run
```

### Custom Configuration

Run with a custom configuration file:
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

Resumes from the last saved state in the database. The `make resume` command appends to existing logs and preserves the database (unlike `make run` which starts fresh and overwrites logs).

### Limit Simulation Ticks

Run for a limited number of ticks:
```bash
python -m src --config configs/dev.yml --max-ticks 100
```

### Command Line Options

- `--config PATH`: Path to configuration file (YAML or JSON)
- `--db PATH`: Path to SQLite database (default: `_running/simulation.db`)
- `--resume`: Resume simulation from database
- `--max-ticks N`: Maximum number of ticks to run
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Project Structure

```
lunaris-civitas/
├── src/                    # Source code
│   ├── core/              # Core engine components
│   ├── models/            # Data models (Resource, Modifier)
│   ├── persistence/       # SQLite database layer
│   ├── config/            # Configuration loading
│   ├── engine/            # Simulation engine and loop
│   └── systems/           # Simulation systems
│       └── resource/      # Resource management systems
├── configs/               # Configuration files
├── docs/                  # Documentation (MkDocs)
├── tests/                 # Unit and integration tests
├── _running/              # Runtime files (database, logs)
├── Makefile              # Build and run commands
└── requirements.txt      # Python dependencies
```

## Adding a New System

Systems are organized by category in subfolders. To add a new system:

1. **Create your system class** extending the `System` base class:

```python
# src/systems/my_category/my_system.py
from src.core.system import System
from datetime import datetime

class MySystem(System):
    @property
    def system_id(self) -> str:
        return "MySystem"
    
    def init(self, world_state, config):
        # Initialize system with configuration
        self.my_config = config.get('my_setting', 'default')
    
    def on_tick(self, world_state, current_datetime):
        # Process each tick
        # Systems decide internally when to act (hourly, daily, etc.)
        if current_datetime.hour == 0:  # Act daily at midnight
            # Do something
            resource = world_state.get_resource('food')
            if resource:
                resource.add(10.0)
    
    def shutdown(self, world_state):
        # Optional cleanup
        pass
```

2. **Register the system** in your simulation code:

```python
from src.systems.my_category.my_system import MySystem

sim = Simulation(config_path=Path("configs/dev.yml"))
sim.register_system(MySystem())
```

3. **Add system configuration** to your config file:

```yaml
systems:
  - MySystem

systems_config:
  MySystem:
    my_setting: "value"
```

## Configuration

See `configs/dev.yml` for an example configuration file. Configuration files can be YAML (`.yml`, `.yaml`) or JSON (`.json`).

Key sections:
- `simulation`: Simulation settings (start datetime, RNG seed, log level)
- `resources`: Resource definitions
- `systems`: List of system IDs to register
- `systems_config`: System-specific configuration

## Testing

Run tests:
```bash
make test
```

## Documentation

Build documentation:
```bash
make docs
```

Serve documentation locally:
```bash
make docs-serve
```

Documentation is built using MkDocs with the Material theme.

## Design Principles

- **Deterministic and replayable**: Same seed produces same results
- **Modular and extensible**: Systems don't depend on each other
- **Data-driven**: All behavior driven by configuration
- **System contract**: Every system follows the same interface
- **Hot-addable**: New systems can be added without engine changes

## Time Model

- 1 tick = 1 hour
- 24 hours = 1 day
- Days follow real-world calendar rules (correct month lengths, leap years)
- 12 months = 1 year

All systems receive hourly ticks and decide internally whether to act hourly, daily, monthly, or yearly.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

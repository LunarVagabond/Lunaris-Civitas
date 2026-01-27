# Getting Started

## Installation

1. Clone the repository
2. Run `make setup` to create virtual environment and install dependencies
3. Activate the virtual environment: `source .venv/bin/activate`

## Running the Simulation

### Basic Run

```bash
make run
```

This runs the simulation with the default `configs/dev.yml` configuration.

### Custom Configuration

```bash
python -m src --config path/to/config.yml
```

### Resume Simulation

```bash
python -m src --resume
```

This resumes from the last saved state in the database.

### Limit Ticks

```bash
python -m src --config configs/dev.yml --max-ticks 100
```

## Configuration

See [Configuration](../Configuration/README.md) for details on configuration files.

## Adding Systems

See [Systems](../Systems/README.md) for information on creating new systems.

# Development

## Setup

1. Clone the repository
2. Run `make setup` to create virtual environment and install dependencies
3. Activate the virtual environment: `source .venv/bin/activate`

## Running Tests

```bash
make test
```

## Code Structure

- `src/core/` - Core engine components
- `src/models/` - Data models
- `src/persistence/` - Database layer
- `src/config/` - Configuration loading
- `src/engine/` - Simulation engine
- `src/systems/` - Simulation systems (organized by category)

## Key Documentation

- **[Core Execution Flows](CORE_FLOWS.md)** - Essential reading for understanding:
  - Entry point flow and simulation loop
  - System interface patterns and extension
  - Model/composable patterns
  - Detailed call chains for common operations

## Analytics & History

The simulation includes a `ResourceHistorySystem` that tracks resource values over time for analytics. History data can be exported to CSV for analysis. See [Operations](../Operations/README.md#exporting-data) for export commands.

## Development Guidelines

- Follow the system contract for all systems
- Systems must not depend on each other
- All interaction through world state
- Write tests for new systems
- Update documentation when adding features

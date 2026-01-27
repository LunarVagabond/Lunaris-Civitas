# Systems

## System Contract

All systems must implement the `System` base class:

```python
from src.core.system import System
from datetime import datetime

class MySystem(System):
    @property
    def system_id(self) -> str:
        return "MySystem"
    
    def init(self, world_state, config):
        # Initialize system
        pass
    
    def on_tick(self, world_state, current_datetime):
        # Process tick
        pass
    
    def shutdown(self, world_state):
        # Optional cleanup
        pass
```

## System Organization

Systems are organized by category in subfolders:
- `src/systems/resource/` - Resource management systems
- Future: `src/systems/human/`, `src/systems/disease/`, etc.

## Phase 1 Systems

### ResourceProductionSystem

Produces resources based on configuration. Respects modifiers affecting production.

### ResourceConsumptionSystem

Consumes resources based on configuration. Respects modifiers affecting consumption.

### ResourceReplenishmentSystem

Replenishes resources based on their `replenishment_rate` property. Only replenishes non-finite resources.

### ResourceHistorySystem

Tracks resource values over time for analytics and trend analysis. Saves resource history to the database at configurable intervals (hourly, daily, weekly, monthly, or yearly).

**Configuration:**
- `enabled`: Enable/disable history tracking (default: `true`)
- `frequency`: Save frequency - `'hourly'`, `'daily'`, `'weekly'`, `'monthly'`, or `'yearly'` (default: `'daily'`)
- `rate`: Save every N periods (e.g., `rate: 2` means every 2 days if frequency is daily) (default: `1`)
- `resources`: List of resource IDs to track (empty list = track all resources) (default: `[]`)

**Example:**
```yaml
systems_config:
  ResourceHistorySystem:
    enabled: true
    frequency: daily  # Save history daily at midnight
    rate: 1  # Every 1 day
    resources: []  # Track all resources
```

History data can be exported to CSV using the `make export-resources` command or `python -m src.cli.export_resources`.

## Adding a New System

See [Adding Systems](ADDING_SYSTEMS.md) for detailed instructions.

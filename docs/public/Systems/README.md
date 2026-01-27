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

## Adding a New System

See [Adding Systems](ADDING_SYSTEMS.md) for detailed instructions.

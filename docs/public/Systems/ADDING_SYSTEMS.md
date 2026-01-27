# Adding a New System

## Step-by-Step Guide

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

2. **Create the category folder** if it doesn't exist:

```bash
mkdir -p src/systems/my_category
touch src/systems/my_category/__init__.py
```

3. **Register the system** in your simulation code:

```python
from src.systems.my_category.my_system import MySystem

sim = Simulation(config_path=Path("configs/dev.yml"))
sim.register_system(MySystem())
```

4. **Add system configuration** to your config file:

```yaml
systems:
  - MySystem

systems_config:
  MySystem:
    my_setting: "value"
```

## Best Practices

- Systems should be organized by category in subfolders
- Systems never call other systems directly
- All interaction happens through world state
- Systems decide internally when to act (hourly, daily, monthly, yearly)
- Handle missing resources/modifiers gracefully
- Use logging for important events

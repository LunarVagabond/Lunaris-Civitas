# Configuration

## Configuration Format

Configuration files can be YAML (`.yml`, `.yaml`) or JSON (`.json`).

## Structure

```yaml
simulation:
  start_datetime: "2024-01-01T00:00:00"
  rng_seed: 12345
  log_level: INFO

resources:
  - id: food
    name: Food
    initial_amount: 1000.0
    max_capacity: 10000.0
    replenishment_rate: 50.0
    finite: false

systems:
  - ResourceProductionSystem
  - ResourceConsumptionSystem
  - ResourceReplenishmentSystem

systems_config:
  ResourceProductionSystem:
    production:
      food: 100.0
      water: 150.0
  
  ResourceConsumptionSystem:
    consumption:
      food: 80.0
      water: 120.0
```

## Simulation Configuration

- `start_datetime`: ISO format datetime string
- `rng_seed`: Optional integer seed for deterministic RNG, or `"RANDOM"` to auto-generate a seed
  - If `"RANDOM"`: System generates a random seed and stores it in the database
  - If numeric: Uses that seed for new simulations (resume always uses seed from database)
  - If omitted/None: No seed (non-deterministic)
- `log_level`: DEBUG, INFO, WARNING, or ERROR

## Logging Configuration

Configurable logging for world state and system metrics:

```yaml
logging:
  world_state:
    enabled: true
    frequency: weekly  # 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
    rate: 1  # Log every N periods (e.g., rate=2 means every 2 weeks)
  
  systems:
    enabled: true
    frequency: daily
    rate: 1
```

**World State Logging:**
- Logs enabled systems, resource states, active modifiers
- Frequency: When to check for logging (hourly, daily, weekly, monthly, yearly)
- Rate: How often to log (e.g., rate=2 with weekly frequency = log every 2 weeks)

**Systems Metrics Logging:**
- Logs system status and metrics
- Same frequency/rate configuration as world state logging

## Resources

Each resource has:
- `id`: Unique identifier
- `name`: Human-readable name
- `initial_amount`: Starting amount
- `max_capacity`: Optional maximum capacity
- `replenishment_rate`: Optional hourly replenishment rate
- `finite`: Boolean, if true resource cannot replenish

## Systems

List of system IDs to register. Systems must be registered with the simulation before use.

## System Configuration

System-specific configuration under `systems_config`. Each system defines its own config structure.

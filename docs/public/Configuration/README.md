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
  - ResourceHistorySystem

systems_config:
  ResourceProductionSystem:
    production:
      food: 100.0
      water: 150.0
  
  ResourceConsumptionSystem:
    consumption:
      food: 80.0
      water: 120.0
  
  ResourceHistorySystem:
    enabled: true
    frequency: daily  # 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
    rate: 1  # Save every N periods
    resources: []  # Empty = track all resources, or list specific IDs
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

### ResourceHistorySystem

Tracks resource values over time for analytics. Configuration:

- `enabled`: Enable/disable history tracking (default: `true`)
- `frequency`: Save frequency - `'hourly'`, `'daily'`, `'weekly'`, `'monthly'`, or `'yearly'` (default: `'daily'`)
- `rate`: Save every N periods (e.g., `rate: 2` with `frequency: daily` = save every 2 days) (default: `1`)
- `resources`: List of resource IDs to track (empty list = track all resources) (default: `[]`)

**Example:**
```yaml
ResourceHistorySystem:
  enabled: true
  frequency: daily  # Save history daily at midnight
  rate: 1  # Every 1 day
  resources: []  # Track all resources
```

History data is stored in the `resource_history` table and can be exported to CSV using `make export-resources`.

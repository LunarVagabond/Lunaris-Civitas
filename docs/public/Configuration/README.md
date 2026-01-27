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
  - EntityHistorySystem
  - HumanSpawnSystem
  - NeedsSystem
  - HumanNeedsFulfillmentSystem
  - HealthSystem
  - DeathSystem

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

### EntityHistorySystem

Tracks entity and component metrics over time for analytics. Configuration:

- `enabled`: Enable/disable history tracking (default: `true`)
- `frequency`: Save frequency - `'hourly'`, `'daily'`, `'weekly'`, `'monthly'`, or `'yearly'` (default: `'daily'`)
- `rate`: Save every N periods (e.g., `rate: 2` with `frequency: daily` = save every 2 days) (default: `1`)
- `component_types`: List of component types to track (empty list = track all components) (default: `[]`)

**Example:**
```yaml
EntityHistorySystem:
  enabled: true
  frequency: daily  # Save history daily at midnight
  rate: 1  # Every 1 day
  component_types: []  # Track all components
```

**Metrics Tracked:**
- Total entity count
- Component distribution (JSON: component_type -> count)
- Average needs levels (hunger, thirst, rest)
- Average pressure level and entities with pressure
- Average health and entities at risk
- Average age and wealth
- Employment count

History data is stored in the `entity_history` table and can be exported to CSV using `make export-entities`.

### HumanSpawnSystem

Creates initial population and supports runtime spawning (TEMPORARY PLACEHOLDER for Phase 3 reproduction system).

**Configuration:**
- `enabled`: Enable/disable spawning (default: `true`)
- `initial_population`: Number of entities to create at simulation start (default: `100`)
- `spawn_frequency`: Spawn frequency - `'hourly'`, `'daily'`, `'weekly'`, `'monthly'`, or `'yearly'` (default: `'daily'`)
- `spawn_rate`: Spawn N entities per period, 0 = disabled (default: `0`)
- `seed_crew`: Configuration for initial population
  - `age_range`: `[min, max]` years for initial population
  - `components`: Dictionary mapping component_type -> percentage (0-100)
- `runtime_spawn`: Configuration for runtime spawning
  - `components`: Dictionary mapping component_type -> percentage

**Example:**
```yaml
HumanSpawnSystem:
  enabled: true
  initial_population: 100
  spawn_frequency: daily
  spawn_rate: 0  # Disabled (placeholder for reproduction system)
  seed_crew:
    age_range: [18, 65]
    components:
      Needs: 100
      Health: 100
      Age: 100
      Pressure: 50
  runtime_spawn:
    components:
      Needs: 100
      Health: 100
      Age: 100  # Always age 0
```

**Note**: Runtime spawning is a temporary placeholder and will be replaced by a proper reproduction system in Phase 3.

### NeedsSystem

Updates entity needs over time with randomized decay rates per entity (individual metabolism).

**Configuration:**
- `enabled`: Enable/disable needs decay (default: `true`)
- `frequency`: Always `'hourly'` for needs decay
- `base_hunger_rate`: Base hunger rate per hour (default: `0.01`)
- `hunger_rate_variance`: ±variance for randomization (default: `0.005`)
- `base_thirst_rate`: Base thirst rate per hour (default: `0.015`)
- `thirst_rate_variance`: ±variance for randomization (default: `0.005`)
- `base_rest_rate`: Base rest rate per hour (default: `0.005`)
- `rest_rate_variance`: ±variance for randomization (default: `0.002`)

**Example:**
```yaml
NeedsSystem:
  enabled: true
  base_hunger_rate: 0.01
  hunger_rate_variance: 0.005
  base_thirst_rate: 0.015
  thirst_rate_variance: 0.005
  base_rest_rate: 0.005
  rest_rate_variance: 0.002
```

### HumanNeedsFulfillmentSystem

Actively fulfills needs through RequirementResolverSystem with randomized satisfaction amounts.

**Configuration:**
- `enabled`: Enable/disable need fulfillment (default: `true`)
- `frequency`: Check frequency - `'hourly'`, `'daily'`, etc. (default: `'hourly'`)
- `satisfaction_ranges`: Ranges for randomized satisfaction rates
  - `food`: `hunger_restore_min`, `hunger_restore_max` (per unit)
  - `water`: `thirst_restore_min`, `thirst_restore_max` (per unit)
  - `rest`: `rest_restore_min`, `rest_restore_max` (per hour)

**Example:**
```yaml
HumanNeedsFulfillmentSystem:
  enabled: true
  frequency: hourly
  satisfaction_ranges:
    food:
      hunger_restore_min: 0.05  # Randomized per call
      hunger_restore_max: 0.15
    water:
      thirst_restore_min: 0.10
      thirst_restore_max: 0.30
```

### HealthSystem

Converts pressure and unmet needs into health degradation with randomized damage amounts.

**Configuration:**
- `enabled`: Enable/disable health updates (default: `true`)
- `frequency`: Update frequency - `'hourly'`, `'daily'`, etc. (default: `'hourly'`)
- `pressure_damage`: Damage from pressure (`min_per_tick`, `max_per_tick` at pressure_level = 1.0)
- `unmet_needs_damage`: Damage from unmet needs
  - `hunger`: `min_per_tick`, `max_per_tick` (at hunger = 1.0)
  - `thirst`: `min_per_tick`, `max_per_tick` (at thirst = 1.0)
  - `rest`: `min_per_tick`, `max_per_tick` (at rest = 1.0)
- `healing_rate`: Healing when needs met (`min_per_tick`, `max_per_tick`)

**Example:**
```yaml
HealthSystem:
  enabled: true
  frequency: hourly
  pressure_damage:
    min_per_tick: 0.001  # Randomized per tick
    max_per_tick: 0.005
  unmet_needs_damage:
    hunger:
      min_per_tick: 0.0005
      max_per_tick: 0.002
  healing_rate:
    min_per_tick: 0.0001
    max_per_tick: 0.0005
```

### DeathSystem

Handles entity death from health degradation and age-based mortality.

**Configuration:**
- `enabled`: Enable/disable death checks (default: `true`)
- `frequency`: Check frequency - `'hourly'`, `'daily'`, etc. (default: `'hourly'`)
- `age_mortality`: Age-based mortality parameters
  - `old_age_start`: Age where mortality starts increasing (default: `70`)
  - `old_age_death_chance_min`: Minimum death chance per hour at old_age_start (default: `0.00001`)
  - `old_age_death_chance_max`: Maximum death chance per hour at old_age_start (default: `0.0001`)
  - `peak_mortality_age`: Age where most deaths occur (default: `85`)
  - `chance_increase_per_year`: Base increase per year past old_age_start (default: `0.00001`)
  - `chance_multiplier_per_year`: Exponential multiplier after peak_mortality_age (default: `1.1`)

**Example:**
```yaml
DeathSystem:
  enabled: true
  frequency: hourly
  age_mortality:
    old_age_start: 70
    old_age_death_chance_min: 0.00001
    old_age_death_chance_max: 0.0001
    peak_mortality_age: 85
    chance_increase_per_year: 0.00001
    chance_multiplier_per_year: 1.1
    # No max_age - outliers can survive past 100 (very rare)
```

**Mortality Curve:**
- Linear increase from `old_age_start` (70) to `peak_mortality_age` (85)
- Exponential increase after `peak_mortality_age` (allows rare outliers past 100)
- Most deaths occur between 73-100, but outliers can survive past 100 (very rare)
- No guaranteed death - probability-based only

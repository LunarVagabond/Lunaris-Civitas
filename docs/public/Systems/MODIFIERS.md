# Modifiers System

Modifiers are dynamic events that affect resources and systems in the simulation. They can be added via the database and support automatic repeat mechanics.

## Overview

Modifiers represent buffs, debuffs, and events that affect:
- **Resources**: Production, consumption, or replenishment rates
- **Systems**: System behavior parameters (e.g., death rates, birth rates, needs decay rates)

The system supports:

- **Dynamic addition**: Add modifiers via CLI without restarting the simulation
- **Effect types**: Percentage-based or direct value effects
- **Repeat mechanics**: Modifiers can automatically repeat based on probability
- **Target flexibility**: One modifier can affect multiple targets (one row per target)
- **System targeting**: Modifiers can target systems to modify their behavior

## Database Structure

Modifiers are stored in a normalized database table with one row per target:

- `modifier_name`: Groups related modifier rows (e.g., "pest_outbreak_2024")
- `target_type`: "resource" or "system"
- `target_id`: Resource ID or System ID
- `resource_id`: Resource ID (for backward compatibility, NULL if targeting system)
- `effect_type`: "percentage" or "direct"
- `effect_value`: Effect amount (percentage as 0.0-1.0, or absolute value)
- `effect_direction`: "increase" or "decrease"
- `start_year`, `end_year`: Active period (end_year is exclusive)
- `is_active`: Whether modifier is currently active
- `repeat_probability`: Chance of repeat (0.0-1.0)
- `repeat_frequency`: When to check for repeat ("hourly", "daily", "weekly", "monthly", "yearly")
- `repeat_rate`: Every N periods to check
- `repeat_duration_years`: Duration of repeat (NULL = same as original)
- `parent_modifier_id`: Links to parent modifier if this is a repeat

## Effect Types

### Percentage Effects

Multiplier-based effects that scale with the base value:

- Example: `effect_type="percentage"`, `effect_value=0.3`, `effect_direction="decrease"`
  - Reduces production/consumption by 30%
  - Base rate 100 → Modified rate 70

### Direct Effects

Absolute value effects that add/subtract a fixed amount:

- Example: `effect_type="direct"`, `effect_value=500`, `effect_direction="decrease"`
  - Removes 500 units from production/consumption
  - Base rate 1000 → Modified rate 500

## Adding Modifiers

Use the interactive CLI tool:

```bash
make modifier-add
```

The tool will prompt for:
- Modifier name
- Resource IDs (comma-separated)
- Effect type (percentage/direct)
- Effect value
- Effect direction (increase/decrease)
- Start year, end year
- Repeat probability (0.0-1.0)
- Repeat frequency (hourly/daily/weekly/monthly/yearly)
- Repeat rate (every N periods)
- Repeat duration (optional, years)

### Example

```bash
$ make modifier-add

Modifier name: pest_outbreak_2024
Resource IDs: food,water
Effect type [percentage]: percentage
Effect value (0.0-1.0): 0.3
Effect direction [decrease]: decrease
Start year: 2024
End year: 2026
Repeat probability [0.0]: 0.5
Repeat frequency [yearly]: yearly
Repeat rate [1]: 1
Repeat duration: 2
```

This creates modifier rows for `food` and `water` that:
- Reduce production by 30% from 2024-2026
- Have a 50% chance to repeat yearly
- If repeated, continue for 2 more years

## Repeat Mechanics

When a modifier expires, the simulation checks if it should repeat based on:

1. **Repeat frequency**: When to check (at year boundary, month boundary, etc.)
2. **Repeat probability**: Chance of repeat (0.0-1.0)
3. **Repeat rate**: Every N periods

If repeat triggers:
- New modifier rows are created for the same resources
- New rows inherit all properties from parent
- Duration may differ if `repeat_duration_years` is set
- Parent relationship is tracked via `parent_modifier_id`

### Repeat Inheritance

Repeated modifiers inherit:
- `effect_type`, `effect_value`, `effect_direction`
- `repeat_probability`, `repeat_frequency`, `repeat_rate`
- `repeat_duration_years` (if set)

## Viewing Modifiers

### List All Modifiers

```bash
make modifier-list
```

Shows all modifiers grouped by name, with details about effects, duration, and repeat settings.

### View Resources with Modifiers

```bash
make resources-view
```

Shows all resources with their current state and active modifier counts.

### View World State

```bash
make world-state-view
```

Shows world state summary including active modifier count.

## Modifier Application

### Resource Modifiers

Modifiers targeting resources are applied in resource systems:

1. **Production System**: Affects resource production rates
2. **Consumption System**: Affects resource consumption rates
3. **Replenishment System**: Affects resource replenishment rates

### System Modifiers

Modifiers targeting systems affect system behavior parameters:

1. **DeathSystem**: Modifies death probability (age-based mortality)
2. **HumanSpawnSystem**: Modifies birth/spawn rates
3. **NeedsSystem**: Can modify needs decay rates (future)
4. **HealthSystem**: Can modify damage/healing rates (future)

### Application Order

1. New structure modifiers (effect_type/effect_value) are applied first
2. Legacy modifiers (multiplier/additive) are applied second

### Stacking

Multiple modifiers affecting the same target are applied sequentially:
- Percentage effects are multiplicative
- Direct effects are additive
- Final value is clamped to valid ranges (non-negative, probability bounds, etc.)

## Examples

### Pest Outbreak

Reduces food production by 70% for 2 years, 30% chance to repeat:

```bash
make modifier-add
# Name: pest_outbreak_2024
# Resources: food
# Effect type: percentage
# Effect value: 0.7
# Direction: decrease
# Start: 2024, End: 2026
# Repeat probability: 0.3
# Repeat frequency: yearly
```

### Drought

Reduces water replenishment by 50% for 1 year:

```bash
make modifier-add
# Name: drought_2024
# Resources: water
# Effect type: percentage
# Effect value: 0.5
# Direction: decrease
# Start: 2024, End: 2025
# Repeat probability: 0.0
```

### Resource Discovery

Adds 1000 units of oil directly:

```bash
make modifier-add
# Name: oil_discovery_2024
# Target type: resource
# Resources: oil
# Effect type: direct
# Effect value: 1000
# Direction: increase
# Start: 2024, End: 2024
# Note: Direct effects on production add resources
```

### Increased Death Rate (Pandemic)

Increases death rate by 50% for 2 years:

```bash
make modifier-add
# Name: pandemic_2024
# Target type: system
# System ID: DeathSystem
# Effect type: percentage
# Effect value: 0.5
# Direction: increase
# Start: 2024, End: 2026
# Note: This increases age-based death probability by 50%
```

### Decreased Birth Rate (Fertility Crisis)

Decreases birth/spawn rate by 30% for 5 years:

```bash
make modifier-add
# Name: fertility_crisis_2024
# Target type: system
# System ID: HumanSpawnSystem
# Effect type: percentage
# Effect value: 0.3
# Direction: decrease
# Start: 2024, End: 2029
# Note: This reduces spawn rate by 30% (e.g., 10 → 7 per period)
```

## Database Queries

Modifiers can also be added directly via SQL:

```sql
INSERT INTO modifiers 
(modifier_name, resource_id, effect_type, effect_value, effect_direction,
 start_year, end_year, is_active, repeat_probability, repeat_frequency, 
 repeat_rate, repeat_duration_years, parent_modifier_id)
VALUES 
('custom_modifier', 'food', 'percentage', 0.2, 'decrease',
 2024, 2026, 1, 0.0, 'yearly', 1, NULL, NULL);
```

## Migration from Legacy Modifiers

The system automatically migrates legacy modifiers (with `target_type`/`target_id`/`parameters`) to the new structure when the database schema is updated. Legacy modifiers are converted assuming:
- `target_type='resource'` → extracted to `resource_id`
- `parameters.multiplier` → converted to percentage effect
- Defaults applied for new fields

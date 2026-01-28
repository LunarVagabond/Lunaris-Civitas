# Configuration Guide

This guide explains how to configure Lunaris Civitas to customize your simulation. You don't need programming experience—just edit a YAML file (think of it as a structured text file) to change how the simulation behaves.

## Table of Contents

- [Understanding Configuration Files](#understanding-configuration-files)
- [Basic Simulation Settings](#basic-simulation-settings)
- [Resources: What Your World Has](#resources-what-your-world-has)
- [Systems: What Happens in Your World](#systems-what-happens-in-your-world)
- [System-Specific Configuration](#system-specific-configuration)
- [Common Scenarios](#common-scenarios)

---

## Understanding Configuration Files

Configuration files are written in **YAML** format (`.yml` or `.yaml` files). Think of YAML as a way to organize information in a readable, structured way. Here's what you need to know:

- **Indentation matters**: Use spaces (not tabs) to indent
- **Colons (`:`) separate names from values**
- **Dashes (`-`) create lists**
- **Comments start with `#`** (everything after `#` is ignored)

**Example:**
```yaml
# This is a comment - it's ignored by the system
simulation:
  start_datetime: "2024-01-01T00:00:00"  # When the simulation starts
  log_level: INFO  # How much detail to log
```

---

## Basic Simulation Settings

These settings control when and how your simulation runs.

### Simulation Start Date

```yaml
simulation:
  start_datetime: "2024-01-01T00:00:00"
```

**What this means:** When your simulation begins. Use the format `YYYY-MM-DDTHH:MM:SS`.

**Example values:**
- `"2024-01-01T00:00:00"` - January 1st, 2024 at midnight
- `"2020-06-15T12:00:00"` - June 15th, 2020 at noon
- `"2050-01-01T00:00:00"` - Start in the future

**Why it matters:** This sets the calendar date for your simulation. Events, logging, and history all use this as the starting point.

### Random Seed

```yaml
simulation:
  rng_seed: RANDOM  # or a number like 12345
```

**What this means:** Controls randomness in the simulation. The same seed produces the same results.

**Options:**
- `RANDOM` - The system picks a random seed (different results each time)
- A number like `12345` - Uses that specific seed (same results every time)

**When to use:**
- Use `RANDOM` for exploring different outcomes
- Use a specific number when you want reproducible results (testing, research)

**Example:** If you run the simulation twice with `rng_seed: 12345`, you'll get identical results. Change it to `RANDOM` and each run will be different.

### Log Level

```yaml
simulation:
  log_level: INFO
```

**What this means:** How much detail gets written to log files.

**Options:**
- `DEBUG` - Everything (very detailed, lots of output)
- `INFO` - Normal information (recommended for most users)
- `WARNING` - Only warnings and errors
- `ERROR` - Only errors

**Recommendation:** Start with `INFO`. Use `DEBUG` if you're troubleshooting problems.

---

## Resources: What Your World Has

Resources are the things in your simulation world—food, water, money, electricity, etc. Each resource has properties that control how it behaves.

### Basic Resource Properties

```yaml
resources:
  - id: food
    name: Food
    initial_amount: 1000.0
    max_capacity: 10000.0
    replenishment_rate: 50.0
    replenishment_frequency: hourly
    finite: false
```

**What each property means:**

- **`id`**: A unique identifier (use lowercase, no spaces). This is how other parts of the system refer to this resource.
- **`name`**: A human-readable name (what you'll see in reports).
- **`initial_amount`**: How much of this resource exists when the simulation starts.
- **`max_capacity`**: The maximum amount this resource can reach (optional). If not set, there's no limit.
- **`replenishment_rate`**: How much of this resource is naturally added per replenishment period.
- **`replenishment_frequency`**: How often replenishment happens (`hourly`, `daily`, `weekly`, `monthly`, `yearly`).
- **`finite`**: If `true`, the resource cannot replenish (like oil or minerals). If `false`, it can replenish naturally.

### Understanding Replenishment

**Replenishment** means resources naturally increase over time (like crops growing, rain filling reservoirs, or solar panels generating electricity).

**Example:**
```yaml
- id: water
  replenishment_rate: 100.0
  replenishment_frequency: hourly
```

This means: Every hour, 100 units of water are added naturally (like rain or rivers).

**Different frequencies:**

- `hourly` - Every hour: `replenishment_rate: 100.0` = 100 units/hour = 2,400 units/day
- `daily` - Every day: `replenishment_rate: 100.0` = 100 units/day
- `monthly` - Every month: `replenishment_rate: 100.0` = 100 units/month

**Tip:** Higher `replenishment_rate` values mean more resources are added. Lower values mean scarcity.

### Finite vs. Renewable Resources

**Finite resources** (like oil, minerals):
```yaml
- id: oil
  initial_amount: 500.0
  finite: true  # Cannot replenish - once it's gone, it's gone
```

**Renewable resources** (like food, water):
```yaml
- id: food
  initial_amount: 1000.0
  replenishment_rate: 50.0
  replenishment_frequency: hourly
  finite: false  # Can replenish naturally
```

**When to use finite:** Use `finite: true` for resources that don't regenerate (mined materials, fossil fuels). Use `finite: false` for resources that can grow or regenerate (food, water, renewable energy).

### Resource Capacity

```yaml
max_capacity: 10000.0
```

**What this means:** The resource cannot exceed this amount, even if production or replenishment would add more.

**Example:** If `max_capacity: 10000.0` and you have 9,500 units, replenishment can only add up to 500 more units (reaching 10,000).

**When to use:** Useful for resources with physical limits (storage capacity, land area, etc.). Leave it out if there's no practical limit.

---

## Systems: What Happens in Your World

Systems are the processes that make things happen in your simulation. You enable systems by listing them, then configure how they behave.

### Enabling Systems

```yaml
systems:
  - ResourceProductionSystem      # Produces resources
  - ResourceConsumptionSystem     # Consumes resources (decay, spoilage)
  - ResourceReplenishmentSystem  # Natural replenishment
  - HumanSpawnSystem             # Creates people
  - NeedsSystem                  # People get hungry/thirsty
  - HealthSystem                 # Health changes over time
  - DeathSystem                  # People die
  - JobSystem                    # People work jobs
```

**What this means:** These are the systems that will be active in your simulation. Each system does something specific (see [System-Specific Configuration](#system-specific-configuration) below).

**Tip:** You can comment out systems you don't want by adding `#` at the start:
```yaml
systems:
  - ResourceProductionSystem
  # - ResourceConsumptionSystem  # Disabled - no resource decay
  - HumanSpawnSystem
```

---

## System-Specific Configuration

Each system can be customized. Configuration goes under `systems_config:`.

### Resource Production System

**What it does:** Produces resources automatically (like natural growth, solar generation, etc.).

```yaml
systems_config:
  ResourceProductionSystem:
    production:
      food: 100.0      # Produces 100 food per hour
      water: 150.0     # Produces 150 water per hour
      electricity:
        rate: 300.0
        frequency: hourly  # Optional: defaults to hourly
```

**Understanding the values:**
- `food: 100.0` means 100 units of food are produced every hour
- Higher values = more production
- Lower values = scarcity

**Example scenarios:**
- **Abundant resources:** `food: 500.0` - Lots of food production
- **Scarce resources:** `food: 10.0` - Very little production (challenging scenario)
- **Balanced:** `food: 100.0` - Moderate production

**Custom frequencies:**
```yaml
wood:
  rate: 50.0
  frequency: daily  # Produces 50 wood per day (not per hour)
```

### Resource Consumption System

**What it does:** Consumes resources automatically (like spoilage, evaporation, natural decay).

```yaml
systems_config:
  ResourceConsumptionSystem:
    consumption:
      food: 80.0      # 80 food spoils/decays per hour
      water: 120.0    # 120 water evaporates per hour
      oil:
        rate: 10.0
        frequency: monthly  # 10 oil degrades per month
```

**Understanding the values:**
- Higher values = resources disappear faster
- Lower values = resources last longer
- If consumption > production, resources will decrease over time

**Example:** If food production is `100.0/hour` and consumption is `80.0/hour`, you gain 20 food per hour. If consumption is `150.0/hour`, you lose 50 food per hour.

### Human Spawn System

**What it does:** Creates the initial population and can spawn new people over time.

```yaml
systems_config:
  HumanSpawnSystem:
    enabled: true
    initial_population: 100        # Start with 100 people
    spawn_frequency: daily         # Check for new spawns daily
    spawn_rate: 10                 # Spawn 10 new people per day (0 = disabled)
    seed_crew:
      age_range: [18, 65]          # Initial people are 18-65 years old
      components:
        Needs: 100                 # 100% get Needs component
        Health: 100                # 100% get Health component
        Age: 100                   # 100% get Age component
        Pressure: 50               # 50% get Pressure component
        Wealth: 20                # 20% start with money
    runtime_spawn:
      components:
        Needs: 100
        Health: 100
        Age: 100                   # Newborns always start at age 0
```

**Key settings explained:**

- **`initial_population`**: How many people exist when the simulation starts
  - Small: `50` - Small community
  - Medium: `100` - Moderate population
  - Large: `500` - Large population

- **`spawn_rate`**: How many new people are created per period
  - `0` - No new people (population only decreases)
  - `5` - Slow growth (5 per day)
  - `10` - Moderate growth
  - `20` - Fast growth

- **`age_range`**: Age range for initial population
  - `[18, 65]` - Working-age adults
  - `[0, 80]` - All ages
  - `[25, 40]` - Young adults only

- **`components`**: What abilities/attributes people have (percentages)
  - `Needs: 100` - Everyone needs food/water/rest
  - `Wealth: 20` - Only 20% start with money
  - `Pressure: 50` - 50% can experience pressure (stress from unmet needs)

### Needs System

**What it does:** People get hungry, thirsty, and tired over time. Each person has different metabolism rates.

```yaml
systems_config:
  NeedsSystem:
    enabled: true
    frequency: hourly  # Always hourly
    base_hunger_rate: 0.01         # Base hunger increase per hour
    hunger_rate_variance: 0.005    # ±0.005 variation per person
    base_thirst_rate: 0.015        # Base thirst increase per hour
    thirst_rate_variance: 0.005    # ±0.005 variation per person
    base_rest_rate: 0.005         # Base rest need increase per hour
    rest_rate_variance: 0.002      # ±0.002 variation per person
```

**Understanding the values:**
- Needs are measured from `0.0` (satisfied) to `1.0` (critical)
- `base_hunger_rate: 0.01` means hunger increases by 0.01 per hour (takes 100 hours to go from 0 to 1.0)
- `variance` adds randomness—each person has slightly different metabolism

**Example scenarios:**
- **Fast metabolism:** `base_hunger_rate: 0.02` - People get hungry twice as fast
- **Slow metabolism:** `base_hunger_rate: 0.005` - People get hungry slower
- **High variance:** `hunger_rate_variance: 0.01` - More variation between people

**Tip:** Higher rates mean people need resources more frequently. Lower rates mean they can go longer without.

### Needs Fulfillment System

**What it does:** People try to satisfy their needs by consuming resources.

```yaml
systems_config:
  HumanNeedsFulfillmentSystem:
    enabled: true
    frequency: hourly
    satisfaction_ranges:
      food:
        hunger_restore_min: 0.05   # Each unit of food restores 0.05-0.15 hunger
        hunger_restore_max: 0.15
      water:
        thirst_restore_min: 0.10   # Each unit of water restores 0.10-0.30 thirst
        thirst_restore_max: 0.30
      rest:
        rest_restore_min: 0.05     # Per hour of rest
        rest_restore_max: 0.15
```

**Understanding the values:**
- When someone consumes food, their hunger decreases by a random amount between `hunger_restore_min` and `hunger_restore_max`
- Higher values = more satisfying (less food needed)
- Lower values = less satisfying (more food needed)

**Example:** If `hunger_restore_min: 0.05` and `hunger_restore_max: 0.15`, consuming 1 unit of food reduces hunger by 0.05-0.15. To go from hunger 1.0 to 0.0, someone might need 7-20 units of food.

### Health System

**What it does:** Converts unmet needs and pressure into health damage. Health can recover when needs are met.

```yaml
systems_config:
  HealthSystem:
    enabled: true
    frequency: hourly
    pressure_damage:
      min_per_tick: 0.001   # At max pressure (1.0), damage is 0.001-0.005 per hour
      max_per_tick: 0.005
    unmet_needs_damage:
      hunger:
        min_per_tick: 0.0005  # At max hunger (1.0), damage is 0.0005-0.002 per hour
        max_per_tick: 0.002
      thirst:
        min_per_tick: 0.001
        max_per_tick: 0.003
      rest:
        min_per_tick: 0.0002
        max_per_tick: 0.001
    healing_rate:
      min_per_tick: 0.0001   # When needs are met, health recovers 0.0001-0.0005 per hour
      max_per_tick: 0.0005
```

**Understanding the values:**
- Health is measured from `0.0` (dead) to `1.0` (perfect health)
- Damage values are per hour when the need/pressure is at maximum (1.0)
- Lower damage values = people survive longer without resources
- Higher damage values = people die faster when resources are scarce

**Example scenarios:**
- **Resilient population:** Lower damage values (people survive longer)
- **Fragile population:** Higher damage values (people die faster)
- **Fast healing:** Higher `healing_rate` values (people recover quickly)

### Death System

**What it does:** People die from low health or old age.

```yaml
systems_config:
  DeathSystem:
    enabled: true
    frequency: hourly
    age_mortality:
      old_age_start: 70              # Mortality starts increasing at age 70
      old_age_death_chance_min: 0.00001  # Minimum death chance per hour at age 70
      old_age_death_chance_max: 0.0001   # Maximum death chance per hour at age 70
      peak_mortality_age: 85         # Most deaths occur around age 85
      chance_increase_per_year: 0.00001  # Base increase per year after 70
      chance_multiplier_per_year: 1.1    # Exponential increase after peak age
```

**Understanding the values:**
- Death from health: If health reaches 0.0, immediate death
- Death from age: Probability-based, increases with age
- `old_age_start: 70` - Death risk starts increasing at age 70
- `peak_mortality_age: 85` - Most deaths happen around this age
- Most people die between 73-100, but rare outliers can survive past 100

**Example scenarios:**
- **Longer lifespans:** Increase `old_age_start` to 80, increase `peak_mortality_age` to 95
- **Shorter lifespans:** Decrease `old_age_start` to 60, decrease `peak_mortality_age` to 75

### Job System

**What it does:** People work jobs, produce resources, and earn money.

```yaml
systems_config:
  JobSystem:
    enabled: true
    assignment_frequency: monthly    # Jobs assigned monthly
    production_frequency: monthly    # Production happens monthly
    min_work_age: 15                # Minimum age to work
    max_work_age: 70                # Retirement age
    base_hiring_chance: 0.3         # 30% chance per month for unemployed to get hired
    yearly_raise_probability: 0.7   # 70% chance of yearly raise
    raise_amount_range: [0.02, 0.05]  # 2-5% raise amount
    jobs:
      farmer:
        name: Farmer
        max_percentage: 10.0         # Max 10% of population can be farmers
        payment:
          money: 100.0              # Earns 100 money per month
        min_payment:
          money: 50.0               # Minimum salary
        max_payment_cap:
          money: 130.0              # Maximum salary after raises
        min_age: 16                 # Must be at least 16 to be a farmer
        production:
          resource_id: food
          rate: 50.0                # Produces 50 food per month per farmer
          frequency: monthly
        required_skill: farming
        skill_weight: 0.7           # Skills matter 70% in hiring
        charisma_weight: 0.1        # Charisma matters 10%
        job_type: production        # Produces resources
```

**Key settings explained:**

- **`max_percentage`**: Maximum percentage of population that can work this job
  - `10.0` = Up to 10% of people can be farmers
  - `5.0` = Up to 5% can be farmers

- **`payment`**: How much money workers earn per production period
  - `money: 100.0` = Earns 100 money per month

- **`production`**: What resources this job produces
  - `resource_id: food` = Produces food
  - `rate: 50.0` = Each farmer produces 50 food per month

- **`min_age`**: Minimum age required for this job
  - `16` = Must be at least 16 years old
  - `21` = Must be at least 21 (professional jobs)

- **`job_type`**: 
  - `production` = Produces resources (farmers, miners)
  - `service` = Provides services but doesn't produce resources (teachers, service workers)

**Example job configurations:**

**High-paying professional job:**
```yaml
teacher:
  name: Teacher
  max_percentage: 3.0
  payment:
    money: 150.0
  min_age: 21
  required_skill: teaching
  skill_weight: 0.9  # Skills very important
  job_type: service  # No resource production
```

**Low-skill entry job:**
```yaml
burger_flipper:
  name: Fast Food Worker
  max_percentage: 8.0
  payment:
    money: 40.0
  min_age: 15
  required_skill: service
  skill_weight: 0.2  # Skills less important
  job_type: service
```

### History Tracking Systems

**What they do:** Record data over time so you can analyze trends later.

#### Resource History System

```yaml
systems_config:
  ResourceHistorySystem:
    enabled: true
    frequency: daily      # Save data daily
    rate: 1              # Every 1 day (rate=2 means every 2 days)
    resources: []        # Empty = track all resources
```

**What this means:** Records resource amounts over time. You can export this data to CSV for analysis.

**Options:**
- `frequency`: When to save (`hourly`, `daily`, `weekly`, `monthly`, `yearly`)
- `rate`: Save every N periods (e.g., `rate: 2` with `daily` = save every 2 days)
- `resources`: List specific resources to track, or `[]` to track all

**Example:** Track only food and water:
```yaml
resources: [food, water]
```

#### Entity History System

```yaml
systems_config:
  EntityHistorySystem:
    enabled: true
    frequency: daily
    rate: 1
    component_types: []  # Empty = track all components
```

**What this means:** Records population statistics over time (total people, average health, employment, etc.).

**Metrics tracked:**
- Total population
- Average hunger, thirst, rest levels
- Average health
- Average age and wealth
- Employment count
- And more...

### Logging Configuration

**What it does:** Controls how much information is written to log files.

```yaml
logging:
  world_state:
    enabled: true
    frequency: monthly   # Log world state monthly
    rate: 1             # Every 1 month
  systems:
    enabled: false      # Disable system metrics logging
    frequency: monthly
    rate: 2
```

**Understanding:**
- **World state logging**: Records resource levels, population, active modifiers
- **Systems logging**: Records system status and metrics
- **Frequency**: When to check for logging (`hourly`, `daily`, `weekly`, `monthly`, `yearly`)
- **Rate**: Log every N periods (e.g., `rate: 2` with `weekly` = log every 2 weeks)

**Recommendations:**
- For short simulations: `frequency: daily` or `hourly`
- For long simulations: `frequency: monthly` or `yearly`
- Disable systems logging if you don't need it: `enabled: false`

---

## Common Scenarios

### Scenario 1: Abundant Resources

**Goal:** Create a world where resources are plentiful and people thrive.

**Configuration changes:**
```yaml
resources:
  - id: food
    initial_amount: 5000.0      # Start with lots
    replenishment_rate: 200.0   # High replenishment
    replenishment_frequency: hourly

systems_config:
  ResourceProductionSystem:
    production:
      food: 500.0  # High production
```

### Scenario 2: Resource Scarcity

**Goal:** Create a challenging scenario where resources are limited.

**Configuration changes:**
```yaml
resources:
  - id: food
    initial_amount: 100.0       # Start with little
    replenishment_rate: 10.0    # Low replenishment
    finite: false

systems_config:
  ResourceProductionSystem:
    production:
      food: 20.0  # Low production
  ResourceConsumptionSystem:
    consumption:
      food: 50.0  # High consumption (more than production)
```

### Scenario 3: Slow Population Growth

**Goal:** Population grows slowly over time.

**Configuration changes:**
```yaml
systems_config:
  HumanSpawnSystem:
    spawn_rate: 2  # Only 2 new people per day (instead of 10)
```

### Scenario 4: Long-Lived Population

**Goal:** People live longer lives.

**Configuration changes:**
```yaml
systems_config:
  DeathSystem:
    age_mortality:
      old_age_start: 80         # Mortality starts later
      peak_mortality_age: 95   # Peak mortality later
  HealthSystem:
    healing_rate:
      min_per_tick: 0.0005     # Faster healing
      max_per_tick: 0.001
```

### Scenario 5: High Employment Economy

**Goal:** Most people work jobs and produce resources.

**Configuration changes:**
```yaml
systems_config:
  JobSystem:
    base_hiring_chance: 0.5    # Higher hiring chance
    jobs:
      farmer:
        max_percentage: 20.0   # More farmers allowed
      teacher:
        max_percentage: 5.0    # More teachers
```

---

## Tips for Configuration

1. **Start simple**: Use the default configuration first, then make small changes
2. **Test incrementally**: Change one thing at a time to see its effect
3. **Balance resources**: Make sure production + replenishment ≥ consumption (or resources will run out)
4. **Monitor population**: If death rate > birth rate, population will decline
5. **Check logs**: Review log files to see what's happening in your simulation
6. **Export data**: Use history systems and export commands to analyze trends

---

## Getting Help

- **Configuration errors?** Check YAML syntax (indentation, colons, dashes)
- **Simulation not working?** Check that all required systems are enabled
- **Resources running out?** Increase production/replenishment or decrease consumption
- **Population dying?** Check if resources are sufficient and health system settings

For more information, see:
- [Getting Started Guide](../Overview/getting-started.md) - How to run simulations
- [Operations Guide](../Operations/README.md) - Exporting data and managing simulations
- [Systems Documentation](../Systems/README.md) - Detailed system information

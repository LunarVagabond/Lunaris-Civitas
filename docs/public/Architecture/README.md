# Architecture

## Design Principles

- **Deterministic and replayable**: Same seed produces same results
- **Modular and extensible**: Systems don't depend on each other
- **Data-driven**: All behavior driven by configuration
- **System contract**: Every system follows the same interface
- **Hot-addable**: New systems can be added without engine changes

## Core Components

### Time System

- 1 tick = 1 hour
- Proper calendar handling (month lengths, leap years)
- Tracks absolute datetime, ticks elapsed, RNG seed

### World State

Contains:
- Current simulation datetime
- Total ticks elapsed
- RNG seed and state
- Config snapshot
- Registered systems
- Global resources
- Active modifiers
- Entities (with components)

## Entity Component System (ECS)

Lunaris Civitas uses a lightweight Entity Component System architecture for managing entities and their behaviors.

### ECS Component Hierarchy

```mermaid
graph TB
    Component[Component Base Class]
    Needs[NeedsComponent]
    Inventory[InventoryComponent]
    Pressure[PressureComponent]
    Health[HealthComponent]
    Age[AgeComponent]
    Wealth[WealthComponent]
    Employment[EmploymentComponent]
    Household[HouseholdComponent]
    
    Component --> Needs
    Component --> Inventory
    Component --> Pressure
    Component --> Health
    Component --> Age
    Component --> Wealth
    Component --> Employment
    Component --> Household
```

### Entity-Component Relationship

```mermaid
graph LR
    Entity[Entity]
    Component1[Component 1]
    Component2[Component 2]
    ComponentN[Component N]
    WorldState[WorldState]
    
    Entity -->|has| Component1
    Entity -->|has| Component2
    Entity -->|has| ComponentN
    WorldState -->|stores| Entity
```

### Requirement Resolution Architecture

Entities have needs that create resource requirements. These requirements can be fulfilled through multiple sources, each with different conditions and requirements:

```mermaid
graph TD
    Needs[NeedsComponent]
    ReqResolver[RequirementResolverSystem]
    Source1[Source: Inventory]
    Source2[Source: Household]
    Source3[Source: Market]
    Source4[Source: Production]
    Pressure[PressureComponent]
    
    Needs -->|generates requirements| ReqResolver
    ReqResolver -->|tries priority 1| Source1
    ReqResolver -->|tries priority 2| Source2
    ReqResolver -->|tries priority 3| Source3
    ReqResolver -->|tries priority 4| Source4
    ReqResolver -->|if all fail| Pressure
```

### System Interaction Flow

```mermaid
sequenceDiagram
    participant HS as HumanSystem
    participant NC as NeedsComponent
    participant RR as RequirementResolver
    participant S1 as Source1: Inventory
    participant S2 as Source2: Market
    participant PC as PressureComponent
    
    HS->>NC: get_resource_requirements()
    NC-->>HS: {"food": 10.0}
    HS->>RR: resolve_requirement(food, 10.0)
    RR->>S1: try_source()
    S1-->>RR: failed (no inventory)
    RR->>S2: try_source()
    S2-->>RR: success (purchased)
    RR-->>HS: fulfilled: 10.0
    alt All sources fail
        RR->>PC: add_pressure(food, 10.0)
    end
```

### System Contract

All systems implement:
- `system_id`: Unique identifier
- `init(world_state, config)`: Initialization
- `on_tick(world_state, current_datetime)`: Tick processing
- `shutdown(world_state)`: Optional cleanup

### Modifiers

Pure data structures for buffs/debuffs/events:
- Target systems, resources, or categories
- Apply multipliers and additive adjustments
- Stacking rules: multiplicative first, then additive

## System Interaction

Systems **never** call each other directly. All interaction happens through the world state:
- Systems read/write resources
- Systems query active modifiers
- Systems add/remove modifiers
- Systems never depend on other systems

## Further Reading

For detailed information about execution flows, call chains, and interface patterns, see:
- **[Core Execution Flows](../Development/CORE_FLOWS.md)** - Complete documentation of simulation loop, system patterns, and call chains

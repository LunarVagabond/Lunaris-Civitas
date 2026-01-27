# Future Tickets & Roadmap

This document tracks planned features, improvements, and technical debt for future phases.

---

## Phase 2: Base Human (Minimal Survival)

### Core Human Components
- [ ] `Needs` component (hunger, thirst, rest)
- [ ] `Inventory` component (personal resources)
- [ ] `Health` component (simple health status)
- [ ] `Age` component (birth date, lifespan)

### Systems
- [ ] `NeedsSystem` - Updates needs (minute/hour ticks)
- [ ] `HumanConsumptionSystem` - Humans consume resources based on needs (day ticks)
- [ ] `DeathSystem` - Handles death from starvation, thirst, age

### Infrastructure
- [ ] ECS-lite implementation (simple component system)
- [ ] Entity registry in world state
- [ ] Component storage system
- [ ] Human entity creation from config

### Testing
- [ ] Unit tests for human components
- [ ] Integration tests for survival mechanics
- [ ] Determinism tests with humans

---

## Phase 2.5: Actions System

**Status:** 🔜 Planned (Likely next phase)

**Goal:** Entities perform time-based actions (eating, sleeping, working) that occupy them for periods of time.

### Components
- [ ] `Action` component - Current action being performed
- [ ] `ActionQueue` component - Planned actions
- [ ] `Traits` component - Individual characteristics (sleep needs, metabolism, etc.)

### Systems
- [ ] `ActionSystem` - Manages entity actions and state transitions (hourly ticks)
- [ ] `ActionSchedulerSystem` - Plans actions based on needs and priorities (hourly ticks)
- [ ] `TraitSystem` - Applies trait effects to actions and needs (hourly ticks)

### Features
- [ ] Action types: `eat`, `sleep`, `work`, `rest`, `travel`, etc.
- [ ] Actions take time (e.g., sleep 6-12 hours)
- [ ] Entities are "occupied" during actions (can't perform other actions)
- [ ] Traits affect action requirements:
  - Sleep needs: Some need 6 hours, others need 10 hours
  - Metabolism: Some need more food, others less
  - Activity level: Some need more rest, others can work longer
- [ ] Action priorities based on need levels
- [ ] Action interruption (emergency needs override current action)

### Design Decisions
- Actions are time-based, not instant
- Entities can only perform one action at a time
- Actions can be interrupted by critical needs
- Traits create individual variation in action requirements
- Action system enables more realistic behavior modeling

### Why This Matters
- Makes entity behavior more realistic
- Enables proper sleep cycles (entities sleep 6-12 hours)
- Foundation for work schedules, daily routines
- Allows for individual variation through traits
- Better models human time constraints

---

## Phase 3: Time, Aging, Reproduction

### Components
- [ ] `Fertility` component
- [ ] `Lifespan` component (mortality curves)
- [ ] `Dependency` component (infant/child care)

### Systems
- [ ] `AgingSystem` - Age progression (year ticks)
- [ ] `BirthSystem` - Reproduction (year ticks)
- [ ] `MortalitySystem` - Age-based death (year ticks)

### Features
- [ ] Lifespan curves (infant mortality, old age)
- [ ] Fertility stats (age-based)
- [ ] Infant dependency periods
- [ ] Population growth/decline tracking

---

## Phase 4: Economy & Jobs

### Components
- [ ] `Employment` component
- [ ] `Wealth` component
- [ ] `Household` component

### Systems
- [ ] `JobSystem` - Job assignment, wages (month ticks)
- [ ] `MarketSystem` - Resource trading (day/month ticks)
- [ ] `HouseholdSystem` - Shared resources
- [ ] `TransferSystem` - Inter-generational transfers

### Features
- [ ] Job types (farmer, miner, etc.)
- [ ] Wage system
- [ ] Basic market dynamics
- [ ] Household resource sharing

---

## Phase 5: Geography & Environment

### Components
- [ ] `Location` component
- [ ] `Area` entity type
- [ ] `Weather` component

### Systems
- [ ] `WeatherSystem` - Climate patterns
- [ ] `MigrationSystem` - Population movement
- [ ] `ResourceLocalitySystem` - Resource distribution by area

### Features
- [ ] Area definitions in config
- [ ] Weather patterns
- [ ] Migration mechanics
- [ ] Regional resource differences

---

## Phase 6: Health, Disease, Pandemics

### Components
- [ ] `Disease` entity type
- [ ] `Immunity` component
- [ ] `Healthcare` component

### Systems
- [ ] `DiseaseSystem` - Disease spread
- [ ] `HealthSystem` - Health status updates
- [ ] `PandemicSystem` - Configurable pandemics
- [ ] `HealthcareSystem` - Medical capacity

### Features
- [ ] Disease transmission models
- [ ] Contact tracing (if needed)
- [ ] Healthcare capacity limits
- [ ] Immunity tracking
- [ ] Mortality from disease

---

## Phase 7: Crime, Corruption, Policing

### Components
- [ ] `Crime` component
- [ ] `Corruption` component
- [ ] `LawEnforcement` component

### Systems
- [ ] `CrimeSystem` - Crime generation
- [ ] `PolicingSystem` - Law enforcement
- [ ] `CorruptionSystem` - Corruption spread
- [ ] `PunishmentSystem` - Prison/punishment

### Features
- [ ] Crime probability based on conditions
- [ ] Detection probabilities
- [ ] Bribe mechanics
- [ ] Prison system
- [ ] Corruption networks

---

## Phase 8: Politics & Power

### Components
- [ ] `PoliticalAffiliation` component
- [ ] `Government` entity type
- [ ] `Policy` entity type

### Systems
- [ ] `PoliticsSystem` - Group formation
- [ ] `GovernmentSystem` - Policy implementation
- [ ] `PolicySystem` - Policy effects
- [ ] `RevolutionSystem` - Unrest and regime change

### Features
- [ ] Political parties
- [ ] Policy creation
- [ ] Policy effects as modifiers
- [ ] Revolution mechanics
- [ ] Government stability

---

## Phase 9: Discord Integration

### Features
- [ ] Read-only query API
- [ ] Human tracking/watching
- [ ] Statistics feeds
- [ ] Event highlights
- [ ] Real-time updates

### Future Enhancements
- [ ] User "birth" system (probabilistic)
- [ ] Probabilistic influence
- [ ] Never full control (scientific integrity)

---

## Phase 10: Expert Mode

### Features
- [ ] Scenario config system
- [ ] Batch run capability
- [x] CSV export (✅ Phase 1 complete - resource history export)
- [ ] Deterministic replay
- [ ] Parameter sweeps
- [ ] Statistical analysis tools

### Research Tools
- [ ] Multi-scenario comparison
- [x] Data export formats (✅ Phase 1 complete - CSV export for resource history)
- [ ] Reproducibility tools
- [ ] Academic-grade outputs

---

## Technical Debt & Improvements

### Core Engine
- [ ] Consider interface/context objects for resource operations (when needed)
- [x] Add change tracking for analytics (✅ Phase 1 complete - ResourceHistorySystem tracks resource values over time)
- [ ] Transaction-like operations (if needed)
- [ ] Performance optimization for large populations

### Testing
- [ ] Expand test coverage
- [ ] Integration test suite
- [ ] Performance benchmarks
- [ ] Determinism validation suite

### Documentation
- [ ] API reference
- [ ] System development guide
- [ ] Config schema documentation
- [x] Analytics/reporting guide (✅ Phase 1 complete - CSV export documented in Operations guide)

### Infrastructure
- [ ] Database migration system (for schema changes)
- [ ] Config validation
- [ ] Better error handling
- [ ] Performance monitoring

---

## Notes

- Tickets are organized by phase
- Priorities may shift based on research needs
- Some features may be combined or split
- All features must maintain determinism
- All systems must be configurable and disable-able

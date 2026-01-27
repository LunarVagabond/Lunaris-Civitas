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

## Phase 3: Job System (Resource Production)

**Status:** 🔜 **NEXT PRIORITY** - Critical for resource sustainability

**Why Critical:** Food is running out quickly. Humans need jobs to produce resources (farmers → food, etc.)

### Components
- [x] `Employment` component (exists, needs enhancement for job assignment)
- [ ] `JobAssignment` component - Tracks job assignments and production rates

### Systems
- [ ] `JobSystem` - Job assignment and resource production (hourly/month ticks)
  - Assigns jobs to entities (farmers, miners, water_workers, etc.)
  - Jobs produce resources directly into world state
  - Production rates scale with number of workers
  - Work hours/rest cycles

### Features
- [ ] Job types: `farmer` (produces food), `miner` (produces raw materials), `water_worker` (produces water), etc.
- [ ] Job assignment logic (probabilistic, based on needs/capabilities)
- [ ] Resource production directly into world state (not through money yet)
- [ ] Production rates configurable per job type
- [ ] Production scales with number of workers
- [ ] Work hours/rest cycles (can't work 24/7)
- [ ] Foundation for later economy system (Phase 6)

### Design Decisions
- Jobs produce resources directly (wages/markets come in Phase 6)
- Simple job assignment (probabilistic)
- Production scales with number of workers
- Addresses current food scarcity crisis

---

## Phase 4: Reproduction System

**Status:** 🔜 **HIGH PRIORITY** - Critical for population sustainability

**Why Critical:** Current spawn system is temporary placeholder. Need proper reproduction based on fertility, relationships, age.

### Components
- [ ] `Fertility` component - Age-based fertility curves
- [ ] `Relationship` component - Partner/parent relationships
- [ ] `Pregnancy` component - Tracks pregnancy state and duration
- [ ] `Dependency` component - Infant/child dependency periods

### Systems
- [ ] `ReproductionSystem` - Handles births based on fertility and relationships (month/year ticks)
- [ ] `RelationshipSystem` - Manages partnerships and family structures
- [x] `AgingSystem` - Age progression (exists, may need enhancement)

### Features
- [ ] Age-based fertility curves (peak 20-35, declines with age)
- [ ] Reproduction requires partners (relationships)
- [ ] Pregnancy duration (9 months)
- [ ] Birth probability based on fertility, age, health, resource availability
- [ ] Infant dependency (requires care from parents)
- [ ] Population growth/decline based on birth/death rates
- [ ] Replaces `HumanSpawnSystem` runtime spawning

### Design Decisions
- Probabilistic reproduction (not deterministic)
- Requires relationships/partnerships
- Birth rates affected by resource availability
- Foundation for demographic modeling

---

## Phase 5: Actions System

**Status:** 🔜 Planned

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

## Phase 6: Economy & Markets

**Status:** 🔜 Planned

**Goal:** Full economic system with money, wages, and markets.

### Components
- [x] `Employment` component (exists, needs wage system)
- [x] `Wealth` component (exists, needs market integration)
- [x] `Household` component (exists, needs enhancement)

### Systems
- [ ] `MarketSystem` - Basic resource trading (day/month ticks)
- [ ] `WageSystem` - Wage distribution based on jobs (month ticks)
- [ ] `HouseholdSystem` - Shared resources within families
- [ ] `TransferSystem` - Inter-generational wealth transfer

### Features
- [ ] Jobs pay wages (money/resources)
- [ ] Markets enable resource trading
- [ ] Wages enable resource purchase
- [ ] Households share resources
- [ ] Basic market dynamics
- [ ] Prices fluctuate based on supply/demand

### Note
This builds on Phase 3 Job System, adding wages and markets to the resource production foundation.

---

## Phase 7: Geography & Environment

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

## Phase 8: Health, Disease, Pandemics

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

## Phase 9: Crime, Corruption, Policing

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

## Phase 10: Politics & Power

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

## Phase 11: Discord Integration

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

## Phase 12: Expert Mode

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

# Future Tickets & Roadmap

This document tracks planned features, improvements, and technical debt for future phases.

---

## Phase 2: Base Human (Minimal Survival)

**Status:** ✅ Complete

### Core Human Components
- [x] `Needs` component (hunger, thirst, rest)
- [x] `Inventory` component (personal resources)
- [x] `Health` component (simple health status)
- [x] `Age` component (birth date, lifespan)
- [x] `Pressure` component (unmet resource requirements)
- [x] `Wealth` component (money/resources)
- [x] `Household` component (household linkage)

### Systems
- [x] `NeedsSystem` - Updates needs (hourly ticks)
- [x] `HumanNeedsFulfillmentSystem` - Fulfills needs through RequirementResolverSystem
- [x] `DeathSystem` - Handles death from starvation, thirst, age
- [x] `RequirementResolverSystem` - Resolves resource requirements through multiple sources

### Infrastructure
- [x] ECS-lite implementation (simple component system)
- [x] Entity registry in world state
- [x] Component storage system
- [x] Human entity creation from config

### Testing
- [x] Unit tests for human components
- [x] Integration tests for survival mechanics
- [x] Determinism tests with humans

---

## Phase 3: Job System (Resource Production)

**Status:** ✅ Complete

**Why Critical:** Food was running out quickly. Humans needed jobs to produce resources (farmers → food, etc.)

### Components
- [x] `Employment` component - Enhanced with job assignment, payment tracking, salary caps
- [x] `Skills` component - Core traits and job-specific skills
- [x] `Wealth` component - Extended to support multiple resource types

### Systems
- [x] `JobSystem` - Job assignment, resource production, and payment distribution
- [x] `JobHistorySystem` - Employment statistics tracking

### Features
- [x] Job types: `farmer`, `miner`, `teacher`, `burger_flipper`, etc.
- [x] Job assignment logic (probabilistic, based on skills, charisma, age)
- [x] Resource production directly into world state
- [x] Payment in any resource type (money, crypto, bananas, etc.)
- [x] Production rates configurable per job type
- [x] Production scales with number of workers
- [x] Percentage-based job limits
- [x] Dynamic hiring chance (increases when jobs are "needy")
- [x] Salary increases and job loss mechanisms

### Design Decisions
- Jobs can pay in any resource type (fully configurable)
- Payment stored as `payment_resources: {resource_id: amount}` dictionary
- Everything config-driven - no hardcoded values
- Config persisted in database (resume doesn't reload from config file)

### Temporary Solutions (Phase 3)
- **Money Generation**: Money resource currently replenishes monthly (5000/month) to prevent running out
  - This is TEMPORARY until Phase 6 (Economy & Markets) implements proper economic systems
  - TODO: Remove money replenishment when proper economic system is in place
- **Unpaid Worker Quitting**: If workers are not paid (insufficient world money), they quit their jobs
  - This is a real-world problem that can happen
  - In Phase 6, proper economic systems will prevent money shortages

### Known Limitations & Future Improvements

- **Job Limits Not Exact**: Percentage-based job limits (e.g., max 10% of population) are calculated dynamically, but population can grow faster than jobs open. Jobs may reach capacity and remain full even as population increases, creating unemployment pressure. This is intentional - real-world companies don't always hire immediately when population grows.

- **No Company/Employer Entities**: Current system treats all jobs as self-employed or abstract "world" employers. Future system should introduce:
  - `Company` entity type with capital/resource constraints
  - Companies have limited budgets for payroll
  - Companies can only hire when they have sufficient capital
  - Creates realistic economic pressure and unemployment
  - Enables company growth/shrinkage based on profitability
  - Foundation for corporate dynamics and economic modeling

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

**Goal:** Full economic system with money, wages, markets, and companies.

### Components
- [x] `Employment` component (exists, enhanced with payment system)
- [x] `Wealth` component (exists, supports multiple resource types)
- [x] `Household` component (exists, needs enhancement)
- [ ] `Company` component - Company entity with capital, payroll budget, profitability
- [ ] `Business` component - Business type, industry sector, market position

### Systems
- [ ] `MarketSystem` - Basic resource trading (day/month ticks)
- [ ] `WageSystem` - Wage distribution based on jobs (month ticks)
- [ ] `CompanySystem` - Company management, hiring decisions, capital management
- [ ] `HouseholdSystem` - Shared resources within families
- [ ] `TransferSystem` - Inter-generational wealth transfer
- [ ] `EconomicPressureSystem` - Tracks unemployment, economic stress, market conditions

### Features
- [ ] Jobs pay wages (money/resources) - ✅ Already implemented in Phase 3
- [ ] Markets enable resource trading
- [ ] Wages enable resource purchase
- [ ] Households share resources
- [ ] Basic market dynamics
- [ ] Prices fluctuate based on supply/demand
- [ ] **Company System**:
  - Companies have capital/resource budgets
  - Companies can only hire when they have sufficient capital for payroll
  - Companies grow/shrink based on profitability
  - Creates realistic unemployment when companies can't afford workers
  - Job openings depend on company financial health, not just population %
  - Enables corporate dynamics and economic modeling
- [ ] **Economic Pressure**:
  - Unemployment creates societal pressure
  - Companies compete for workers when labor is scarce
  - Companies lay off workers when capital is low
  - Economic cycles and recessions

### Design Decisions
- Companies are entities with their own resources/capital
- Hiring decisions based on company financial health
- Job limits become dynamic based on company capacity, not just population %
- Creates realistic economic constraints and pressure

### Note
This builds on Phase 3 Job System, adding companies, markets, and proper economic constraints to replace temporary money generation.

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

### Configuration Management
- [ ] **Modular YAML Config Loader** - Split `dev.yml` into system-specific config files
  - Each system has its own config file (e.g., `configs/systems/job_system.yml`)
  - Main config file imports/merges system configs
  - Easier to manage and version control
  - Reduces conflicts when multiple developers work on different systems
  - Priority: High (config file is getting large and unwieldy)

### Logging & Observability

- [ ] **Log Batching/Aggregation** - Reduce log verbosity by grouping similar events
  - Batch similar events (e.g., "35 entities received payment raises" instead of 35 individual lines)
  - Aggregate statistics: "Payment raises: 35 entities, avg 3.2%, range 2.0-5.0%"
  - Configurable aggregation level (per system, per event type)
  - Summary lines with details available on demand
  - Reduces log noise while preserving important information
  - Priority: Medium-High (log files are becoming unreadable)

- [ ] **Watched List System** - Mark entities/resources/jobs for detailed logging
  - Config file or runtime command to mark entities as "watched"
  - Watched entities log all actions/events in detail
  - Unwatched entities use aggregated/batched logging
  - Can watch: entities (by ID), resources (by ID), job types, or patterns
  - Example: `watched_entities: [entity_id_1, entity_id_2]` or `watched_jobs: [teacher, farmer]`
  - Enables focused debugging and observation without log spam
  - Priority: Medium-High (complements log batching)

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

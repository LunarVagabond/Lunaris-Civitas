# Development Phases

## Overview

Lunaris Civitas is being developed in phases, building from a minimal core engine to a comprehensive simulation platform. Each phase adds capabilities while maintaining the core principles of determinism, modularity, and extensibility.

## Core Design Principles

1. **No system talks directly to another system** - All interaction via world state
2. **Everything is config + stats** - Data-driven behavior
3. **Humans never "decide"** - Systems decide probabilistically
4. **Every feature must be disable-able** - Modular and optional
5. **If it can't be graphed, it's not real** - Analytics-first design
6. **Complexity is allowed only when isolated** - Systems are independent

---

## Phase 0: Simulation Spine (Foundation)

**Status:** ✅ Complete

**Goal:** Prove the engine works with a minimal, stable core.

**Deliverables:**

- Tick scheduler (1 tick = 1 hour)
- System registry and contract
- Event bus (modifiers system)
- SQLite persistence
- Config loader + snapshot system
- Seeded RNG for determinism

**Test Criteria:**

- Run 10 years with fake entities
- Restart sim, resume state exactly
- Add a dummy system later and migrate cleanly

**Key Constraint:** No humans. No fun stuff. This phase is boring but critical.

---

## Phase 1: Resources & World State

**Status:** ✅ Complete

**Goal:** Scarcity exists. Resources can be produced, consumed, and replenished.

**Deliverables:**
- `Resource` model (food, water, electricity, oil, etc.)
- Resource production system (natural/baseline)
- Resource consumption system (natural/baseline - decay, evaporation)
- Resource replenishment system (natural - rain, growth)
- Frequency support (hourly, daily, weekly, monthly, yearly)
- Modifier system for buffs/debuffs

**No humans yet** - just abstract consumers/producers.

**Why This First:**
- Lets you debug depletion, growth, collapse
- Sets up economic pressure *before* humans exist
- Establishes baseline natural processes

---

## Phase 2: Base Human (Minimal Survival)

**Status:** ✅ Complete

**Goal:** Humans don't die immediately. Basic survival mechanics.

**Deliverables:**

**Human Components:**
- `Needs`: hunger, thirst, rest
- `Inventory`: personal resources
- `Health`: simple health status
- `Age`: birth date, lifespan tracking
- `Pressure`: unmet resource requirements
- `Wealth`: money/resources
- `Employment`: job information
- `Household`: household linkage

**Systems:**
- `HumanSpawnSystem`: Creates initial population and runtime spawning (TEMPORARY PLACEHOLDER for Phase 4 reproduction system)
- `NeedsSystem`: Updates needs with randomized per-entity decay rates (hourly ticks)
- `HumanNeedsFulfillmentSystem`: Actively fulfills needs through RequirementResolverSystem (hourly ticks)
- `HealthSystem`: Converts pressure and unmet needs into health degradation (hourly ticks)
- `DeathSystem`: Handles death from health degradation and age-based mortality (hourly ticks)
- `RequirementResolverSystem`: Resolves resource requirements through multiple sources

**Constraints:**
- No families (household component exists but not fully utilized)
- No jobs (employment component exists but not fully utilized)
- Basic money/wealth tracking
- Just survival

**Success Criteria:**
- ✅ Humans can survive with adequate resources
- ✅ Humans die when resources depleted
- ✅ Population can grow/shrink based on resource availability
- ✅ All decay and satisfaction amounts use randomized ranges
- ✅ Age-based mortality allows rare outliers past 100

**Note**: `HumanSpawnSystem` runtime spawning is a temporary placeholder and will be replaced by a proper reproduction system in Phase 4.

---

## Phase 3: Job System (Resource Production)

**Status:** ✅ Complete

**Goal:** Humans can produce resources through jobs, enabling sustainable resource generation.

**Why This Was Critical:**
- Simulation showed food running out quickly (natural production insufficient)
- Humans were dying from hunger faster than resources could be replenished
- Jobs enable humans to actively contribute to resource production (farmers → food, etc.)

**Deliverables:**

**Components:**
- ✅ `Employment`: Enhanced with job assignment, payment tracking, salary caps
- ✅ `Skills`: Core traits (charisma, intelligence, strength, creativity, work_ethic) and job-specific skills
- ✅ `Wealth`: Extended to support multiple resource types (money, crypto, bananas, etc.)

**Systems:**
- ✅ `JobSystem`: Job assignment, resource production, and payment distribution
  - Assigns jobs to entities based on skills, charisma, age, and dynamic hiring chance
  - Jobs produce resources based on job type and worker count
  - Payment in any resource type (money, crypto, food, etc.) - fully configurable
  - Salary increases (yearly and rare 6-month raises) up to max payment cap
  - Job loss mechanism (firing, quitting, layoffs) with probabilistic chance
  - Unpaid workers automatically quit (real-world consequence)
- ✅ `JobHistorySystem`: Tracks employment statistics over time

**Features:**
- ✅ Job types: `farmer` (produces food), `miner` (produces raw materials), `teacher` (service), etc.
- ✅ Jobs produce resources directly into world state
- ✅ Production rates configurable per job type
- ✅ Jobs can pay in any resource type (money, crypto, bananas, etc.)
- ✅ Payment can be multiple resource types simultaneously (e.g., money + crypto)
- ✅ Jobs assigned based on skills, charisma, age requirements
- ✅ Dynamic hiring chance (increases when jobs are "needy", decreases when "picky")
- ✅ Percentage-based job limits (e.g., max 10% of population can be farmers)
- ✅ Age requirements per job type (e.g., 15+ for low-skill, 21+ for professional)
- ✅ Macro-level employment statistics in world state logging
- ✅ History tracking for employment rates, job distribution, average salaries

**Design Decisions:**
- ✅ Jobs can pay in any resource type (not just money) - fully configurable
- ✅ Payment stored as `payment_resources: {resource_id: amount}` dictionary
- ✅ Market costs can require multiple resource types (e.g., money + crypto)
- ✅ Everything config-driven - no hardcoded values
- ✅ Config persisted in database (resume doesn't reload from config file)
- ✅ Production scales with number of workers
- ✅ Foundation for later economy system (Phase 6)

**Why This Matters:**
- ✅ **Critical for survival**: Enables sustainable food production
- ✅ Humans become active contributors to world resources
- ✅ Foundation for economy (Phase 6 will enhance with markets)
- ✅ Addresses food scarcity crisis in simulation
- ✅ Flexible payment system supports diverse economic models

---

## Phase 4: Reproduction System

**Status:** 🔜 **HIGH PRIORITY** - Critical for population sustainability

**Goal:** Proper population dynamics through realistic reproduction, replacing spawn rate placeholder.

**Why This Is Critical:**
- Current `HumanSpawnSystem` uses simple spawn rate (temporary placeholder)
- Need proper reproduction based on fertility, relationships, age
- Population needs to grow/decline naturally based on conditions

**Deliverables:**

**Components:**
- `Fertility`: reproduction capability, age-based fertility curves
- `Relationship`: partner/parent relationships (for reproduction)
- `Pregnancy`: tracks pregnancy state and duration
- `Dependency`: infant/child dependency periods

**Systems:**
- `ReproductionSystem`: Handles births based on fertility and relationships (month/year ticks)
- `AgingSystem`: Age progression (already exists, may need enhancement)
- `RelationshipSystem`: Manages partnerships and family structures

**Features:**
- Age-based fertility curves (peak fertility 20-35, declines with age)
- Reproduction requires partners (relationships)
- Pregnancy duration (9 months)
- Birth probability based on fertility, age, health, resource availability
- Infant dependency (requires care from parents)
- Population growth/decline based on birth/death rates
- Replaces `HumanSpawnSystem` runtime spawning

**Design Decisions:**
- Probabilistic reproduction (not deterministic)
- Requires relationships/partnerships
- Birth rates affected by resource availability (scarcity reduces birth rates)
- Foundation for demographic modeling

**Why This Matters:**
- Replaces temporary spawn system with realistic reproduction
- Enables proper demographic modeling
- Population dynamics emerge from conditions
- Foundation for inter-generational effects
- Critical for long-term simulation sustainability

---

## Phase 5: Actions System

**Status:** 🔜 Planned

**Goal:** Entities perform time-based actions (eating, sleeping, working) that occupy them for periods of time.

**Deliverables:**

**Components:**
- `Action` component - Current action being performed
- `ActionQueue` component - Planned actions
- `Traits` component - Individual characteristics (sleep needs, metabolism, etc.)

**Systems:**
- `ActionSystem` - Manages entity actions and state transitions (hourly ticks)
- `ActionSchedulerSystem` - Plans actions based on needs and priorities (hourly ticks)
- `TraitSystem` - Applies trait effects to actions and needs (hourly ticks)

**Features:**
- Action types: `eat`, `sleep`, `work`, `rest`, `travel`, etc.
- Actions take time (e.g., sleep 6-12 hours)
- Entities are "occupied" during actions (can't perform other actions)
- Traits affect action requirements:
  - Sleep needs: Some need 6 hours, others need 10 hours
  - Metabolism: Some need more food, others less
  - Activity level: Some need more rest, others can work longer
- Action priorities based on need levels
- Action interruption (emergency needs override current action)

**Design Decisions:**
- Actions are time-based, not instant
- Entities can only perform one action at a time
- Actions can be interrupted by critical needs
- Traits create individual variation in action requirements
- Action system enables more realistic behavior modeling

**Why This Matters:**
- Makes entity behavior more realistic
- Enables proper sleep cycles (entities sleep 6-12 hours)
- Foundation for work schedules, daily routines
- Allows for individual variation through traits
- Better models human time constraints

---

## Phase 6: Economy & Markets

**Status:** 🔜 Planned

**Goal:** Full economic system with money, wages, and markets.

**Deliverables:**

**Components:**
- `Employment`: Enhanced with wages (already exists, needs wage system)
- `Wealth`: money/resources owned (already exists, needs market integration)
- `Household`: shared inventory for families (already exists, needs enhancement)

**Systems:**
- `MarketSystem`: Basic resource trading (day/month ticks)
- `WageSystem`: Wage distribution based on jobs (month ticks)
- `HouseholdSystem`: Shared resources within families
- `TransferSystem`: Inter-generational wealth transfer

**Features:**
- Jobs pay wages (money/resources)
- Markets enable resource trading
- Wages enable resource purchase
- Households share resources
- Basic market dynamics
- Prices fluctuate based on supply/demand

**Constraints:**
- No corruption yet
- No crime yet
- Simple economic model

**Note:** This builds on Phase 3 Job System, adding wages and markets to the resource production foundation.

---

## Phase 7: Geography & Environment

**Status:** 🔜 Planned

**Goal:** Location matters. Scarcity becomes spatial.

**Deliverables:**

**Components:**
- `Location`: geographic position
- `Area`: regions/zones with properties
- `Weather`: climate conditions

**Systems:**
- `WeatherSystem`: Climate patterns (day/month ticks)
- `MigrationSystem`: Population movement (month/year ticks)
- `ResourceLocalitySystem`: Resource distribution by area

**Features:**
- Areas have different resource availability
- Weather affects production/replenishment
- Migration based on resource scarcity
- Regional economic differences

**Impact:**
- Scarcity feels *real*
- Enables disaster modeling
- Foundation for political boundaries

---

## Phase 8: Health, Disease, Pandemics

**Status:** 🔜 Planned

**Goal:** Public health modeling. Disease transmission and control.

**Deliverables:**

**Components:**
- `Disease`: disease entity with properties
- `Immunity`: resistance to diseases
- `Healthcare`: medical capacity

**Systems:**
- `DiseaseSystem`: Disease spread and transmission (hour/day ticks)
- `HealthSystem`: Health status updates (hour/day ticks)
- `PandemicSystem`: Configurable pandemic events (year ticks)
- `HealthcareSystem`: Medical treatment capacity

**Features:**
- Disease entities with transmission rates
- Mortality & immunity tracking
- Healthcare capacity limits
- Configurable pandemic start/end years
- Contact-based transmission

**Expert-Facing Milestone:**
- This is a major "expert-facing" milestone
- Enables epidemiological research
- Foundation for public health policy modeling

---

## Phase 9: Crime, Corruption, Policing

**Status:** 🔜 Planned

**Goal:** Evil exists. Social systems respond.

**Deliverables:**

**Components:**
- `Crime`: criminal activity tracking
- `Corruption`: corruption level
- `LawEnforcement`: policing capacity

**Systems:**
- `CrimeSystem`: Crime generation based on stress/resources (day/month ticks)
- `PolicingSystem`: Law enforcement and detection (day ticks)
- `CorruptionSystem`: Corruption spread (month ticks)
- `PunishmentSystem`: Prison/punishment effects

**Features:**
- Probabilistic crime generation
- Detection probabilities
- Bribes and corruption
- Prison/punishment effects
- Crime affects resource distribution

**Design Note:**
- Mostly probabilistic systems layered over economy + stress
- Crime emerges from scarcity and inequality
- Policing effectiveness affects crime rates

---

## Phase 10: Politics & Power

**Status:** 🔜 Planned

**Goal:** Groups emerge. Policies modify system behavior.

**Deliverables:**

**Components:**
- `PoliticalAffiliation`: party/group membership
- `Government`: governing body
- `Policy`: policy modifiers

**Systems:**
- `PoliticsSystem`: Political group formation (year ticks)
- `GovernmentSystem`: Policy implementation (month/year ticks)
- `PolicySystem`: Policy effects as modifiers
- `RevolutionSystem`: Unrest and regime change

**Features:**
- Political parties/groups
- Governments implement policies
- Policies are modifiers applied to systems
- Revolutions/unrest based on conditions
- Policy effects cascade through systems

**Key Insight:**
- Policies literally are: "Modifiers applied to systems"
- Enables policy experimentation
- Foundation for political science research

---

## Phase 11: Discord Integration

**Status:** 🔜 Planned

**Goal:** Humans become observable. Real-time visibility into simulation.

**Deliverables:**

**Features:**
- Read-only queries
- Watch specific humans
- Statistics feeds
- Event highlights
- Real-time updates

**Future Enhancements:**
- Let users *be born* (probabilistic influence)
- Influence decisions probabilistically
- Never full control (keeps it scientific)

**Why Discord:**
- Forces observability
- Humanizes stats
- Surfaces weird emergent behavior
- Keeps motivation high
- Watching one corrupt cop ruin a city is compelling

---

## Phase 12: Expert Mode

**Status:** 🔜 Planned

**Goal:** Research tool. Batch runs, analytics, parameter sweeps.

**Deliverables:**

**Features:**
- Scenario configs
- Batch runs
- Output CSVs
- Deterministic replay
- Parameter sweeps
- Statistical analysis tools

**Research Capabilities:**
- Run multiple scenarios
- Compare outcomes
- Export data for analysis
- Reproducible experiments
- Academic-grade outputs

**Target Audience:**
- Epidemiologists
- Economists
- Political scientists
- Sociologists
- Urban planners

---

## Tick Model

The simulation uses a layered tick system:

| Tick   | Used For                                    |
|--------|---------------------------------------------|
| Minute | Biological needs, emergencies               |
| Hour   | Work shifts, travel, resource production    |
| Day    | Consumption, sleep, crime checks             |
| Month  | Economy, rent, taxes, policy updates        |
| Year   | Aging, births, deaths, politics, pandemics   |

Systems register for specific ticks:

```python
HealthSystem.run_on = ['hour', 'day']
EconomySystem.run_on = ['month']
DemographicsSystem.run_on = ['year']
```

---

## System Architecture

### Core Engine (Tiny, Boring, Sacred)

**Never changes much.**

Responsibilities:
- Tick scheduler
- Entity registry
- System registry
- Event bus (modifiers)
- Persistence (SQLite)
- Deterministic RNG (seeded)

**It should NOT know:**
- What hunger is
- What crime is
- What politics is
- What a pandemic is

### Systems (Plug-ins)

Everything else is a **system module**.

Each system:
- Declares what components it reads
- Declares what components it writes
- Declares which ticks it runs on
- Declares its config schema

This is *huge* for extensibility.

### Entities + Components (ECS-lite)

**Do NOT over-engineer ECS.**

Simple structure:
```
Entity {
  id
  components: Map<ComponentType, ComponentData>
}
```

Examples:
- `Human`
- `Household`
- `City`
- `Country`
- `Organization`
- `ResourceNode`

Components:
- `Needs`
- `Inventory`
- `Health`
- `Location`
- `Wealth`
- `Employment`
- `Relationships`
- `PoliticalAffiliation`

Systems operate on *components*, not entity types.

---

## Config-Driven World Initialization

**Key Insight:** Config drives everything.

Flow:
1. Read config files
2. Migrate DB schema if needed
3. Populate missing systems / components
4. Lock config snapshot into DB
5. Run simulation

When adding a new system:
- Config is re-read
- DB is migrated
- New system state is initialized
- Existing entities get default components if needed

**This avoids resets.**

---

## Future Considerations

### Interface/Context Objects

**Status:** Deferred

Consider adding standardized interfaces for resource operations when:
- Multiple systems need similar operations
- Change tracking/analytics needed
- Transaction-like behavior required
- Testing becomes difficult

**Current approach:** Direct world state interaction is sufficient for Phase 1-2.

### ECS Implementation

**Status:** Deferred until Phase 2

When humans are added, implement ECS-lite:
- Simple component system
- Not over-engineered
- Systems operate on components
- Easy to extend

---

## Phase Completion Criteria

Each phase must:
- ✅ Pass all tests
- ✅ Maintain determinism (same seed = same results)
- ✅ Support save/resume
- ✅ Be configurable
- ✅ Be disable-able
- ✅ Not break previous phases
- ✅ Have documentation

---

## Notes

- Phases build on each other
- Each phase adds capabilities without breaking existing ones
- The core engine remains stable
- Systems are hot-addable
- Config drives behavior
- Everything is data-driven

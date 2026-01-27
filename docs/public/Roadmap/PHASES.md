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

**Status:** 🔜 Planned

**Goal:** Humans don't die immediately. Basic survival mechanics.

**Deliverables:**

**Human Components:**
- `Needs`: hunger, thirst, rest
- `Inventory`: personal resources
- `Health`: simple health status
- `Age`: birth date, lifespan tracking

**Systems:**
- `NeedsSystem`: Updates needs (minute/hour ticks)
- `ConsumptionSystem`: Humans consume resources based on needs (day ticks)
- `DeathSystem`: Handles death from starvation, thirst, age

**Constraints:**
- No families
- No jobs
- No money
- Just survival

**Success Criteria:**
- Humans can survive with adequate resources
- Humans die when resources depleted
- Population can grow/shrink based on resource availability

---

## Phase 3: Time, Aging, Reproduction

**Status:** 🔜 Planned

**Goal:** Population dynamics emerge naturally.

**Deliverables:**

**Components:**
- `Fertility`: reproduction capability
- `Lifespan`: age-based mortality curves
- `Dependency`: infant/child dependency periods

**Systems:**
- `AgingSystem`: Age progression (year ticks)
- `BirthSystem`: Reproduction based on fertility (year ticks)
- `MortalitySystem`: Age-based death probabilities

**Features:**
- Lifespan curves (infant mortality, old age)
- Fertility stats (age-based)
- Infant dependency (requires care)
- Population growth/decline

**Why This Matters:**
- This is where epidemiologists start caring
- Enables demographic modeling
- Foundation for inter-generational effects

---

## Phase 4: Economy & Jobs

**Status:** 🔜 Planned

**Goal:** Money exists. Economic activity drives resource distribution.

**Deliverables:**

**Components:**
- `Employment`: job assignment, wages
- `Wealth`: money/resources owned
- `Household`: shared inventory for families

**Systems:**
- `JobSystem`: Job assignment, wage distribution (month ticks)
- `MarketSystem`: Basic resource trading (day/month ticks)
- `HouseholdSystem`: Shared resources within families
- `TransferSystem`: Inter-generational wealth transfer

**Features:**
- Jobs produce resources (farmers → food, etc.)
- Wages enable resource purchase
- Households share resources
- Basic market dynamics

**Constraints:**
- No corruption yet
- No crime yet
- Simple economic model

---

## Phase 5: Geography & Environment

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

## Phase 6: Health, Disease, Pandemics

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

## Phase 7: Crime, Corruption, Policing

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

## Phase 8: Politics & Power

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

## Phase 9: Discord Integration

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

## Phase 10: Expert Mode

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

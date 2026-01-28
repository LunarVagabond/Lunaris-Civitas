# Roadmap

## Current Status

**Phase 2: Base Human (Minimal Survival)** - ✅ Complete

The simulation engine now supports:
- Resource management (production, consumption, replenishment)
- Natural/baseline processes with configurable frequencies
- Modifier system for buffs/debuffs
- Human entities with needs, health, and survival mechanics
- SQLite persistence
- Config-driven initialization

**Current Issue:** Food is running out quickly. Humans are dying from hunger faster than natural production can replenish resources. **Phase 3 (Job System) is critical** to enable humans to produce resources.

## Development Phases

See [Development Phases](PHASES.md) for detailed phase breakdown:

- Phase 0: Simulation Spine ✅
- Phase 1: Resources & World State ✅
- Phase 2: Base Human (Minimal Survival) ✅
- **Phase 3: Job System (Resource Production)** 🔜 **NEXT PRIORITY**
- **Phase 4: Reproduction System** 🔜 **HIGH PRIORITY**
- Phase 5: Actions System 🔜
- Phase 6: Economy & Markets 🔜
- Phase 7: Geography & Environment 🔜
- Phase 8: Health, Disease, Pandemics 🔜
- Phase 9: Crime, Corruption, Policing 🔜
- Phase 10: Politics & Power 🔜
- Phase 11: Discord Integration 🔜
- Phase 12: Expert Mode 🔜

## Future Tickets

See [Future Tickets](FUTURE_TICKETS.md) for detailed feature tracking and planned improvements.

## Design Principles

1. **No system talks directly to another system** - All interaction via world state
2. **Everything is config + stats** - Data-driven behavior
3. **Humans never "decide"** - Systems decide probabilistically
4. **Every feature must be disable-able** - Modular and optional
5. **If it can't be graphed, it's not real** - Analytics-first design
6. **Complexity is allowed only when isolated** - Systems are independent

## Contributing

When adding features:
- Follow the phase plan
- Maintain determinism
- Keep systems independent
- Make everything configurable
- Update documentation
- Add tests

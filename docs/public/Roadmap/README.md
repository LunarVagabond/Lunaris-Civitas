# Roadmap

## Current Status

**Phase 1: Resources & World State** - ✅ Complete

The simulation engine now supports:
- Resource management (production, consumption, replenishment)
- Natural/baseline processes with configurable frequencies
- Modifier system for buffs/debuffs
- SQLite persistence
- Config-driven initialization

## Development Phases

See [Development Phases](PHASES.md) for detailed phase breakdown:
- Phase 0: Simulation Spine ✅
- Phase 1: Resources & World State ✅
- Phase 2: Base Human (Minimal Survival) 🔜
- Phase 3: Time, Aging, Reproduction 🔜
- Phase 4: Economy & Jobs 🔜
- Phase 5: Geography & Environment 🔜
- Phase 6: Health, Disease, Pandemics 🔜
- Phase 7: Crime, Corruption, Policing 🔜
- Phase 8: Politics & Power 🔜
- Phase 9: Discord Integration 🔜
- Phase 10: Expert Mode 🔜

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

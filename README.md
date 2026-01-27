# 🌙 Lunaris Civitas

> A deterministic, modular zero-player simulation engine that models human societies, resources, and emergent behaviors. Built for both **interactive exploration** and **serious research**.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 What is This?

Lunaris Civitas is a **background simulation kernel** that models human societies, resource management, and complex emergent behaviors. Think of it as a "digital petri dish" where you can:

- 🧪 **Run research simulations** - Deterministic, reproducible experiments for academics and researchers
- 🎮 **Watch societies evolve** - Observe how populations, resources, and systems interact over time
- 🤖 **Future Discord integration** - Eventually, humans will be able to interact with the simulation in real-time through Discord! *(Coming in Phase 11)*

This is **not a game UI** - it's a simulation engine that runs in the background, producing data, analytics, and (eventually) real-time updates.

## ✨ Key Features

- 🔄 **Deterministic**: Fully replayable with seeded RNG - same seed = same results
- 🧩 **Modular**: Systems interact only through world state - no direct dependencies
- 🔌 **Extensible**: Add new systems without changing the engine core
- 💾 **Persistent**: SQLite-based state management with save/resume capability
- ⚙️ **Data-driven**: All behavior driven by configuration files
- 📊 **Analytics-first**: Built-in history tracking and CSV export for analysis

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/LunarVagabond/lunaris-civitas.git
cd lunaris-civitas

# Setup (creates virtual environment and installs dependencies)
make setup

# Run simulation
make run

# Or resume from last saved state
make resume
```

## 📖 What's Currently Implemented?

### ✅ Phase 0-2: Foundation & Basic Humans (Complete)

- **Resource Management**: Production, consumption, and replenishment systems
- **Human Entities**: Needs (hunger, thirst, rest), health, aging, and survival mechanics
- **Analytics**: Resource and entity history tracking with CSV export
- **Persistence**: SQLite database with save/resume capability
- **Modifier System**: Buffs/debuffs that affect resource production/consumption

### 🔜 Coming Next (Phase 3-4)

- **🌾 Job System** (Phase 3) - Humans can produce resources through jobs (farmers → food, etc.)
- **👶 Reproduction System** (Phase 4) - Proper population dynamics based on fertility and relationships

*See the [Roadmap](docs/public/Roadmap/PHASES.md) for the full development plan!*

## 🎮 Future: Discord Integration

One of our long-term goals is to integrate with **Discord** so humans can:

- 👀 **Watch the simulation** in real-time
- 📊 **Query statistics** about the world state
- 🎲 **Influence events** probabilistically (never full control - keeps it scientific!)
- 👤 **Be born** into the simulation (probabilistic)
- 📈 **Track specific humans** and their life stories

This will make the simulation **observable and interactive** while maintaining scientific integrity. The simulation will continue running in the background, and Discord will provide a window into what's happening.

*This is planned for Phase 11 - see the [Roadmap](docs/public/Roadmap/PHASES.md) for details.*

## 🔬 Research Use Cases

Lunaris Civitas is designed to be useful for:

- **Epidemiologists**: Model disease spread, pandemics, and public health interventions
- **Economists**: Study resource distribution, markets, and economic systems
- **Political Scientists**: Explore policy effects, governance, and social dynamics
- **Sociologists**: Understand population dynamics, relationships, and social structures
- **Urban Planners**: Model city growth, resource allocation, and infrastructure needs

The deterministic nature and data export capabilities make it perfect for:
- Batch runs with different parameters
- Statistical analysis and comparison
- Reproducible experiments
- Academic research

## 📚 Documentation

Full documentation is available in the `docs/` directory and can be built with MkDocs:

```bash
# Build documentation
make docs

# Serve documentation locally
make docs-serve
```

**Quick Links:**
- 📘 [Getting Started](docs/public/Overview/getting-started.md)
- 🏗️ [Architecture](docs/public/Architecture/README.md)
- ⚙️ [Systems](docs/public/Systems/README.md)
- ⚙️ [Configuration](docs/public/Configuration/README.md)
- 🗺️ [Roadmap](docs/public/Roadmap/PHASES.md) - See what's coming next!
- 🛠️ [Development Guide](docs/public/Development/README.md)
- 📊 [Operations](docs/public/Operations/README.md)

## 🏗️ Project Structure

```
lunaris-civitas/
├── src/                    # Source code
│   ├── core/              # Core engine (time, world state, systems)
│   ├── models/            # Data models (Resource, Modifier, Entity, Component)
│   ├── persistence/       # SQLite database layer
│   ├── config/            # Configuration loading
│   ├── engine/            # Simulation engine and tick loop
│   └── systems/           # Simulation systems
│       ├── resource/      # Resource management
│       ├── human/         # Human entity systems
│       └── analytics/     # History and analytics
├── configs/               # Configuration files
├── docs/                  # Documentation (MkDocs)
├── tests/                 # Unit and integration tests
├── _running/              # Runtime files (database, logs, exports)
├── Makefile              # Build and run commands
└── requirements.txt      # Python dependencies
```

## 🧪 Running the Simulation

### Basic Commands

```bash
# Run with default config
make run

# Resume from last saved state (recommended for long runs)
make resume

# Run with custom config
python -m src --config path/to/config.yml

# Limit number of ticks
python -m src --max-ticks 100

# Export resource history to CSV
make export-resources

# Export entity history to CSV
make export-entities
```

### Command Line Options

- `--config PATH`: Path to configuration file (YAML or JSON)
- `--db PATH`: Path to SQLite database (default: `_running/simulation.db`)
- `--resume`: Resume simulation from database
- `--max-ticks N`: Maximum number of ticks to run
- `--log-level LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## 🧩 Adding a New System

Systems are the building blocks of the simulation. Each system operates independently and interacts only through the world state. Here's how to add one:

```python
# src/systems/my_category/my_system.py
from src.core.system import System
from datetime import datetime

class MySystem(System):
    @property
    def system_id(self) -> str:
        return "MySystem"
    
    def init(self, world_state, config):
        # Initialize with configuration
        self.my_setting = config.get('my_setting', 'default')
    
    def on_tick(self, world_state, current_datetime):
        # Process each tick (systems decide internally when to act)
        if current_datetime.hour == 0:  # Act daily at midnight
            resource = world_state.get_resource('food')
            if resource:
                resource.add(10.0)
```

Then register it in your config:

```yaml
systems:
  - MySystem

systems_config:
  MySystem:
    my_setting: "value"
```

See [Adding Systems](docs/public/Systems/ADDING_SYSTEMS.md) for detailed instructions!

## 🎯 Design Principles

1. **No system talks directly to another system** - All interaction via world state
2. **Everything is config + stats** - Data-driven behavior
3. **Humans never "decide"** - Systems decide probabilistically
4. **Every feature must be disable-able** - Modular and optional
5. **If it can't be graphed, it's not real** - Analytics-first design
6. **Complexity is allowed only when isolated** - Systems are independent

## ⏰ Time Model

- **1 tick = 1 hour** of simulation time
- Systems receive hourly ticks and decide internally when to act
- Calendar-aware: Correct month lengths, leap years, etc.
- Systems can act hourly, daily, monthly, or yearly based on their needs

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/path/to/test_file.py
```

## 🤝 Contributing

Contributions are welcome! This is a public repository and we're happy to have contributors.

When contributing:
- Follow the phase plan (see [Roadmap](docs/public/Roadmap/PHASES.md))
- Maintain determinism (same seed = same results)
- Keep systems independent
- Make everything configurable
- Update documentation
- Add tests

## 📄 License

[Add your license here]

## 🌟 Roadmap

We're actively developing! Current priorities:

1. **🌾 Job System** (Phase 3) - Enable humans to produce resources
2. **👶 Reproduction System** (Phase 4) - Proper population dynamics
3. **🎮 Actions System** (Phase 5) - Time-based entity actions
4. **💰 Economy & Markets** (Phase 6) - Full economic system
5. **🌍 Geography** (Phase 7) - Spatial resource distribution
6. **🦠 Disease & Pandemics** (Phase 8) - Public health modeling
7. **⚖️ Crime & Policing** (Phase 9) - Social systems
8. **🏛️ Politics & Power** (Phase 10) - Governance and policy
9. **💬 Discord Integration** (Phase 11) - Real-time observability and interaction
10. **🔬 Expert Mode** (Phase 12) - Research tools and batch runs

See the [full roadmap](docs/public/Roadmap/PHASES.md) for detailed information!

---

**Built with ❤️ for simulation enthusiasts, researchers, and curious minds.**

*Want to watch a society evolve? Want to run experiments? Want to eventually interact with it through Discord? You're in the right place!* 🚀

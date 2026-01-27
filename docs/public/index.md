# Lunaris Civitas

A deterministic, modular zero-player simulation engine written in Python.

## Overview

Lunaris Civitas is a background simulation kernel designed for:
- Analytics
- Research
- Long-running scenario modeling
- Future human and societal simulations

This is **not** a game UI - it's a deterministic simulation engine focused on analytical reporting and research.

## Key Features

- **Deterministic**: Fully replayable with seeded RNG
- **Modular**: Systems interact only through world state
- **Extensible**: Add new systems without changing the engine
- **Persistent**: SQLite-based state management with resume capability
- **Data-driven**: All behavior driven by configuration

## Quick Start

```bash
# Setup
make setup

# Run simulation
make run
```

## Documentation

- [Getting Started](Overview/getting-started.md)
- [Architecture](Architecture/README.md)
- [Systems](Systems/README.md)
- [Configuration](Configuration/README.md)
- [Roadmap](Roadmap/PHASES.md) - Development phases and future plans
- [Development](Development/README.md)
- [Operations](Operations/README.md)

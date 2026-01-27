"""CLI entry point for running the simulation."""

import argparse
import sys
from pathlib import Path

from src.engine.simulation import Simulation
from src.systems.resource.production import ResourceProductionSystem
from src.systems.resource.consumption import ResourceConsumptionSystem
from src.systems.resource.replenishment import ResourceReplenishmentSystem
from src.systems.analytics.history import ResourceHistorySystem
from src.systems.analytics.entity_history import EntityHistorySystem
from src.systems.human.spawn import HumanSpawnSystem
from src.systems.human.needs import NeedsSystem
from src.systems.human.requirement_resolver import RequirementResolverSystem
from src.systems.human.needs_fulfillment import HumanNeedsFulfillmentSystem
from src.systems.human.health import HealthSystem
from src.systems.human.death import DeathSystem
from src.core.logging import setup_logging


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Lunaris Civitas - Zero-player simulation engine"
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--db',
        type=Path,
        help='Path to SQLite database (default: _running/simulation.db)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume simulation from database'
    )
    parser.add_argument(
        '--max-ticks',
        type=int,
        help='Maximum number of ticks to run'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging (console only - Makefile redirects to file)
    setup_logging(log_level=args.log_level, log_file=None, detailed=True)
    
    # Create simulation
    sim = Simulation(
        config_path=args.config,
        db_path=args.db,
        resume=args.resume
    )
    
    # Register systems
    sim.register_system(ResourceProductionSystem())
    sim.register_system(ResourceConsumptionSystem())
    sim.register_system(ResourceReplenishmentSystem())
    sim.register_system(ResourceHistorySystem())
    sim.register_system(EntityHistorySystem())
    sim.register_system(HumanSpawnSystem())
    sim.register_system(NeedsSystem())
    sim.register_system(RequirementResolverSystem())
    sim.register_system(HumanNeedsFulfillmentSystem())
    sim.register_system(HealthSystem())
    sim.register_system(DeathSystem())
    
    # Run simulation
    try:
        sim.run(max_ticks=args.max_ticks)
    except KeyboardInterrupt:
        print("\nSimulation interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        sim.shutdown()


if __name__ == '__main__':
    main()

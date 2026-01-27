"""Integration tests for simulation with history tracking."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.engine.simulation import Simulation
from src.systems.resource.production import ResourceProductionSystem
from src.systems.resource.consumption import ResourceConsumptionSystem
from src.systems.resource.replenishment import ResourceReplenishmentSystem
from src.systems.analytics.history import ResourceHistorySystem
from src.persistence.database import Database


def test_simulation_saves_history():
    """Test history is saved during simulation run."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        sim = Simulation(db_path=db_path)
        sim.register_system(ResourceProductionSystem())
        sim.register_system(ResourceConsumptionSystem())
        sim.register_system(ResourceReplenishmentSystem())
        sim.register_system(ResourceHistorySystem())
        
        config = {
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42,
                'db_path': str(db_path)
            },
            'resources': [
                {
                    'id': 'food',
                    'name': 'Food',
                    'initial_amount': 1000.0,
                    'max_capacity': 5000.0
                }
            ],
            'systems': [
                'ResourceProductionSystem',
                'ResourceConsumptionSystem',
                'ResourceReplenishmentSystem',
                'ResourceHistorySystem'
            ],
            'systems_config': {
                'ResourceHistorySystem': {
                    'enabled': True,
                    'frequency': 'hourly',
                    'rate': 1
                }
            }
        }
        
        sim._initialize_new_simulation(config)
        
        # Run for a few ticks
        sim.run(max_ticks=3)
        
        # Verify history was saved
        with Database(db_path) as db:
            history = db.get_all_resource_history()
            assert len(history) > 0
            assert all(h['resource_id'] == 'food' for h in history)


def test_simulation_history_frequency():
    """Test history is saved at correct frequency."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        sim = Simulation(db_path=db_path)
        sim.register_system(ResourceProductionSystem())
        sim.register_system(ResourceHistorySystem())
        
        config = {
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42,
                'db_path': str(db_path)
            },
            'resources': [
                {
                    'id': 'food',
                    'name': 'Food',
                    'initial_amount': 1000.0
                }
            ],
            'systems': [
                'ResourceProductionSystem',
                'ResourceHistorySystem'
            ],
            'systems_config': {
                'ResourceHistorySystem': {
                    'enabled': True,
                    'frequency': 'daily',  # Daily at midnight
                    'rate': 1
                }
            }
        }
        
        sim._initialize_new_simulation(config)
        
        # Run for 25 ticks (1 day + 1 hour)
        sim.run(max_ticks=25)
        
        # Verify history was saved only at daily boundaries (midnight)
        with Database(db_path) as db:
            history = db.get_all_resource_history()
            # Should have saved at initialization (tick 0) and at tick 24 (1 day = 24 hours later)
            # Note: History system saves when _should_save_history returns True
            # For daily frequency, it saves at midnight (hour == 0)
            # Initialization happens at tick 0 (2024-01-01T00:00:00) - saves
            # Tick 24 advances to 2024-01-02T00:00:00 - should save
            assert len(history) >= 1  # At least one save (at initialization)
            
            # Check that all saved timestamps are at midnight
            for h in history:
                timestamp = datetime.fromisoformat(h['timestamp'])
                assert timestamp.hour == 0, f"Expected midnight, got {timestamp}"


def test_resume_simulation_preserves_history():
    """Test history persists across resume."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        # First simulation run
        sim1 = Simulation(db_path=db_path)
        sim1.register_system(ResourceProductionSystem())
        sim1.register_system(ResourceHistorySystem())
        
        config = {
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42,
                'db_path': str(db_path)
            },
            'resources': [
                {
                    'id': 'food',
                    'name': 'Food',
                    'initial_amount': 1000.0
                }
            ],
            'systems': [
                'ResourceProductionSystem',
                'ResourceHistorySystem'
            ],
            'systems_config': {
                'ResourceHistorySystem': {
                    'enabled': True,
                    'frequency': 'hourly',
                    'rate': 1
                }
            }
        }
        
        sim1._initialize_new_simulation(config)
        sim1.run(max_ticks=5)
        sim1.shutdown()
        
        # Get history count from first run
        with Database(db_path) as db:
            history_before = db.get_all_resource_history()
            count_before = len(history_before)
        
        # Resume simulation
        sim2 = Simulation(db_path=db_path, resume=True)
        sim2.register_system(ResourceProductionSystem())
        sim2.register_system(ResourceHistorySystem())
        sim2._resume_simulation()
        sim2.run(max_ticks=3)
        sim2.shutdown()
        
        # Verify history from first run is still there and new history was added
        with Database(db_path) as db:
            history_after = db.get_all_resource_history()
            count_after = len(history_after)
            
            assert count_after > count_before
            assert count_after >= count_before + 3  # At least 3 new records


def test_history_does_not_break_existing_tests():
    """Test that adding history system doesn't break existing functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        sim = Simulation(db_path=db_path)
        sim.register_system(ResourceProductionSystem())
        sim.register_system(ResourceConsumptionSystem())
        sim.register_system(ResourceReplenishmentSystem())
        sim.register_system(ResourceHistorySystem())
        
        config = {
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42,
                'db_path': str(db_path)
            },
            'resources': [
                {
                    'id': 'food',
                    'name': 'Food',
                    'initial_amount': 1000.0,
                    'max_capacity': 5000.0,
                    'replenishment_rate': 50.0
                }
            ],
            'systems': [
                'ResourceProductionSystem',
                'ResourceConsumptionSystem',
                'ResourceReplenishmentSystem',
                'ResourceHistorySystem'
            ],
            'systems_config': {
                'ResourceProductionSystem': {
                    'production': {'food': 100.0}
                },
                'ResourceConsumptionSystem': {
                    'consumption': {'food': 80.0}
                },
                'ResourceHistorySystem': {
                    'enabled': True,
                    'frequency': 'hourly',
                    'rate': 1
                }
            }
        }
        
        sim._initialize_new_simulation(config)
        
        # Run simulation
        sim.run(max_ticks=10)
        sim.shutdown()
        
        # Verify resources still work correctly
        with Database(db_path) as db:
            world_state = db.load_world_state()
            resource = world_state.get_resource('food')
            assert resource is not None
            assert resource.current_amount > 0  # Should have increased due to production

"""Integration tests for simulation with entity history."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from src.engine.simulation import Simulation
from src.systems.analytics.entity_history import EntityHistorySystem
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.health import HealthComponent
from src.models.components.pressure import PressureComponent


class TestSimulationWithEntityHistory:
    """Integration tests for simulation with entity history."""
    
    def test_entity_history_saves_during_simulation(self):
        """Test that entity history is saved during simulation run."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': ['EntityHistorySystem'],
                'resources': [
                    {
                        'id': 'food',
                        'name': 'Food',
                        'initial_amount': 1000.0,
                        'max_capacity': None,
                        'replenishment_rate': None,
                        'finite': False
                    }
                ],
                'systems_config': {
                    'EntityHistorySystem': {
                        'enabled': True,
                        'frequency': 'hourly',
                        'rate': 1,
                        'db_path': str(db_path)
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(EntityHistorySystem())
            sim._initialize_new_simulation(config)
            
            # Create entities
            entity1 = sim.world_state.create_entity()
            entity1.add_component(NeedsComponent(hunger=0.5))
            entity1.add_component(HealthComponent(health=0.8))
            
            entity2 = sim.world_state.create_entity()
            entity2.add_component(NeedsComponent(hunger=0.7))
            entity2.add_component(HealthComponent(health=0.6))
            
            # Run simulation for a few ticks
            sim.run(max_ticks=3)
            
            # Verify history was saved
            from src.persistence.database import Database
            with Database(db_path) as db:
                history = db.get_entity_history()
                assert len(history) > 0
                assert history[0]['total_entities'] == 2
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_entity_history_frequency_adherence_in_simulation(self):
        """Test that entity history respects frequency settings in simulation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': ['EntityHistorySystem'],
                'resources': [
                    {
                        'id': 'food',
                        'name': 'Food',
                        'initial_amount': 1000.0,
                        'max_capacity': None,
                        'replenishment_rate': None,
                        'finite': False
                    }
                ],
                'systems_config': {
                    'EntityHistorySystem': {
                        'enabled': True,
                        'frequency': 'hourly',
                        'rate': 1,
                        'db_path': str(db_path)
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(EntityHistorySystem())
            sim._initialize_new_simulation(config)
            
            # Create entity
            entity = sim.world_state.create_entity()
            entity.add_component(NeedsComponent())
            
            # Run simulation - with hourly frequency, should save every hour
            # Start at midnight, run for 2 hours
            sim.run(max_ticks=2)
            
            # Verify history was saved (should have records for each hour)
            from src.persistence.database import Database
            with Database(db_path) as db:
                history = db.get_entity_history()
                # Should have records (at least 1, possibly 2 with hourly frequency)
                assert len(history) >= 1
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_entity_history_persists_across_resume(self):
        """Test that entity history persists across simulation resume."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': ['EntityHistorySystem'],
                'resources': [
                    {
                        'id': 'food',
                        'name': 'Food',
                        'initial_amount': 1000.0,
                        'max_capacity': None,
                        'replenishment_rate': None,
                        'finite': False
                    }
                ],
                'systems_config': {
                    'EntityHistorySystem': {
                        'enabled': True,
                        'frequency': 'hourly',
                        'rate': 1,
                        'db_path': str(db_path)
                    }
                }
            }
            
            # Create and run first simulation
            sim1 = Simulation(config_path=None, db_path=db_path, resume=False)
            sim1.register_system(EntityHistorySystem())
            sim1._initialize_new_simulation(config)
            
            entity = sim1.world_state.create_entity()
            entity.add_component(NeedsComponent(hunger=0.5))
            
            sim1.run(max_ticks=2)
            sim1.shutdown()
            
            # Resume simulation
            sim2 = Simulation(config_path=None, db_path=db_path, resume=True)
            sim2.register_system(EntityHistorySystem())
            sim2._resume_simulation()
            
            # Add another entity and run more
            entity2 = sim2.world_state.create_entity()
            entity2.add_component(NeedsComponent(hunger=0.7))
            
            sim2.run(max_ticks=2)
            sim2.shutdown()
            
            # Verify all history is present
            from src.persistence.database import Database
            with Database(db_path) as db:
                history = db.get_entity_history()
                # Should have records from both runs
                assert len(history) >= 2
                # First record should have 1 entity, later records may have 2
                assert history[0]['total_entities'] == 1
            
        finally:
            if db_path.exists():
                db_path.unlink()

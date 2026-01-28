"""Tests for entity history system."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

from src.systems.analytics.entity_history import EntityHistorySystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.pressure import PressureComponent
from src.models.components.health import HealthComponent
from src.models.components.age import AgeComponent
from src.models.components.wealth import WealthComponent
from src.models.components.employment import EmploymentComponent


def test_entity_history_system_init():
    """Test system initializes correctly."""
    system = EntityHistorySystem()
    
    assert system.system_id == "EntityHistorySystem"
    assert system.enabled == True
    assert system.frequency == 'daily'
    assert system.rate == 1
    assert system.component_types == []
    assert system.last_save is None


def test_entity_history_system_init_with_config():
    """Test system initializes with configuration."""
    system = EntityHistorySystem()
    world_state = Mock()
    world_state.config_snapshot = {'simulation': {'db_path': '_running/test.db'}}
    
    config = {
        'enabled': True,
        'frequency': 'weekly',
        'rate': 2,
        'component_types': ['Needs', 'Health']
    }
    
    system.init(world_state, config)
    
    assert system.enabled == True
    assert system.frequency == 'weekly'
    assert system.rate == 2
    assert system.component_types == ['Needs', 'Health']


def test_entity_history_system_init_disabled():
    """Test system can be disabled."""
    system = EntityHistorySystem()
    world_state = Mock()
    world_state.config_snapshot = {}
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    assert system.enabled == False


def test_entity_history_system_calculates_metrics():
    """Test system calculates metrics correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = EntityHistorySystem()
        
        # Create world state with entities
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        # Create entities with various components
        entity1 = world_state.create_entity(entity_id="entity-1")
        entity1.add_component(NeedsComponent(hunger=0.5, thirst=0.3, rest=0.2))
        entity1.add_component(HealthComponent(health=0.8))
        entity1.add_component(PressureComponent())
        
        entity2 = world_state.create_entity(entity_id="entity-2")
        entity2.add_component(NeedsComponent(hunger=0.7, thirst=0.5, rest=0.4))
        entity2.add_component(HealthComponent(health=0.6))
        entity2.add_component(AgeComponent(birth_date=datetime(2020, 1, 1), current_date=datetime(2024, 1, 1)))
        entity2.add_component(WealthComponent(resources={'money': 100.0}))
        entity2.add_component(EmploymentComponent(job_type="farmer"))
        
        entity3 = world_state.create_entity(entity_id="entity-3")
        entity3.add_component(NeedsComponent(hunger=0.9, thirst=0.8, rest=0.7))
        pressure = PressureComponent()
        pressure.add_pressure('food', 10.0)
        entity3.add_component(pressure)
        entity3.add_component(HealthComponent(health=0.3))  # At risk
        
        config = {'enabled': True, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Save history
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify history was saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_entity_history()
            assert len(history) == 1
            
            record = history[0]
            assert record['total_entities'] == 3
            assert record['avg_hunger'] == pytest.approx(0.7, abs=0.01)  # (0.5 + 0.7 + 0.9) / 3
            assert record['avg_thirst'] == pytest.approx(0.533, abs=0.01)  # (0.3 + 0.5 + 0.8) / 3
            assert record['avg_health'] == pytest.approx(0.567, abs=0.01)  # (0.8 + 0.6 + 0.3) / 3
            assert record['entities_at_risk'] == 1  # entity3 has health < 0.5
            assert record['entities_with_pressure'] == 1  # entity3 has pressure
            assert record['employed_count'] == 1  # entity2 is employed
            
            # Check component counts
            component_counts = json.loads(record['component_counts'])
            assert component_counts['Needs'] == 3
            assert component_counts['Health'] == 3
            assert component_counts['Pressure'] == 2
            assert component_counts['Age'] == 1
            assert component_counts['Wealth'] == 1
            assert component_counts['Employment'] == 1


def test_entity_history_system_frequency_adherence():
    """Test system respects frequency and rate settings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = EntityHistorySystem()
        
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        entity = world_state.create_entity()
        entity.add_component(NeedsComponent())
        
        config = {'enabled': True, 'frequency': 'daily', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # First save at midnight (should save)
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Advance time but not to next day (should not save)
        world_state.simulation_time.advance_tick()  # Advance 1 hour
        system.on_tick(world_state, datetime(2024, 1, 1, 1, 0, 0))
        
        # Advance to next day midnight (should save)
        world_state.simulation_time.advance_tick()  # Advance to tick 2
        system.on_tick(world_state, datetime(2024, 1, 2, 0, 0, 0))
        
        # Verify only 2 records saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_entity_history()
            assert len(history) == 2


def test_entity_history_system_no_entities():
    """Test system handles empty entity list gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = EntityHistorySystem()
        
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        config = {'enabled': True, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Should not crash with no entities
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # No history should be saved (no entities)
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_entity_history()
            assert len(history) == 0


def test_entity_history_system_disabled():
    """Test system doesn't save when disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = EntityHistorySystem()
        
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        entity = world_state.create_entity()
        entity.add_component(NeedsComponent())
        
        config = {'enabled': False, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # No history should be saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_entity_history()
            assert len(history) == 0

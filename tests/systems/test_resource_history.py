"""Tests for resource history system."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.systems.analytics.history import ResourceHistorySystem, _should_save_history
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource


def test_history_system_init():
    """Test system initializes correctly."""
    system = ResourceHistorySystem()
    
    assert system.system_id == "ResourceHistorySystem"
    assert system.enabled == True
    assert system.frequency == 'daily'
    assert system.rate == 1
    assert system.resources == []
    assert system.last_save is None


def test_history_system_init_with_config():
    """Test system initializes with configuration."""
    system = ResourceHistorySystem()
    world_state = Mock()
    world_state.config_snapshot = {}  # Empty config snapshot
    
    config = {
        'enabled': True,
        'frequency': 'weekly',
        'rate': 2,
        'resources': ['food', 'water']
    }
    
    system.init(world_state, config)
    
    assert system.enabled == True
    assert system.frequency == 'weekly'
    assert system.rate == 2
    assert system.resources == ['food', 'water']


def test_history_system_init_disabled():
    """Test system can be disabled."""
    system = ResourceHistorySystem()
    world_state = Mock()
    world_state.config_snapshot = {}  # Empty config snapshot
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    assert system.enabled == False


def test_history_system_saves_on_frequency():
    """Test system saves at correct frequency boundaries."""
    system = ResourceHistorySystem()
    
    # Test daily frequency at midnight
    current_datetime = datetime(2024, 1, 1, 0, 0, 0)  # Midnight
    assert _should_save_history('daily', 1, None, current_datetime) == True
    
    # Test daily frequency not at midnight
    current_datetime = datetime(2024, 1, 1, 12, 0, 0)  # Noon
    assert _should_save_history('daily', 1, None, current_datetime) == False
    
    # Test weekly frequency on Monday
    current_datetime = datetime(2024, 1, 1, 0, 0, 0)  # Monday midnight
    assert current_datetime.weekday() == 0
    assert _should_save_history('weekly', 1, None, current_datetime) == True
    
    # Test monthly frequency on 1st
    current_datetime = datetime(2024, 1, 1, 0, 0, 0)  # 1st of month
    assert _should_save_history('monthly', 1, None, current_datetime) == True
    
    # Test yearly frequency on Jan 1
    current_datetime = datetime(2024, 1, 1, 0, 0, 0)  # Jan 1
    assert _should_save_history('yearly', 1, None, current_datetime) == True


def test_history_system_respects_rate():
    """Test system respects rate parameter (every N periods)."""
    # Test rate=2 means every 2 days
    last_save = datetime(2024, 1, 1, 0, 0, 0)
    current_datetime = datetime(2024, 1, 2, 0, 0, 0)  # 1 day later
    assert _should_save_history('daily', 2, last_save, current_datetime) == False
    
    current_datetime = datetime(2024, 1, 3, 0, 0, 0)  # 2 days later
    assert _should_save_history('daily', 2, last_save, current_datetime) == True


def test_history_system_saves_all_resources():
    """Test system saves all resources when no filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = ResourceHistorySystem()
        
        # Create world state with resources
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        world_state.add_resource(Resource('food', 'Food', 1000.0, max_capacity=5000.0))
        world_state.add_resource(Resource('water', 'Water', 2000.0, max_capacity=5000.0))
        
        config = {'enabled': True, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Save history
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify both resources were saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_all_resource_history()
            assert len(history) == 2
            resource_ids = {h['resource_id'] for h in history}
            assert 'food' in resource_ids
            assert 'water' in resource_ids


def test_history_system_filters_resources():
    """Test system saves only specified resources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = ResourceHistorySystem()
        
        # Create world state with resources
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        world_state.add_resource(Resource('food', 'Food', 1000.0))
        world_state.add_resource(Resource('water', 'Water', 2000.0))
        
        config = {
            'enabled': True,
            'frequency': 'hourly',
            'rate': 1,
            'resources': ['food'],
            'db_path': str(db_path)
        }
        system.init(world_state, config)
        
        # Save history
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify only food was saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_all_resource_history()
            assert len(history) == 1
            assert history[0]['resource_id'] == 'food'


def test_history_system_calculates_utilization():
    """Test system calculates utilization correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = ResourceHistorySystem()
        
        # Create world state with resource
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        # Resource with 2000/5000 = 40% utilization
        world_state.add_resource(Resource('food', 'Food', 2000.0, max_capacity=5000.0))
        
        config = {'enabled': True, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Save history
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify utilization was calculated
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_resource_history('food')
            assert len(history) == 1
            assert history[0]['utilization_percent'] == pytest.approx(40.0, rel=0.01)
        
        # Resource without max_capacity should have None utilization
        world_state.add_resource(Resource('unlimited', 'Unlimited', 1000.0))
        system.on_tick(world_state, datetime(2024, 1, 1, 1, 0, 0))
        
        with Database(db_path) as db:
            history = db.get_resource_history('unlimited')
            assert len(history) == 1
            assert history[0]['utilization_percent'] is None


def test_history_system_stores_status():
    """Test system stores correct status_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = ResourceHistorySystem()
        
        # Create world state with resource
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        world_state.add_resource(Resource('food', 'Food', 1000.0, max_capacity=5000.0))
        
        config = {'enabled': True, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Save history
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify status was stored
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_resource_history('food')
            assert len(history) == 1
            assert 'status_id' in history[0]
            assert history[0]['status_id'] in ['depleted', 'at_risk', 'moderate', 'sufficient', 'abundant']


def test_history_system_disabled():
    """Test system doesn't save when disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        system = ResourceHistorySystem()
        
        # Create world state
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        world_state.add_resource(Resource('food', 'Food', 1000.0))
        
        config = {'enabled': False, 'frequency': 'hourly', 'rate': 1, 'db_path': str(db_path)}
        system.init(world_state, config)
        
        # Try to save history (should not save)
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Verify nothing was saved
        from src.persistence.database import Database
        with Database(db_path) as db:
            history = db.get_all_resource_history()
            assert len(history) == 0

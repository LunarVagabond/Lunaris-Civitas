"""Extended tests for simulation engine - logging, save/load, run loop."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.engine.simulation import Simulation
from src.core.time import SimulationTime
from src.core.world_state import WorldState
from src.models.resource import Resource
from src.systems.resource.production import ResourceProductionSystem


def test_simulation_run_with_max_ticks():
    """Test running simulation with max_ticks limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yml"
        db_path = Path(tmpdir) / "test.db"
        
        # Create config file
        config_path.write_text("""
simulation:
  start_datetime: "2024-01-01T00:00:00"
  rng_seed: 42
resources: []
systems: []
""")
        
        sim = Simulation(config_path=config_path, db_path=db_path)
        
        # Register a system
        production_system = ResourceProductionSystem()
        sim.register_system(production_system)
        
        # Run with max_ticks
        sim.run(max_ticks=5)
        
        assert sim.world_state.simulation_time.ticks_elapsed >= 5
        assert not sim.running


def test_simulation_run_already_running():
    """Test that running simulation when already running raises error."""
    sim = Simulation()
    sim.running = True
    
    with pytest.raises(RuntimeError, match="already running"):
        sim.run()


def test_simulation_run_no_config():
    """Test that running without config raises error."""
    sim = Simulation(resume=False)
    
    with pytest.raises(ValueError, match="config_path required"):
        sim.run()


def test_simulation_resume_no_db():
    """Test resuming when no database exists raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "nonexistent.db"
        sim = Simulation(db_path=db_path, resume=True)
        
        with pytest.raises(ValueError, match="No saved simulation"):
            sim._resume_simulation()


def test_simulation_save():
    """Test saving simulation state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sim = Simulation(db_path=db_path)
        
        config = {
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42
            },
            'resources': [
                {
                    'id': 'food',
                    'name': 'Food',
                    'initial_amount': 1000.0,
                    'max_capacity': 5000.0
                }
            ]
        }
        
        sim._initialize_new_simulation(config)
        
        # Modify resource
        resource = sim.world_state.get_resource('food')
        resource.add(500.0)
        
        # Save
        sim.save()
        
        # Verify DB exists
        assert db_path.exists()


def test_simulation_should_log_hourly():
    """Test _should_log for hourly frequency."""
    sim = Simulation()
    
    # Hourly - should log every hour
    assert sim._should_log('hourly', 1, None, datetime(2024, 1, 1, 12, 0, 0))
    assert sim._should_log('hourly', 1, None, datetime(2024, 1, 1, 13, 0, 0))
    
    # With rate=2, log every 2 hours
    last_log = datetime(2024, 1, 1, 10, 0, 0)
    assert not sim._should_log('hourly', 2, last_log, datetime(2024, 1, 1, 11, 0, 0))
    assert sim._should_log('hourly', 2, last_log, datetime(2024, 1, 1, 12, 0, 0))


def test_simulation_should_log_daily():
    """Test _should_log for daily frequency."""
    sim = Simulation()
    
    # Daily - should log at midnight
    assert sim._should_log('daily', 1, None, datetime(2024, 1, 1, 0, 0, 0))
    assert not sim._should_log('daily', 1, None, datetime(2024, 1, 1, 12, 0, 0))
    
    # With rate=2, log every 2 days
    last_log = datetime(2024, 1, 1, 0, 0, 0)
    assert not sim._should_log('daily', 2, last_log, datetime(2024, 1, 2, 0, 0, 0))
    assert sim._should_log('daily', 2, last_log, datetime(2024, 1, 3, 0, 0, 0))


def test_simulation_should_log_weekly():
    """Test _should_log for weekly frequency."""
    sim = Simulation()
    
    # Weekly - should log on Monday at midnight
    monday = datetime(2024, 1, 1, 0, 0, 0)  # Monday
    assert sim._should_log('weekly', 1, None, monday)
    
    tuesday = datetime(2024, 1, 2, 0, 0, 0)
    assert not sim._should_log('weekly', 1, None, tuesday)


def test_simulation_should_log_monthly():
    """Test _should_log for monthly frequency."""
    sim = Simulation()
    
    # Monthly - should log on 1st at midnight
    assert sim._should_log('monthly', 1, None, datetime(2024, 1, 1, 0, 0, 0))
    assert sim._should_log('monthly', 1, None, datetime(2024, 2, 1, 0, 0, 0))
    assert not sim._should_log('monthly', 1, None, datetime(2024, 1, 2, 0, 0, 0))


def test_simulation_should_log_yearly():
    """Test _should_log for yearly frequency."""
    sim = Simulation()
    
    # Yearly - should log on Jan 1 at midnight
    assert sim._should_log('yearly', 1, None, datetime(2024, 1, 1, 0, 0, 0))
    assert sim._should_log('yearly', 1, None, datetime(2025, 1, 1, 0, 0, 0))
    assert not sim._should_log('yearly', 1, None, datetime(2024, 1, 2, 0, 0, 0))


def test_simulation_calculate_period_rate_hourly():
    """Test _calculate_period_rate for hourly."""
    sim = Simulation()
    
    last_dt = datetime(2024, 1, 1, 10, 0, 0)
    current_dt = datetime(2024, 1, 1, 12, 0, 0)
    
    rate, unit = sim._calculate_period_rate(100.0, 'hourly', 1, last_dt, current_dt)
    assert rate == 50.0  # 100 / 2 hours
    assert unit == '/hr'


def test_simulation_calculate_period_rate_daily():
    """Test _calculate_period_rate for daily."""
    sim = Simulation()
    
    last_dt = datetime(2024, 1, 1, 0, 0, 0)
    current_dt = datetime(2024, 1, 3, 0, 0, 0)
    
    rate, unit = sim._calculate_period_rate(100.0, 'daily', 1, last_dt, current_dt)
    assert rate == 50.0  # 100 / 2 days
    assert unit == '/day'


def test_simulation_calculate_period_rate_weekly():
    """Test _calculate_period_rate for weekly."""
    sim = Simulation()
    
    last_dt = datetime(2024, 1, 1, 0, 0, 0)  # Monday
    current_dt = datetime(2024, 1, 15, 0, 0, 0)  # Monday, 2 weeks later
    
    rate, unit = sim._calculate_period_rate(100.0, 'weekly', 1, last_dt, current_dt)
    assert rate == 50.0  # 100 / 2 weeks
    assert unit == '/week'


def test_simulation_get_resource_status():
    """Test _get_resource_status helper."""
    sim = Simulation()
    
    resource = Resource("food", "Food", 100.0, max_capacity=1000.0)
    status_str = sim._get_resource_status(resource)
    
    assert '[' in status_str
    assert ']' in status_str

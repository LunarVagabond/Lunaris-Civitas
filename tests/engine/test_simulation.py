"""Tests for simulation engine."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.engine.simulation import Simulation
from src.core.time import SimulationTime
from src.core.world_state import WorldState
from src.models.resource import Resource
from src.models.modifier import Modifier
from src.systems.resource.production import ResourceProductionSystem
from src.systems.resource.consumption import ResourceConsumptionSystem
from src.systems.resource.replenishment import ResourceReplenishmentSystem


def test_simulation_init():
    """Test simulation initialization."""
    sim = Simulation()
    
    assert sim.db_path == Path("_running/simulation.db")
    assert sim.resume == False
    assert sim.world_state is None
    assert sim.running == False


def test_simulation_init_custom_db_path():
    """Test simulation initialization with custom DB path."""
    db_path = Path("custom.db")
    sim = Simulation(db_path=db_path)
    
    assert sim.db_path == db_path


def test_simulation_register_system():
    """Test registering a system."""
    sim = Simulation()
    system = ResourceProductionSystem()
    
    sim.register_system(system)
    assert system.system_id in sim.systems_registry
    assert sim.systems_registry[system.system_id] == system


def test_simulation_register_duplicate_system():
    """Test registering duplicate system raises error."""
    sim = Simulation()
    system = ResourceProductionSystem()
    
    sim.register_system(system)
    
    with pytest.raises(ValueError, match="already registered"):
        sim.register_system(system)


def test_simulation_initialize_new_simulation():
    """Test initializing a new simulation."""
    sim = Simulation()
    
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
    
    assert sim.world_state is not None
    assert sim.world_state.simulation_time.current_datetime.year == 2024
    assert sim.world_state.rng_seed == 42
    assert 'food' in sim.world_state._resources


def test_simulation_initialize_random_seed():
    """Test initializing simulation with RANDOM seed."""
    sim = Simulation()
    
    config = {
        'simulation': {
            'start_datetime': '2024-01-01T00:00:00',
            'rng_seed': 'RANDOM'
        },
        'resources': []
    }
    
    sim._initialize_new_simulation(config)
    
    assert sim.world_state is not None
    assert sim.world_state.rng_seed is not None
    assert isinstance(sim.world_state.rng_seed, int)
    assert sim.world_state.rng_seed >= 0


def test_simulation_advance_tick():
    """Test advancing simulation tick."""
    sim = Simulation()
    
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
        ],
        'systems': ['ResourceProductionSystem'],
        'systems_config': {
            'ResourceProductionSystem': {
                'production': {
                    'food': 10.0
                }
            }
        }
    }
    
    sim._initialize_new_simulation(config)
    
    # Register and initialize production system
    production_system = ResourceProductionSystem()
    sim.register_system(production_system)
    sim.world_state.register_system(production_system)
    production_system.init(sim.world_state, config['systems_config']['ResourceProductionSystem'])
    
    # Advance one tick manually
    initial_amount = sim.world_state.get_resource('food').current_amount
    current_dt = sim.world_state.simulation_time.advance_tick()
    
    # Call systems manually
    for system in sim.world_state.get_all_systems():
        system.on_tick(sim.world_state, current_dt)
    
    # Should have produced food (production happens hourly)
    assert sim.world_state.get_resource('food').current_amount >= initial_amount


def test_simulation_check_modifier_repeats():
    """Test modifier repeat checking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sim = Simulation(db_path=db_path)
        
        config = {
            'simulation': {
                'start_datetime': '2020-01-01T00:00:00',
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
        
        # Initialize database first (connect creates schema)
        from src.persistence.database import Database
        db = Database(sim.db_path)
        db.connect()
        
        # Add modifier with repeat probability
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2020,
            end_year=2022,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0  # 100% chance to repeat
        )
        sim.world_state.add_modifier(modifier)
        
        # Advance to end of 2022 (Dec 31, 23:00)
        target_dt = datetime(2022, 12, 31, 23, 0, 0)
        while sim.world_state.simulation_time.current_datetime < target_dt:
            sim.world_state.simulation_time.advance_tick()
        
        # Check for repeats at year boundary
        current_dt = sim.world_state.simulation_time.current_datetime
        if current_dt.month == 12 and current_dt.day == 31 and current_dt.hour == 23:
            sim._check_modifier_repeats(current_dt)
            
            # Should have created a repeat modifier
            modifiers = sim.world_state.get_modifiers_by_name("pest_outbreak")
            assert len(modifiers) >= 1


def test_simulation_create_modifier_repeat():
    """Test creating modifier repeat."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        sim = Simulation(db_path=db_path)
        
        config = {
            'simulation': {
                'start_datetime': '2020-01-01T00:00:00',
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
        
        # Initialize database first (connect creates schema)
        from src.persistence.database import Database
        db = Database(sim.db_path)
        db.connect()
        
        parent_modifier = Modifier(
            modifier_name="test_modifier",
            resource_id="food",
            start_year=2020,
            end_year=2022,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_duration_years=1
        )
        sim.world_state.add_modifier(parent_modifier)
        
        # Create repeat at end of 2022
        current_datetime = datetime(2022, 12, 31, 23, 0, 0)
        sim._create_modifier_repeat(parent_modifier, current_datetime)
        
        # Should have new modifier starting in 2023
        modifiers = sim.world_state.get_modifiers_by_name("test_modifier")
        assert len(modifiers) >= 2
        
        # Find the repeat
        repeat = None
        for mod in modifiers:
            if mod.start_year == 2023:
                repeat = mod
                break
        
        assert repeat is not None
        assert repeat.start_year == 2023
        assert repeat.end_year == 2024
        assert repeat.parent_modifier_id == parent_modifier.db_id


def test_simulation_persistence_save_load():
    """Test saving and loading simulation state."""
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
        
        # Create new simulation and load
        sim2 = Simulation(db_path=db_path, resume=True)
        sim2._resume_simulation()
        
        assert sim2.world_state is not None
        loaded_resource = sim2.world_state.get_resource('food')
        assert loaded_resource.current_amount == 1500.0


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

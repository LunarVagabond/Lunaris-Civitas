"""Tests for human spawn system."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.systems.human.spawn import HumanSpawnSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.components.needs import NeedsComponent
from src.models.components.health import HealthComponent
from src.models.components.age import AgeComponent


def test_spawn_system_init():
    """Test system initializes correctly."""
    system = HumanSpawnSystem()
    
    assert system.system_id == "HumanSpawnSystem"
    assert system.enabled == True
    assert system.initial_population == 100
    assert system.spawn_rate == 0


def test_spawn_system_creates_initial_population():
    """Test system creates initial population."""
    system = HumanSpawnSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': True,
        'initial_population': 10,
        'seed_crew': {
            'age_range': [20, 30],
            'components': {
                'Needs': 100,
                'Health': 100,
                'Age': 100
            }
        }
    }
    
    system.init(world_state, config)
    
    # Check entities were created
    entities = world_state.get_all_entities()
    assert len(entities) == 10
    
    # Check all entities have core components
    for entity in entities.values():
        assert entity.has_component('Needs')
        assert entity.has_component('Health')
        assert entity.has_component('Age')
        
        # Check age is in range
        age = entity.get_component('Age')
        age_years = age.get_age_years(datetime(2024, 1, 1, 0, 0, 0))
        assert 20 <= age_years <= 30


def test_spawn_system_runtime_spawning():
    """Test runtime spawning creates entities with age 0."""
    system = HumanSpawnSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': True,
        'initial_population': 0,
        'spawn_frequency': 'hourly',
        'spawn_rate': 2,
        'runtime_spawn': {
            'components': {
                'Needs': 100,
                'Health': 100,
                'Age': 100
            }
        }
    }
    
    system.init(world_state, config)
    
    # Trigger runtime spawn
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Check entities were created
    entities = world_state.get_all_entities()
    assert len(entities) == 2
    
    # Check all runtime spawns have age 0
    for entity in entities.values():
        age = entity.get_component('Age')
        age_years = age.get_age_years(datetime(2024, 1, 1, 0, 0, 0))
        assert age_years == 0.0


def test_spawn_system_component_probabilities():
    """Test component assignment respects probabilities."""
    system = HumanSpawnSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': True,
        'initial_population': 100,
        'seed_crew': {
            'age_range': [20, 30],
            'components': {
                'Needs': 100,
                'Health': 100,
                'Age': 100,
                'Pressure': 50  # 50% should get Pressure
            }
        }
    }
    
    system.init(world_state, config)
    
    # Count entities with Pressure component
    entities = world_state.get_all_entities()
    pressure_count = sum(1 for e in entities.values() if e.has_component('Pressure'))
    
    # With 100 entities and 50% probability, we should get roughly 50 (allow variance)
    assert 30 <= pressure_count <= 70  # Allow variance due to randomness


def test_spawn_system_disabled():
    """Test system doesn't spawn when disabled."""
    system = HumanSpawnSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': False,
        'initial_population': 10
    }
    
    system.init(world_state, config)
    
    # No entities should be created
    entities = world_state.get_all_entities()
    assert len(entities) == 0

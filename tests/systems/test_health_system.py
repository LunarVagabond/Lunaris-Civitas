"""Tests for health system."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.systems.human.health import HealthSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.health import HealthComponent
from src.models.components.pressure import PressureComponent
from src.models.components.needs import NeedsComponent


def test_health_system_init():
    """Test system initializes correctly."""
    system = HealthSystem()
    
    assert system.system_id == "HealthSystem"
    assert system.enabled == True
    assert system.frequency == 'hourly'


def test_health_system_applies_pressure_damage():
    """Test system applies damage from pressure."""
    system = HealthSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=1.0)
    entity.add_component(health)
    
    pressure = PressureComponent()
    pressure.add_pressure('food', 50.0)  # pressure_level should be ~0.5
    entity.add_component(pressure)
    
    config = {
        'enabled': True,
        'pressure_damage': {
            'min_per_tick': 0.001,
            'max_per_tick': 0.005
        }
    }
    
    system.init(world_state, config)
    
    initial_health = health.health
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Health should be reduced
    assert health.health < initial_health
    assert health.health >= 0.0


def test_health_system_applies_unmet_needs_damage():
    """Test system applies damage from unmet needs."""
    system = HealthSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=1.0)
    entity.add_component(health)
    
    needs = NeedsComponent(hunger=0.8, thirst=0.7)  # High unmet needs
    entity.add_component(needs)
    
    config = {
        'enabled': True,
        'unmet_needs_damage': {
            'hunger': {'min_per_tick': 0.0005, 'max_per_tick': 0.002},
            'thirst': {'min_per_tick': 0.001, 'max_per_tick': 0.003}
        }
    }
    
    system.init(world_state, config)
    
    initial_health = health.health
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Health should be reduced
    assert health.health < initial_health


def test_health_system_applies_healing():
    """Test system applies healing when needs are met."""
    system = HealthSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=0.5)  # Below max
    entity.add_component(health)
    
    needs = NeedsComponent(hunger=0.3, thirst=0.2, rest=0.1)  # Needs met
    entity.add_component(needs)
    
    config = {
        'enabled': True,
        'healing_rate': {
            'min_per_tick': 0.0001,
            'max_per_tick': 0.0005
        }
    }
    
    system.init(world_state, config)
    
    initial_health = health.health
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Health should increase
    assert health.health > initial_health
    assert health.health <= health.max_health


def test_health_system_no_healing_at_max():
    """Test system doesn't heal beyond max health."""
    system = HealthSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=1.0)  # At max
    entity.add_component(health)
    
    needs = NeedsComponent(hunger=0.3, thirst=0.2, rest=0.1)  # Needs met
    entity.add_component(needs)
    
    config = {'enabled': True, 'healing_rate': {'min_per_tick': 0.0001, 'max_per_tick': 0.0005}}
    system.init(world_state, config)
    
    initial_health = health.health
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Health should not exceed max
    assert health.health == initial_health
    assert health.health <= health.max_health


def test_health_system_disabled():
    """Test system doesn't process when disabled."""
    system = HealthSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=1.0)
    entity.add_component(health)
    
    pressure = PressureComponent()
    pressure.add_pressure('food', 50.0)
    entity.add_component(pressure)
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    initial_health = health.health
    
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Health should not change
    assert health.health == initial_health

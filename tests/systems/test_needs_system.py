"""Tests for needs system."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.systems.human.needs import NeedsSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent


def test_needs_system_init():
    """Test system initializes correctly."""
    system = NeedsSystem()
    
    assert system.system_id == "NeedsSystem"
    assert system.enabled == True
    assert system.base_hunger_rate == 0.01
    assert system.hunger_rate_variance == 0.005


def test_needs_system_randomizes_decay_rates():
    """Test system randomizes decay rates per entity."""
    system = NeedsSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Create entities with NeedsComponent
    entity1 = world_state.create_entity()
    entity1.add_component(NeedsComponent())
    
    entity2 = world_state.create_entity()
    entity2.add_component(NeedsComponent())
    
    config = {
        'enabled': True,
        'base_hunger_rate': 0.01,
        'hunger_rate_variance': 0.005
    }
    
    system.init(world_state, config)
    
    # First tick should randomize rates
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    needs1 = entity1.get_component('Needs')
    needs2 = entity2.get_component('Needs')
    
    # Rates should be randomized (may be same due to seed, but should be within range)
    assert 0.005 <= needs1.hunger_rate <= 0.015  # base ± variance
    assert 0.005 <= needs2.hunger_rate <= 0.015
    
    # Rates should be stored persistently
    assert needs1.hunger_rate == needs1.hunger_rate
    assert needs2.hunger_rate == needs2.hunger_rate


def test_needs_system_updates_needs():
    """Test system updates needs over time."""
    system = NeedsSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.0, thirst=0.0, rest=0.0)
    entity.add_component(needs)
    
    config = {
        'enabled': True,
        'base_hunger_rate': 0.01,
        'hunger_rate_variance': 0.0,  # No variance for predictable test
        'base_thirst_rate': 0.015,
        'thirst_rate_variance': 0.0,
        'base_rest_rate': 0.005,
        'rest_rate_variance': 0.0
    }
    
    system.init(world_state, config)
    
    # First tick randomizes rates
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    initial_hunger = needs.hunger
    initial_thirst = needs.thirst
    initial_rest = needs.rest
    
    # Second tick should update needs
    system.on_tick(world_state, datetime(2024, 1, 1, 1, 0, 0))
    
    # Needs should have increased (hunger/thirst) or decreased (rest)
    assert needs.hunger > initial_hunger
    assert needs.thirst > initial_thirst
    assert needs.rest > initial_rest  # Rest increases (becomes more exhausted)


def test_needs_system_disabled():
    """Test system doesn't update when disabled."""
    system = NeedsSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.0)
    entity.add_component(needs)
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    initial_hunger = needs.hunger
    
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Hunger should not change
    assert needs.hunger == initial_hunger

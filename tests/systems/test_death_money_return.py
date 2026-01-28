"""Tests for death system money return."""

import pytest
from datetime import datetime

from src.systems.human.death import DeathSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.health import HealthComponent
from src.models.components.wealth import WealthComponent
from src.models.resource import Resource


def test_death_system_returns_money():
    """Test death system returns money to world supply."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add money resource
    money_resource = Resource('money', 'Money', 1000.0, finite=True)
    world_state.add_resource(money_resource)
    
    # Create entity with money
    entity = world_state.create_entity()
    health = HealthComponent(health=0.0)  # Dead
    entity.add_component(health)
    
    wealth = WealthComponent(resources={'money': 500.0})
    entity.add_component(wealth)
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    initial_money = money_resource.current_amount
    
    # Process tick (should remove dead entity)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Money should be returned to world
    assert money_resource.current_amount == initial_money + 500.0
    
    # Entity should be removed
    assert world_state.get_entity(entity.entity_id) is None


def test_death_system_handles_no_money_resource():
    """Test death system handles missing money resource gracefully."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Create entity with money but no money resource
    entity = world_state.create_entity()
    health = HealthComponent(health=0.0)  # Dead
    entity.add_component(health)
    
    wealth = WealthComponent(resources={'money': 500.0})
    entity.add_component(wealth)
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    # Should not crash, just log warning
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should still be removed
    assert world_state.get_entity(entity.entity_id) is None


def test_death_system_handles_no_wealth_component():
    """Test death system handles entities without wealth component."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add money resource
    money_resource = Resource('money', 'Money', 1000.0, finite=True)
    world_state.add_resource(money_resource)
    
    # Create entity without wealth component
    entity = world_state.create_entity()
    health = HealthComponent(health=0.0)  # Dead
    entity.add_component(health)
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    initial_money = money_resource.current_amount
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Money should be unchanged
    assert money_resource.current_amount == initial_money
    
    # Entity should be removed
    assert world_state.get_entity(entity.entity_id) is None

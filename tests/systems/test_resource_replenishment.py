"""Tests for resource replenishment system."""

import pytest
from datetime import datetime

from src.systems.resource.replenishment import ResourceReplenishmentSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier


def test_replenishment_system_init():
    """Test replenishment system initialization."""
    system = ResourceReplenishmentSystem()
    
    assert system.system_id == "ResourceReplenishmentSystem"
    assert system.last_replenishment_hour == {}


def test_replenishment_system_on_tick_hourly():
    """Test replenishment system on_tick for hourly replenishment."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 100.0, max_capacity=200.0, 
                       replenishment_rate=5.0, replenishment_frequency='hourly')
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount + 5.0


def test_replenishment_system_on_tick_daily():
    """Test replenishment system on_tick for daily replenishment."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 100.0, max_capacity=200.0,
                       replenishment_rate=10.0, replenishment_frequency='daily')
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount + 10.0
    
    # Advance to noon - should not replenish
    time.advance_tick()
    system.on_tick(world_state, time.current_datetime)
    assert resource.current_amount == initial_amount + 10.0


def test_replenishment_system_with_modifier():
    """Test replenishment system with modifier applied."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 100.0, max_capacity=200.0,
                       replenishment_rate=10.0, replenishment_frequency='hourly')
    world_state.add_resource(resource)
    
    # Add modifier that increases replenishment by 20%
    modifier = Modifier(
        modifier_name="rainy_season",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.2,
        effect_direction="increase"
    )
    world_state.add_modifier(modifier)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should replenish 12.0 (10 * (1 + 0.2))
    assert resource.current_amount == initial_amount + 12.0


def test_replenishment_system_skips_finite_resources():
    """Test that finite resources are skipped."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("oil", "Oil", 1000.0, finite=True)
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should not replenish finite resources
    assert resource.current_amount == initial_amount


def test_replenishment_system_skips_at_capacity():
    """Test that resources at capacity are skipped."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 200.0, max_capacity=200.0,
                       replenishment_rate=10.0, replenishment_frequency='hourly')
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    assert resource.is_at_capacity()
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should not replenish when at capacity
    assert resource.current_amount == initial_amount


def test_replenishment_system_skips_no_replenishment_rate():
    """Test that resources without replenishment rate are skipped."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 100.0, max_capacity=200.0,
                       replenishment_rate=0.0, replenishment_frequency='hourly')
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should not replenish with zero rate
    assert resource.current_amount == initial_amount


def test_replenishment_system_respects_capacity():
    """Test that replenishment respects capacity limits."""
    system = ResourceReplenishmentSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("water", "Water", 195.0, max_capacity=200.0,
                       replenishment_rate=10.0, replenishment_frequency='hourly')
    world_state.add_resource(resource)
    
    system.init(world_state, {})
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should only add 5.0 (to reach capacity of 200.0)
    assert resource.current_amount == 200.0
    assert resource.is_at_capacity()

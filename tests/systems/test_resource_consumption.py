"""Tests for resource consumption system."""

import pytest
from datetime import datetime

from src.systems.resource.consumption import ResourceConsumptionSystem, _should_consume
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier


def test_should_consume_hourly():
    """Test consumption frequency check for hourly."""
    assert _should_consume('hourly', datetime(2024, 1, 1, 0, 0, 0))
    assert _should_consume('hourly', datetime(2024, 1, 1, 12, 30, 0))
    assert _should_consume('hourly', datetime(2024, 1, 1, 23, 59, 0))


def test_should_consume_daily():
    """Test consumption frequency check for daily."""
    assert _should_consume('daily', datetime(2024, 1, 1, 0, 0, 0))
    assert not _should_consume('daily', datetime(2024, 1, 1, 12, 0, 0))
    assert not _should_consume('daily', datetime(2024, 1, 1, 23, 59, 0))


def test_consumption_system_init():
    """Test consumption system initialization."""
    system = ResourceConsumptionSystem()
    
    assert system.system_id == "ResourceConsumptionSystem"
    assert system.consumption_rates == {}
    assert system.consumption_frequencies == {}


def test_consumption_system_init_with_config():
    """Test consumption system initialization with config."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1))
    world_state = WorldState(time, {})
    
    config = {
        'consumption': {
            'food': 5.0,
            'water': {'rate': 10.0, 'frequency': 'daily'}
        }
    }
    
    system.init(world_state, config)
    
    assert system.consumption_rates['food'] == 5.0
    assert system.consumption_rates['water'] == 10.0
    assert system.consumption_frequencies['food'] == 'hourly'
    assert system.consumption_frequencies['water'] == 'daily'


def test_consumption_system_on_tick_hourly():
    """Test consumption system on_tick for hourly consumption."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    config = {'consumption': {'food': 5.0}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount - 5.0


def test_consumption_system_on_tick_daily():
    """Test consumption system on_tick for daily consumption."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    config = {'consumption': {'food': {'rate': 10.0, 'frequency': 'daily'}}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount - 10.0
    
    # Advance to noon - should not consume
    time.advance_tick()
    system.on_tick(world_state, time.current_datetime)
    assert resource.current_amount == initial_amount - 10.0


def test_consumption_system_with_modifier():
    """Test consumption system with modifier applied."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    # Add modifier that increases consumption by 50%
    modifier = Modifier(
        modifier_name="pest_outbreak",
        resource_id="food",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.5,
        effect_direction="increase"
    )
    world_state.add_modifier(modifier)
    
    config = {'consumption': {'food': 10.0}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should consume 15.0 (10 * (1 + 0.5))
    assert resource.current_amount == initial_amount - 15.0


def test_consumption_system_depletion():
    """Test consumption system handles depletion correctly."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 5.0)
    world_state.add_resource(resource)
    
    config = {'consumption': {'food': 10.0}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should consume only what's available (5.0)
    assert resource.current_amount == 0.0
    assert resource.is_depleted()


def test_consumption_system_negative_rate_ignored():
    """Test that negative consumption rates are ignored."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1))
    world_state = WorldState(time, {})
    
    config = {'consumption': {'food': -10.0}}
    system.init(world_state, config)
    
    assert 'food' not in system.consumption_rates


def test_consumption_system_missing_resource():
    """Test consumption system handles missing resource gracefully."""
    system = ResourceConsumptionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    config = {'consumption': {'nonexistent': 10.0}}
    system.init(world_state, config)
    
    # Should not raise error, just skip
    system.on_tick(world_state, time.current_datetime)

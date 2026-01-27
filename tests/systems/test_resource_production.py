"""Tests for resource production system."""

import pytest
from datetime import datetime

from src.systems.resource.production import ResourceProductionSystem, _should_produce
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier


def test_should_produce_hourly():
    """Test production frequency check for hourly."""
    assert _should_produce('hourly', datetime(2024, 1, 1, 0, 0, 0))
    assert _should_produce('hourly', datetime(2024, 1, 1, 12, 30, 0))
    assert _should_produce('hourly', datetime(2024, 1, 1, 23, 59, 0))


def test_should_produce_daily():
    """Test production frequency check for daily."""
    assert _should_produce('daily', datetime(2024, 1, 1, 0, 0, 0))
    assert not _should_produce('daily', datetime(2024, 1, 1, 12, 0, 0))
    assert not _should_produce('daily', datetime(2024, 1, 1, 23, 59, 0))


def test_should_produce_weekly():
    """Test production frequency check for weekly."""
    monday = datetime(2024, 1, 1, 0, 0, 0)  # Monday
    assert _should_produce('weekly', monday)
    
    tuesday = datetime(2024, 1, 2, 0, 0, 0)
    assert not _should_produce('weekly', tuesday)
    
    monday_noon = datetime(2024, 1, 1, 12, 0, 0)
    assert not _should_produce('weekly', monday_noon)


def test_should_produce_monthly():
    """Test production frequency check for monthly."""
    assert _should_produce('monthly', datetime(2024, 1, 1, 0, 0, 0))
    assert _should_produce('monthly', datetime(2024, 2, 1, 0, 0, 0))
    assert not _should_produce('monthly', datetime(2024, 1, 2, 0, 0, 0))
    assert not _should_produce('monthly', datetime(2024, 1, 1, 12, 0, 0))


def test_should_produce_yearly():
    """Test production frequency check for yearly."""
    assert _should_produce('yearly', datetime(2024, 1, 1, 0, 0, 0))
    assert _should_produce('yearly', datetime(2025, 1, 1, 0, 0, 0))
    assert not _should_produce('yearly', datetime(2024, 1, 2, 0, 0, 0))
    assert not _should_produce('yearly', datetime(2024, 1, 1, 12, 0, 0))


def test_production_system_init():
    """Test production system initialization."""
    system = ResourceProductionSystem()
    
    assert system.system_id == "ResourceProductionSystem"
    assert system.production_rates == {}
    assert system.production_frequencies == {}


def test_production_system_init_with_config():
    """Test production system initialization with config."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1))
    world_state = WorldState(time, {})
    
    config = {
        'production': {
            'food': 10.0,
            'water': {'rate': 20.0, 'frequency': 'daily'}
        }
    }
    
    system.init(world_state, config)
    
    assert system.production_rates['food'] == 10.0
    assert system.production_rates['water'] == 20.0
    assert system.production_frequencies['food'] == 'hourly'
    assert system.production_frequencies['water'] == 'daily'


def test_production_system_on_tick_hourly():
    """Test production system on_tick for hourly production."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    config = {'production': {'food': 5.0}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount + 5.0


def test_production_system_on_tick_daily():
    """Test production system on_tick for daily production."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    config = {'production': {'food': {'rate': 10.0, 'frequency': 'daily'}}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    assert resource.current_amount == initial_amount + 10.0
    
    # Advance to noon - should not produce
    time.advance_tick()
    system.on_tick(world_state, time.current_datetime)
    assert resource.current_amount == initial_amount + 10.0


def test_production_system_with_modifier():
    """Test production system with modifier applied."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 100.0)
    world_state.add_resource(resource)
    
    # Add modifier that decreases production by 30%
    modifier = Modifier(
        modifier_name="drought",
        resource_id="food",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    world_state.add_modifier(modifier)
    
    config = {'production': {'food': 100.0}}
    system.init(world_state, config)
    
    initial_amount = resource.current_amount
    system.on_tick(world_state, time.current_datetime)
    
    # Should produce 70.0 (100 * (1 - 0.3))
    assert resource.current_amount == initial_amount + 70.0


def test_production_system_negative_rate_ignored():
    """Test that negative production rates are ignored."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1))
    world_state = WorldState(time, {})
    
    config = {'production': {'food': -10.0}}
    system.init(world_state, config)
    
    assert 'food' not in system.production_rates


def test_production_system_invalid_frequency():
    """Test that invalid frequency defaults to hourly."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1))
    world_state = WorldState(time, {})
    
    config = {'production': {'food': {'rate': 10.0, 'frequency': 'invalid'}}}
    system.init(world_state, config)
    
    assert system.production_frequencies['food'] == 'hourly'


def test_production_system_missing_resource():
    """Test production system handles missing resource gracefully."""
    system = ResourceProductionSystem()
    time = SimulationTime(datetime(2024, 1, 1, 12, 0, 0))
    world_state = WorldState(time, {})
    
    config = {'production': {'nonexistent': 10.0}}
    system.init(world_state, config)
    
    # Should not raise error, just skip
    system.on_tick(world_state, time.current_datetime)

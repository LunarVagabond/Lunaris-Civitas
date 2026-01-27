"""Tests for world state."""

import pytest
from datetime import datetime

from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier
from src.core.system import System


class MockSystem(System):
    """Mock system for testing."""
    
    @property
    def system_id(self) -> str:
        return "MockSystem"
    
    def init(self, world_state, config):
        pass
    
    def on_tick(self, world_state, current_datetime):
        pass


def test_world_state_initialization():
    """Test world state initialization."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start, rng_seed=42)
    config = {"test": "config"}
    
    world_state = WorldState(time, config, rng_seed=42)
    
    assert world_state.simulation_time == time
    assert world_state.config_snapshot == config
    assert world_state.rng_seed == 42


def test_world_state_resources():
    """Test resource management."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    world_state = WorldState(time, {})
    
    resource = Resource("food", "Food", 1000.0)
    world_state.add_resource(resource)
    
    assert world_state.get_resource("food") == resource
    assert world_state.get_resource("nonexistent") is None
    
    # Duplicate resource
    with pytest.raises(ValueError):
        world_state.add_resource(resource)


def test_world_state_systems():
    """Test system registration."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    world_state = WorldState(time, {})
    
    system = MockSystem()
    world_state.register_system(system)
    
    assert world_state.get_system("MockSystem") == system
    assert len(world_state.get_all_systems()) == 1
    
    # Duplicate system
    with pytest.raises(ValueError):
        world_state.register_system(system)


def test_world_state_modifiers():
    """Test modifier management."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    world_state = WorldState(time, {})
    
    modifier = Modifier(
        modifier_name="drought",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    world_state.add_modifier(modifier)
    
    modifier_id = list(world_state._modifiers.keys())[0]
    assert world_state.get_modifier(modifier_id) == modifier
    
    # Test active modifiers
    active = world_state.get_active_modifiers()
    assert len(active) == 1
    
    # Test filtering
    resource_mods = world_state.get_modifiers_for_resource("water")
    assert len(resource_mods) == 1
    
    resource_mods = world_state.get_modifiers_for_resource("food")
    assert len(resource_mods) == 0


def test_world_state_cleanup_expired():
    """Test expired modifier cleanup."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    world_state = WorldState(time, {})
    
    modifier = Modifier(
        modifier_name="expired",
        resource_id="water",
        start_year=2020,
        end_year=2022,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    world_state.add_modifier(modifier)
    
    # Advance time to 2024 (modifier expired)
    for _ in range(24 * 365 * 2):  # Advance 2 years
        time.advance_tick()
    
    expired = world_state.cleanup_expired_modifiers()
    assert len(expired) == 1
    
    # Modifier should still exist but be inactive
    modifier_id = list(world_state._modifiers.keys())[0]
    assert world_state.get_modifier(modifier_id) is not None
    assert modifier._is_active_flag == False

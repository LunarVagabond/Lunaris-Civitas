"""Tests for human needs fulfillment system."""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from src.systems.human.needs_fulfillment import HumanNeedsFulfillmentSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.pressure import PressureComponent
from src.models.requirement_resolution import RequirementResolution
from src.systems.human.requirement_resolver import RequirementResolverSystem


def test_fulfillment_system_init():
    """Test system initializes correctly."""
    system = HumanNeedsFulfillmentSystem()
    
    assert system.system_id == "HumanNeedsFulfillmentSystem"
    assert system.enabled == True
    assert system.frequency == 'hourly'


def test_fulfillment_system_fulfills_needs():
    """Test system fulfills needs through RequirementResolverSystem."""
    system = HumanNeedsFulfillmentSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Create mock resolver system
    resolver = Mock(spec=RequirementResolverSystem)
    resolver.system_id = "RequirementResolver"
    world_state.register_system(resolver)
    
    # Create entity with needs
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.8)  # High hunger
    entity.add_component(needs)
    
    # Mock successful resolution
    resolver.resolve_requirement.return_value = RequirementResolution(
        success=True,
        source_id='inventory',
        amount_fulfilled=5.0,
        amount_requested=8.0,
        reason='Fulfilled from inventory'
    )
    
    config = {
        'enabled': True,
        'satisfaction_ranges': {
            'food': {'hunger_restore_min': 0.05, 'hunger_restore_max': 0.15}
        }
    }
    
    system.init(world_state, config)
    
    initial_hunger = needs.hunger
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Hunger should be reduced
    assert needs.hunger < initial_hunger
    assert resolver.resolve_requirement.called


def test_fulfillment_system_adds_pressure_on_failure():
    """Test system adds pressure when fulfillment fails."""
    system = HumanNeedsFulfillmentSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Create mock resolver system
    resolver = Mock(spec=RequirementResolverSystem)
    resolver.system_id = "RequirementResolver"
    world_state.register_system(resolver)
    
    # Create entity with needs
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.8)
    entity.add_component(needs)
    
    # Mock failed resolution
    resolver.resolve_requirement.return_value = RequirementResolution(
        success=False,
        source_id=None,
        amount_fulfilled=0.0,
        amount_requested=8.0,
        reason='No sources available'
    )
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Pressure should be added
    pressure = entity.get_component('Pressure')
    assert pressure is not None
    assert pressure.get_pressure('food') > 0


def test_fulfillment_system_applies_randomized_satisfaction():
    """Test system applies randomized satisfaction amounts."""
    system = HumanNeedsFulfillmentSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Create mock resolver system
    resolver = Mock(spec=RequirementResolverSystem)
    resolver.system_id = "RequirementResolver"
    world_state.register_system(resolver)
    
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.8)
    entity.add_component(needs)
    
    resolver.resolve_requirement.return_value = RequirementResolution(
        success=True,
        source_id='inventory',
        amount_fulfilled=5.0,
        amount_requested=8.0,
        reason='Fulfilled'
    )
    
    config = {
        'enabled': True,
        'satisfaction_ranges': {
            'food': {'hunger_restore_min': 0.05, 'hunger_restore_max': 0.15}
        }
    }
    
    system.init(world_state, config)
    
    initial_hunger = needs.hunger
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Hunger should be reduced by randomized amount
    hunger_reduction = initial_hunger - needs.hunger
    # Should be between min and max satisfaction rates * amount
    assert 0.05 * 5.0 <= hunger_reduction <= 0.15 * 5.0


def test_fulfillment_system_disabled():
    """Test system doesn't process when disabled."""
    system = HumanNeedsFulfillmentSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    resolver = Mock(spec=RequirementResolverSystem)
    resolver.system_id = "RequirementResolver"
    world_state.register_system(resolver)
    
    entity = world_state.create_entity()
    needs = NeedsComponent(hunger=0.8)
    entity.add_component(needs)
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Resolver should not be called
    assert not resolver.resolve_requirement.called

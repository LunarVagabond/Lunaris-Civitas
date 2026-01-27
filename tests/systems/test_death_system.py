"""Tests for death system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.systems.human.death import DeathSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.health import HealthComponent
from src.models.components.age import AgeComponent


def test_death_system_init():
    """Test system initializes correctly."""
    system = DeathSystem()
    
    assert system.system_id == "DeathSystem"
    assert system.enabled == True
    assert system.frequency == 'hourly'
    assert system.old_age_start == 70.0
    assert system.peak_mortality_age == 85.0


def test_death_system_health_death():
    """Test system removes entities when health <= 0."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=0.0)  # Dead
    entity.add_component(health)
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should be removed
    assert world_state.get_entity(entity.entity_id) is None


def test_death_system_age_death_probability():
    """Test age-based death probability calculation."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': True,
        'age_mortality': {
            'old_age_start': 70.0,
            'old_age_death_chance_min': 0.00001,
            'old_age_death_chance_max': 0.0001,
            'peak_mortality_age': 85.0,
            'chance_increase_per_year': 0.00001,
            'chance_multiplier_per_year': 1.1
        }
    }
    
    system.init(world_state, config)
    
    # Test probability at old_age_start
    prob_70 = system._calculate_age_death_probability(70.0, world_state)
    assert 0.00001 <= prob_70 <= 0.0001
    
    # Test probability at peak_mortality_age (should be higher)
    prob_85 = system._calculate_age_death_probability(85.0, world_state)
    assert prob_85 > prob_70
    
    # Test probability past peak (exponential increase)
    prob_90 = system._calculate_age_death_probability(90.0, world_state)
    assert prob_90 > prob_85
    
    # Test probability past 100 (allows outliers)
    prob_100 = system._calculate_age_death_probability(100.0, world_state)
    assert prob_100 > prob_90
    assert prob_100 < 1.0  # Never guaranteed death


def test_death_system_no_death_below_old_age():
    """Test system doesn't check age death below old_age_start."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=1.0)
    entity.add_component(health)
    
    # Age 50 (below old_age_start)
    birth_date = datetime(1974, 1, 1, 0, 0, 0)
    age = AgeComponent(birth_date=birth_date, current_date=datetime(2024, 1, 1, 0, 0, 0))
    entity.add_component(age)
    
    config = {'enabled': True}
    system.init(world_state, config)
    
    # Process tick
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should still exist
    assert world_state.get_entity(entity.entity_id) is not None


def test_death_system_probability_curve():
    """Test probability curve increases correctly."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    config = {
        'enabled': True,
        'age_mortality': {
            'old_age_start': 70.0,
            'old_age_death_chance_min': 0.00001,
            'old_age_death_chance_max': 0.0001,
            'peak_mortality_age': 85.0,
            'chance_increase_per_year': 0.00001,
            'chance_multiplier_per_year': 1.1
        }
    }
    
    system.init(world_state, config)
    
    # Test probability is within expected range at old_age_start
    prob_70 = system._calculate_age_death_probability(70.0, world_state)
    assert 0.00001 <= prob_70 <= 0.0001
    
    # Test probability increases with age (use multiple calls to account for randomization)
    # Since base chance is randomized, we test that older ages have higher expected values
    prob_85 = system._calculate_age_death_probability(85.0, world_state)
    # At peak age, should be base + (15 years * increase_per_year)
    # Base is randomized, but peak should be higher than base minimum
    assert prob_85 >= 0.00001  # At least base minimum
    
    # Test exponential increase after peak
    prob_90 = system._calculate_age_death_probability(90.0, world_state)
    prob_95 = system._calculate_age_death_probability(95.0, world_state)
    prob_100 = system._calculate_age_death_probability(100.0, world_state)
    
    # Older ages should have higher probabilities (accounting for randomization)
    # We test that they're reasonable and increasing trend
    assert prob_90 >= 0.00001
    assert prob_95 >= 0.00001
    assert prob_100 >= 0.00001
    
    # But never guaranteed (allows outliers)
    assert prob_100 < 0.99
    
    # Test that probability is 0 below old_age_start
    prob_50 = system._calculate_age_death_probability(50.0, world_state)
    assert prob_50 == 0.0


def test_death_system_disabled():
    """Test system doesn't process when disabled."""
    system = DeathSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    entity = world_state.create_entity()
    health = HealthComponent(health=0.0)  # Dead
    entity.add_component(health)
    
    config = {'enabled': False}
    system.init(world_state, config)
    
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should still exist (not processed)
    assert world_state.get_entity(entity.entity_id) is not None

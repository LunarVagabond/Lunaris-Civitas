"""Tests for job system with multiple payment resource types."""

import pytest
from datetime import datetime

from src.systems.human.job import JobSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.components.employment import EmploymentComponent
from src.models.components.skills import SkillsComponent
from src.models.components.age import AgeComponent
from src.models.components.wealth import WealthComponent
from src.models.resource import Resource


def test_job_pays_in_multiple_resources():
    """Test job can pay in multiple resource types (money + crypto)."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add resources
    world_state.add_resource(Resource('money', 'Money', 10000.0, finite=False))
    world_state.add_resource(Resource('crypto', 'Crypto', 100.0, finite=False))
    
    # Create entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    entity.add_component(SkillsComponent(charisma=0.8, job_skills={'trading': 0.9}))
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'base_hiring_chance': 1.0,
        'jobs': {
            'crypto_trader': {
                'name': 'Crypto Trader',
                'max_percentage': 5.0,
                'payment': {'money': 80.0, 'crypto': 2.0},  # Pays in both
                'max_payment_cap': {'money': 120.0, 'crypto': 3.0},
                'min_payment': {'money': 50.0, 'crypto': 1.0},
                'min_age': 18,
                'required_skill': 'trading',
                'skill_weight': 0.8,
                'charisma_weight': 0.2,
                'job_type': 'service'
            }
        }
    }
    
    system.init(world_state, config)
    
    # Hire entity
    system._hire_entity(world_state, datetime(2024, 1, 1, 0, 0, 0), entity, 'crypto_trader', config['jobs']['crypto_trader'])
    
    employment = entity.get_component('Employment')
    assert employment is not None
    assert employment.is_employed()
    assert 'money' in employment.payment_resources
    assert 'crypto' in employment.payment_resources
    assert employment.payment_resources['money'] > 0
    assert employment.payment_resources['crypto'] > 0


def test_job_pays_in_integer_resource():
    """Test job can pay in integer-based resources (like bananas)."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add banana resource (integer-based)
    world_state.add_resource(Resource('bananas', 'Bananas', 1000.0, finite=False))
    
    # Create entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    entity.add_component(SkillsComponent(charisma=0.7, job_skills={'farming': 0.8}))
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'base_hiring_chance': 1.0,
        'jobs': {
            'banana_farmer': {
                'name': 'Banana Farmer',
                'max_percentage': 5.0,
                'payment': {'bananas': 10.0},  # Pays in bananas
                'max_payment_cap': {'bananas': 15.0},
                'min_payment': {'bananas': 5.0},
                'min_age': 16,
                'required_skill': 'farming',
                'skill_weight': 0.7,
                'charisma_weight': 0.1,
                'job_type': 'production',
                'production': {
                    'resource_id': 'bananas',
                    'rate': 50.0,
                    'frequency': 'monthly'
                }
            }
        }
    }
    
    system.init(world_state, config)
    
    # Hire entity
    system._hire_entity(world_state, datetime(2024, 1, 1, 0, 0, 0), entity, 'banana_farmer', config['jobs']['banana_farmer'])
    
    employment = entity.get_component('Employment')
    assert employment is not None
    assert employment.is_employed()
    assert 'bananas' in employment.payment_resources
    assert employment.payment_resources['bananas'] >= 5.0  # At least min payment


def test_job_payment_with_multiple_resources():
    """Test payment system handles multiple resource types correctly."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add multiple resources
    world_state.add_resource(Resource('money', 'Money', 10000.0, finite=False))
    world_state.add_resource(Resource('bananas', 'Bananas', 1000.0, finite=False))
    world_state.add_resource(Resource('crypto', 'Crypto', 100.0, finite=False))
    
    # Create employed entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    employment = EmploymentComponent(
        job_type='multi_payment_job',
        payment_resources={'money': 100.0, 'bananas': 5.0, 'crypto': 1.0},
        hire_date=datetime(2024, 1, 1, 0, 0, 0),
        max_payment_cap={'money': 150.0, 'bananas': 10.0, 'crypto': 2.0}
    )
    entity.add_component(employment)
    
    config = {
        'enabled': True,
        'jobs': {
            'multi_payment_job': {
                'name': 'Multi Payment Job',
                'max_percentage': 10.0,
                'payment': {'money': 100.0, 'bananas': 5.0, 'crypto': 1.0},
                'job_type': 'service'
            }
        }
    }
    
    system.init(world_state, config)
    
    initial_money = world_state.get_resource('money').current_amount
    initial_bananas = world_state.get_resource('bananas').current_amount
    initial_crypto = world_state.get_resource('crypto').current_amount
    
    # Pay salary (monthly)
    system._pay_salaries(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Check world resources decreased
    assert world_state.get_resource('money').current_amount < initial_money
    assert world_state.get_resource('bananas').current_amount < initial_bananas
    assert world_state.get_resource('crypto').current_amount < initial_crypto
    
    # Check entity wealth increased
    wealth = entity.get_component('Wealth')
    assert wealth is not None
    assert wealth.get_amount('money') > 0
    assert wealth.get_amount('bananas') > 0
    assert wealth.get_amount('crypto') > 0


def test_job_payment_insufficient_resources():
    """Test that workers quit if world doesn't have enough payment resources."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add resources with insufficient amounts
    world_state.add_resource(Resource('money', 'Money', 50.0, finite=False))  # Not enough
    world_state.add_resource(Resource('bananas', 'Bananas', 2.0, finite=False))  # Not enough
    
    # Create employed entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    employment = EmploymentComponent(
        job_type='test_job',
        payment_resources={'money': 100.0, 'bananas': 5.0},  # More than available
        hire_date=datetime(2024, 1, 1, 0, 0, 0)
    )
    entity.add_component(employment)
    
    config = {
        'enabled': True,
        'jobs': {
            'test_job': {
                'name': 'Test Job',
                'max_percentage': 10.0,
                'payment': {'money': 100.0, 'bananas': 5.0},
                'job_type': 'service'
            }
        }
    }
    
    system.init(world_state, config)
    
    # Pay salary (should fail and employee quits)
    system._pay_salaries(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should no longer be employed
    employment = entity.get_component('Employment')
    assert employment is not None
    assert not employment.is_employed()  # Quit due to insufficient payment

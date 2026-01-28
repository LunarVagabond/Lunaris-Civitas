"""Tests for job system."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from src.systems.human.job import JobSystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.employment import EmploymentComponent
from src.models.components.skills import SkillsComponent
from src.models.components.age import AgeComponent
from src.models.components.wealth import WealthComponent
from src.models.resource import Resource


def test_job_system_init():
    """Test system initializes correctly."""
    system = JobSystem()
    
    assert system.system_id == "JobSystem"
    assert system.enabled == True
    assert system.assignment_frequency == 'monthly'
    assert system.production_frequency == 'monthly'


def test_job_system_config_loading():
    """Test system loads configuration correctly."""
    system = JobSystem()
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'production_frequency': 'monthly',
        'min_work_age': 16,
        'max_work_age': 70,
        'base_hiring_chance': 0.5,
        'hiring_chance_multiplier': 0.6,
        'yearly_raise_probability': 0.8,
        'six_month_raise_probability': 0.1,
        'raise_amount_range': [0.03, 0.06],
        'jobs': {
            'farmer': {
                'name': 'Farmer',
                'max_percentage': 10.0,
                'payment': {'money': 100.0},
                'max_payment_cap': {'money': 130.0},
                'min_payment': {'money': 50.0},
                'min_age': 16,
                'production': {
                    'resource_id': 'food',
                    'rate': 50.0,
                    'frequency': 'monthly'
                },
                'required_skill': 'farming',
                'skill_weight': 0.7,
                'charisma_weight': 0.1,
                'job_type': 'production'
            }
        }
    }
    
    world_state = Mock()
    world_state.config_snapshot = {}
    
    system.init(world_state, config)
    
    assert system.enabled == True
    assert system.min_work_age == 16
    assert system.max_work_age == 70
    assert system.base_hiring_chance == 0.5
    assert system.hiring_chance_multiplier == 0.6
    assert system.yearly_raise_probability == 0.8
    assert 'farmer' in system.jobs
    assert system.jobs['farmer']['name'] == 'Farmer'


def test_job_system_assigns_jobs():
    """Test system assigns jobs to eligible entities."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add money resource
    money_resource = Resource(
        resource_id='money',
        name='Money',
        initial_amount=10000.0,
        finite=True
    )
    world_state.add_resource(money_resource)
    
    # Add food resource for production
    food_resource = Resource(
        resource_id='food',
        name='Food',
        initial_amount=1000.0,
        max_capacity=10000.0
    )
    world_state.add_resource(food_resource)
    
    # Create multiple eligible entities to ensure at least one gets hired
    # With 10 entities and 10% max_percentage, we get 1 max worker
    entities = []
    for i in range(10):
        entity = world_state.create_entity()
        entity.add_component(AgeComponent(
            birth_date=datetime(2000, 1, 1, 0, 0, 0),
            current_date=datetime(2024, 1, 1, 0, 0, 0)
        ))
        entity.add_component(SkillsComponent(
            charisma=0.9,  # High charisma
            intelligence=0.6,
            job_skills={'farming': 0.9}  # High farming skill
        ))
        entities.append(entity)
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'base_hiring_chance': 1.0,  # 100% chance for testing
        'hiring_chance_multiplier': 0.5,
        'jobs': {
            'farmer': {
                'name': 'Farmer',
                'max_percentage': 10.0,  # 10% of 10 = 1 worker
                'payment': {'money': 100.0},
                'max_payment_cap': {'money': 130.0},
                'min_payment': {'money': 50.0},
                'min_age': 16,
                'production': {
                    'resource_id': 'food',
                    'rate': 50.0,
                    'frequency': 'monthly'
                },
                'required_skill': 'farming',
                'skill_weight': 0.7,
                'charisma_weight': 0.1,
                'job_type': 'production'
            }
        }
    }
    
    system.init(world_state, config)
    
    # Run job assignment (monthly - 1st of month)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Check if at least one entity got hired
    hired_entities = [
        e for e in entities
        if e.get_component('Employment') and e.get_component('Employment').is_employed()
    ]
    
    assert len(hired_entities) > 0, "At least one entity should be hired"
    
    # Check the first hired entity
    employment = hired_entities[0].get_component('Employment')
    assert employment is not None
    assert employment.is_employed()
    assert employment.job_type == 'farmer'
    assert employment.payment_resources
    assert 'money' in employment.payment_resources
    assert employment.payment_resources['money'] > 0
    assert employment.hire_date == datetime(2024, 1, 1, 0, 0, 0)


def test_job_system_respects_age_requirements():
    """Test system respects job age requirements."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add resources
    world_state.add_resource(Resource('money', 'Money', 10000.0, finite=True))
    world_state.add_resource(Resource('food', 'Food', 1000.0))
    
    # Create entity too young for job
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2010, 1, 1, 0, 0, 0),  # 14 years old
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    entity.add_component(SkillsComponent(job_skills={'farming': 0.8}))
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'base_hiring_chance': 1.0,
        'jobs': {
            'farmer': {
                'name': 'Farmer',
                'max_percentage': 10.0,
                'payment': {'money': 100.0},
                'max_payment_cap': {'money': 130.0},
                'min_payment': {'money': 50.0},
                'min_age': 16,  # Requires 16+
                'production': {
                    'resource_id': 'food',
                    'rate': 50.0,
                    'frequency': 'monthly'
                },
                'required_skill': 'farming',
                'skill_weight': 0.7,
                'charisma_weight': 0.1,
                'job_type': 'production'
            }
        }
    }
    
    system.init(world_state, config)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Entity should not be hired (too young)
    employment = entity.get_component('Employment')
    if employment:
        assert not employment.is_employed()


def test_job_system_produces_resources():
    """Test system produces resources from jobs."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add resources
    food_resource = Resource('food', 'Food', 1000.0, max_capacity=10000.0)
    world_state.add_resource(food_resource)
    world_state.add_resource(Resource('money', 'Money', 10000.0, finite=True))
    
    # Create employed entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    employment = EmploymentComponent(
        job_type='farmer',
        payment_resources={'money': 100.0},
        hire_date=datetime(2024, 1, 1, 0, 0, 0),
        max_payment_cap={'money': 130.0}
    )
    entity.add_component(employment)
    
    config = {
        'enabled': True,
        'production_frequency': 'monthly',
        'jobs': {
            'farmer': {
                'name': 'Farmer',
                'max_percentage': 10.0,
                'production': {
                    'resource_id': 'food',
                    'rate': 50.0,
                    'frequency': 'monthly'
                }
            }
        }
    }
    
    system.init(world_state, config)
    
    initial_food = food_resource.current_amount
    
    # Run production (monthly - 1st of month)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Food should have increased
    assert food_resource.current_amount > initial_food
    assert food_resource.current_amount == initial_food + 50.0  # 1 worker × 50.0 rate


def test_job_system_pays_salaries():
    """Test system pays salaries to workers."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add money resource
    money_resource = Resource('money', 'Money', 10000.0, finite=True)
    world_state.add_resource(money_resource)
    
    # Create employed entity
    entity = world_state.create_entity()
    entity.add_component(AgeComponent(
        birth_date=datetime(2000, 1, 1, 0, 0, 0),
        current_date=datetime(2024, 1, 1, 0, 0, 0)
    ))
    employment = EmploymentComponent(
        job_type='teacher',
        payment_resources={'money': 150.0},
        hire_date=datetime(2024, 1, 1, 0, 0, 0),
        max_payment_cap={'money': 200.0}
    )
    entity.add_component(employment)
    
    config = {
        'enabled': True,
        'jobs': {
            'teacher': {
                'name': 'Teacher',
                'max_percentage': 3.0,
                # No production - service job
            }
        }
    }
    
    system.init(world_state, config)
    
    initial_money = money_resource.current_amount
    wealth = entity.get_component('Wealth')
    if not wealth:
        wealth = WealthComponent()
        entity.add_component(wealth)
    initial_wealth = wealth.get_amount('money')
    
    # Run salary payment (monthly - 1st of month)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # World money should decrease, entity wealth should increase
    assert money_resource.current_amount < initial_money
    assert wealth.get_amount('money') > initial_wealth
    assert wealth.get_amount('money') == initial_wealth + 150.0  # Payment amount


def test_job_system_dynamic_limits():
    """Test system respects dynamic employment limits."""
    system = JobSystem()
    
    simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
    world_state = WorldState(
        simulation_time=simulation_time,
        config_snapshot={},
        rng_seed=42
    )
    
    # Add resources
    world_state.add_resource(Resource('money', 'Money', 10000.0, finite=True))
    world_state.add_resource(Resource('food', 'Food', 1000.0))
    
    # Create 10 entities (10% of 100 = 10 max farmers)
    for i in range(10):
        entity = world_state.create_entity()
        entity.add_component(AgeComponent(
            birth_date=datetime(2000, 1, 1, 0, 0, 0),
            current_date=datetime(2024, 1, 1, 0, 0, 0)
        ))
        entity.add_component(SkillsComponent(job_skills={'farming': 0.8}))
    
    config = {
        'enabled': True,
        'assignment_frequency': 'monthly',
        'base_hiring_chance': 1.0,  # 100% chance
        'jobs': {
            'farmer': {
                'name': 'Farmer',
                'max_percentage': 10.0,  # 10% of population
                'payment': {'money': 100.0},
                'max_payment_cap': {'money': 130.0},
                'min_payment': {'money': 50.0},
                'min_age': 16,
                'production': {
                    'resource_id': 'food',
                    'rate': 50.0,
                    'frequency': 'monthly'
                },
                'required_skill': 'farming',
                'skill_weight': 0.7,
                'charisma_weight': 0.1,
                'job_type': 'production'
            }
        }
    }
    
    system.init(world_state, config)
    system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
    
    # Count employed farmers
    farmer_count = sum(
        1 for e in world_state.get_all_entities().values()
        if (e.get_component('Employment') and 
            e.get_component('Employment').job_type == 'farmer')
    )
    
    # Should be at most 10% of 10 = 1 farmer (or could be less due to randomness)
    # But with 100% hiring chance, should get close to max
    assert farmer_count <= 1  # 10% of 10 entities = 1 max


# Mock class for testing
class Mock:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

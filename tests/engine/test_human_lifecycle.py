"""Integration tests for full human lifecycle systems."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

from src.engine.simulation import Simulation
from src.systems.human.spawn import HumanSpawnSystem
from src.systems.human.needs import NeedsSystem
from src.systems.human.needs_fulfillment import HumanNeedsFulfillmentSystem
from src.systems.human.health import HealthSystem
from src.systems.human.death import DeathSystem
from src.systems.human.requirement_resolver import RequirementResolverSystem
from src.models.requirement_resolution import RequirementResolution


class TestHumanLifecycle:
    """Integration tests for full human lifecycle."""
    
    def test_full_lifecycle_spawn_to_death(self):
        """Test complete lifecycle: spawn -> needs -> health -> death."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': [
                    'HumanSpawnSystem',
                    'NeedsSystem',
                    'HumanNeedsFulfillmentSystem',
                    'HealthSystem',
                    'DeathSystem'
                ],
                'resources': [
                    {
                        'id': 'food',
                        'name': 'Food',
                        'initial_amount': 1000.0,
                        'max_capacity': None,
                        'replenishment_rate': None,
                        'finite': False
                    }
                ],
                'systems_config': {
                    'HumanSpawnSystem': {
                        'enabled': True,
                        'initial_population': 5,
                        'seed_crew': {
                            'age_range': [20, 30],
                            'components': {
                                'Needs': 100,
                                'Health': 100,
                                'Age': 100
                            }
                        }
                    },
                    'NeedsSystem': {
                        'enabled': True,
                        'base_hunger_rate': 0.01,
                        'hunger_rate_variance': 0.0  # No variance for predictable test
                    },
                    'HealthSystem': {
                        'enabled': True,
                        'pressure_damage': {'min_per_tick': 0.01, 'max_per_tick': 0.01}
                    },
                    'DeathSystem': {
                        'enabled': True
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(HumanSpawnSystem())
            sim.register_system(NeedsSystem())
            sim.register_system(HealthSystem())
            sim.register_system(DeathSystem())
            sim._initialize_new_simulation(config)
            
            # Check initial population created
            entities = sim.world_state.get_all_entities()
            assert len(entities) == 5
            
            # Run simulation for a few ticks
            sim.run(max_ticks=3)
            
            # Entities should still exist (unless health reached 0)
            entities_after = sim.world_state.get_all_entities()
            assert len(entities_after) <= 5  # Some may have died
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_needs_decay_and_fulfillment(self):
        """Test needs decay and fulfillment cycle."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': [
                    'HumanSpawnSystem',
                    'NeedsSystem',
                    'HumanNeedsFulfillmentSystem'
                ],
                'resources': [
                    {
                        'id': 'food',
                        'name': 'Food',
                        'initial_amount': 1000.0,
                        'max_capacity': None,
                        'replenishment_rate': None,
                        'finite': False
                    }
                ],
                'systems_config': {
                    'HumanSpawnSystem': {
                        'enabled': True,
                        'initial_population': 1,
                        'seed_crew': {
                            'age_range': [20, 30],
                            'components': {
                                'Needs': 100,
                                'Health': 100,
                                'Age': 100
                            }
                        }
                    },
                    'NeedsSystem': {
                        'enabled': True,
                        'base_hunger_rate': 0.01,
                        'hunger_rate_variance': 0.0
                    },
                    'HumanNeedsFulfillmentSystem': {
                        'enabled': True,
                        'satisfaction_ranges': {
                            'food': {'hunger_restore_min': 0.1, 'hunger_restore_max': 0.1}
                        }
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(HumanSpawnSystem())
            sim.register_system(NeedsSystem())
            
            # Create mock resolver
            resolver = RequirementResolverSystem()
            resolver.source_definitions = {}  # Empty for now
            sim.register_system(resolver)
            sim.register_system(HumanNeedsFulfillmentSystem())
            
            sim._initialize_new_simulation(config)
            
            # Get entity
            entities = sim.world_state.get_all_entities()
            assert len(entities) == 1
            entity = list(entities.values())[0]
            needs = entity.get_component('Needs')
            
            initial_hunger = needs.hunger
            
            # Run one tick - needs should decay
            sim.run(max_ticks=1)
            
            # Hunger should have increased
            assert needs.hunger > initial_hunger
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_health_degradation_from_pressure(self):
        """Test health degrades from pressure."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': [
                    'HumanSpawnSystem',
                    'HealthSystem'
                ],
                'resources': [],
                'systems_config': {
                    'HumanSpawnSystem': {
                        'enabled': True,
                        'initial_population': 1,
                        'seed_crew': {
                            'age_range': [20, 30],
                            'components': {
                                'Needs': 100,
                                'Health': 100,
                                'Age': 100,
                                'Pressure': 100
                            }
                        }
                    },
                    'HealthSystem': {
                        'enabled': True,
                        'pressure_damage': {'min_per_tick': 0.01, 'max_per_tick': 0.01}
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(HumanSpawnSystem())
            sim.register_system(HealthSystem())
            sim._initialize_new_simulation(config)
            
            # Get entity and add pressure
            entities = sim.world_state.get_all_entities()
            entity = list(entities.values())[0]
            pressure = entity.get_component('Pressure')
            pressure.add_pressure('food', 100.0)  # High pressure
            
            health = entity.get_component('Health')
            initial_health = health.health
            
            # Run one tick
            sim.run(max_ticks=1)
            
            # Health should be reduced
            assert health.health < initial_health
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_death_from_health(self):
        """Test entity dies when health reaches 0."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2024-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': [
                    'HumanSpawnSystem',
                    'DeathSystem'
                ],
                'resources': [],
                'systems_config': {
                    'HumanSpawnSystem': {
                        'enabled': True,
                        'initial_population': 1,
                        'seed_crew': {
                            'age_range': [20, 30],
                            'components': {
                                'Needs': 100,
                                'Health': 100,
                                'Age': 100
                            }
                        }
                    },
                    'DeathSystem': {
                        'enabled': True
                    }
                }
            }
            
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim.register_system(HumanSpawnSystem())
            sim.register_system(DeathSystem())
            sim._initialize_new_simulation(config)
            
            # Get entity and set health to 0
            entities = sim.world_state.get_all_entities()
            assert len(entities) == 1
            entity = list(entities.values())[0]
            health = entity.get_component('Health')
            health.take_damage(1.0)  # Kill entity
            
            # Run one tick
            sim.run(max_ticks=1)
            
            # Entity should be removed
            entities_after = sim.world_state.get_all_entities()
            assert len(entities_after) == 0
            
        finally:
            if db_path.exists():
                db_path.unlink()

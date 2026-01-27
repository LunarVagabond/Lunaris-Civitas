"""Integration tests for simulation with entities and requirements."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from src.engine.simulation import Simulation
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.wealth import WealthComponent
from src.models.components.pressure import PressureComponent
from src.models.resource import Resource
from src.systems.human.requirement_resolver import RequirementResolverSystem


class TestSimulationWithEntities:
    """Integration tests for simulation with entities."""
    
    def test_entity_persistence_across_save_load(self):
        """Test that entities persist across save/load cycles."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            config = {
                'simulation': {
                    'start_datetime': '2020-01-01T00:00:00',
                    'db_path': str(db_path)
                },
                'systems': [],
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
                'systems_config': {}
            }
            
            # Create simulation and add entity
            sim = Simulation(config_path=None, db_path=db_path, resume=False)
            sim._initialize_new_simulation(config)
            
            entity = sim.world_state.create_entity(entity_id="test-entity")
            entity.add_component(NeedsComponent(hunger=0.5))
            entity.add_component(InventoryComponent(resources={'food': 10.0}))
            
            # Save world state
            from src.persistence.database import Database
            db = Database(db_path)
            db.connect()
            db.save_world_state(sim.world_state)
            db.close()
            
            # Create new simulation and load
            sim2 = Simulation(config_path=None, db_path=db_path, resume=True)
            sim2.register_system(RequirementResolverSystem())
            sim2._resume_simulation()
            
            # Verify entity exists
            loaded_entity = sim2.world_state.get_entity("test-entity")
            assert loaded_entity is not None
            assert loaded_entity.has_component("Needs")
            assert loaded_entity.has_component("Inventory")
            assert loaded_entity.get_component("Needs").hunger == 0.5
            assert loaded_entity.get_component("Inventory").get_amount('food') == 10.0
            
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_requirement_resolver_with_inventory_source(self):
        """Test requirement resolver with inventory source."""
        config = {
            'simulation': {
                'start_datetime': '2020-01-01T00:00:00'
            },
            'systems': ['RequirementResolver'],
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
                'RequirementResolver': {
                    'requirement_sources': {
                        'food': [
                            {
                                'source_id': 'inventory',
                                'source_type': 'inventory',
                                'priority': 1,
                                'conditions': {'has_component': 'Inventory'},
                                'requirements': {},
                                'fulfillment_method': 'consume_from_inventory'
                            }
                        ]
                    }
                }
            }
        }
        
        sim = Simulation(config_path=None, db_path=None, resume=False)
        sim.register_system(RequirementResolverSystem())
        sim._initialize_new_simulation(config)
        
        # Create entity with inventory
        entity = sim.world_state.create_entity()
        entity.add_component(InventoryComponent(resources={'food': 10.0}))
        
        # Get requirement resolver
        resolver = sim.world_state.get_system('RequirementResolver')
        assert resolver is not None
        
        # Resolve requirement
        resolution = resolver.resolve_requirement(
            entity, 'food', 5.0, sim.world_state
        )
        
        assert resolution.success
        assert resolution.source_id == 'inventory'
        assert resolution.amount_fulfilled == 5.0
        
        # Verify inventory was consumed
        inventory = entity.get_component('Inventory')
        assert inventory.get_amount('food') == 5.0
    
    def test_requirement_resolver_with_market_source(self):
        """Test requirement resolver with market source."""
        config = {
            'simulation': {
                'start_datetime': '2020-01-01T00:00:00'
            },
            'systems': ['RequirementResolver'],
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
                'RequirementResolver': {
                    'requirement_sources': {
                        'food': [
                            {
                                'source_id': 'market',
                                'source_type': 'market',
                                'priority': 1,
                                'conditions': {'has_component': 'Wealth'},
                                'requirements': {'money': 5.0},
                                'fulfillment_method': 'purchase_from_market'
                            }
                        ]
                    }
                }
            }
        }
        
        sim = Simulation(config_path=None, db_path=None, resume=False)
        sim.register_system(RequirementResolverSystem())
        sim._initialize_new_simulation(config)
        
        # Create entity with wealth
        entity = sim.world_state.create_entity()
        entity.add_component(WealthComponent(money=100.0))
        
        # Get requirement resolver
        resolver = sim.world_state.get_system('RequirementResolver')
        
        # Resolve requirement (need 10 units * 5.0 = 50.0 money)
        resolution = resolver.resolve_requirement(
            entity, 'food', 10.0, sim.world_state
        )
        
        assert resolution.success
        assert resolution.source_id == 'market'
        assert resolution.amount_fulfilled == 10.0
        
        # Verify money was spent
        wealth = entity.get_component('Wealth')
        assert wealth.money == 50.0
        
        # Verify global resource was consumed
        food_resource = sim.world_state.get_resource('food')
        assert food_resource.current_amount == 990.0
    
    def test_requirement_resolver_creates_pressure_on_failure(self):
        """Test that failed requirements create pressure."""
        config = {
            'simulation': {
                'start_datetime': '2020-01-01T00:00:00'
            },
            'systems': ['RequirementResolver'],
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
                'RequirementResolver': {
                    'requirement_sources': {
                        'food': [
                            {
                                'source_id': 'inventory',
                                'source_type': 'inventory',
                                'priority': 1,
                                'conditions': {'has_component': 'Inventory'},
                                'requirements': {},
                                'fulfillment_method': 'consume_from_inventory'
                            }
                        ]
                    }
                }
            }
        }
        
        sim = Simulation(config_path=None, db_path=None, resume=False)
        sim.register_system(RequirementResolverSystem())
        sim._initialize_new_simulation(config)
        
        # Create entity without inventory
        entity = sim.world_state.create_entity()
        entity.add_component(PressureComponent())
        
        # Get requirement resolver
        resolver = sim.world_state.get_system('RequirementResolver')
        
        # Try to resolve requirement (should fail)
        resolution = resolver.resolve_requirement(
            entity, 'food', 10.0, sim.world_state
        )
        
        assert not resolution.success
        assert resolution.amount_fulfilled == 0.0
        
        # Add pressure manually (in real system, this would be done by the calling system)
        pressure = entity.get_component('Pressure')
        pressure.add_pressure('food', resolution.unmet_pressure)
        
        assert pressure.get_pressure('food') == 10.0
        assert pressure.pressure_level > 0.0

"""Unit tests for database entity persistence."""

import tempfile
import pytest
from pathlib import Path
from datetime import datetime

from src.persistence.database import Database
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.health import HealthComponent


class TestDatabaseEntities:
    """Test database entity persistence."""
    
    def test_save_and_load_entities(self):
        """Test saving and loading entities."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            # Create world state with entities
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2020, 1, 1)),
                config_snapshot={}
            )
            
            entity1 = world_state.create_entity(entity_id="test-1")
            entity1.add_component(NeedsComponent(hunger=0.5))
            entity1.add_component(InventoryComponent(resources={'food': 10.0}))
            
            entity2 = world_state.create_entity(entity_id="test-2")
            entity2.add_component(HealthComponent(health=0.8))
            
            # Save world state
            db.save_world_state(world_state)
            
            # Load world state
            loaded = db.load_world_state()
            
            # Verify entities
            assert len(loaded.get_all_entities()) == 2
            
            loaded_entity1 = loaded.get_entity("test-1")
            assert loaded_entity1 is not None
            assert loaded_entity1.has_component("Needs")
            assert loaded_entity1.has_component("Inventory")
            assert loaded_entity1.get_component("Needs").hunger == 0.5
            assert loaded_entity1.get_component("Inventory").get_amount('food') == 10.0
            
            loaded_entity2 = loaded.get_entity("test-2")
            assert loaded_entity2 is not None
            assert loaded_entity2.has_component("Health")
            assert loaded_entity2.get_component("Health").health == 0.8
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_save_entities_overwrites_previous(self):
        """Test that saving entities overwrites previous entities."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            # Create and save first world state
            world_state1 = WorldState(
                simulation_time=SimulationTime(datetime(2020, 1, 1)),
                config_snapshot={}
            )
            entity1 = world_state1.create_entity(entity_id="test-1")
            entity1.add_component(NeedsComponent())
            db.save_world_state(world_state1)
            
            # Create and save second world state
            world_state2 = WorldState(
                simulation_time=SimulationTime(datetime(2020, 1, 2)),
                config_snapshot={}
            )
            entity2 = world_state2.create_entity(entity_id="test-2")
            entity2.add_component(HealthComponent())
            db.save_world_state(world_state2)
            
            # Load and verify only second entity exists
            loaded = db.load_world_state()
            assert len(loaded.get_all_entities()) == 1
            assert loaded.get_entity("test-1") is None
            assert loaded.get_entity("test-2") is not None
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_load_empty_entities(self):
        """Test loading world state with no entities."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2020, 1, 1)),
                config_snapshot={}
            )
            db.save_world_state(world_state)
            
            loaded = db.load_world_state()
            assert len(loaded.get_all_entities()) == 0
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()

"""Unit tests for WorldState entity methods."""

import pytest
from datetime import datetime

from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.health import HealthComponent


class TestWorldStateEntities:
    """Test WorldState entity management methods."""
    
    def test_create_entity(self):
        """Test creating an entity through world state."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity = world_state.create_entity()
        assert entity.entity_id is not None
        assert world_state.get_entity(entity.entity_id) == entity
    
    def test_create_entity_with_id(self):
        """Test creating entity with specific ID."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity = world_state.create_entity(entity_id="test-123")
        assert entity.entity_id == "test-123"
        assert world_state.get_entity("test-123") == entity
    
    def test_add_entity(self):
        """Test adding an entity to world state."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity = Entity(entity_id="test-123")
        world_state.add_entity(entity)
        
        assert world_state.get_entity("test-123") == entity
    
    def test_add_duplicate_entity_raises(self):
        """Test that adding duplicate entity raises error."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity1 = Entity(entity_id="test-123")
        entity2 = Entity(entity_id="test-123")
        
        world_state.add_entity(entity1)
        with pytest.raises(ValueError, match="already exists"):
            world_state.add_entity(entity2)
    
    def test_remove_entity(self):
        """Test removing an entity."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity = world_state.create_entity(entity_id="test-123")
        removed = world_state.remove_entity("test-123")
        
        assert removed == entity
        assert world_state.get_entity("test-123") is None
    
    def test_get_all_entities(self):
        """Test getting all entities."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity1 = world_state.create_entity(entity_id="test-1")
        entity2 = world_state.create_entity(entity_id="test-2")
        
        all_entities = world_state.get_all_entities()
        assert len(all_entities) == 2
        assert "test-1" in all_entities
        assert "test-2" in all_entities
    
    def test_query_entities_by_component(self):
        """Test querying entities by component type."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity1 = world_state.create_entity(entity_id="test-1")
        entity1.add_component(NeedsComponent())
        
        entity2 = world_state.create_entity(entity_id="test-2")
        entity2.add_component(InventoryComponent())
        
        entity3 = world_state.create_entity(entity_id="test-3")
        entity3.add_component(NeedsComponent())
        
        entities_with_needs = world_state.query_entities_by_component("Needs")
        assert len(entities_with_needs) == 2
        assert entity1 in entities_with_needs
        assert entity3 in entities_with_needs
        assert entity2 not in entities_with_needs
    
    def test_query_entities_by_components(self):
        """Test querying entities by multiple component types."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity1 = world_state.create_entity(entity_id="test-1")
        entity1.add_component(NeedsComponent())
        entity1.add_component(HealthComponent())
        
        entity2 = world_state.create_entity(entity_id="test-2")
        entity2.add_component(NeedsComponent())
        
        entity3 = world_state.create_entity(entity_id="test-3")
        entity3.add_component(NeedsComponent())
        entity3.add_component(HealthComponent())
        
        entities = world_state.query_entities_by_components(["Needs", "Health"])
        assert len(entities) == 2
        assert entity1 in entities
        assert entity3 in entities
        assert entity2 not in entities
    
    def test_world_state_serialization_with_entities(self):
        """Test world state serialization includes entities."""
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        entity = world_state.create_entity(entity_id="test-123")
        entity.add_component(NeedsComponent(hunger=0.5))
        
        data = world_state.to_dict()
        assert "entities" in data
        assert "test-123" in data["entities"]
        
        # Test deserialization
        restored = WorldState.from_dict(data)
        restored_entity = restored.get_entity("test-123")
        assert restored_entity is not None
        assert restored_entity.has_component("Needs")
        assert restored_entity.get_component("Needs").hunger == 0.5

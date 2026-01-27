"""Unit tests for Entity class."""

import pytest

from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.health import HealthComponent


class TestEntity:
    """Test Entity class."""
    
    def test_entity_creation(self):
        """Test creating an entity."""
        entity = Entity()
        assert entity.entity_id is not None
        assert len(entity.entity_id) > 0
        
        entity = Entity(entity_id="test-123")
        assert entity.entity_id == "test-123"
    
    def test_add_component(self):
        """Test adding components to entity."""
        entity = Entity()
        needs = NeedsComponent()
        
        entity.add_component(needs)
        assert entity.has_component("Needs")
        assert entity.get_component("Needs") == needs
    
    def test_add_duplicate_component_raises(self):
        """Test that adding duplicate component raises error."""
        entity = Entity()
        needs1 = NeedsComponent()
        needs2 = NeedsComponent()
        
        entity.add_component(needs1)
        with pytest.raises(ValueError, match="already has component"):
            entity.add_component(needs2)
    
    def test_replace_component(self):
        """Test replacing existing component."""
        entity = Entity()
        needs1 = NeedsComponent(hunger=0.5)
        needs2 = NeedsComponent(hunger=0.8)
        
        entity.add_component(needs1)
        entity.replace_component(needs2)
        
        assert entity.get_component("Needs").hunger == 0.8
    
    def test_remove_component(self):
        """Test removing components."""
        entity = Entity()
        needs = NeedsComponent()
        
        entity.add_component(needs)
        removed = entity.remove_component("Needs")
        
        assert removed == needs
        assert not entity.has_component("Needs")
        assert entity.remove_component("Needs") is None
    
    def test_get_component_typed(self):
        """Test getting component with type checking."""
        entity = Entity()
        needs = NeedsComponent()
        
        entity.add_component(needs)
        retrieved = entity.get_component_typed("Needs", NeedsComponent)
        assert retrieved == needs
        
        with pytest.raises(TypeError):
            entity.get_component_typed("Needs", InventoryComponent)
    
    def test_get_all_components(self):
        """Test getting all components."""
        entity = Entity()
        needs = NeedsComponent()
        inventory = InventoryComponent()
        
        entity.add_component(needs)
        entity.add_component(inventory)
        
        all_components = entity.get_all_components()
        assert len(all_components) == 2
        assert "Needs" in all_components
        assert "Inventory" in all_components
    
    def test_get_component_types(self):
        """Test getting component types."""
        entity = Entity()
        entity.add_component(NeedsComponent())
        entity.add_component(InventoryComponent())
        
        types = entity.get_component_types()
        assert "Needs" in types
        assert "Inventory" in types
        assert len(types) == 2
    
    def test_entity_serialization(self):
        """Test entity serialization."""
        entity = Entity(entity_id="test-123")
        entity.add_component(NeedsComponent(hunger=0.5))
        entity.add_component(InventoryComponent(resources={'food': 10.0}))
        
        data = entity.to_dict()
        assert data['entity_id'] == "test-123"
        assert "Needs" in data['components']
        assert "Inventory" in data['components']
        
        restored = Entity.from_dict(data)
        assert restored.entity_id == "test-123"
        assert restored.has_component("Needs")
        assert restored.has_component("Inventory")
        assert restored.get_component("Needs").hunger == 0.5
        assert restored.get_component("Inventory").get_amount('food') == 10.0

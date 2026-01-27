"""Unit tests for Component base class and registry."""

import pytest

from src.models.component import Component
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent


class TestComponent:
    """Test Component base class."""
    
    def test_component_type_property(self):
        """Test component_type property."""
        assert NeedsComponent.component_type() == "Needs"
        assert InventoryComponent.component_type() == "Inventory"
    
    def test_component_registration(self):
        """Test that components are automatically registered."""
        registered_types = Component.get_all_registered_types()
        assert "Needs" in registered_types
        assert "Inventory" in registered_types
    
    def test_get_component_class(self):
        """Test getting component class by type."""
        comp_class = Component.get_component_class("Needs")
        assert comp_class == NeedsComponent
        
        comp_class = Component.get_component_class("Inventory")
        assert comp_class == InventoryComponent
        
        comp_class = Component.get_component_class("Unknown")
        assert comp_class is None
    
    def test_create_component(self):
        """Test creating component instance from type and data."""
        data = {'hunger': 0.5, 'thirst': 0.3, 'rest': 0.2}
        component = Component.create_component("Needs", data)
        assert isinstance(component, NeedsComponent)
        assert component.hunger == 0.5
        assert component.thirst == 0.3
        
        component = Component.create_component("Unknown", {})
        assert component is None
    
    def test_component_serialization(self):
        """Test component serialization."""
        needs = NeedsComponent(hunger=0.5, thirst=0.3)
        data = needs.to_dict()
        assert data['hunger'] == 0.5
        assert data['thirst'] == 0.3
        
        restored = NeedsComponent.from_dict(data)
        assert restored.hunger == 0.5
        assert restored.thirst == 0.3

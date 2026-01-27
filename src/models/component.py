"""Base component class for Entity Component System.

All components must inherit from Component and implement serialization methods.
Components are registered by their component_type for dynamic instantiation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Type, Optional


# Component registry: component_type -> Component class
_component_registry: Dict[str, Type['Component']] = {}


class Component(ABC):
    """Base class for all components.
    
    Components are data containers attached to entities. They must:
    1. Have a unique component_type (class property)
    2. Implement to_dict() for serialization
    3. Implement from_dict() for deserialization
    
    Components are automatically registered by their component_type when
    the class is defined.
    """
    
    def __init_subclass__(cls, **kwargs):
        """Register component class when subclassed."""
        super().__init_subclass__(**kwargs)
        # Only register if component_type is implemented (not abstract)
        try:
            component_type = cls.component_type()
            if component_type in _component_registry:
                raise ValueError(
                    f"Component type '{component_type}' is already registered by "
                    f"{_component_registry[component_type].__name__}"
                )
            _component_registry[component_type] = cls
        except (AttributeError, TypeError):
            # Abstract base class - skip registration
            pass
    
    @classmethod
    @abstractmethod
    def component_type(cls) -> str:
        """Get the unique component type identifier.
        
        Returns:
            Unique component type string (e.g., "Needs", "Inventory", "Health")
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary.
        
        Returns:
            Dictionary representation of component
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Deserialize component from dictionary.
        
        Args:
            data: Dictionary containing component data
            
        Returns:
            Component instance restored from data
        """
        pass
    
    @classmethod
    def get_component_class(cls, component_type: str) -> Optional[Type['Component']]:
        """Get component class by type.
        
        Args:
            component_type: Component type identifier
            
        Returns:
            Component class or None if not found
        """
        return _component_registry.get(component_type)
    
    @classmethod
    def create_component(cls, component_type: str, data: Dict[str, Any]) -> Optional['Component']:
        """Create a component instance from type and data.
        
        Args:
            component_type: Component type identifier
            data: Component data dictionary
            
        Returns:
            Component instance or None if type not found
        """
        comp_class = _component_registry.get(component_type)
        if comp_class is None:
            return None
        return comp_class.from_dict(data)
    
    @classmethod
    def get_all_registered_types(cls) -> list[str]:
        """Get all registered component types.
        
        Returns:
            List of registered component type strings
        """
        return [comp_class.component_type() for comp_class in _component_registry.values()]

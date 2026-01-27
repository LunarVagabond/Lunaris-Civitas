"""Entity class for Entity Component System.

Entities are containers for components. They have a unique ID and can have
multiple components attached to them.
"""

import uuid
from typing import Dict, Optional, Type, TypeVar, List, Any

from src.models.component import Component

T = TypeVar('T', bound=Component)


class Entity:
    """Represents an entity in the simulation.
    
    Entities are containers for components. They have:
    - A unique entity_id
    - A collection of components (component_type -> Component instance)
    
    Entities can be queried by component type, and components can be
    added/removed dynamically.
    """
    
    def __init__(self, entity_id: Optional[str] = None):
        """Initialize an entity.
        
        Args:
            entity_id: Optional unique identifier. If None, generates a UUID.
        """
        if entity_id is None:
            entity_id = str(uuid.uuid4())
        self.entity_id = entity_id
        self._components: Dict[str, Component] = {}
    
    def add_component(self, component: Component) -> None:
        """Add a component to the entity.
        
        Args:
            component: Component instance to add
            
        Raises:
            ValueError: If component type already exists (use replace_component to overwrite)
        """
        comp_type = component.__class__.component_type()
        if comp_type in self._components:
            raise ValueError(
                f"Entity {self.entity_id} already has component type '{comp_type}'. "
                f"Use replace_component() to overwrite."
            )
        self._components[comp_type] = component
    
    def replace_component(self, component: Component) -> None:
        """Replace an existing component or add if it doesn't exist.
        
        Args:
            component: Component instance to add/replace
        """
        comp_type = component.__class__.component_type()
        self._components[comp_type] = component
    
    def remove_component(self, component_type: str) -> Optional[Component]:
        """Remove a component from the entity.
        
        Args:
            component_type: Component type to remove
            
        Returns:
            Removed component or None if not found
        """
        return self._components.pop(component_type, None)
    
    def get_component(self, component_type: str) -> Optional[Component]:
        """Get a component by type.
        
        Args:
            component_type: Component type identifier
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(component_type)
    
    def get_component_typed(self, component_type: str, component_class: Type[T]) -> Optional[T]:
        """Get a component by type with type checking.
        
        Args:
            component_type: Component type identifier
            component_class: Expected component class for type checking
            
        Returns:
            Component instance of specified type or None if not found
            
        Raises:
            TypeError: If component exists but is not of the expected type
        """
        component = self._components.get(component_type)
        if component is None:
            return None
        if not isinstance(component, component_class):
            raise TypeError(
                f"Component '{component_type}' is not an instance of {component_class.__name__}"
            )
        return component
    
    def has_component(self, component_type: str) -> bool:
        """Check if entity has a component of the given type.
        
        Args:
            component_type: Component type identifier
            
        Returns:
            True if component exists, False otherwise
        """
        return component_type in self._components
    
    def get_all_components(self) -> Dict[str, Component]:
        """Get all components attached to this entity.
        
        Returns:
            Dictionary mapping component_type -> Component instance
        """
        return self._components.copy()
    
    def get_component_types(self) -> List[str]:
        """Get all component types attached to this entity.
        
        Returns:
            List of component type strings
        """
        return list(self._components.keys())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entity to dictionary.
        
        Returns:
            Dictionary representation of entity
        """
        return {
            'entity_id': self.entity_id,
            'components': {
                comp_type: comp.to_dict()
                for comp_type, comp in self._components.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Entity':
        """Deserialize entity from dictionary.
        
        Args:
            data: Dictionary containing entity data
            
        Returns:
            Entity instance restored from data
        """
        entity = cls(entity_id=data['entity_id'])
        
        # Restore components
        for comp_type, comp_data in data.get('components', {}).items():
            component = Component.create_component(comp_type, comp_data)
            if component is None:
                raise ValueError(f"Unknown component type: {comp_type}")
            entity._components[comp_type] = component
        
        return entity
    
    def __repr__(self) -> str:
        """String representation of entity."""
        comp_types = ', '.join(self.get_component_types())
        return f"Entity(entity_id={self.entity_id}, components=[{comp_types}])"

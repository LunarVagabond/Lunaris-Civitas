"""World state container for the simulation.

The world state represents the entire simulation universe and must be
fully reconstructible from SQLite alone.
"""

import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier
from src.models.entity import Entity
from src.models.component import Component
from src.core.system import System


class WorldState:
    """Container for all simulation state.
    
    The world state includes:
    - Current simulation datetime and time tracking
    - RNG seed and state
    - Config snapshot (from initialization)
    - Registered systems
    - Global resources
    - Active and scheduled modifiers
    - Entities (with components)
    """
    
    def __init__(
        self,
        simulation_time: SimulationTime,
        config_snapshot: Dict[str, Any],
        rng_seed: Optional[int] = None
    ):
        """Initialize world state.
        
        Args:
            simulation_time: SimulationTime instance
            config_snapshot: Snapshot of configuration used to initialize
            rng_seed: Optional RNG seed for determinism
        """
        self.simulation_time = simulation_time
        self.config_snapshot = config_snapshot.copy()  # Store copy to prevent mutation
        
        # Initialize RNG
        if rng_seed is not None:
            self.rng_seed = rng_seed
            self.rng = random.Random(rng_seed)
        else:
            self.rng_seed = None
            self.rng = random.Random()
        
        # Systems registry: system_id -> System instance
        self._systems: Dict[str, System] = {}
        
        # Resources: resource_id -> Resource instance
        self._resources: Dict[str, Resource] = {}
        
        # Modifiers: modifier_id -> Modifier instance
        self._modifiers: Dict[str, Modifier] = {}
        
        # Entities: entity_id -> Entity instance
        self._entities: Dict[str, Entity] = {}
    
    def register_system(self, system: System) -> None:
        """Register a system with the world state.
        
        Args:
            system: System instance to register
            
        Raises:
            ValueError: If system_id already exists
        """
        if system.system_id in self._systems:
            raise ValueError(f"System {system.system_id} is already registered")
        
        self._systems[system.system_id] = system
    
    def get_system(self, system_id: str) -> Optional[System]:
        """Get a registered system by ID.
        
        Args:
            system_id: System identifier
            
        Returns:
            System instance or None if not found
        """
        return self._systems.get(system_id)
    
    def get_all_systems(self) -> List[System]:
        """Get all registered systems.
        
        Returns:
            List of all registered systems
        """
        return list(self._systems.values())
    
    def add_resource(self, resource: Resource) -> None:
        """Add a resource to the world state.
        
        Args:
            resource: Resource instance to add
            
        Raises:
            ValueError: If resource ID already exists
        """
        if resource.id in self._resources:
            raise ValueError(f"Resource {resource.id} already exists")
        
        self._resources[resource.id] = resource
    
    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource instance or None if not found
        """
        return self._resources.get(resource_id)
    
    def get_all_resources(self) -> Dict[str, Resource]:
        """Get all resources.
        
        Returns:
            Dictionary of resource_id -> Resource
        """
        return self._resources.copy()
    
    def add_modifier(self, modifier: Modifier) -> None:
        """Add a modifier to the world state.
        
        Args:
            modifier: Modifier instance to add
            
        Raises:
            ValueError: If modifier ID already exists
        """
        if modifier.id in self._modifiers:
            raise ValueError(f"Modifier {modifier.id} already exists")
        
        self._modifiers[modifier.id] = modifier
    
    def remove_modifier(self, modifier_id: str) -> None:
        """Remove a modifier from the world state.
        
        Args:
            modifier_id: Modifier identifier
        """
        self._modifiers.pop(modifier_id, None)
    
    def get_modifier(self, modifier_id: str) -> Optional[Modifier]:
        """Get a modifier by ID.
        
        Args:
            modifier_id: Modifier identifier
            
        Returns:
            Modifier instance or None if not found
        """
        return self._modifiers.get(modifier_id)
    
    def get_active_modifiers(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None
    ) -> List[Modifier]:
        """Get all active modifiers, optionally filtered by target.
        
        Args:
            target_type: Optional filter by target type ('system', 'resource', 'category')
            target_id: Optional filter by target ID
            
        Returns:
            List of active modifiers matching the criteria
        """
        current_datetime = self.simulation_time.current_datetime
        active = [
            mod for mod in self._modifiers.values()
            if mod.is_active(current_datetime)
        ]
        
        if target_type:
            active = [mod for mod in active if mod.target_type == target_type]
        
        if target_id:
            active = [mod for mod in active if mod.target_id == target_id]
        
        return active
    
    def get_modifiers_for_system(self, system_id: str) -> List[Modifier]:
        """Get all active modifiers targeting a specific system.
        
        Args:
            system_id: System identifier
            
        Returns:
            List of active modifiers targeting the system
        """
        return self.get_active_modifiers(target_type='system', target_id=system_id)
    
    def get_modifiers_for_resource(self, resource_id: str) -> List[Modifier]:
        """Get all active modifiers targeting a specific resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            List of active modifiers targeting the resource
        """
        current_datetime = self.simulation_time.current_datetime
        active = []
        
        for mod in self._modifiers.values():
            if mod.resource_id == resource_id and mod.is_active(current_datetime):
                active.append(mod)
        
        return active
    
    def get_modifiers_by_name(self, modifier_name: str) -> List[Modifier]:
        """Get all modifiers with a given name (groups related rows).
        
        Args:
            modifier_name: Modifier name to search for
            
        Returns:
            List of modifiers with the given name
        """
        modifiers = []
        for mod in self._modifiers.values():
            if hasattr(mod, 'modifier_name') and mod.modifier_name == modifier_name:
                modifiers.append(mod)
        return modifiers
    
    def cleanup_expired_modifiers(self) -> List[str]:
        """Cleanup expired modifiers from the world state.
        
        Modifiers are deactivated (not deleted) so repeat checking can still find them.
        When a modifier repeats, a new active record is created immediately, ensuring
        the modifier never "falls off" - seamless continuation.
        
        Returns:
            List of deactivated modifier IDs
        """
        current_datetime = self.simulation_time.current_datetime
        expired_ids = []
        
        for mod_id, mod in list(self._modifiers.items()):
            if mod.has_expired(current_datetime):
                # Deactivate (don't delete - may repeat)
                mod._is_active_flag = False
                expired_ids.append(mod_id)
        
        return expired_ids
    
    # Entity management methods
    
    def create_entity(self, entity_id: Optional[str] = None) -> Entity:
        """Create a new entity and register it with the world state.
        
        Args:
            entity_id: Optional unique identifier. If None, generates a UUID.
            
        Returns:
            Created Entity instance
            
        Raises:
            ValueError: If entity_id already exists
        """
        entity = Entity(entity_id=entity_id)
        if entity.entity_id in self._entities:
            raise ValueError(f"Entity {entity.entity_id} already exists")
        self._entities[entity.entity_id] = entity
        return entity
    
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the world state.
        
        Args:
            entity: Entity instance to add
            
        Raises:
            ValueError: If entity ID already exists
        """
        if entity.entity_id in self._entities:
            raise ValueError(f"Entity {entity.entity_id} already exists")
        self._entities[entity.entity_id] = entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Entity instance or None if not found
        """
        return self._entities.get(entity_id)
    
    def remove_entity(self, entity_id: str) -> Optional[Entity]:
        """Remove an entity from the world state.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Removed Entity instance or None if not found
        """
        return self._entities.pop(entity_id, None)
    
    def get_all_entities(self) -> Dict[str, Entity]:
        """Get all entities.
        
        Returns:
            Dictionary of entity_id -> Entity
        """
        return self._entities.copy()
    
    def query_entities_by_component(self, component_type: str) -> List[Entity]:
        """Query entities that have a specific component type.
        
        Args:
            component_type: Component type to search for
            
        Returns:
            List of entities that have the component
        """
        return [
            entity for entity in self._entities.values()
            if entity.has_component(component_type)
        ]
    
    def query_entities_by_components(self, component_types: List[str]) -> List[Entity]:
        """Query entities that have all of the specified component types.
        
        Args:
            component_types: List of component types to search for
            
        Returns:
            List of entities that have all the specified components
        """
        return [
            entity for entity in self._entities.values()
            if all(entity.has_component(comp_type) for comp_type in component_types)
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize world state to dictionary.
        
        Returns:
            Dictionary representation of world state
        """
        return {
            'simulation_time': self.simulation_time.to_dict(),
            'rng_seed': self.rng_seed,
            'config_snapshot': self.config_snapshot,
            'resources': {rid: res.to_dict() for rid, res in self._resources.items()},
            'modifiers': {mid: mod.to_dict() for mid, mod in self._modifiers.items()},
            'entities': {eid: entity.to_dict() for eid, entity in self._entities.items()},
            'systems': list(self._systems.keys())  # Only store IDs, not instances
        }
    
    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        systems_registry: Optional[Dict[str, System]] = None
    ) -> 'WorldState':
        """Deserialize world state from dictionary.
        
        Args:
            data: Dictionary containing world state data
            systems_registry: Optional dictionary of system_id -> System to restore systems
            
        Returns:
            WorldState instance restored from data
        """
        simulation_time = SimulationTime.from_dict(data['simulation_time'])
        
        world_state = cls(
            simulation_time=simulation_time,
            config_snapshot=data['config_snapshot'],
            rng_seed=data.get('rng_seed')
        )
        
        # Restore resources
        for res_data in data['resources'].values():
            resource = Resource.from_dict(res_data)
            world_state._resources[resource.id] = resource
        
        # Restore modifiers
        for mod_data in data['modifiers'].values():
            modifier = Modifier.from_dict(mod_data)
            world_state._modifiers[modifier.id] = modifier
        
        # Restore entities
        for entity_data in data.get('entities', {}).values():
            entity = Entity.from_dict(entity_data)
            world_state._entities[entity.entity_id] = entity
        
        # Restore systems (if registry provided)
        if systems_registry:
            for system_id in data.get('systems', []):
                if system_id in systems_registry:
                    world_state._systems[system_id] = systems_registry[system_id]
        
        return world_state

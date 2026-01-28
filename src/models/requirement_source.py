"""Requirement source definition for fulfilling resource requirements.

Each source defines how a resource requirement can be fulfilled, including
conditions (when available) and requirements (what's needed).
"""

from typing import Dict, Any, Optional, Tuple

from src.models.entity import Entity
from src.core.world_state import WorldState


class RequirementSource:
    """Defines a source for fulfilling a resource requirement.
    
    Each source has:
    - Conditions (when this source is available)
    - Requirements (what's needed to use this source)
    - Priority (order to try sources)
    - Fulfillment method (how to fulfill)
    """
    
    def __init__(
        self,
        source_id: str,
        source_type: str,  # "inventory", "household", "market", "production"
        priority: int,
        conditions: Dict[str, Any],  # e.g., {"has_component": "Inventory"}
        requirements: Dict[str, float],  # e.g., {"money": 5.0}
        fulfillment_method: str  # How to fulfill: "consume", "purchase", "produce"
    ):
        """Initialize requirement source.
        
        Args:
            source_id: Unique source identifier
            source_type: Type of source ("inventory", "household", "market", "production")
            priority: Priority order (lower = tried first)
            conditions: Conditions for availability (e.g., {"has_component": "Inventory"})
            requirements: Requirements to use this source (e.g., {"money": 5.0})
            fulfillment_method: Method name for fulfillment
        """
        self.source_id = source_id
        self.source_type = source_type
        self.priority = priority
        self.conditions = conditions
        self.requirements = requirements
        self.fulfillment_method = fulfillment_method
    
    def is_available(self, entity: Entity, world_state: WorldState) -> bool:
        """Check if this source is available for the entity.
        
        Args:
            entity: Entity to check
            world_state: World state for context
            
        Returns:
            True if source is available, False otherwise
        """
        # Check has_component condition
        if 'has_component' in self.conditions:
            comp_type = self.conditions['has_component']
            if not entity.has_component(comp_type):
                return False
        
        # Check employment_type condition (for production sources)
        if 'employment_type' in self.conditions:
            employment = entity.get_component('Employment')
            if employment is None:
                return False
            if hasattr(employment, 'job_type'):
                if employment.job_type != self.conditions['employment_type']:
                    return False
        
        # Check household_id condition (for household sources)
        if 'has_household' in self.conditions:
            household = entity.get_component('Household')
            if household is None:
                return False
        
        return True
    
    def can_fulfill(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        world_state: WorldState
    ) -> Tuple[bool, Optional[str]]:
        """Check if this source can fulfill the requirement.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            world_state: World state for context
            
        Returns:
            (can_fulfill: bool, reason: Optional[str])
        """
        # Check if source is available
        if not self.is_available(entity, world_state):
            return False, f"Source {self.source_id} not available"
        
        # Check source-specific availability
        if self.source_type == 'inventory':
            # Inventory source - check if entity has the resource
            inventory = entity.get_component('Inventory')
            if inventory is None:
                return False, f"No Inventory component"
            available = inventory.get_amount(resource_id)
            if available < amount:
                return False, f"Insufficient {resource_id} in inventory: need {amount}, have {available}"
        
        elif self.source_type == 'household':
            # Household source - check if household has the resource
            household = entity.get_component('Household')
            if household is None:
                return False, f"No Household component"
            # Get household entity
            household_id = getattr(household, 'household_id', None)
            if household_id is None:
                return False, f"No household_id in Household component"
            household_entity = world_state.get_entity(household_id)
            if household_entity is None:
                return False, f"Household entity {household_id} not found"
            household_inventory = household_entity.get_component('Inventory')
            if household_inventory is None:
                return False, f"Household has no Inventory component"
            available = household_inventory.get_amount(resource_id)
            if available < amount:
                return False, f"Insufficient {resource_id} in household: need {amount}, have {available}"
        
        # Check requirements are met (for market and production sources)
        for req_resource_id, req_amount in self.requirements.items():
            # Calculate total requirement (per unit * amount)
            total_required = req_amount * amount
            
            if self.source_type == 'market':
                # Market requires resources from Wealth component (money, crypto, or any resource type)
                wealth = entity.get_component('Wealth')
                if wealth is None:
                    return False, f"No Wealth component for market purchase"
                if not wealth.has_resource(req_resource_id, total_required):
                    available = wealth.get_amount(req_resource_id)
                    return False, f"Insufficient {req_resource_id}: need {total_required}, have {available}"
            
            elif self.source_type == 'production':
                # Production requires inputs from Inventory
                inventory = entity.get_component('Inventory')
                if inventory is None:
                    return False, f"No Inventory component for production"
                if not inventory.has_resource(req_resource_id, total_required):
                    available = inventory.get_amount(req_resource_id)
                    return False, f"Insufficient {req_resource_id}: need {total_required}, have {available}"
        
        return True, None

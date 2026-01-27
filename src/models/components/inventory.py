"""Inventory component for entities.

Stores personal resources owned by an entity.
"""

from typing import Dict, Optional

from src.models.component import Component


class InventoryComponent(Component):
    """Component representing entity's personal inventory.
    
    Stores personal resources (resource_id -> amount).
    Used by inventory source to check availability.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Inventory"
    
    def __init__(self, resources: Optional[Dict[str, float]] = None):
        """Initialize inventory component.
        
        Args:
            resources: Optional initial resources dict (resource_id -> amount)
        """
        self.resources: Dict[str, float] = resources.copy() if resources else {}
    
    def get_amount(self, resource_id: str) -> float:
        """Get amount of a resource in inventory.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Amount of resource (0.0 if not present)
        """
        return self.resources.get(resource_id, 0.0)
    
    def has_resource(self, resource_id: str, amount: float = 0.0) -> bool:
        """Check if inventory has enough of a resource.
        
        Args:
            resource_id: Resource identifier
            amount: Required amount (default: any amount > 0)
            
        Returns:
            True if has enough, False otherwise
        """
        return self.get_amount(resource_id) >= amount
    
    def add_resource(self, resource_id: str, amount: float) -> None:
        """Add resources to inventory.
        
        Args:
            resource_id: Resource identifier
            amount: Amount to add (must be >= 0)
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot add negative amount: {amount}")
        self.resources[resource_id] = self.resources.get(resource_id, 0.0) + amount
    
    def remove_resource(self, resource_id: str, amount: float) -> bool:
        """Remove resources from inventory.
        
        Args:
            resource_id: Resource identifier
            amount: Amount to remove (must be >= 0)
            
        Returns:
            True if removed successfully, False if insufficient resources
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot remove negative amount: {amount}")
        
        current = self.resources.get(resource_id, 0.0)
        if current < amount:
            return False
        
        self.resources[resource_id] = current - amount
        
        # Clean up zero amounts
        if self.resources[resource_id] == 0.0:
            del self.resources[resource_id]
        
        return True
    
    def get_all_resources(self) -> Dict[str, float]:
        """Get all resources in inventory.
        
        Returns:
            Dictionary mapping resource_id -> amount
        """
        return self.resources.copy()
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'resources': self.resources.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'InventoryComponent':
        """Deserialize component from dictionary."""
        return cls(resources=data.get('resources', {}))

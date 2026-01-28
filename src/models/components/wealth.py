"""Wealth component for entities.

Stores resources owned by an entity (money, crypto, or any other resource type).
Used by market source to check purchasing power and for general resource storage.
"""

from typing import Dict, Optional

from src.models.component import Component


class WealthComponent(Component):
    """Component representing entity wealth.
    
    Stores resources owned (resource_id -> amount). Can store money, crypto, or any resource type.
    Used by market source to check purchasing power and for general resource storage.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Wealth"
    
    def __init__(self, resources: Optional[Dict[str, float]] = None):
        """Initialize wealth component.
        
        Args:
            resources: Optional initial resources dict (resource_id -> amount)
                      If None, creates empty dict. For backward compat, can pass {'money': amount}
        """
        if resources is None:
            self.resources: Dict[str, float] = {}
        else:
            # Ensure all values are non-negative
            self.resources = {k: max(0.0, v) for k, v in resources.items()}
    
    def get_amount(self, resource_id: str) -> float:
        """Get amount of a resource in wealth.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Amount of resource (0.0 if not present)
        """
        return self.resources.get(resource_id, 0.0)
    
    def has_resource(self, resource_id: str, amount: float) -> bool:
        """Check if entity has enough of a resource.
        
        Args:
            resource_id: Resource identifier
            amount: Required amount
            
        Returns:
            True if has enough, False otherwise
        """
        return self.get_amount(resource_id) >= amount
    
    def add_resource(self, resource_id: str, amount: float) -> None:
        """Add amount of a resource.
        
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
        """Remove amount of a resource.
        
        Args:
            resource_id: Resource identifier
            amount: Amount to remove (must be >= 0)
            
        Returns:
            True if removed successfully, False if insufficient funds
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot remove negative amount: {amount}")
        
        current = self.resources.get(resource_id, 0.0)
        if current < amount:
            return False
        
        self.resources[resource_id] = current - amount
        if self.resources[resource_id] <= 0:
            # Remove key if zero or negative
            self.resources.pop(resource_id, None)
        return True
    
    def has_resources(self, requirements: Dict[str, float]) -> bool:
        """Check if entity has enough of all required resources.
        
        Args:
            requirements: Dictionary mapping resource_id -> required amount
            
        Returns:
            True if has enough of all resources, False otherwise
        """
        for resource_id, amount in requirements.items():
            if not self.has_resource(resource_id, amount):
                return False
        return True
    
    # Backward compatibility methods (deprecated - use get_amount/add_resource/remove_resource)
    @property
    def money(self) -> float:
        """Get money amount (backward compatibility)."""
        return self.get_amount('money')
    
    def add_money(self, amount: float) -> None:
        """Add money (backward compatibility)."""
        self.add_resource('money', amount)
    
    def remove_money(self, amount: float) -> bool:
        """Remove money (backward compatibility)."""
        return self.remove_resource('money', amount)
    
    def has_money(self, amount: float) -> bool:
        """Check if has enough money (backward compatibility)."""
        return self.has_resource('money', amount)
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'resources': self.resources.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'WealthComponent':
        """Deserialize component from dictionary."""
        # Handle both old format (money) and new format (resources)
        if 'resources' in data:
            return cls(resources=data['resources'])
        elif 'money' in data:
            # Backward compatibility
            return cls(resources={'money': data.get('money', 0.0)})
        else:
            return cls()

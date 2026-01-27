"""Household component for entities."""

from typing import Dict, Optional

from src.models.component import Component


class HouseholdComponent(Component):
    """Component linking entity to household entity.
    
    Used by household source to access shared resources.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Household"
    
    def __init__(self, household_id: str):
        """Initialize household component.
        
        Args:
            household_id: ID of the household entity
        """
        self.household_id = household_id
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'household_id': self.household_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'HouseholdComponent':
        """Deserialize component from dictionary."""
        return cls(household_id=data['household_id'])

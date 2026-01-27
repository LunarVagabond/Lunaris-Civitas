"""Needs component for entities.

Tracks hunger, thirst, and rest levels. Needs create resource requirements
that are fulfilled through RequirementResolver which checks multiple sources.
"""

from typing import Dict

from src.models.component import Component


class NeedsComponent(Component):
    """Component representing entity needs (hunger, thirst, rest).
    
    Needs create pressure on resources, but fulfillment happens through
    RequirementResolver which checks multiple sources.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Needs"
    
    def __init__(
        self,
        hunger: float = 0.0,
        thirst: float = 0.0,
        rest: float = 0.0,
        hunger_rate: float = 0.01,  # Per hour
        thirst_rate: float = 0.015,  # Per hour
        rest_rate: float = 0.005  # Per hour
    ):
        """Initialize needs component.
        
        Args:
            hunger: Hunger level (0.0 = full, 1.0 = starving)
            thirst: Thirst level (0.0 = hydrated, 1.0 = dehydrated)
            rest: Rest level (0.0 = rested, 1.0 = exhausted)
            hunger_rate: Rate at which hunger increases per hour
            thirst_rate: Rate at which thirst increases per hour
            rest_rate: Rate at which rest decreases per hour
        """
        self.hunger = max(0.0, min(1.0, hunger))
        self.thirst = max(0.0, min(1.0, thirst))
        self.rest = max(0.0, min(1.0, rest))
        self.hunger_rate = hunger_rate
        self.thirst_rate = thirst_rate
        self.rest_rate = rest_rate
    
    def get_resource_requirements(self) -> Dict[str, float]:
        """Get current resource requirements based on needs.
        
        Returns:
            Dict mapping resource_id -> required_amount
        """
        requirements = {}
        if self.hunger > 0.5:  # Need food if hunger > 50%
            requirements['food'] = self.hunger * 10.0  # Scale with hunger level
        if self.thirst > 0.5:  # Need water if thirst > 50%
            requirements['water'] = self.thirst * 5.0  # Scale with thirst level
        return requirements
    
    def update_needs(self, hours: float = 1.0) -> None:
        """Update needs based on time elapsed.
        
        Args:
            hours: Number of hours elapsed
        """
        # Increase hunger and thirst, decrease rest
        self.hunger = min(1.0, self.hunger + self.hunger_rate * hours)
        self.thirst = min(1.0, self.thirst + self.thirst_rate * hours)
        self.rest = min(1.0, self.rest + self.rest_rate * hours)
    
    def satisfy_hunger(self, amount: float) -> None:
        """Satisfy hunger by consuming food.
        
        Args:
            amount: Amount of food consumed (reduces hunger proportionally)
        """
        # Each unit of food reduces hunger by 0.1
        self.hunger = max(0.0, self.hunger - amount * 0.1)
    
    def satisfy_thirst(self, amount: float) -> None:
        """Satisfy thirst by consuming water.
        
        Args:
            amount: Amount of water consumed (reduces thirst proportionally)
        """
        # Each unit of water reduces thirst by 0.2
        self.thirst = max(0.0, self.thirst - amount * 0.2)
    
    def satisfy_rest(self, hours: float) -> None:
        """Satisfy rest by sleeping.
        
        Args:
            hours: Hours of rest (reduces rest level)
        """
        # Each hour of rest reduces rest level by 0.1
        self.rest = max(0.0, self.rest - hours * 0.1)
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'hunger': self.hunger,
            'thirst': self.thirst,
            'rest': self.rest,
            'hunger_rate': self.hunger_rate,
            'thirst_rate': self.thirst_rate,
            'rest_rate': self.rest_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'NeedsComponent':
        """Deserialize component from dictionary."""
        return cls(
            hunger=data.get('hunger', 0.0),
            thirst=data.get('thirst', 0.0),
            rest=data.get('rest', 0.0),
            hunger_rate=data.get('hunger_rate', 0.01),
            thirst_rate=data.get('thirst_rate', 0.015),
            rest_rate=data.get('rest_rate', 0.005)
        )

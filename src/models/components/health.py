"""Health component for entities."""

from typing import Dict

from src.models.component import Component


class HealthComponent(Component):
    """Component representing entity health.
    
    Health is affected by pressure, age, and other factors.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Health"
    
    def __init__(self, health: float = 1.0, max_health: float = 1.0):
        """Initialize health component.
        
        Args:
            health: Current health level (0.0 = dead, 1.0 = full health)
            max_health: Maximum health level
        """
        self.health = max(0.0, min(max_health, health))
        self.max_health = max_health
    
    def is_alive(self) -> bool:
        """Check if entity is alive.
        
        Returns:
            True if health > 0, False otherwise
        """
        return self.health > 0.0
    
    def take_damage(self, amount: float) -> None:
        """Apply damage to health.
        
        Args:
            amount: Damage amount
        """
        self.health = max(0.0, self.health - amount)
    
    def heal(self, amount: float) -> None:
        """Heal health.
        
        Args:
            amount: Healing amount
        """
        self.health = min(self.max_health, self.health + amount)
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'health': self.health,
            'max_health': self.max_health
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'HealthComponent':
        """Deserialize component from dictionary."""
        return cls(
            health=data.get('health', 1.0),
            max_health=data.get('max_health', 1.0)
        )

"""Wealth component for entities."""

from typing import Dict

from src.models.component import Component


class WealthComponent(Component):
    """Component representing entity wealth.
    
    Stores money/resources owned. Used by market source to check purchasing power.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Wealth"
    
    def __init__(self, money: float = 0.0):
        """Initialize wealth component.
        
        Args:
            money: Initial money amount
        """
        self.money = max(0.0, money)
    
    def add_money(self, amount: float) -> None:
        """Add money.
        
        Args:
            amount: Amount to add (must be >= 0)
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot add negative amount: {amount}")
        self.money += amount
    
    def remove_money(self, amount: float) -> bool:
        """Remove money.
        
        Args:
            amount: Amount to remove (must be >= 0)
            
        Returns:
            True if removed successfully, False if insufficient funds
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot remove negative amount: {amount}")
        
        if self.money < amount:
            return False
        
        self.money -= amount
        return True
    
    def has_money(self, amount: float) -> bool:
        """Check if entity has enough money.
        
        Args:
            amount: Required amount
            
        Returns:
            True if has enough, False otherwise
        """
        return self.money >= amount
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'money': self.money
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'WealthComponent':
        """Deserialize component from dictionary."""
        return cls(money=data.get('money', 0.0))

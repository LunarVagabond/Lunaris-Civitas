"""Age component for entities."""

from datetime import datetime
from typing import Dict, Optional

from src.models.component import Component


class AgeComponent(Component):
    """Component representing entity age.
    
    Tracks birth date and calculates age.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Age"
    
    def __init__(self, birth_date: Optional[datetime] = None, current_date: Optional[datetime] = None):
        """Initialize age component.
        
        Args:
            birth_date: Birth date (defaults to current date if None)
            current_date: Current date for age calculation (defaults to now if None)
        """
        if birth_date is None:
            birth_date = datetime.now()
        self.birth_date = birth_date
        
        if current_date is None:
            current_date = datetime.now()
        self._current_date = current_date
    
    def get_age_years(self, current_date: Optional[datetime] = None) -> float:
        """Get age in years.
        
        Args:
            current_date: Current date (defaults to stored current_date)
            
        Returns:
            Age in years
        """
        if current_date is None:
            current_date = self._current_date
        
        delta = current_date - self.birth_date
        return delta.days / 365.25
    
    def update_current_date(self, current_date: datetime) -> None:
        """Update current date for age calculation.
        
        Args:
            current_date: Current simulation date
        """
        self._current_date = current_date
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'birth_date': self.birth_date.isoformat(),
            'current_date': self._current_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'AgeComponent':
        """Deserialize component from dictionary."""
        birth_date = datetime.fromisoformat(data['birth_date'])
        current_date = datetime.fromisoformat(data.get('current_date', data['birth_date']))
        component = cls(birth_date=birth_date, current_date=current_date)
        return component

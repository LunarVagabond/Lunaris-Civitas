"""Pressure component for entities.

Tracks unmet resource requirements (pressure). Pressure accumulates when
requirements can't be fulfilled, leading to negative consequences.
"""

from typing import Dict, List, Optional

from src.models.component import Component


class PressureComponent(Component):
    """Tracks unmet resource requirements (pressure).
    
    Pressure accumulates when requirements can't be fulfilled,
    leading to negative consequences (health degradation, death, etc.).
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Pressure"
    
    def __init__(self):
        """Initialize pressure component."""
        self.unmet_requirements: Dict[str, float] = {}  # resource_id -> unmet amount
        self.pressure_level: float = 0.0  # 0.0-1.0, aggregated pressure
        self.last_resolution_attempts: List[Dict[str, any]] = []  # Store recent attempts
    
    def add_pressure(self, resource_id: str, amount: float) -> None:
        """Add unmet requirement pressure.
        
        Args:
            resource_id: Resource identifier
            amount: Unmet amount
        """
        self.unmet_requirements[resource_id] = \
            self.unmet_requirements.get(resource_id, 0.0) + amount
        self._update_pressure_level()
    
    def reduce_pressure(self, resource_id: str, amount: float) -> None:
        """Reduce pressure for a resource.
        
        Args:
            resource_id: Resource identifier
            amount: Amount to reduce
        """
        if resource_id in self.unmet_requirements:
            self.unmet_requirements[resource_id] = max(
                0.0,
                self.unmet_requirements[resource_id] - amount
            )
            # Clean up zero amounts
            if self.unmet_requirements[resource_id] == 0.0:
                del self.unmet_requirements[resource_id]
            self._update_pressure_level()
    
    def clear_pressure(self, resource_id: Optional[str] = None) -> None:
        """Clear pressure for a resource or all resources.
        
        Args:
            resource_id: Optional resource identifier. If None, clears all.
        """
        if resource_id is None:
            self.unmet_requirements.clear()
        else:
            self.unmet_requirements.pop(resource_id, None)
        self._update_pressure_level()
    
    def get_pressure(self, resource_id: str) -> float:
        """Get pressure level for a specific resource.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Pressure amount for the resource (0.0 if none)
        """
        return self.unmet_requirements.get(resource_id, 0.0)
    
    def get_all_pressure(self) -> Dict[str, float]:
        """Get all pressure levels.
        
        Returns:
            Dictionary mapping resource_id -> pressure amount
        """
        return self.unmet_requirements.copy()
    
    def _update_pressure_level(self) -> None:
        """Calculate aggregate pressure level."""
        # Simple aggregation - can be made more sophisticated
        total_unmet = sum(self.unmet_requirements.values())
        # Normalize: 100 units of unmet requirements = 1.0 pressure level
        self.pressure_level = min(1.0, total_unmet / 100.0)
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'unmet_requirements': self.unmet_requirements.copy(),
            'pressure_level': self.pressure_level,
            'last_resolution_attempts': self.last_resolution_attempts.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'PressureComponent':
        """Deserialize component from dictionary."""
        component = cls()
        component.unmet_requirements = data.get('unmet_requirements', {}).copy()
        component.pressure_level = data.get('pressure_level', 0.0)
        component.last_resolution_attempts = data.get('last_resolution_attempts', []).copy()
        return component

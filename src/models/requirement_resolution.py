"""Requirement resolution result model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RequirementResolution:
    """Result of attempting to resolve a resource requirement."""
    success: bool
    source_id: Optional[str]  # Which source was used
    amount_fulfilled: float
    amount_requested: float
    reason: Optional[str] = None  # Why it failed (if failed)
    
    @property
    def unmet_pressure(self) -> float:
        """Calculate unmet pressure amount."""
        return max(0.0, self.amount_requested - self.amount_fulfilled)

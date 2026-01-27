"""Generic status enum system for resources and other entities.

This provides a standardized 5-stage status system:
- DEPLETED (black): Zero or negative
- AT_RISK (red): Low but not depleted (< 20%)
- MODERATE (yellow): Middle range (20-50%)
- SUFFICIENT (blue): Good amount (50-80%)
- ABUNDANT (green): At or near capacity (>= 80%)
"""

from enum import Enum
from typing import Optional


class StatusLevel(Enum):
    """Status level enum with color coding."""
    DEPLETED = ("depleted", "black", 0)
    AT_RISK = ("at_risk", "red", 1)
    MODERATE = ("moderate", "yellow", 2)
    SUFFICIENT = ("sufficient", "blue", 3)
    ABUNDANT = ("abundant", "green", 4)
    
    def __init__(self, label: str, color: str, level: int):
        """Initialize status level.
        
        Args:
            label: Human-readable label (lowercase with underscores)
            color: Color identifier for visualization
            level: Numeric level (0-4)
        """
        self.label = label  # Use 'label' instead of 'name' to avoid conflict with Enum.name
        self.color = color
        self.level = level
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.label.replace('_', ' ').title()
    
    @property
    def short_name(self) -> str:
        """Get short identifier."""
        return self.name  # Use Enum's built-in name property (e.g., "DEPLETED")


def calculate_resource_status(
    current_amount: float,
    max_capacity: Optional[float] = None
) -> StatusLevel:
    """Calculate status level for a resource based on utilization.
    
    Args:
        current_amount: Current amount of the resource
        max_capacity: Optional maximum capacity (None = unlimited)
        
    Returns:
        StatusLevel enum value
    """
    # Depleted: zero or negative
    if current_amount <= 0:
        return StatusLevel.DEPLETED
    
    # If no capacity limit, use absolute thresholds
    if max_capacity is None:
        # For unlimited resources, use absolute amounts
        # This is a simple heuristic - may need adjustment based on use cases
        if current_amount < 100:
            return StatusLevel.AT_RISK
        elif current_amount < 500:
            return StatusLevel.MODERATE
        elif current_amount < 2000:
            return StatusLevel.SUFFICIENT
        else:
            return StatusLevel.ABUNDANT
    
    # Calculate utilization percentage
    utilization = (current_amount / max_capacity) * 100
    
    # Determine status based on utilization
    if utilization < 5:
        return StatusLevel.DEPLETED
    elif utilization < 20:
        return StatusLevel.AT_RISK
    elif utilization < 50:
        return StatusLevel.MODERATE
    elif utilization < 80:
        return StatusLevel.SUFFICIENT
    else:
        return StatusLevel.ABUNDANT


def get_status_by_id(status_id: str) -> Optional[StatusLevel]:
    """Get StatusLevel by ID string.
    
    Args:
        status_id: Status ID string (e.g., "depleted", "at_risk")
        
    Returns:
        StatusLevel enum value or None if not found
    """
    status_id_lower = status_id.lower()
    for status in StatusLevel:
        # Check both label (lowercase) and name (uppercase enum name)
        if status.label == status_id_lower or status.name.lower() == status_id_lower:
            return status
    return None


def get_all_status_levels() -> list[StatusLevel]:
    """Get all status levels ordered by level.
    
    Returns:
        List of all StatusLevel enum values ordered by level (0-4)
    """
    return sorted(StatusLevel, key=lambda s: s.level)

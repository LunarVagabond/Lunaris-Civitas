"""Generic repeat frequency enum system.

This provides a standardized repeat frequency system:
- HOURLY: Check every N hours
- DAILY: Check every N days
- WEEKLY: Check every N weeks
- MONTHLY: Check every N months
- YEARLY: Check every N years (default)

This enum is generic and may be used for modifiers and other systems.
"""

from enum import Enum
from datetime import timedelta
from typing import Optional


class RepeatFrequency(Enum):
    """Repeat frequency enum."""
    HOURLY = ("hourly", 0)
    DAILY = ("daily", 1)
    WEEKLY = ("weekly", 2)
    MONTHLY = ("monthly", 3)
    YEARLY = ("yearly", 4)
    
    def __init__(self, label: str, level: int):
        """Initialize repeat frequency.
        
        Args:
            label: Human-readable label (lowercase)
            level: Numeric level
        """
        self.label = label
        self.level = level
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.label.title()
    
    @property
    def short_name(self) -> str:
        """Get short identifier."""
        return self.name
    
    def to_timedelta(self, rate: int = 1) -> timedelta:
        """Convert frequency to timedelta.
        
        Args:
            rate: Number of periods (e.g., rate=2 means every 2 weeks)
            
        Returns:
            Timedelta representing the frequency
        """
        if self == RepeatFrequency.HOURLY:
            return timedelta(hours=rate)
        elif self == RepeatFrequency.DAILY:
            return timedelta(days=rate)
        elif self == RepeatFrequency.WEEKLY:
            return timedelta(weeks=rate)
        elif self == RepeatFrequency.MONTHLY:
            # Approximate: 30 days per month
            return timedelta(days=30 * rate)
        elif self == RepeatFrequency.YEARLY:
            # Approximate: 365 days per year
            return timedelta(days=365 * rate)
        else:
            raise ValueError(f"Unknown repeat frequency: {self}")


def get_repeat_frequency_by_id(frequency_id: str) -> Optional[RepeatFrequency]:
    """Get RepeatFrequency by ID string.
    
    Args:
        frequency_id: Frequency ID string (e.g., "hourly", "yearly")
        
    Returns:
        RepeatFrequency enum value or None if not found
    """
    frequency_id_lower = frequency_id.lower()
    for frequency in RepeatFrequency:
        if frequency.label == frequency_id_lower or frequency.name.lower() == frequency_id_lower:
            return frequency
    return None


def get_all_repeat_frequencies() -> list[RepeatFrequency]:
    """Get all repeat frequencies ordered by level.
    
    Returns:
        List of all RepeatFrequency enum values ordered by level
    """
    return sorted(RepeatFrequency, key=lambda f: f.level)

"""Generic effect type enum system.

This provides a standardized effect type system:
- PERCENTAGE: Multiplier-based effect (e.g., reduce by 30%)
- DIRECT: Absolute value effect (e.g., remove 500 units)

This enum is generic and may be used for modifiers and other systems.
"""

from enum import Enum
from typing import Optional


class EffectType(Enum):
    """Effect type enum."""
    PERCENTAGE = ("percentage", 0)
    DIRECT = ("direct", 1)
    
    def __init__(self, label: str, level: int):
        """Initialize effect type.
        
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


def apply_percentage_effect(base_value: float, effect_value: float, direction: str) -> float:
    """Apply a percentage-based effect to a base value.
    
    Args:
        base_value: The base value to modify
        effect_value: Percentage as decimal (0.0-1.0, e.g., 0.3 = 30%)
        direction: 'increase' or 'decrease'
        
    Returns:
        Modified value
    """
    if direction == 'increase':
        return base_value * (1.0 + effect_value)
    elif direction == 'decrease':
        return base_value * (1.0 - effect_value)
    else:
        raise ValueError(f"Invalid direction: {direction}. Must be 'increase' or 'decrease'")


def apply_direct_effect(base_value: float, effect_value: float, direction: str) -> float:
    """Apply a direct value effect to a base value.
    
    Args:
        base_value: The base value to modify
        effect_value: Absolute amount to add/subtract
        direction: 'increase' or 'decrease'
        
    Returns:
        Modified value
    """
    if direction == 'increase':
        return base_value + effect_value
    elif direction == 'decrease':
        return base_value - effect_value
    else:
        raise ValueError(f"Invalid direction: {direction}. Must be 'increase' or 'decrease'")


def apply_effect(
    base_value: float,
    effect_type: EffectType,
    effect_value: float,
    direction: str
) -> float:
    """Apply an effect to a base value based on effect type.
    
    Args:
        base_value: The base value to modify
        effect_type: Type of effect (PERCENTAGE or DIRECT)
        effect_value: Effect value (percentage as decimal or absolute amount)
        direction: 'increase' or 'decrease'
        
    Returns:
        Modified value
    """
    if effect_type == EffectType.PERCENTAGE:
        return apply_percentage_effect(base_value, effect_value, direction)
    elif effect_type == EffectType.DIRECT:
        return apply_direct_effect(base_value, effect_value, direction)
    else:
        raise ValueError(f"Unknown effect type: {effect_type}")


def get_effect_type_by_id(effect_type_id: str) -> Optional[EffectType]:
    """Get EffectType by ID string.
    
    Args:
        effect_type_id: Effect type ID string (e.g., "percentage", "direct")
        
    Returns:
        EffectType enum value or None if not found
    """
    effect_type_id_lower = effect_type_id.lower()
    for effect_type in EffectType:
        if effect_type.label == effect_type_id_lower or effect_type.name.lower() == effect_type_id_lower:
            return effect_type
    return None


def get_all_effect_types() -> list[EffectType]:
    """Get all effect types ordered by level.
    
    Returns:
        List of all EffectType enum values ordered by level
    """
    return sorted(EffectType, key=lambda e: e.level)

"""Modifier model for buffs, debuffs, and events."""

from datetime import datetime
from typing import Optional, Dict, Any

from src.systems.generics.effect_type import EffectType, get_effect_type_by_id
from src.systems.generics.repeat_frequency import RepeatFrequency, get_repeat_frequency_by_id


class Modifier:
    """Represents a modifier (buff/debuff/event) in the simulation.
    
    Modifiers are pure data - they contain no logic. They apply parameter
    changes such as multipliers, additive adjustments, caps, and probability shifts.
    
    Structure (normalized):
    - One modifier can affect multiple resources (one row per resource)
    - Uses effect_type (percentage/direct) and effect_value
    - Tracks repeat probability and frequency for automatic re-occurrence
    - When a modifier expires and repeats, a new record is created immediately
      so the modifier never "falls off" - seamless continuation
    """
    
    def __init__(
        self,
        modifier_name: str,
        resource_id: Optional[str] = None,
        start_year: int = None,
        end_year: int = None,
        effect_type: str = None,
        effect_value: float = None,
        effect_direction: str = None,
        is_active: bool = True,
        repeat_probability: float = 0.0,
        repeat_frequency: str = 'yearly',
        repeat_rate: int = 1,
        repeat_duration_years: Optional[int] = None,
        parent_modifier_id: Optional[int] = None,
        db_id: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None
    ):
        """Initialize a modifier.
        
        Args:
            modifier_name: Human-readable name grouping related modifier rows
            resource_id: Resource ID this modifier affects (for backward compatibility)
            start_year: Start year
            end_year: End year, exclusive
            effect_type: Effect type ('percentage' or 'direct')
            effect_value: Effect value (percentage as 0.0-1.0 or absolute amount)
            effect_direction: 'increase' or 'decrease'
            is_active: Whether modifier is currently active
            repeat_probability: Probability of repeat (0.0-1.0)
            repeat_frequency: Frequency for repeat checks ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
            repeat_rate: Every N periods to check
            repeat_duration_years: Duration of repeat in years (None = same as original)
            parent_modifier_id: ID of parent modifier if this is a repeat
            db_id: Database ID
            target_type: Target type ('resource' or 'system')
            target_id: Target ID (resource_id or system_id)
        """
        # Validate required fields
        if start_year is None or end_year is None:
            raise ValueError("start_year and end_year required")
        if end_year <= start_year:
            raise ValueError(f"end_year ({end_year}) must be after start_year ({start_year})")
        if effect_type is None or effect_value is None or effect_direction is None:
            raise ValueError("effect_type, effect_value, and effect_direction required")
        if effect_direction not in ('increase', 'decrease'):
            raise ValueError(f"effect_direction must be 'increase' or 'decrease', got '{effect_direction}'")
        
        # Determine target_type and target_id
        # Backward compatibility: if resource_id provided, use it
        if resource_id is not None:
            self.target_type = 'resource'
            self.target_id = resource_id
            self.resource_id = resource_id
        elif target_type and target_id:
            self.target_type = target_type
            self.target_id = target_id
            # Set resource_id for backward compatibility if targeting resource
            self.resource_id = target_id if target_type == 'resource' else None
        else:
            raise ValueError("Either resource_id or (target_type, target_id) must be provided")
        
        # Validate target_type
        if self.target_type not in ('resource', 'system'):
            raise ValueError(f"target_type must be 'resource' or 'system', got '{self.target_type}'")
        
        # Set fields
        self.db_id = db_id
        self.modifier_name = modifier_name
        self.start_year = start_year
        self.end_year = end_year
        self.effect_type_str = effect_type
        self.effect_type = get_effect_type_by_id(effect_type)
        if not self.effect_type:
            raise ValueError(f"Invalid effect_type: {effect_type}. Must be 'percentage' or 'direct'")
        self.effect_value = effect_value
        self.effect_direction = effect_direction
        self._is_active_flag = is_active
        self.repeat_probability = repeat_probability
        self.repeat_frequency_str = repeat_frequency
        self.repeat_frequency = get_repeat_frequency_by_id(repeat_frequency)
        if not self.repeat_frequency:
            raise ValueError(f"Invalid repeat_frequency: {repeat_frequency}")
        self.repeat_rate = repeat_rate
        self.repeat_duration_years = repeat_duration_years
        self.parent_modifier_id = parent_modifier_id
        
        # Convert years to datetime for compatibility
        self.start_datetime = datetime(start_year, 1, 1)
        self.end_datetime = datetime(end_year, 1, 1)
        self.id = f"{modifier_name}_{self.target_type}_{self.target_id}_{db_id}" if db_id else f"{modifier_name}_{self.target_type}_{self.target_id}"
        
        # Always new structure
        self._is_new_structure = True
    
    def is_active(self, current_datetime: Optional[datetime] = None) -> bool:
        """Check if the modifier is currently active.
        
        Args:
            current_datetime: Current simulation datetime (optional)
            
        Returns:
            True if modifier is active, False otherwise
        """
        if not self._is_active_flag:
            return False
        if current_datetime:
            current_year = current_datetime.year
            return self.start_year <= current_year < self.end_year
        else:
            # Just check the flag
            return self._is_active_flag
    
    def has_expired(self, current_datetime: datetime) -> bool:
        """Check if the modifier has expired.
        
        Args:
            current_datetime: Current simulation datetime
            
        Returns:
            True if modifier has expired, False otherwise
        """
        if self._is_new_structure:
            current_year = current_datetime.year
            return current_year >= self.end_year
        else:
            return current_datetime >= self.end_datetime
    
    def should_check_repeat(self, current_datetime: datetime) -> bool:
        """Check if we should check for repeat at this datetime.
        
        Args:
            current_datetime: Current simulation datetime
            
        Returns:
            True if we should check for repeat
        """
        if self._is_new_structure:
            # Check if we're at the appropriate boundary based on repeat_frequency
            if self.repeat_frequency == RepeatFrequency.YEARLY:
                # Check at end of year
                return current_datetime.month == 12 and current_datetime.day == 31 and current_datetime.hour == 23
            elif self.repeat_frequency == RepeatFrequency.MONTHLY:
                # Check at end of month
                from calendar import monthrange
                last_day = monthrange(current_datetime.year, current_datetime.month)[1]
                return current_datetime.day == last_day and current_datetime.hour == 23
            elif self.repeat_frequency == RepeatFrequency.WEEKLY:
                # Check at end of week (Sunday)
                return current_datetime.weekday() == 6 and current_datetime.hour == 23
            elif self.repeat_frequency == RepeatFrequency.DAILY:
                # Check at end of day
                return current_datetime.hour == 23
            elif self.repeat_frequency == RepeatFrequency.HOURLY:
                # Check every hour
                return True
        return False
    
    def calculate_effect(self, base_value: float) -> float:
        """Calculate the effect of this modifier on a base value.
        
        Args:
            base_value: The base value to modify
            
        Returns:
            Modified value
        """
        from src.systems.generics.effect_type import apply_effect
        return apply_effect(base_value, self.effect_type, self.effect_value, self.effect_direction)
    
    def targets_resource(self, resource_id: str) -> bool:
        """Check if this modifier targets a specific resource.
        
        Args:
            resource_id: Resource ID to check
            
        Returns:
            True if modifier targets this resource
        """
        return self.target_type == 'resource' and self.target_id == resource_id
    
    def targets_system(self, system_id: str) -> bool:
        """Check if this modifier targets a specific system.
        
        Args:
            system_id: System ID to check
            
        Returns:
            True if modifier targets this system
        """
        return self.target_type == 'system' and self.target_id == system_id
    
    def to_dict(self) -> dict:
        """Serialize modifier to dictionary.
        
        Returns:
            Dictionary representation of the modifier
        """
        return {
            'modifier_name': self.modifier_name,
            'resource_id': self.resource_id,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'effect_type': self.effect_type_str,
            'effect_value': self.effect_value,
            'effect_direction': self.effect_direction,
            'is_active': self._is_active_flag,
            'repeat_probability': self.repeat_probability,
            'repeat_frequency': self.repeat_frequency_str,
            'repeat_rate': self.repeat_rate,
            'repeat_duration_years': self.repeat_duration_years,
            'parent_modifier_id': self.parent_modifier_id,
            'db_id': self.db_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Modifier':
        """Deserialize modifier from dictionary.
        
        Args:
            data: Dictionary containing modifier data
            
        Returns:
            Modifier instance restored from data
        """
        # Support both old format (resource_id) and new format (target_type/target_id)
        target_type = data.get('target_type')
        target_id = data.get('target_id')
        resource_id = data.get('resource_id')
        
        return cls(
            modifier_name=data['modifier_name'],
            resource_id=resource_id,  # For backward compatibility
            start_year=data['start_year'],
            end_year=data['end_year'],
            effect_type=data['effect_type'],
            effect_value=data['effect_value'],
            effect_direction=data['effect_direction'],
            is_active=data.get('is_active', True),
            repeat_probability=data.get('repeat_probability', 0.0),
            repeat_frequency=data.get('repeat_frequency', 'yearly'),
            repeat_rate=data.get('repeat_rate', 1),
            repeat_duration_years=data.get('repeat_duration_years'),
            parent_modifier_id=data.get('parent_modifier_id'),
            db_id=data.get('db_id'),
            target_type=target_type,
            target_id=target_id
        )

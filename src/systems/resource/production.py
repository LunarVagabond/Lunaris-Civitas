"""Resource production system.

Produces resources based on configuration and respects modifiers affecting production.
Represents natural/baseline production processes. Future systems (jobs, etc.) will add
additional production on top of this baseline.
"""

from datetime import datetime
from typing import Any, Dict

from src.core.system import System
from src.core.logging import get_logger


logger = get_logger('systems.resource.production')


def _should_produce(frequency: str, current_datetime: datetime) -> bool:
    """Check if production should happen based on frequency.
    
    Args:
        frequency: Production frequency - 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
        current_datetime: Current simulation datetime
        
    Returns:
        True if production should happen this tick
    """
    if frequency == 'hourly':
        return True
    
    if frequency == 'daily':
        return current_datetime.hour == 0
    
    if frequency == 'weekly':
        # Monday (weekday 0) at midnight
        return current_datetime.weekday() == 0 and current_datetime.hour == 0
    
    if frequency == 'monthly':
        # 1st of month at midnight
        return current_datetime.day == 1 and current_datetime.hour == 0
    
    if frequency == 'yearly':
        # January 1st at midnight
        return (current_datetime.month == 1 and 
                current_datetime.day == 1 and 
                current_datetime.hour == 0)
    
    return False


class ResourceProductionSystem(System):
    """System that produces resources based on configuration.
    
    Production rates are configured per resource and can be modified
    by active modifiers targeting the system or specific resources.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "ResourceProductionSystem"
    
    def __init__(self):
        """Initialize the production system."""
        self.production_rates: Dict[str, float] = {}  # resource_id -> production rate per frequency period
        self.production_frequencies: Dict[str, str] = {}  # resource_id -> frequency
        self.last_production_hour: Dict[str, int] = {}  # Track last production hour per resource
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing production rates and frequencies
                   Format: {
                       'production': {
                           'resource_id': rate,  # or {'rate': rate, 'frequency': 'hourly'}
                           ...
                       }
                   }
        """
        # Extract production config
        production_config = config.get('production', {})
        
        for resource_id, rate_config in production_config.items():
            # Handle both simple format (just rate) and dict format (rate + frequency)
            if isinstance(rate_config, dict):
                rate = rate_config.get('rate', rate_config.get('amount', 0))
                frequency = rate_config.get('frequency', 'hourly')
            else:
                rate = float(rate_config)
                frequency = 'hourly'  # Default to hourly
            
            if rate < 0:
                logger.warning(f"Negative production rate for {resource_id}, ignoring")
                continue
            
            valid_frequencies = ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
            if frequency not in valid_frequencies:
                logger.warning(
                    f"Invalid production frequency '{frequency}' for {resource_id}, "
                    f"defaulting to 'hourly'"
                )
                frequency = 'hourly'
            
            self.production_rates[resource_id] = float(rate)
            self.production_frequencies[resource_id] = frequency
            self.last_production_hour[resource_id] = -1  # Initialize
        
        logger.debug(
            f"Initialized {self.system_id} with {len(self.production_rates)} resources"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Produces resources hourly based on configured rates and active modifiers.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        current_hour = current_datetime.hour
        
        for resource_id, base_rate in self.production_rates.items():
            resource = world_state.get_resource(resource_id)
            if not resource:
                logger.warning(f"Resource {resource_id} not found, skipping production")
                continue
            
            # Check if production should happen based on configured frequency
            frequency = self.production_frequencies.get(resource_id, 'hourly')
            if not _should_produce(frequency, current_datetime):
                continue
            
            # Skip if already produced this hour
            if self.last_production_hour.get(resource_id) == current_hour:
                continue
            
            # Calculate production rate with modifiers
            production_rate = self._calculate_production_rate(
                world_state,
                resource_id,
                base_rate
            )
            
            if production_rate > 0:
                produced = resource.add(production_rate)
                self.last_production_hour[resource_id] = current_hour
                # Removed verbose debug logging - too frequent for hourly operations
    
    def _calculate_production_rate(
        self,
        world_state: Any,
        resource_id: str,
        base_rate: float
    ) -> float:
        """Calculate production rate with modifiers applied.
        
        Supports both new structure (effect_type/effect_value) and legacy (multiplier/additive).
        New structure modifiers are applied first, then legacy modifiers.
        
        Args:
            world_state: World state instance
            resource_id: Resource identifier
            base_rate: Base production rate
            
        Returns:
            Modified production rate
        """
        rate = base_rate
        
        # Get modifiers targeting this resource
        resource_modifiers = world_state.get_modifiers_for_resource(resource_id)
        
        # Apply modifiers (effect_type/effect_value)
        # Modifiers are applied sequentially - each modifier affects the result of the previous
        for modifier in resource_modifiers:
            rate = modifier.calculate_effect(rate)
        
        # Ensure non-negative
        return max(0.0, rate)

"""Resource consumption system.

Consumes resources based on configuration and respects modifiers affecting consumption.
Represents natural/baseline consumption processes (decay, evaporation, etc.). Future systems
(humans, etc.) will add additional consumption on top of this baseline.
"""

from datetime import datetime
from typing import Any, Dict

from src.core.system import System
from src.core.logging import get_logger


logger = get_logger('systems.resource.consumption')


def _should_consume(frequency: str, current_datetime: datetime) -> bool:
    """Check if consumption should happen based on frequency.
    
    Args:
        frequency: Consumption frequency - 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
        current_datetime: Current simulation datetime
        
    Returns:
        True if consumption should happen this tick
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


class ResourceConsumptionSystem(System):
    """System that consumes resources based on configuration.
    
    Consumption rates are configured per resource and can be modified
    by active modifiers targeting the system or specific resources.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "ResourceConsumptionSystem"
    
    def __init__(self):
        """Initialize the consumption system."""
        self.consumption_rates: Dict[str, float] = {}  # resource_id -> consumption rate per frequency period
        self.consumption_frequencies: Dict[str, str] = {}  # resource_id -> frequency
        self.last_consumption_hour: Dict[str, int] = {}  # Track last consumption hour per resource
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing consumption rates and frequencies
                   Format: {
                       'consumption': {
                           'resource_id': rate,  # or {'rate': rate, 'frequency': 'hourly'}
                           ...
                       }
                   }
        """
        # Extract consumption config
        consumption_config = config.get('consumption', {})
        
        for resource_id, rate_config in consumption_config.items():
            # Handle both simple format (just rate) and dict format (rate + frequency)
            if isinstance(rate_config, dict):
                rate = rate_config.get('rate', rate_config.get('amount', 0))
                frequency = rate_config.get('frequency', 'hourly')
            else:
                rate = float(rate_config)
                frequency = 'hourly'  # Default to hourly
            
            if rate < 0:
                logger.warning(f"Negative consumption rate for {resource_id}, ignoring")
                continue
            
            valid_frequencies = ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
            if frequency not in valid_frequencies:
                logger.warning(
                    f"Invalid consumption frequency '{frequency}' for {resource_id}, "
                    f"defaulting to 'hourly'"
                )
                frequency = 'hourly'
            
            self.consumption_rates[resource_id] = float(rate)
            self.consumption_frequencies[resource_id] = frequency
            self.last_consumption_hour[resource_id] = -1  # Initialize
        
        logger.debug(
            f"Initialized {self.system_id} with {len(self.consumption_rates)} resources"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Consumes resources hourly based on configured rates and active modifiers.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        current_hour = current_datetime.hour
        
        for resource_id, base_rate in self.consumption_rates.items():
            resource = world_state.get_resource(resource_id)
            if not resource:
                logger.warning(f"Resource {resource_id} not found, skipping consumption")
                continue
            
            # Check if consumption should happen based on configured frequency
            frequency = self.consumption_frequencies.get(resource_id, 'hourly')
            if not _should_consume(frequency, current_datetime):
                continue
            
            # Skip if already consumed this hour
            if self.last_consumption_hour.get(resource_id) == current_hour:
                continue
            
            # Calculate consumption rate with modifiers
            consumption_rate = self._calculate_consumption_rate(
                world_state,
                resource_id,
                base_rate
            )
            
            if consumption_rate > 0:
                # Check if resource is already depleted before attempting consumption
                was_depleted = resource.is_depleted()
                
                consumed = resource.consume(consumption_rate)
                self.last_consumption_hour[resource_id] = current_hour
                
                if consumed < consumption_rate:
                    # Only log if resource wasn't already depleted (first time depletion)
                    if not was_depleted:
                        logger.warning(
                            f"Resource {resource_id} depleted: "
                            f"requested {consumption_rate:.2f}, consumed {consumed:.2f}"
                        )
                # Removed verbose debug logging - too frequent for hourly operations
    
    def _calculate_consumption_rate(
        self,
        world_state: Any,
        resource_id: str,
        base_rate: float
    ) -> float:
        """Calculate consumption rate with modifiers applied.
        
        Modifier stacking: multiplicative first, then additive.
        
        Args:
            world_state: World state instance
            resource_id: Resource identifier
            base_rate: Base consumption rate
            
        Returns:
            Modified consumption rate
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

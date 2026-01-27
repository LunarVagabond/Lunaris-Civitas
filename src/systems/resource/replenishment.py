"""Resource replenishment system.

Replenishes resources based on their replenishment_rate property.
Only replenishes non-finite resources and respects capacity limits.
"""

from datetime import datetime
from typing import Any, Dict

from src.core.system import System
from src.core.logging import get_logger


logger = get_logger('systems.resource.replenishment')


class ResourceReplenishmentSystem(System):
    """System that replenishes resources based on their replenishment_rate.
    
    Only replenishes non-finite resources. Respects capacity limits
    and modifiers affecting replenishment.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "ResourceReplenishmentSystem"
    
    def __init__(self):
        """Initialize the replenishment system."""
        self.last_replenishment_hour: Dict[str, int] = {}  # Track last replenishment hour per resource
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system.
        
        Args:
            world_state: World state instance
            config: System configuration (not used for this system)
        """
        logger.debug(f"Initialized {self.system_id}")
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Replenishes resources hourly based on their replenishment_rate
        and active modifiers.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        current_hour = current_datetime.hour
        
        for resource_id, resource in world_state.get_all_resources().items():
            # Skip finite resources
            if resource.finite:
                continue
            
            # Skip resources without replenishment rate
            if resource.replenishment_rate is None or resource.replenishment_rate <= 0:
                continue
            
            # Check if resource should replenish based on its replenishment_frequency
            if not resource.should_replenish(current_datetime):
                continue
            
            # Skip if already replenished this hour
            if self.last_replenishment_hour.get(resource_id) == current_hour:
                continue
            
            # Skip if at capacity
            if resource.is_at_capacity():
                continue
            
            # Calculate replenishment rate with modifiers
            replenishment_rate = self._calculate_replenishment_rate(
                world_state,
                resource_id,
                resource.replenishment_rate
            )
            
            if replenishment_rate > 0:
                replenished = resource.add(replenishment_rate)
                self.last_replenishment_hour[resource_id] = current_hour
                # Removed verbose debug logging - too frequent for hourly operations
    
    def _calculate_replenishment_rate(
        self,
        world_state: Any,
        resource_id: str,
        base_rate: float
    ) -> float:
        """Calculate replenishment rate with modifiers applied.
        
        Modifier stacking: multiplicative first, then additive.
        
        Args:
            world_state: World state instance
            resource_id: Resource identifier
            base_rate: Base replenishment rate
            
        Returns:
            Modified replenishment rate
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

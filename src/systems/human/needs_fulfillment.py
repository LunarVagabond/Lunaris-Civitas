"""Human needs fulfillment system.

Actively fulfills needs by calling RequirementResolverSystem with randomized
satisfaction amounts. Updates needs when fulfilled, adds pressure on failure.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from src.core.system import System
from src.core.logging import get_logger
from src.models.components.needs import NeedsComponent
from src.models.components.pressure import PressureComponent
from src.systems.human.requirement_resolver import RequirementResolverSystem


logger = get_logger('systems.human.needs_fulfillment')


class HumanNeedsFulfillmentSystem(System):
    """System that actively fulfills entity needs through RequirementResolverSystem.
    
    Gets resource requirements from NeedsComponent, attempts fulfillment through
    RequirementResolverSystem, and applies randomized satisfaction amounts.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "HumanNeedsFulfillmentSystem"
    
    def __init__(self):
        """Initialize the needs fulfillment system."""
        self.enabled: bool = True
        self.frequency: str = 'hourly'
        self.satisfaction_ranges: Dict[str, Dict[str, float]] = {}
        self.resolver_system: Optional[RequirementResolverSystem] = None
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', etc. (default: 'hourly')
                satisfaction_ranges: dict - Ranges for randomized satisfaction rates
                    Format: {
                        'food': {'hunger_restore_min': 0.05, 'hunger_restore_max': 0.15},
                        'water': {'thirst_restore_min': 0.10, 'thirst_restore_max': 0.30},
                        'rest': {'rest_restore_min': 0.05, 'rest_restore_max': 0.15}
                    }
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'hourly')
        self.satisfaction_ranges = config.get('satisfaction_ranges', {
            'food': {'hunger_restore_min': 0.05, 'hunger_restore_max': 0.15},
            'water': {'thirst_restore_min': 0.10, 'thirst_restore_max': 0.30},
            'rest': {'rest_restore_min': 0.05, 'rest_restore_max': 0.15}
        })
        
        # Get RequirementResolverSystem reference
        resolver = world_state.get_system('RequirementResolver')
        if resolver and isinstance(resolver, RequirementResolverSystem):
            self.resolver_system = resolver
        else:
            logger.warning(
                "RequirementResolverSystem not found. Need fulfillment will be disabled. "
                "Make sure RequirementResolver is registered before HumanNeedsFulfillmentSystem."
            )
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"frequency={self.frequency}, resolver_system={'found' if self.resolver_system else 'not found'}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Attempts to fulfill needs for all entities with NeedsComponent.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Get RequirementResolverSystem - must be available
        if not self.resolver_system:
            resolver = world_state.get_system('RequirementResolver')
            if resolver and isinstance(resolver, RequirementResolverSystem):
                self.resolver_system = resolver
            else:
                # RequirementResolverSystem is required for resource fulfillment
                logger.error(
                    "RequirementResolverSystem not found. Resource fulfillment disabled. "
                    "Make sure RequirementResolver is registered and initialized."
                )
                # Can still handle rest, but can't fulfill food/water needs
                # Continue to process rest fulfillment
        
        # Check frequency (for now, always run hourly - can be extended)
        if self.frequency != 'hourly':
            # TODO: Implement frequency checking similar to other systems
            pass
        
        # Get all entities with NeedsComponent
        entities = world_state.query_entities_by_component('Needs')
        
        for entity in entities:
            needs = entity.get_component('Needs')
            if not needs:
                continue
            
            # Get resource requirements (food, water)
            requirements = needs.get_resource_requirements()
            
            # Attempt to fulfill each resource requirement
            for resource_id, required_amount in requirements.items():
                self._fulfill_requirement(
                    entity,
                    resource_id,
                    required_amount,
                    needs,
                    world_state
                )
            
            # Handle rest separately (time-based, not resource-based)
            # Entities can rest if their hunger and thirst are low enough
            # (they have time/energy to rest)
            if needs.rest > 0.0:
                # Can rest if hunger and thirst are below threshold (not starving/dehydrated)
                can_rest = needs.hunger < 0.7 and needs.thirst < 0.7
                
                if can_rest:
                    # Satisfy rest with randomized amount per hour
                    range_config = self.satisfaction_ranges.get('rest', {})
                    satisfaction_rate = world_state.rng.uniform(
                        range_config.get('rest_restore_min', 0.05),
                        range_config.get('rest_restore_max', 0.15)
                    )
                    # 1 hour of rest per tick
                    needs.satisfy_rest(hours=1.0, satisfaction_rate=satisfaction_rate)
    
    def _fulfill_requirement(
        self,
        entity: Any,
        resource_id: str,
        required_amount: float,
        needs: NeedsComponent,
        world_state: Any
    ) -> None:
        """Attempt to fulfill a resource requirement.
        
        Args:
            entity: Entity instance
            resource_id: Resource identifier
            required_amount: Required amount
            needs: NeedsComponent instance
            world_state: World state instance
        """
        # Call RequirementResolverSystem (must be available)
        if not self.resolver_system:
            # Should not happen if init() worked correctly, but handle gracefully
            self._add_pressure(entity, resource_id, required_amount, world_state)
            return
        
        resolution = self.resolver_system.resolve_requirement(
            entity=entity,
            resource_id=resource_id,
            amount=required_amount,
            world_state=world_state
        )
        
        if resolution.success:
            # Apply randomized satisfaction
            self._apply_satisfaction(
                entity,
                resource_id,
                resolution.amount_fulfilled,
                needs,
                world_state
            )
        else:
            # Add pressure on failure
            self._add_pressure(entity, resource_id, required_amount, world_state)
    
    def _apply_satisfaction(
        self,
        entity: Any,
        resource_id: str,
        amount_fulfilled: float,
        needs: NeedsComponent,
        world_state: Any
    ) -> None:
        """Apply randomized satisfaction to needs.
        
        Args:
            entity: Entity instance
            resource_id: Resource identifier
            amount_fulfilled: Amount that was fulfilled
            needs: NeedsComponent instance
            world_state: World state instance (for RNG)
        """
        if resource_id == 'food':
            # Randomize hunger satisfaction rate
            range_config = self.satisfaction_ranges.get('food', {})
            satisfaction_rate = world_state.rng.uniform(
                range_config.get('hunger_restore_min', 0.05),
                range_config.get('hunger_restore_max', 0.15)
            )
            needs.satisfy_hunger(amount_fulfilled, satisfaction_rate)
            
        elif resource_id == 'water':
            # Randomize thirst satisfaction rate
            range_config = self.satisfaction_ranges.get('water', {})
            satisfaction_rate = world_state.rng.uniform(
                range_config.get('thirst_restore_min', 0.10),
                range_config.get('thirst_restore_max', 0.30)
            )
            needs.satisfy_thirst(amount_fulfilled, satisfaction_rate)
    
    def _add_pressure(
        self,
        entity: Any,
        resource_id: str,
        unmet_amount: float,
        world_state: Any
    ) -> None:
        """Add pressure for unmet requirement.
        
        Args:
            entity: Entity instance
            resource_id: Resource identifier
            unmet_amount: Unmet amount
            world_state: World state instance
        """
        # Get or create PressureComponent
        pressure = entity.get_component('Pressure')
        if not pressure:
            pressure = PressureComponent()
            entity.add_component(pressure)
        
        # Add pressure
        pressure.add_pressure(resource_id, unmet_amount)

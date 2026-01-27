"""Needs system for updating entity needs over time.

Updates hunger, thirst, and rest levels with randomized decay rates per entity
(individual metabolism variation).
"""

from datetime import datetime
from typing import Any, Dict

from src.core.system import System
from src.core.logging import get_logger
from src.models.components.needs import NeedsComponent


logger = get_logger('systems.human.needs')


class NeedsSystem(System):
    """System that updates entity needs over time with randomized decay rates.
    
    Each entity has randomized decay rates (individual metabolism) that are
    set on first tick and persist across ticks.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "NeedsSystem"
    
    def __init__(self):
        """Initialize the needs system."""
        self.enabled: bool = True
        self.base_hunger_rate: float = 0.01
        self.hunger_rate_variance: float = 0.005
        self.base_thirst_rate: float = 0.015
        self.thirst_rate_variance: float = 0.005
        self.base_rest_rate: float = 0.005
        self.rest_rate_variance: float = 0.002
        self.entities_with_randomized_rates: set = set()  # Track which entities have randomized rates
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - Always 'hourly' for needs decay
                base_hunger_rate: float - Base hunger rate per hour (default: 0.01)
                hunger_rate_variance: float - ±variance for randomization (default: 0.005)
                base_thirst_rate: float - Base thirst rate per hour (default: 0.015)
                thirst_rate_variance: float - ±variance for randomization (default: 0.005)
                base_rest_rate: float - Base rest rate per hour (default: 0.005)
                rest_rate_variance: float - ±variance for randomization (default: 0.002)
        """
        self.enabled = config.get('enabled', True)
        self.base_hunger_rate = config.get('base_hunger_rate', 0.01)
        self.hunger_rate_variance = config.get('hunger_rate_variance', 0.005)
        self.base_thirst_rate = config.get('base_thirst_rate', 0.015)
        self.thirst_rate_variance = config.get('thirst_rate_variance', 0.005)
        self.base_rest_rate = config.get('base_rest_rate', 0.005)
        self.rest_rate_variance = config.get('rest_rate_variance', 0.002)
        
        # Validate rates are non-negative
        if self.base_hunger_rate < 0 or self.base_thirst_rate < 0 or self.base_rest_rate < 0:
            logger.warning("Negative base rates detected, setting to 0")
            self.base_hunger_rate = max(0.0, self.base_hunger_rate)
            self.base_thirst_rate = max(0.0, self.base_thirst_rate)
            self.base_rest_rate = max(0.0, self.base_rest_rate)
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"base_hunger_rate={self.base_hunger_rate}±{self.hunger_rate_variance}, "
            f"base_thirst_rate={self.base_thirst_rate}±{self.thirst_rate_variance}, "
            f"base_rest_rate={self.base_rest_rate}±{self.rest_rate_variance}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Updates needs for all entities with NeedsComponent. Randomizes decay rates
        for new entities on first tick.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Get all entities with NeedsComponent
        entities = world_state.query_entities_by_component('Needs')
        
        for entity in entities:
            needs = entity.get_component('Needs')
            if not needs:
                continue
            
            # Randomize decay rates for new entities (first tick)
            if entity.entity_id not in self.entities_with_randomized_rates:
                self._randomize_decay_rates(entity, needs, world_state)
                self.entities_with_randomized_rates.add(entity.entity_id)
            
            # Update needs using stored rates
            needs.update_needs(hours=1.0)
    
    def _randomize_decay_rates(
        self,
        entity: Any,
        needs: NeedsComponent,
        world_state: Any
    ) -> None:
        """Randomize decay rates for an entity (individual metabolism).
        
        Rates are randomized within variance range and stored in the component.
        
        Args:
            entity: Entity instance
            needs: NeedsComponent instance
            world_state: World state instance (for RNG)
        """
        # Randomize hunger rate
        hunger_rate = world_state.rng.uniform(
            max(0.0, self.base_hunger_rate - self.hunger_rate_variance),
            self.base_hunger_rate + self.hunger_rate_variance
        )
        
        # Randomize thirst rate
        thirst_rate = world_state.rng.uniform(
            max(0.0, self.base_thirst_rate - self.thirst_rate_variance),
            self.base_thirst_rate + self.thirst_rate_variance
        )
        
        # Randomize rest rate
        rest_rate = world_state.rng.uniform(
            max(0.0, self.base_rest_rate - self.rest_rate_variance),
            self.base_rest_rate + self.rest_rate_variance
        )
        
        # Update component with randomized rates
        needs.hunger_rate = hunger_rate
        needs.thirst_rate = thirst_rate
        needs.rest_rate = rest_rate
        
        logger.debug(
            f"Randomized decay rates for entity {entity.entity_id}: "
            f"hunger={hunger_rate:.4f}, thirst={thirst_rate:.4f}, rest={rest_rate:.4f}"
        )

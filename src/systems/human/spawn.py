"""Human spawn system for creating initial population and runtime spawning.

NOTE: Runtime spawning is a TEMPORARY PLACEHOLDER for Phase 3 reproduction system.
This system will be replaced by a proper reproduction system that handles births
based on fertility, relationships, and other factors. For now, this allows
testing of the human lifecycle systems with ongoing population growth.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pathlib import Path

from src.core.system import System
from src.core.logging import get_logger
from src.models.entity import Entity
from src.models.components.needs import NeedsComponent
from src.models.components.health import HealthComponent
from src.models.components.age import AgeComponent
from src.models.components.pressure import PressureComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.wealth import WealthComponent


logger = get_logger('systems.human.spawn')


def _should_spawn(
    frequency: str,
    last_spawn: Optional[datetime],
    current_datetime: datetime,
    rate: int
) -> bool:
    """Check if spawning should happen based on frequency and rate.
    
    Args:
        frequency: 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
        last_spawn: Last time spawning occurred (None = never spawned)
        current_datetime: Current simulation datetime
        rate: Spawn every N periods (e.g., rate=2 means every 2 days)
        
    Returns:
        True if spawning should happen
    """
    # Check if we're at the start of a period boundary
    at_period_start = False
    
    if frequency == 'hourly':
        at_period_start = True  # Every hour is a period start
    elif frequency == 'daily':
        at_period_start = current_datetime.hour == 0
    elif frequency == 'weekly':
        at_period_start = current_datetime.weekday() == 0 and current_datetime.hour == 0
    elif frequency == 'monthly':
        at_period_start = current_datetime.day == 1 and current_datetime.hour == 0
    elif frequency == 'yearly':
        at_period_start = (current_datetime.month == 1 and 
                          current_datetime.day == 1 and 
                          current_datetime.hour == 0)
    else:
        return False
    
    if not at_period_start:
        return False
    
    if last_spawn is None:
        # First spawn - spawn immediately if at period start
        return True
    
    # Calculate periods since last spawn
    if frequency == 'hourly':
        hours_diff = int((current_datetime - last_spawn).total_seconds() / 3600)
        return hours_diff >= rate
    elif frequency == 'daily':
        days_diff = (current_datetime.date() - last_spawn.date()).days
        return days_diff >= rate
    elif frequency == 'weekly':
        weeks_diff = (current_datetime.date() - last_spawn.date()).days / 7
        return int(weeks_diff) >= rate
    elif frequency == 'monthly':
        months_diff = (current_datetime.year - last_spawn.year) * 12 + (current_datetime.month - last_spawn.month)
        return months_diff >= rate
    elif frequency == 'yearly':
        years_diff = current_datetime.year - last_spawn.year
        return years_diff >= rate
    
    return False


class HumanSpawnSystem(System):
    """System that creates initial population and supports runtime spawning.
    
    NOTE: Runtime spawning is a TEMPORARY PLACEHOLDER for Phase 3 reproduction system.
    This will be replaced by a proper reproduction system based on fertility and relationships.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "HumanSpawnSystem"
    
    def __init__(self):
        """Initialize the spawn system."""
        self.enabled: bool = True
        self.initial_population: int = 100
        self.spawn_frequency: str = 'daily'
        self.spawn_rate: int = 0  # 0 = disabled
        self.seed_crew_config: Dict[str, Any] = {}
        self.runtime_spawn_config: Dict[str, Any] = {}
        self.last_spawn: Optional[datetime] = None
        self.initial_population_created: bool = False
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                initial_population: int (default: 100)
                spawn_frequency: str - 'hourly', 'daily', 'weekly', 'monthly', 'yearly' (default: 'daily')
                spawn_rate: int - Spawn N entities per period, 0 = disabled (default: 0)
                seed_crew: dict - Configuration for initial population
                runtime_spawn: dict - Configuration for runtime spawning
        """
        self.enabled = config.get('enabled', True)
        self.initial_population = config.get('initial_population', 100)
        self.spawn_frequency = config.get('spawn_frequency', 'daily')
        self.spawn_rate = config.get('spawn_rate', 0)
        self.seed_crew_config = config.get('seed_crew', {})
        self.runtime_spawn_config = config.get('runtime_spawn', {})
        
        # Validate frequency
        valid_frequencies = ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        if self.spawn_frequency not in valid_frequencies:
            logger.warning(
                f"Invalid spawn frequency '{self.spawn_frequency}', defaulting to 'daily'"
            )
            self.spawn_frequency = 'daily'
        
        # Create initial population
        if self.enabled and self.initial_population > 0:
            self._create_initial_population(world_state)
            self.initial_population_created = True
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"initial_population={self.initial_population}, "
            f"spawn_frequency={self.spawn_frequency}, spawn_rate={self.spawn_rate}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Creates new entities at configured frequency if runtime spawning is enabled.
        
        NOTE: Runtime spawning is a TEMPORARY PLACEHOLDER for Phase 3 reproduction system.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Runtime spawning (TEMPORARY PLACEHOLDER - will be replaced by reproduction system)
        if self.spawn_rate > 0:
            if _should_spawn(self.spawn_frequency, self.last_spawn, current_datetime, self.spawn_rate):
                # Apply modifiers targeting HumanSpawnSystem to modify spawn rate
                effective_spawn_rate = float(self.spawn_rate)
                modifiers = world_state.get_modifiers_for_system(self.system_id)
                for modifier in modifiers:
                    effective_spawn_rate = modifier.calculate_effect(effective_spawn_rate)
                
                # Round to integer (spawn rate is count of entities)
                spawn_count = max(0, int(round(effective_spawn_rate)))
                
                for _ in range(spawn_count):
                    self._create_runtime_entity(world_state, current_datetime)
                self.last_spawn = current_datetime
                logger.debug(
                    f"Spawned {spawn_count} new entities at {current_datetime.isoformat()}"
                )
    
    def _create_initial_population(self, world_state: Any) -> None:
        """Create initial seed crew population.
        
        Args:
            world_state: World state instance
        """
        age_range = self.seed_crew_config.get('age_range', [18, 65])
        components_config = self.seed_crew_config.get('components', {})
        
        current_date = world_state.simulation_time.current_datetime
        
        for i in range(self.initial_population):
            entity = world_state.create_entity()
            
            # Randomize age for seed crew
            age_years = world_state.rng.uniform(age_range[0], age_range[1])
            birth_date = current_date - timedelta(days=int(age_years * 365.25))
            
            # Assign components based on probabilities
            self._assign_components(
                entity,
                components_config,
                world_state,
                birth_date=birth_date,
                is_runtime_spawn=False
            )
        
        logger.info(
            f"Created initial population of {self.initial_population} entities "
            f"with ages between {age_range[0]}-{age_range[1]} years"
        )
    
    def _create_runtime_entity(
        self,
        world_state: Any,
        current_datetime: datetime
    ) -> Entity:
        """Create a new entity during runtime (TEMPORARY PLACEHOLDER).
        
        NOTE: This is a placeholder for Phase 3 reproduction system.
        Runtime births always use current simulation date as birth_date (age = 0).
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
            
        Returns:
            Created Entity instance
        """
        entity = world_state.create_entity()
        
        # Runtime births always use current date (age = 0)
        birth_date = current_datetime
        
        # Get runtime spawn component config
        components_config = self.runtime_spawn_config.get('components', {})
        
        # Assign components
        self._assign_components(
            entity,
            components_config,
            world_state,
            birth_date=birth_date,
            is_runtime_spawn=True
        )
        
        return entity
    
    def _assign_components(
        self,
        entity: Entity,
        components_config: Dict[str, Any],
        world_state: Any,
        birth_date: datetime,
        is_runtime_spawn: bool = False
    ) -> None:
        """Assign components to entity based on configuration probabilities.
        
        Args:
            entity: Entity to assign components to
            components_config: Dictionary mapping component_type -> probability (0-100)
            world_state: World state instance (for RNG)
            birth_date: Birth date for AgeComponent
            is_runtime_spawn: Whether this is a runtime spawn (affects default components)
        """
        # Always assign core components if not specified
        if 'Needs' not in components_config or components_config.get('Needs', 0) > 0:
            entity.add_component(NeedsComponent())
        
        if 'Health' not in components_config or components_config.get('Health', 0) > 0:
            entity.add_component(HealthComponent())
        
        if 'Age' not in components_config or components_config.get('Age', 0) > 0:
            entity.add_component(AgeComponent(birth_date=birth_date, current_date=birth_date))
        
        # Assign optional components based on probabilities
        for component_type, probability in components_config.items():
            if component_type in ('Needs', 'Health', 'Age'):
                continue  # Already handled above
            
            # Probability is 0-100 (percentage)
            if world_state.rng.random() * 100 < probability:
                if component_type == 'Pressure':
                    entity.add_component(PressureComponent())
                elif component_type == 'Inventory':
                    entity.add_component(InventoryComponent())
                elif component_type == 'Wealth':
                    entity.add_component(WealthComponent())
                # Add more component types as needed

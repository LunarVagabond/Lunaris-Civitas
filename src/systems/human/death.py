"""Death system for handling entity mortality.

Checks for death from health degradation and age-based mortality.
Uses probability-based mortality curve allowing rare outliers past 100.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from src.core.system import System
from src.core.logging import get_logger
from src.models.components.health import HealthComponent
from src.models.components.age import AgeComponent


logger = get_logger('systems.human.death')


class DeathSystem(System):
    """System that handles entity death from health and age-based mortality.
    
    Checks health <= 0 for immediate death, and calculates age-based death
    probability with a curve that allows rare outliers past 100.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "DeathSystem"
    
    def __init__(self):
        """Initialize the death system."""
        self.enabled: bool = True
        self.frequency: str = 'hourly'
        self.old_age_start: float = 70.0
        self.old_age_death_chance_min: float = 0.00001
        self.old_age_death_chance_max: float = 0.0001
        self.peak_mortality_age: float = 85.0
        self.chance_increase_per_year: float = 0.00001
        self.chance_multiplier_per_year: float = 1.1
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', etc. (default: 'hourly')
                age_mortality: dict with mortality curve parameters
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'hourly')
        
        age_mortality = config.get('age_mortality', {})
        self.old_age_start = age_mortality.get('old_age_start', 70.0)
        self.old_age_death_chance_min = age_mortality.get('old_age_death_chance_min', 0.00001)
        self.old_age_death_chance_max = age_mortality.get('old_age_death_chance_max', 0.0001)
        self.peak_mortality_age = age_mortality.get('peak_mortality_age', 85.0)
        self.chance_increase_per_year = age_mortality.get('chance_increase_per_year', 0.00001)
        self.chance_multiplier_per_year = age_mortality.get('chance_multiplier_per_year', 1.1)
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"frequency={self.frequency}, old_age_start={self.old_age_start}, "
            f"peak_mortality_age={self.peak_mortality_age}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Checks all entities for death from health or age.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Check frequency (for now, always run hourly - can be extended)
        if self.frequency != 'hourly':
            # TODO: Implement frequency checking similar to other systems
            pass
        
        # Get all entities with HealthComponent
        entities = world_state.query_entities_by_component('Health')
        
        entities_to_remove = []
        
        for entity in entities:
            health = entity.get_component('Health')
            if not health:
                continue
            
            # Check health-based death
            if self._check_health_death(entity, health):
                entities_to_remove.append((entity, 'health'))
                continue
            
            # Check age-based death
            if self._check_age_death(entity, health, current_datetime, world_state):
                entities_to_remove.append((entity, 'age'))
        
        # Remove dead entities
        for entity, reason in entities_to_remove:
            self._remove_entity(entity, reason, world_state)
    
    def _check_health_death(
        self,
        entity: Any,
        health: HealthComponent
    ) -> bool:
        """Check if entity dies from health degradation.
        
        Args:
            entity: Entity instance
            health: HealthComponent instance
            
        Returns:
            True if entity should die (health <= 0)
        """
        return health.health <= 0.0
    
    def _check_age_death(
        self,
        entity: Any,
        health: HealthComponent,
        current_datetime: datetime,
        world_state: Any
    ) -> bool:
        """Check if entity dies from age-based mortality.
        
        Uses probability curve: linear increase from old_age_start to peak_mortality_age,
        then exponential increase (allowing rare outliers past 100).
        
        Args:
            entity: Entity instance
            health: HealthComponent instance
            current_datetime: Current simulation datetime
            world_state: World state instance (for RNG)
            
        Returns:
            True if entity should die based on age probability
        """
        age_component = entity.get_component('Age')
        if not age_component:
            return False
        
        age_years = age_component.get_age_years(current_datetime)
        
        # Only check if age >= old_age_start
        if age_years < self.old_age_start:
            return False
        
        # Calculate death probability based on age curve
        death_chance = self._calculate_age_death_probability(age_years, world_state)
        
        # Roll for death
        return world_state.rng.random() < death_chance
    
    def _calculate_age_death_probability(
        self,
        age_years: float,
        world_state: Any
    ) -> float:
        """Calculate death probability based on age curve.
        
        Probability increases linearly from old_age_start to peak_mortality_age,
        then exponentially after peak_mortality_age (allowing outliers past 100).
        Applies modifiers targeting DeathSystem to modify the probability.
        
        Args:
            age_years: Age in years
            world_state: World state instance (for RNG to randomize base chance)
            
        Returns:
            Death probability per hour (0.0-1.0)
        """
        if age_years < self.old_age_start:
            return 0.0
        
        # Randomize base death chance at old_age_start
        base_chance = world_state.rng.uniform(
            self.old_age_death_chance_min,
            self.old_age_death_chance_max
        )
        
        if age_years <= self.peak_mortality_age:
            # Linear increase from old_age_start to peak_mortality_age
            years_past_start = age_years - self.old_age_start
            years_to_peak = self.peak_mortality_age - self.old_age_start
            
            if years_to_peak > 0:
                # Linear interpolation
                progress = years_past_start / years_to_peak
                peak_chance = base_chance + (self.chance_increase_per_year * years_past_start)
                death_chance = min(1.0, peak_chance)
            else:
                death_chance = base_chance
        else:
            # Exponential increase after peak_mortality_age
            years_past_peak = age_years - self.peak_mortality_age
            years_to_peak = self.peak_mortality_age - self.old_age_start
            
            # Calculate peak chance
            peak_chance = base_chance + (self.chance_increase_per_year * years_to_peak)
            
            # Exponential increase: chance = peak_chance * (multiplier ^ years_past_peak)
            death_chance = peak_chance * (self.chance_multiplier_per_year ** years_past_peak)
            
            # Cap at reasonable maximum (very high but not 1.0 to allow outliers)
            death_chance = min(0.99, death_chance)
        
        # Apply modifiers targeting DeathSystem
        modifiers = world_state.get_modifiers_for_system(self.system_id)
        for modifier in modifiers:
            death_chance = modifier.calculate_effect(death_chance)
        
        # Ensure valid range
        return max(0.0, min(0.99, death_chance))
    
    def _remove_entity(
        self,
        entity: Any,
        reason: str,
        world_state: Any
    ) -> None:
        """Remove dead entity from world state.
        
        Args:
            entity: Entity instance to remove
            reason: Death reason ('health' or 'age')
            world_state: World state instance
        """
        current_datetime = world_state.simulation_time.current_datetime
        
        # Get age for logging
        age_component = entity.get_component('Age')
        age_info = ""
        if age_component:
            age_years = age_component.get_age_years(current_datetime)
            age_info = f" (age {age_years:.1f} years)"
        
        # Build detailed death cause
        cause_parts = []
        
        if reason == 'health':
            # Check what caused the health degradation
            needs = entity.get_component('Needs')
            pressure = entity.get_component('Pressure')
            health = entity.get_component('Health')
            
            unmet_needs = []
            if needs:
                if needs.hunger > 0.5:
                    unmet_needs.append(f"hunger({needs.hunger:.2f})")
                if needs.thirst > 0.5:
                    unmet_needs.append(f"thirst({needs.thirst:.2f})")
                if needs.rest > 0.5:
                    unmet_needs.append(f"rest({needs.rest:.2f})")
            
            if unmet_needs:
                cause_parts.append(f"unmet needs: {', '.join(unmet_needs)}")
            
            if pressure and pressure.pressure_level > 0.3:
                cause_parts.append(f"pressure({pressure.pressure_level:.2f})")
            
            if health:
                cause_parts.append(f"health({health.health:.2f})")
            
            if not cause_parts:
                cause_parts.append("poor health")
            
            death_cause = " - " + ", ".join(cause_parts) if cause_parts else ""
        else:
            death_cause = " - natural causes (age)"
        
        logger.info(
            f"Entity {entity.entity_id} died from {reason}{death_cause}{age_info}"
        )
        
        # Return all resources to world supply
        # NOTE: Future phases will add family inheritance, government policies, etc.
        # For now, all resources return to world supply when humans die
        wealth = entity.get_component('Wealth')
        if wealth and wealth.resources:
            returned_resources = []
            for resource_id, amount in wealth.resources.items():
                if amount > 0:
                    resource = world_state.get_resource(resource_id)
                    if resource:
                        returned = resource.add(amount)
                        returned_resources.append(f"{resource_id}: {returned:.2f}")
                    else:
                        logger.warning(
                            f"Entity {entity.entity_id} had {resource_id} ({amount:.2f}) but "
                            f"resource not found in world state"
                        )
            
            if returned_resources:
                resources_str = ", ".join(returned_resources)
                logger.info(
                    f"Entity {entity.entity_id} resources returned to world supply: {resources_str}"
                )
        
        # Remove from world state
        world_state.remove_entity(entity.entity_id)

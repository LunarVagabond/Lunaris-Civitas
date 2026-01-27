"""Health system for converting pressure and unmet needs into health degradation.

Applies randomized damage amounts based on pressure levels and unmet needs.
Health can recover slowly if needs are met.
"""

from datetime import datetime
from typing import Any, Dict

from src.core.system import System
from src.core.logging import get_logger
from src.models.components.health import HealthComponent
from src.models.components.pressure import PressureComponent
from src.models.components.needs import NeedsComponent


logger = get_logger('systems.human.health')


class HealthSystem(System):
    """System that converts pressure and unmet needs into health degradation.
    
    Applies randomized damage per tick based on pressure level and unmet needs.
    Health can recover slowly if needs are met.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "HealthSystem"
    
    def __init__(self):
        """Initialize the health system."""
        self.enabled: bool = True
        self.frequency: str = 'hourly'
        self.pressure_damage_min: float = 0.001
        self.pressure_damage_max: float = 0.005
        self.hunger_damage_min: float = 0.0005
        self.hunger_damage_max: float = 0.002
        self.thirst_damage_min: float = 0.001
        self.thirst_damage_max: float = 0.003
        self.rest_damage_min: float = 0.0002
        self.rest_damage_max: float = 0.001
        self.healing_rate_min: float = 0.0001
        self.healing_rate_max: float = 0.0005
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', etc. (default: 'hourly')
                pressure_damage: dict with min_per_tick and max_per_tick
                unmet_needs_damage: dict with hunger, thirst, rest damage ranges
                healing_rate: dict with min_per_tick and max_per_tick
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'hourly')
        
        # Load pressure damage config
        pressure_config = config.get('pressure_damage', {})
        self.pressure_damage_min = pressure_config.get('min_per_tick', 0.001)
        self.pressure_damage_max = pressure_config.get('max_per_tick', 0.005)
        
        # Load unmet needs damage config
        unmet_config = config.get('unmet_needs_damage', {})
        hunger_config = unmet_config.get('hunger', {})
        self.hunger_damage_min = hunger_config.get('min_per_tick', 0.0005)
        self.hunger_damage_max = hunger_config.get('max_per_tick', 0.002)
        
        thirst_config = unmet_config.get('thirst', {})
        self.thirst_damage_min = thirst_config.get('min_per_tick', 0.001)
        self.thirst_damage_max = thirst_config.get('max_per_tick', 0.003)
        
        rest_config = unmet_config.get('rest', {})
        self.rest_damage_min = rest_config.get('min_per_tick', 0.0002)
        self.rest_damage_max = rest_config.get('max_per_tick', 0.001)
        
        # Load healing rate config
        healing_config = config.get('healing_rate', {})
        self.healing_rate_min = healing_config.get('min_per_tick', 0.0001)
        self.healing_rate_max = healing_config.get('max_per_tick', 0.0005)
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"frequency={self.frequency}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Updates health for all entities with HealthComponent.
        
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
        
        for entity in entities:
            health = entity.get_component('Health')
            if not health:
                continue
            
            # Calculate damage from all sources
            damage = self._calculate_damage(entity, world_state)
            
            if damage > 0:
                # Apply randomized damage
                self._apply_damage(health, damage, world_state)
            
            # Check if needs are met for healing
            needs = entity.get_component('Needs')
            if needs and self._needs_met(needs):
                # Apply randomized healing
                self._apply_healing(health, world_state)
    
    def _calculate_damage(self, entity: Any, world_state: Any) -> float:
        """Calculate total damage from all sources.
        
        Args:
            entity: Entity instance
            world_state: World state instance
            
        Returns:
            Total damage amount (0.0-1.0 scale)
        """
        total_damage = 0.0
        
        # Damage from pressure
        pressure = entity.get_component('Pressure')
        if pressure and pressure.pressure_level > 0:
            # Damage scales with pressure level (0.0-1.0)
            pressure_damage_base = world_state.rng.uniform(
                self.pressure_damage_min,
                self.pressure_damage_max
            )
            total_damage += pressure_damage_base * pressure.pressure_level
        
        # Damage from unmet needs
        needs = entity.get_component('Needs')
        if needs:
            # Hunger damage (scales with hunger level)
            if needs.hunger > 0.5:  # Only damage if hunger is significant
                hunger_damage = world_state.rng.uniform(
                    self.hunger_damage_min,
                    self.hunger_damage_max
                )
                total_damage += hunger_damage * needs.hunger
            
            # Thirst damage (scales with thirst level)
            if needs.thirst > 0.5:  # Only damage if thirst is significant
                thirst_damage = world_state.rng.uniform(
                    self.thirst_damage_min,
                    self.thirst_damage_max
                )
                total_damage += thirst_damage * needs.thirst
            
            # Rest damage (scales with rest level)
            if needs.rest > 0.5:  # Only damage if rest is significant
                rest_damage = world_state.rng.uniform(
                    self.rest_damage_min,
                    self.rest_damage_max
                )
                total_damage += rest_damage * needs.rest
        
        return total_damage
    
    def _apply_damage(
        self,
        health: HealthComponent,
        damage: float,
        world_state: Any
    ) -> None:
        """Apply randomized damage to health.
        
        Args:
            health: HealthComponent instance
            damage: Base damage amount
            world_state: World state instance (for RNG if needed)
        """
        health.take_damage(damage)
    
    def _apply_healing(
        self,
        health: HealthComponent,
        world_state: Any
    ) -> None:
        """Apply randomized healing if health is below max.
        
        Args:
            health: HealthComponent instance
            world_state: World state instance (for RNG)
        """
        if health.health < health.max_health:
            healing_amount = world_state.rng.uniform(
                self.healing_rate_min,
                self.healing_rate_max
            )
            health.heal(healing_amount)
    
    def _needs_met(self, needs: NeedsComponent) -> bool:
        """Check if needs are met (low hunger, thirst, rest).
        
        Args:
            needs: NeedsComponent instance
            
        Returns:
            True if needs are met (all below 0.5 threshold)
        """
        return (needs.hunger < 0.5 and 
                needs.thirst < 0.5 and 
                needs.rest < 0.5)

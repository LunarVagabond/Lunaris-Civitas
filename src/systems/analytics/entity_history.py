"""Entity history tracking system.

Tracks entity and component metrics over time for analytics and trend analysis.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.system import System
from src.core.logging import get_logger
from src.persistence.database import Database
from src.systems.analytics.history import _should_save_history


logger = get_logger('systems.analytics.entity_history')


class EntityHistorySystem(System):
    """System that tracks entity metrics over time for analytics.
    
    Saves aggregated entity history to database at configurable intervals.
    History can be exported to CSV for analysis.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "EntityHistorySystem"
    
    def __init__(self):
        """Initialize the entity history system."""
        self.enabled: bool = True
        self.frequency: str = 'daily'
        self.rate: int = 1
        self.component_types: List[str] = []  # Empty = track all components
        self.last_save: Optional[datetime] = None
        self.db_path: Optional[Path] = None
        self.last_population: Optional[int] = None  # Track previous population for rate calculation
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', 'weekly', 'monthly', 'yearly' (default: 'daily')
                rate: int - Every N periods (default: 1)
                component_types: List[str] - Component types to track (empty = all)
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'daily')
        self.rate = config.get('rate', 1)
        self.component_types = config.get('component_types', [])
        
        # Get database path from config or world state config snapshot
        # Default to _running/simulation.db
        db_path_str = config.get('db_path')
        if db_path_str and isinstance(db_path_str, (str, Path)):
            self.db_path = Path(db_path_str)
        else:
            # Try to get from world state config snapshot (set by simulation)
            sim_config = world_state.config_snapshot.get('simulation', {})
            db_path_str = sim_config.get('db_path')
            if db_path_str and isinstance(db_path_str, (str, Path)):
                self.db_path = Path(db_path_str)
            else:
                self.db_path = Path("_running/simulation.db")
        
        # Validate frequency
        valid_frequencies = ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        if self.frequency not in valid_frequencies:
            logger.warning(
                f"Invalid history frequency '{self.frequency}', defaulting to 'daily'"
            )
            self.frequency = 'daily'
        
        # Validate rate
        if self.rate < 1:
            logger.warning(f"Invalid history rate '{self.rate}', defaulting to 1")
            self.rate = 1
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"frequency={self.frequency}, rate={self.rate}, "
            f"component_types={len(self.component_types) if self.component_types else 'all'}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Saves entity history at configured frequency intervals.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Check if we should save history
        if not _should_save_history(self.frequency, self.rate, self.last_save, current_datetime):
            return
        
        # Get all entities
        all_entities = world_state.get_all_entities()
        if not all_entities:
            return
        
        # Calculate aggregated metrics
        current_population = len(all_entities)
        metrics = self._calculate_metrics(all_entities, current_datetime)
        
        # Calculate birth and death rates (per 1000 population per period)
        birth_rate = None
        death_rate = None
        
        if self.last_population is not None:
            # Calculate change in population
            population_change = current_population - self.last_population
            
            # Calculate period length in days for rate normalization
            if self.last_save:
                period_days = (current_datetime - self.last_save).days
                if period_days > 0:
                    # Average population during period
                    avg_population = (self.last_population + current_population) / 2.0
                    if avg_population > 0:
                        # Births = positive change (new entities)
                        births = max(0, population_change)
                        # Deaths = negative change (removed entities)
                        deaths = max(0, -population_change)
                        
                        # Calculate rates per 1000 population per period
                        # Then normalize to per year for consistency
                        days_per_year = 365.25
                        if period_days > 0:
                            birth_rate = (births / avg_population) * 1000 * (days_per_year / period_days)
                            death_rate = (deaths / avg_population) * 1000 * (days_per_year / period_days)
        
        metrics['birth_rate'] = birth_rate
        metrics['death_rate'] = death_rate
        
        # Save history
        timestamp = current_datetime.isoformat()
        tick = world_state.simulation_time.ticks_elapsed
        
        try:
            with Database(self.db_path) as db:
                db.save_entity_history(
                    timestamp=timestamp,
                    tick=tick,
                    **metrics
                )
            
            self.last_save = current_datetime
            self.last_population = current_population
            logger.debug(
                f"Saved entity history for {metrics['total_entities']} entities "
                f"at {current_datetime.isoformat()}"
            )
        
        except Exception as e:
            logger.error(
                f"Error saving entity history: {e}",
                exc_info=True
            )
    
    def _calculate_metrics(
        self,
        entities: Dict[str, Any],
        current_datetime: datetime
    ) -> Dict[str, Any]:
        """Calculate aggregated entity metrics.
        
        Args:
            entities: Dictionary of entity_id -> Entity
            current_datetime: Current simulation datetime
            
        Returns:
            Dictionary of metrics to save
        """
        total_entities = len(entities)
        
        # Component counts
        component_counts: Dict[str, int] = {}
        
        # Needs metrics
        hunger_values: List[float] = []
        thirst_values: List[float] = []
        rest_values: List[float] = []
        
        # Pressure metrics
        pressure_values: List[float] = []
        entities_with_pressure = 0
        
        # Health metrics
        health_values: List[float] = []
        entities_at_risk = 0
        
        # Age metrics
        age_values: List[float] = []
        
        # Wealth metrics
        wealth_values: List[float] = []
        
        # Employment metrics
        employed_count = 0
        
        # Calculate metrics for each entity
        for entity in entities.values():
            # Component counts
            for comp_type in entity.get_component_types():
                component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
            
            # Needs component
            needs = entity.get_component('Needs')
            if needs:
                hunger_values.append(needs.hunger)
                thirst_values.append(needs.thirst)
                rest_values.append(needs.rest)
            
            # Pressure component
            pressure = entity.get_component('Pressure')
            if pressure:
                pressure_values.append(pressure.pressure_level)
                if pressure.pressure_level > 0:
                    entities_with_pressure += 1
            
            # Health component
            health = entity.get_component('Health')
            if health:
                health_values.append(health.health)
                if health.health < 0.5:
                    entities_at_risk += 1
            
            # Age component
            age = entity.get_component('Age')
            if age:
                age_years = age.get_age_years(current_datetime)
                age_values.append(age_years)
            
            # Wealth component
            wealth = entity.get_component('Wealth')
            if wealth:
                # Sum all resources in wealth (for backward compat, prefer money if available)
                if 'money' in wealth.resources:
                    wealth_values.append(wealth.resources['money'])
                elif wealth.resources:
                    # Sum all resources if no money
                    wealth_values.append(sum(wealth.resources.values()))
            
            # Employment component
            employment = entity.get_component('Employment')
            if employment and employment.is_employed():
                employed_count += 1
        
        # Calculate averages
        metrics = {
            'total_entities': total_entities,
            'component_counts': json.dumps(component_counts),
            'avg_hunger': self._average(hunger_values),
            'avg_thirst': self._average(thirst_values),
            'avg_rest': self._average(rest_values),
            'avg_pressure_level': self._average(pressure_values),
            'entities_with_pressure': entities_with_pressure,
            'avg_health': self._average(health_values),
            'entities_at_risk': entities_at_risk,
            'avg_age_years': self._average(age_values),
            'avg_wealth': self._average(wealth_values),
            'employed_count': employed_count
        }
        
        return metrics
    
    def _average(self, values: List[float]) -> Optional[float]:
        """Calculate average of values, returning None if empty.
        
        Args:
            values: List of float values
            
        Returns:
            Average value or None if list is empty
        """
        if not values:
            return None
        return sum(values) / len(values)

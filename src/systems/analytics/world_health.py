"""World Health System - tracks overall simulation health and trends."""

from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum

from src.core.system import System
from src.core.logging import get_logger
from src.systems.generics.status import StatusLevel

logger = get_logger('systems.analytics.world_health')


class HealthTrend(Enum):
    """Health trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


class WorldHealthSystem(System):
    """Tracks overall world health based on entity health and resource status.
    
    Calculates a composite health score (0.0-1.0) from:
    - Average entity health
    - Resource availability status
    - Population trends
    - Needs fulfillment rates
    
    Tracks trends by comparing current health to historical values.
    """
    
    @property
    def system_id(self) -> str:
        return "WorldHealthSystem"
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system.
        
        Args:
            world_state: World state instance
            config: System configuration
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'daily')  # When to calculate
        self.rate = config.get('rate', 1)  # Every N periods
        
        # Historical health values for trend calculation
        self.health_history: List[float] = []
        self.max_history = config.get('max_history', 10)  # Keep last N values
        
        # Last calculation time
        self.last_calculation: Optional[datetime] = None
        
        # Weights for composite score (sum should be ~1.0)
        self.weights = {
            'entity_health': config.get('weights', {}).get('entity_health', 0.4),
            'resource_health': config.get('weights', {}).get('resource_health', 0.3),
            'population_trend': config.get('weights', {}).get('population_trend', 0.2),
            'needs_fulfillment': config.get('weights', {}).get('needs_fulfillment', 0.1)
        }
        
        logger.info(
            f"WorldHealthSystem initialized: enabled={self.enabled}, "
            f"frequency={self.frequency}, rate={self.rate}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Check if we should calculate health
        if not self._should_calculate(current_datetime):
            return
        
        # Calculate world health
        health_score, components = self._calculate_world_health(world_state, current_datetime)
        
        # Calculate trend
        trend = self._calculate_trend(health_score)
        
        # Store in history
        self.health_history.append(health_score)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        # Store in world state for logging
        world_state._world_health = {
            'score': health_score,
            'trend': trend.value,
            'components': components,
            'timestamp': current_datetime
        }
        
        self.last_calculation = current_datetime
        
        logger.debug(
            f"World health: {health_score:.3f} ({trend.value}) - "
            f"Entities: {components['entity_health']:.3f}, "
            f"Resources: {components['resource_health']:.3f}, "
            f"Population: {components['population_trend']:.3f}, "
            f"Needs: {components['needs_fulfillment']:.3f}"
        )
    
    def _should_calculate(self, current_datetime: datetime) -> bool:
        """Check if we should calculate health at this time.
        
        Args:
            current_datetime: Current simulation datetime
            
        Returns:
            True if should calculate
        """
        if self.last_calculation is None:
            return True
        
        # Use same logic as simulation logging
        # Check if we're at the start of a period boundary
        at_period_start = False
        
        if self.frequency == 'hourly':
            at_period_start = True  # Every hour is a period start
        elif self.frequency == 'daily':
            at_period_start = current_datetime.hour == 0
        elif self.frequency == 'weekly':
            at_period_start = current_datetime.weekday() == 0 and current_datetime.hour == 0
        elif self.frequency == 'monthly':
            at_period_start = current_datetime.day == 1 and current_datetime.hour == 0
        elif self.frequency == 'yearly':
            at_period_start = (current_datetime.month == 1 and 
                              current_datetime.day == 1 and 
                              current_datetime.hour == 0)
        else:
            return False
        
        if not at_period_start:
            return False
        
        # Check rate (every N periods)
        if self.rate <= 1:
            return True
        
        # Calculate periods since last calculation
        periods_elapsed = self._calculate_periods_elapsed(
            self.last_calculation, 
            current_datetime, 
            self.frequency
        )
        
        return periods_elapsed >= self.rate
    
    def _calculate_periods_elapsed(
        self,
        start: datetime,
        end: datetime,
        frequency: str
    ) -> int:
        """Calculate number of periods elapsed between two datetimes.
        
        Args:
            start: Start datetime
            end: End datetime
            frequency: Period frequency
            
        Returns:
            Number of periods elapsed
        """
        if frequency == 'hourly':
            return int((end - start).total_seconds() / 3600)
        elif frequency == 'daily':
            return (end - start).days
        elif frequency == 'weekly':
            return (end - start).days // 7
        elif frequency == 'monthly':
            return (end.year - start.year) * 12 + (end.month - start.month)
        elif frequency == 'yearly':
            return end.year - start.year
        else:
            return 0
    
    def _calculate_world_health(
        self,
        world_state: Any,
        current_datetime: datetime
    ) -> tuple[float, Dict[str, float]]:
        """Calculate composite world health score.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
            
        Returns:
            Tuple of (health_score, components_dict)
        """
        components = {}
        
        # 1. Entity Health (average health of all entities)
        entity_health = self._calculate_entity_health(world_state)
        components['entity_health'] = entity_health
        
        # 2. Resource Health (weighted by resource status)
        resource_health = self._calculate_resource_health(world_state)
        components['resource_health'] = resource_health
        
        # 3. Population Trend (growing = good, declining = bad)
        population_trend = self._calculate_population_trend(world_state)
        components['population_trend'] = population_trend
        
        # 4. Needs Fulfillment (how well needs are being met)
        needs_fulfillment = self._calculate_needs_fulfillment(world_state)
        components['needs_fulfillment'] = needs_fulfillment
        
        # Calculate weighted composite score
        health_score = (
            entity_health * self.weights['entity_health'] +
            resource_health * self.weights['resource_health'] +
            population_trend * self.weights['population_trend'] +
            needs_fulfillment * self.weights['needs_fulfillment']
        )
        
        # Clamp to 0.0-1.0
        health_score = max(0.0, min(1.0, health_score))
        
        return health_score, components
    
    def _calculate_entity_health(self, world_state: Any) -> float:
        """Calculate average entity health.
        
        Returns:
            Average health score (0.0-1.0)
        """
        entities = world_state.get_all_entities()
        if not entities:
            return 0.5  # Neutral if no entities
        
        health_values = []
        for entity in entities.values():
            health_comp = entity.get_component('Health')
            if health_comp:
                health_values.append(health_comp.health)
        
        if not health_values:
            return 0.5  # Neutral if no health components
        
        return sum(health_values) / len(health_values)
    
    def _calculate_resource_health(self, world_state: Any) -> float:
        """Calculate resource health based on status levels.
        
        Maps resource status to health scores:
        - ABUNDANT: 1.0
        - SUFFICIENT: 0.8
        - MODERATE: 0.6
        - AT_RISK: 0.4
        - DEPLETED: 0.2
        - CRITICAL: 0.0
        
        Returns:
            Average resource health score (0.0-1.0)
        """
        resources = world_state.get_all_resources()
        if not resources:
            return 0.5  # Neutral if no resources
        
        status_scores = {
            StatusLevel.ABUNDANT: 1.0,
            StatusLevel.SUFFICIENT: 0.8,
            StatusLevel.MODERATE: 0.6,
            StatusLevel.AT_RISK: 0.4,
            StatusLevel.DEPLETED: 0.2
        }
        
        resource_scores = []
        for resource in resources.values():
            status = resource.status
            score = status_scores.get(status, 0.5)  # Default to moderate
            resource_scores.append(score)
        
        if not resource_scores:
            return 0.5
        
        return sum(resource_scores) / len(resource_scores)
    
    def _calculate_population_trend(self, world_state: Any) -> float:
        """Calculate population trend score.
        
        Compares current population to previous value if available.
        Growing population = higher score, declining = lower score.
        
        Returns:
            Population trend score (0.0-1.0)
        """
        entities = world_state.get_all_entities()
        current_population = len(entities)
        
        # Get previous population from world state if available
        # (stored by simulation for birth/death rate calculation)
        previous_population = getattr(world_state, '_last_population_for_health', None)
        
        if previous_population is None:
            # No history - assume stable (neutral)
            world_state._last_population_for_health = current_population
            return 0.5
        
        # Calculate trend
        if current_population == 0:
            return 0.0  # Extinction = worst
        
        if previous_population == 0:
            return 1.0  # Recovery from extinction = best
        
        # Calculate growth rate
        if previous_population > 0:
            growth_rate = (current_population - previous_population) / previous_population
        else:
            growth_rate = 0.0
        
        # Map growth rate to score
        # -0.1 (10% decline) = 0.0, 0.0 (stable) = 0.5, +0.1 (10% growth) = 1.0
        # Clamp to reasonable bounds
        growth_rate = max(-0.2, min(0.2, growth_rate))  # Cap at ±20%
        score = 0.5 + (growth_rate * 5.0)  # Scale to 0.0-1.0
        score = max(0.0, min(1.0, score))
        
        # Update stored population
        world_state._last_population_for_health = current_population
        
        return score
    
    def _calculate_needs_fulfillment(self, world_state: Any) -> float:
        """Calculate needs fulfillment score.
        
        Based on average needs levels (lower needs = better fulfillment).
        
        Returns:
            Needs fulfillment score (0.0-1.0)
        """
        entities = world_state.get_all_entities()
        if not entities:
            return 0.5  # Neutral if no entities
        
        fulfillment_scores = []
        for entity in entities.values():
            needs_comp = entity.get_component('Needs')
            if needs_comp:
                # Lower needs = better fulfillment
                # Average of (1 - hunger), (1 - thirst), (1 - rest)
                hunger_score = 1.0 - needs_comp.hunger
                thirst_score = 1.0 - needs_comp.thirst
                rest_score = 1.0 - needs_comp.rest
                
                avg_fulfillment = (hunger_score + thirst_score + rest_score) / 3.0
                fulfillment_scores.append(avg_fulfillment)
        
        if not fulfillment_scores:
            return 0.5
        
        return sum(fulfillment_scores) / len(fulfillment_scores)
    
    def _calculate_trend(self, current_health: float) -> HealthTrend:
        """Calculate health trend based on history.
        
        Args:
            current_health: Current health score
            
        Returns:
            HealthTrend enum value
        """
        if len(self.health_history) < 2:
            return HealthTrend.UNKNOWN
        
        # Compare current to average of last N values
        recent_avg = sum(self.health_history[-3:]) / min(3, len(self.health_history))
        
        # Threshold for trend detection
        threshold = 0.02  # 2% change
        
        if current_health > recent_avg + threshold:
            return HealthTrend.IMPROVING
        elif current_health < recent_avg - threshold:
            return HealthTrend.DECLINING
        else:
            return HealthTrend.STABLE
    
    def get_current_health(self, world_state: Any) -> Optional[Dict[str, Any]]:
        """Get current world health data.
        
        Args:
            world_state: World state instance
            
        Returns:
            Dictionary with health data or None if not calculated yet
        """
        return getattr(world_state, '_world_health', None)

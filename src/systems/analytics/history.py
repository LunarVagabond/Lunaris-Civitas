"""Resource history tracking system.

Tracks resource values over time for analytics and trend analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.system import System
from src.core.logging import get_logger
from src.persistence.database import Database


logger = get_logger('systems.analytics.history')


def _should_save_history(
    frequency: str,
    rate: int,
    last_save: Optional[datetime],
    current_datetime: datetime
) -> bool:
    """Check if history should be saved based on frequency and rate.
    
    Args:
        frequency: 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
        rate: Save every N periods (e.g., rate=2 means every 2 weeks)
        last_save: Last time history was saved (None = never saved)
        current_datetime: Current simulation datetime
        
    Returns:
        True if history should be saved
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
    
    if last_save is None:
        # First save - save immediately if at period start
        return True
    
    # Calculate periods since last save
    if frequency == 'hourly':
        hours_diff = int((current_datetime - last_save).total_seconds() / 3600)
        return hours_diff >= rate
    elif frequency == 'daily':
        days_diff = (current_datetime.date() - last_save.date()).days
        return days_diff >= rate
    elif frequency == 'weekly':
        # Calculate weeks difference
        weeks_diff = (current_datetime.date() - last_save.date()).days / 7
        return int(weeks_diff) >= rate
    elif frequency == 'monthly':
        months_diff = (current_datetime.year - last_save.year) * 12 + (current_datetime.month - last_save.month)
        return months_diff >= rate
    elif frequency == 'yearly':
        years_diff = current_datetime.year - last_save.year
        return years_diff >= rate
    
    return False


class ResourceHistorySystem(System):
    """System that tracks resource values over time for analytics.
    
    Saves resource history to database at configurable intervals.
    History can be exported to CSV for analysis.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "ResourceHistorySystem"
    
    def __init__(self):
        """Initialize the history system."""
        self.enabled: bool = True
        self.frequency: str = 'daily'
        self.rate: int = 1
        self.resources: List[str] = []  # Empty = all resources
        self.last_save: Optional[datetime] = None
        self.db_path: Optional[Path] = None
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', 'weekly', 'monthly', 'yearly' (default: 'daily')
                rate: int - Every N periods (default: 1)
                resources: List[str] - Resource IDs to track (empty = all)
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'daily')
        self.rate = config.get('rate', 1)
        self.resources = config.get('resources', [])
        
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
            f"resources={len(self.resources) if self.resources else 'all'}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Saves resource history at configured frequency intervals.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Check if we should save history
        if not _should_save_history(self.frequency, self.rate, self.last_save, current_datetime):
            return
        
        # Get resources to track
        all_resources = world_state.get_all_resources()
        if self.resources:
            # Filter to specified resources
            resources_to_track = {
                rid: res for rid, res in all_resources.items()
                if rid in self.resources
            }
        else:
            # Track all resources
            resources_to_track = all_resources
        
        if not resources_to_track:
            return
        
        # Save history for each resource
        timestamp = current_datetime.isoformat()
        tick = world_state.simulation_time.ticks_elapsed
        
        try:
            with Database(self.db_path) as db:
                for resource_id, resource in resources_to_track.items():
                    # Calculate utilization percentage
                    utilization_percent = None
                    if resource.max_capacity is not None and resource.max_capacity > 0:
                        utilization_percent = (resource.current_amount / resource.max_capacity) * 100
                    
                    # Get status_id
                    status_id = resource.status_id if hasattr(resource, 'status_id') else 'moderate'
                    
                    # Save to database
                    db.save_resource_history(
                        timestamp=timestamp,
                        tick=tick,
                        resource_id=resource_id,
                        amount=resource.current_amount,
                        status_id=status_id,
                        utilization_percent=utilization_percent
                    )
            
            self.last_save = current_datetime
            logger.debug(
                f"Saved history for {len(resources_to_track)} resources "
                f"at {current_datetime.isoformat()}"
            )
        
        except Exception as e:
            logger.error(
                f"Error saving resource history: {e}",
                exc_info=True
            )

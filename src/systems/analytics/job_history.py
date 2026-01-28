"""Job history tracking system.

Tracks employment statistics over time for analytics and trend analysis.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.core.system import System
from src.core.logging import get_logger
from src.persistence.database import Database
from src.systems.analytics.history import _should_save_history


logger = get_logger('systems.analytics.job_history')


class JobHistorySystem(System):
    """System that tracks employment statistics over time for analytics.
    
    Saves job history to database at configurable intervals.
    History can be exported to CSV for analysis.
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "JobHistorySystem"
    
    def __init__(self):
        """Initialize the job history system."""
        self.enabled: bool = True
        self.frequency: str = 'monthly'
        self.rate: int = 1
        self.last_save: Optional[datetime] = None
        self.db_path: Optional[Path] = None
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing:
                enabled: bool (default: true)
                frequency: str - 'hourly', 'daily', 'weekly', 'monthly', 'yearly' (default: 'monthly')
                rate: int - Every N periods (default: 1)
        """
        self.enabled = config.get('enabled', True)
        self.frequency = config.get('frequency', 'monthly')
        self.rate = config.get('rate', 1)
        
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
                f"Invalid history frequency '{self.frequency}', defaulting to 'monthly'"
            )
            self.frequency = 'monthly'
        
        # Validate rate
        if self.rate < 1:
            logger.warning(f"Invalid history rate '{self.rate}', defaulting to 1")
            self.rate = 1
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"frequency={self.frequency}, rate={self.rate}"
        )
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Saves job history at configured frequency intervals.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Check if we should save history
        if not _should_save_history(self.frequency, self.rate, self.last_save, current_datetime):
            return
        
        # Calculate employment statistics
        stats = self._calculate_employment_stats(world_state, current_datetime)
        
        if not stats:
            return
        
        # Save to database
        timestamp = current_datetime.isoformat()
        tick = world_state.simulation_time.ticks_elapsed
        
        try:
            with Database(self.db_path) as db:
                db.save_job_history(
                    timestamp=timestamp,
                    tick=tick,
                    total_employed=stats['total_employed'],
                    employment_rate=stats['employment_rate'],
                    job_distribution=stats['job_distribution'],
                    avg_salary_by_job=stats['avg_salary_by_job'],
                    total_salary_paid=stats['total_salary_paid'],
                    job_openings=stats['job_openings']
                )
            
            self.last_save = current_datetime
            logger.debug(
                f"Saved job history at {current_datetime.isoformat()}: "
                f"{stats['total_employed']} employed ({stats['employment_rate']:.1f}%)"
            )
        
        except Exception as e:
            logger.error(
                f"Error saving job history: {e}",
                exc_info=True
            )
    
    def _calculate_employment_stats(
        self,
        world_state: Any,
        current_datetime: datetime
    ) -> Optional[Dict[str, Any]]:
        """Calculate employment statistics.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
            
        Returns:
            Dictionary with employment statistics or None if no entities
        """
        all_entities = world_state.get_all_entities()
        if not all_entities:
            return None
        
        total_population = len(all_entities)
        total_employed = 0
        job_distribution: Dict[str, int] = {}
        salary_by_job: Dict[str, List[float]] = {}
        total_salary_paid = 0.0
        
        # Get JobSystem to access job definitions
        job_system = world_state.get_system('JobSystem')
        job_openings: Dict[str, int] = {}
        
        for entity in all_entities.values():
            employment = entity.get_component('Employment')
            if not employment or not employment.is_employed():
                continue
            
            total_employed += 1
            job_type = employment.job_type
            
            # Count by job type
            job_distribution[job_type] = job_distribution.get(job_type, 0) + 1
            
            # Track salaries
            if employment.salary > 0:
                if job_type not in salary_by_job:
                    salary_by_job[job_type] = []
                salary_by_job[job_type].append(employment.salary)
                total_salary_paid += employment.salary
        
        # Calculate average salary per job type
        avg_salary_by_job: Dict[str, float] = {}
        for job_type, salaries in salary_by_job.items():
            if salaries:
                avg_salary_by_job[job_type] = sum(salaries) / len(salaries)
        
        # Calculate job openings (if JobSystem is available)
        if job_system and hasattr(job_system, 'jobs'):
            for job_id, job_config in job_system.jobs.items():
                max_workers = int((total_population * job_config['max_percentage']) / 100.0)
                current_workers = job_distribution.get(job_id, 0)
                open_slots = max(0, max_workers - current_workers)
                job_openings[job_id] = open_slots
        
        # Calculate employment rate
        employment_rate = (total_employed / total_population * 100.0) if total_population > 0 else 0.0
        
        return {
            'total_employed': total_employed,
            'employment_rate': employment_rate,
            'job_distribution': job_distribution,
            'avg_salary_by_job': avg_salary_by_job,
            'total_salary_paid': total_salary_paid,
            'job_openings': job_openings
        }

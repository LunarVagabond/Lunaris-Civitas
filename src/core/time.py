"""Time system for the simulation.

Handles simulation time progression with 1 tick = 1 hour.
Properly handles calendar rules including month lengths and leap years.
"""

from datetime import datetime, timedelta
from typing import Optional


class SimulationTime:
    """Manages simulation time progression.
    
    Time model:
    - 1 tick = 1 hour
    - 24 hours = 1 day
    - Days follow real-world calendar rules (correct month lengths, leap years)
    - 12 months = 1 year
    """
    
    def __init__(self, start_datetime: datetime, rng_seed: Optional[int] = None):
        """Initialize simulation time.
        
        Args:
            start_datetime: Starting datetime for the simulation
            rng_seed: Optional RNG seed for deterministic behavior
        """
        self._current_datetime = start_datetime
        self._ticks_elapsed = 0
        self._rng_seed = rng_seed
        
    @property
    def current_datetime(self) -> datetime:
        """Get the current simulation datetime."""
        return self._current_datetime
    
    @property
    def ticks_elapsed(self) -> int:
        """Get the total number of ticks elapsed."""
        return self._ticks_elapsed
    
    @property
    def rng_seed(self) -> Optional[int]:
        """Get the RNG seed."""
        return self._rng_seed
    
    def advance_tick(self) -> datetime:
        """Advance time by exactly 1 hour (1 tick).
        
        Returns:
            The new current datetime after advancing
        """
        self._current_datetime += timedelta(hours=1)
        self._ticks_elapsed += 1
        return self._current_datetime
    
    def get_year(self) -> int:
        """Get the current simulation year."""
        return self._current_datetime.year
    
    def get_month(self) -> int:
        """Get the current simulation month (1-12)."""
        return self._current_datetime.month
    
    def get_day(self) -> int:
        """Get the current simulation day of month."""
        return self._current_datetime.day
    
    def get_hour(self) -> int:
        """Get the current simulation hour (0-23)."""
        return self._current_datetime.hour
    
    def is_new_day(self) -> bool:
        """Check if the current tick is the start of a new day (hour 0)."""
        return self._current_datetime.hour == 0
    
    def is_new_month(self) -> bool:
        """Check if the current tick is the start of a new month (day 1, hour 0)."""
        return self._current_datetime.day == 1 and self._current_datetime.hour == 0
    
    def is_new_year(self) -> bool:
        """Check if the current tick is the start of a new year (Jan 1, hour 0)."""
        return (self._current_datetime.month == 1 and 
                self._current_datetime.day == 1 and 
                self._current_datetime.hour == 0)
    
    def to_dict(self) -> dict:
        """Serialize time state to dictionary.
        
        Returns:
            Dictionary containing datetime, ticks_elapsed, and rng_seed
        """
        return {
            'datetime': self._current_datetime.isoformat(),
            'ticks_elapsed': self._ticks_elapsed,
            'rng_seed': self._rng_seed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SimulationTime':
        """Deserialize time state from dictionary.
        
        Args:
            data: Dictionary containing datetime, ticks_elapsed, and rng_seed
            
        Returns:
            SimulationTime instance restored from data
        """
        instance = cls(
            start_datetime=datetime.fromisoformat(data['datetime']),
            rng_seed=data.get('rng_seed')
        )
        instance._ticks_elapsed = data['ticks_elapsed']
        return instance

"""Base system contract for all simulation systems.

All systems must implement this interface to be compatible with the simulation engine.
Systems interact only through the world state - they never call each other directly.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict


class System(ABC):
    """Base class for all simulation systems.
    
    All systems must:
    1. Have a unique system_id
    2. Implement init() to set up initial state
    3. Implement on_tick() to process each simulation tick
    4. Optionally implement shutdown() for cleanup
    
    Systems receive the world_state and current_datetime on each tick.
    They decide internally whether to act hourly, daily, monthly, or yearly
    by inspecting the provided datetime.
    
    Systems must NOT:
    - Call other systems directly
    - Depend on other systems
    - Store references to other systems
    
    Systems MUST:
    - Interact only through the world state
    - Tolerate unknown modifiers gracefully
    - Be hot-addable without engine changes
    """
    
    @property
    @abstractmethod
    def system_id(self) -> str:
        """Get the unique identifier for this system.
        
        Returns:
            Unique system identifier string
        """
        pass
    
    @abstractmethod
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system.
        
        Called once when the system is registered with the simulation.
        Use this to set up initial state, read configuration, etc.
        
        Args:
            world_state: The world state object
            config: System-specific configuration dictionary
        """
        pass
    
    @abstractmethod
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Called every tick (hourly) by the simulation engine.
        The system decides internally whether to act based on the datetime.
        
        Args:
            world_state: The world state object
            current_datetime: Current simulation datetime
        """
        pass
    
    def shutdown(self, world_state: Any) -> None:
        """Shutdown the system.
        
        Called when the simulation is shutting down.
        Override this method if cleanup is needed.
        
        Args:
            world_state: The world state object
        """
        pass

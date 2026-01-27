"""Resource model for global resources in the simulation."""

from datetime import datetime
from typing import Optional

from src.systems.generics.status import StatusLevel, calculate_resource_status


class Resource:
    """Represents a global resource in the simulation.
    
    Attributes:
        id: Unique identifier for the resource
        name: Human-readable name
        current_amount: Current amount of the resource
        max_capacity: Optional maximum capacity limit
        replenishment_rate: Optional replenishment rate (per replenishment_frequency period)
        finite: Whether the resource is finite (non-replenishable)
        replenishment_frequency: How often resource replenishes naturally - 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
    """
    
    def __init__(
        self,
        resource_id: str,
        name: str,
        initial_amount: float,
        max_capacity: Optional[float] = None,
        replenishment_rate: Optional[float] = None,
        finite: bool = False,
        replenishment_frequency: str = 'hourly'
    ):
        """Initialize a resource.
        
        Args:
            resource_id: Unique identifier
            name: Human-readable name
            initial_amount: Starting amount
            max_capacity: Optional maximum capacity (None = unlimited)
            replenishment_rate: Optional replenishment rate (per replenishment_frequency period)
            finite: True if resource is finite (cannot replenish)
            replenishment_frequency: How often resource replenishes naturally - 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
            
        Raises:
            ValueError: If initial_amount is negative or exceeds max_capacity, or invalid frequency
        """
        if initial_amount < 0:
            raise ValueError(f"Resource {resource_id}: initial_amount cannot be negative")
        
        if max_capacity is not None and initial_amount > max_capacity:
            raise ValueError(
                f"Resource {resource_id}: initial_amount ({initial_amount}) "
                f"exceeds max_capacity ({max_capacity})"
            )
        
        if finite and replenishment_rate is not None:
            raise ValueError(
                f"Resource {resource_id}: finite resources cannot have replenishment_rate"
            )
        
        valid_frequencies = ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
        if replenishment_frequency not in valid_frequencies:
            raise ValueError(
                f"Resource {resource_id}: replenishment_frequency must be one of {valid_frequencies}, got '{replenishment_frequency}'"
            )
        
        self.id = resource_id
        self.name = name
        self._current_amount = initial_amount
        self.max_capacity = max_capacity
        self.replenishment_rate = replenishment_rate if not finite else None
        self.finite = finite
        self.replenishment_frequency = replenishment_frequency
        
        # Calculate initial status
        initial_status = calculate_resource_status(initial_amount, max_capacity)
        self.status_id = initial_status.label
    
    @property
    def current_amount(self) -> float:
        """Get the current amount of the resource."""
        return self._current_amount
    
    def add(self, amount: float) -> float:
        """Add amount to the resource.
        
        Args:
            amount: Amount to add (must be non-negative)
            
        Returns:
            The actual amount added (may be less if capacity limit reached)
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot add negative amount to resource {self.id}")
        
        if self.max_capacity is not None:
            available_space = self.max_capacity - self._current_amount
            amount_to_add = min(amount, available_space)
        else:
            amount_to_add = amount
        
        self._current_amount += amount_to_add
        self._update_status()
        return amount_to_add
    
    def consume(self, amount: float) -> float:
        """Consume amount from the resource.
        
        Args:
            amount: Amount to consume (must be non-negative)
            
        Returns:
            The actual amount consumed (may be less if insufficient)
            
        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError(f"Cannot consume negative amount from resource {self.id}")
        
        amount_to_consume = min(amount, self._current_amount)
        self._current_amount -= amount_to_consume
        self._update_status()
        
        return amount_to_consume
    
    def set_amount(self, amount: float) -> None:
        """Set the resource amount directly.
        
        Args:
            amount: New amount (must be non-negative and within capacity)
            
        Raises:
            ValueError: If amount is invalid
        """
        if amount < 0:
            raise ValueError(f"Resource amount cannot be negative")
        
        if self.max_capacity is not None and amount > self.max_capacity:
            raise ValueError(
                f"Resource amount ({amount}) exceeds max_capacity ({self.max_capacity})"
            )
        
        self._current_amount = amount
        self._update_status()
    
    def is_depleted(self) -> bool:
        """Check if the resource is depleted (amount is zero)."""
        return self._current_amount <= 0
    
    def is_at_capacity(self) -> bool:
        """Check if the resource is at maximum capacity."""
        if self.max_capacity is None:
            return False
        return self._current_amount >= self.max_capacity
    
    def should_replenish(self, current_datetime: datetime) -> bool:
        """Check if resource should replenish based on replenishment_frequency.
        
        Args:
            current_datetime: Current simulation datetime
            
        Returns:
            True if resource should replenish this tick
        """
        if self.finite or self.replenishment_rate is None:
            return False
        
        if self.replenishment_frequency == 'hourly':
            return True
        
        if self.replenishment_frequency == 'daily':
            return current_datetime.hour == 0
        
        if self.replenishment_frequency == 'weekly':
            # Monday (weekday 0) at midnight
            return current_datetime.weekday() == 0 and current_datetime.hour == 0
        
        if self.replenishment_frequency == 'monthly':
            # 1st of month at midnight
            return current_datetime.day == 1 and current_datetime.hour == 0
        
        if self.replenishment_frequency == 'yearly':
            # January 1st at midnight
            return (current_datetime.month == 1 and 
                    current_datetime.day == 1 and 
                    current_datetime.hour == 0)
        
        return False
    
    def _update_status(self) -> None:
        """Update status based on current amount and capacity."""
        status = calculate_resource_status(self._current_amount, self.max_capacity)
        self.status_id = status.label  # Use label (lowercase) for storage
    
    @property
    def status(self) -> StatusLevel:
        """Get current status level."""
        # status_id is stored as lowercase label (e.g., "depleted", "at_risk")
        # Map to StatusLevel enum
        for status in StatusLevel:
            if status.label == self.status_id:
                return status
        # Fallback to moderate if not found
        return StatusLevel.MODERATE
    
    def to_dict(self) -> dict:
        """Serialize resource to dictionary.
        
        Returns:
            Dictionary representation of the resource
        """
        return {
            'id': self.id,
            'name': self.name,
            'current_amount': self._current_amount,
            'max_capacity': self.max_capacity,
            'replenishment_rate': self.replenishment_rate,
            'finite': self.finite,
            'replenishment_frequency': self.replenishment_frequency,
            'status_id': self.status_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Resource':
        """Deserialize resource from dictionary.
        
        Args:
            data: Dictionary containing resource data
            
        Returns:
            Resource instance restored from data
        """
        resource = cls(
            resource_id=data['id'],
            name=data['name'],
            initial_amount=data['current_amount'],
            max_capacity=data.get('max_capacity'),
            replenishment_rate=data.get('replenishment_rate'),
            finite=data.get('finite', False),
            replenishment_frequency=data.get('replenishment_frequency', 'hourly')
        )
        # Set status_id if provided, otherwise calculate it
        if 'status_id' in data and data['status_id']:
            resource.status_id = data['status_id']
        else:
            resource._update_status()
        return resource

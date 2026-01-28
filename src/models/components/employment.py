"""Employment component for entities."""

from datetime import datetime
from typing import Dict, Optional

from src.models.component import Component


class EmploymentComponent(Component):
    """Component representing entity employment.
    
    Stores job information (job_type, employer_id, payment_resources, hire_date).
    Used by production source to check if can produce.
    Tracks payment resources and payment increase history.
    
    Payment resources are stored as a dictionary: {resource_id: amount}
    This allows jobs to pay in any resource type (money, crypto, food, etc.)
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Employment"
    
    def __init__(
        self,
        job_type: Optional[str] = None,
        employer_id: Optional[str] = None,
        payment_resources: Optional[Dict[str, float]] = None,
        hire_date: Optional[datetime] = None,
        last_raise_date: Optional[datetime] = None,
        max_payment_cap: Optional[Dict[str, float]] = None
    ):
        """Initialize employment component.
        
        Args:
            job_type: Type of job (e.g., "farmer", "miner", "merchant")
            employer_id: ID of employer entity (None if self-employed)
            payment_resources: Dictionary of payment resources (resource_id -> amount)
                             e.g., {"money": 100.0} or {"money": 80.0, "crypto": 2.0}
            hire_date: Date/time when hired
            last_raise_date: Date/time of last payment increase
            max_payment_cap: Maximum payment this job can pay per resource (resource_id -> max_amount)
        """
        self.job_type = job_type
        self.employer_id = employer_id
        self.payment_resources: Dict[str, float] = payment_resources.copy() if payment_resources else {}
        # Ensure all values are non-negative
        self.payment_resources = {k: max(0.0, v) for k, v in self.payment_resources.items()}
        self.hire_date = hire_date
        self.last_raise_date = last_raise_date
        self.max_payment_cap: Dict[str, float] = max_payment_cap.copy() if max_payment_cap else {}
        # Ensure all values are non-negative
        self.max_payment_cap = {k: max(0.0, v) for k, v in self.max_payment_cap.items()}
    
    def get_total_payment_value(self) -> float:
        """Get total payment value (sum of all payment resources).
        
        This is a convenience method for analytics/comparison.
        Note: Different resource types may have different values, but this provides a simple sum.
        
        Returns:
            Sum of all payment resource amounts
        """
        return sum(self.payment_resources.values())
    
    # Backward compatibility properties (deprecated)
    @property
    def salary(self) -> float:
        """Get salary as money amount (backward compatibility)."""
        return self.payment_resources.get('money', 0.0)
    
    @property
    def max_salary_cap(self) -> float:
        """Get max salary cap as money amount (backward compatibility)."""
        return self.max_payment_cap.get('money', 0.0)
    
    def is_employed(self) -> bool:
        """Check if entity is employed.
        
        Returns:
            True if has a job, False otherwise
        """
        return self.job_type is not None
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        result = {
            'job_type': self.job_type,
            'employer_id': self.employer_id,
            'payment_resources': self.payment_resources.copy(),
            'max_payment_cap': self.max_payment_cap.copy()
        }
        
        # Serialize datetime objects as ISO strings
        if self.hire_date:
            result['hire_date'] = self.hire_date.isoformat()
        if self.last_raise_date:
            result['last_raise_date'] = self.last_raise_date.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'EmploymentComponent':
        """Deserialize component from dictionary."""
        # Parse datetime strings if present
        hire_date = None
        if 'hire_date' in data and data['hire_date']:
            if isinstance(data['hire_date'], str):
                hire_date = datetime.fromisoformat(data['hire_date'])
            elif isinstance(data['hire_date'], datetime):
                hire_date = data['hire_date']
        
        last_raise_date = None
        if 'last_raise_date' in data and data['last_raise_date']:
            if isinstance(data['last_raise_date'], str):
                last_raise_date = datetime.fromisoformat(data['last_raise_date'])
            elif isinstance(data['last_raise_date'], datetime):
                last_raise_date = data['last_raise_date']
        
        # Handle both old format (salary) and new format (payment_resources)
        if 'payment_resources' in data:
            payment_resources = data['payment_resources']
        elif 'salary' in data:
            # Backward compatibility - convert salary to payment_resources
            payment_resources = {'money': data.get('salary', 0.0)}
        else:
            payment_resources = {}
        
        if 'max_payment_cap' in data:
            max_payment_cap = data['max_payment_cap']
        elif 'max_salary_cap' in data:
            # Backward compatibility
            max_payment_cap = {'money': data.get('max_salary_cap', 0.0)}
        else:
            max_payment_cap = {}
        
        return cls(
            job_type=data.get('job_type'),
            employer_id=data.get('employer_id'),
            payment_resources=payment_resources,
            hire_date=hire_date,
            last_raise_date=last_raise_date,
            max_payment_cap=max_payment_cap
        )

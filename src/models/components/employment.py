"""Employment component for entities."""

from datetime import datetime
from typing import Dict, Optional

from src.models.component import Component


class EmploymentComponent(Component):
    """Component representing entity employment.
    
    Stores job information (job_type, employer_id, salary, hire_date).
    Used by production source to check if can produce.
    Tracks salary and salary increase history.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Employment"
    
    def __init__(
        self,
        job_type: Optional[str] = None,
        employer_id: Optional[str] = None,
        salary: float = 0.0,
        hire_date: Optional[datetime] = None,
        last_raise_date: Optional[datetime] = None,
        max_salary_cap: float = 0.0
    ):
        """Initialize employment component.
        
        Args:
            job_type: Type of job (e.g., "farmer", "miner", "merchant")
            employer_id: ID of employer entity (None if self-employed)
            salary: Current salary (actual salary, not max)
            hire_date: Date/time when hired
            last_raise_date: Date/time of last salary increase
            max_salary_cap: Maximum salary this job can pay (higher than initial max_salary)
        """
        self.job_type = job_type
        self.employer_id = employer_id
        self.salary = max(0.0, salary)
        self.hire_date = hire_date
        self.last_raise_date = last_raise_date
        self.max_salary_cap = max(0.0, max_salary_cap)
    
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
            'salary': self.salary,
            'max_salary_cap': self.max_salary_cap
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
        
        return cls(
            job_type=data.get('job_type'),
            employer_id=data.get('employer_id'),
            salary=data.get('salary', 0.0),
            hire_date=hire_date,
            last_raise_date=last_raise_date,
            max_salary_cap=data.get('max_salary_cap', 0.0)
        )

"""Employment component for entities."""

from typing import Dict, Optional

from src.models.component import Component


class EmploymentComponent(Component):
    """Component representing entity employment.
    
    Stores job information (job_type, employer_id).
    Used by production source to check if can produce.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Employment"
    
    def __init__(self, job_type: Optional[str] = None, employer_id: Optional[str] = None):
        """Initialize employment component.
        
        Args:
            job_type: Type of job (e.g., "farmer", "miner", "merchant")
            employer_id: ID of employer entity (None if self-employed)
        """
        self.job_type = job_type
        self.employer_id = employer_id
    
    def is_employed(self) -> bool:
        """Check if entity is employed.
        
        Returns:
            True if has a job, False otherwise
        """
        return self.job_type is not None
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'job_type': self.job_type,
            'employer_id': self.employer_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'EmploymentComponent':
        """Deserialize component from dictionary."""
        return cls(
            job_type=data.get('job_type'),
            employer_id=data.get('employer_id')
        )

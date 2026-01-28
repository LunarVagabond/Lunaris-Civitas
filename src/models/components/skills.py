"""Skills component for entities.

RPG/Sims-like trait system with core traits and job-specific skills.
Uses a trait point system to prevent everyone from being maxed in all traits.

Future Enhancement: Traits can grow/decay over time (not implementing now).
"""

from typing import Dict, Optional


from src.models.component import Component


class SkillsComponent(Component):
    """Component representing entity skills and traits.
    
    Tracks core traits (charisma, intelligence, strength, creativity, work_ethic)
    and job-specific skills (farming, mining, teaching, etc.).
    
    Uses a trait point system where humans have limited "trait points" to distribute.
    Total trait value is constrained (e.g., sum of core traits ~3.0-4.0).
    Rare outliers can have higher or lower total trait values.
    This prevents everyone from being maxed in all traits.
    
    Future Enhancement: Traits can grow/decay over time based on experience,
    age, and activities. This is documented but not implemented yet.
    """
    
    @classmethod
    def component_type(cls) -> str:
        return "Skills"
    
    def __init__(
        self,
        charisma: float = 0.5,
        intelligence: float = 0.5,
        strength: float = 0.5,
        creativity: float = 0.5,
        work_ethic: float = 0.5,
        job_skills: Optional[Dict[str, float]] = None
    ):
        """Initialize skills component.
        
        Args:
            charisma: Social skills, interview success, negotiation (0.0-1.0)
            intelligence: Learning ability, problem-solving (0.0-1.0)
            strength: Physical capability, manual labor (0.0-1.0)
            creativity: Innovation, artistic ability (0.0-1.0)
            work_ethic: Reliability, productivity (0.0-1.0)
            job_skills: Dictionary of job-specific skills (skill_name -> value 0.0-1.0)
                       e.g., {"farming": 0.7, "mining": 0.3, "teaching": 0.5}
        """
        # Core traits
        self.charisma = max(0.0, min(1.0, charisma))
        self.intelligence = max(0.0, min(1.0, intelligence))
        self.strength = max(0.0, min(1.0, strength))
        self.creativity = max(0.0, min(1.0, creativity))
        self.work_ethic = max(0.0, min(1.0, work_ethic))
        
        # Job-specific skills
        self.job_skills: Dict[str, float] = {}
        if job_skills:
            for skill_name, skill_value in job_skills.items():
                self.job_skills[skill_name] = max(0.0, min(1.0, skill_value))
    
    def get_core_trait_total(self) -> float:
        """Get the sum of all core traits.
        
        Returns:
            Sum of charisma, intelligence, strength, creativity, and work_ethic
        """
        return (
            self.charisma +
            self.intelligence +
            self.strength +
            self.creativity +
            self.work_ethic
        )
    
    def get_job_skill(self, skill_name: str, default: float = 0.0) -> float:
        """Get a job-specific skill value.
        
        Args:
            skill_name: Name of the skill (e.g., "farming", "mining")
            default: Default value if skill doesn't exist
            
        Returns:
            Skill value (0.0-1.0) or default if not found
        """
        return self.job_skills.get(skill_name, default)
    
    def set_job_skill(self, skill_name: str, value: float) -> None:
        """Set a job-specific skill value.
        
        Args:
            skill_name: Name of the skill
            value: Skill value (0.0-1.0, will be clamped)
        """
        self.job_skills[skill_name] = max(0.0, min(1.0, value))
    
    def to_dict(self) -> Dict[str, any]:
        """Serialize component to dictionary."""
        return {
            'charisma': self.charisma,
            'intelligence': self.intelligence,
            'strength': self.strength,
            'creativity': self.creativity,
            'work_ethic': self.work_ethic,
            'job_skills': self.job_skills.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'SkillsComponent':
        """Deserialize component from dictionary."""
        return cls(
            charisma=data.get('charisma', 0.5),
            intelligence=data.get('intelligence', 0.5),
            strength=data.get('strength', 0.5),
            creativity=data.get('creativity', 0.5),
            work_ethic=data.get('work_ethic', 0.5),
            job_skills=data.get('job_skills')
        )

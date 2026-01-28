"""Unit tests for SkillsComponent."""

import pytest
from datetime import datetime

from src.models.components.skills import SkillsComponent


class TestSkillsComponent:
    """Test SkillsComponent."""
    
    def test_component_type(self):
        """Test component_type property."""
        assert SkillsComponent.component_type() == "Skills"
    
    def test_default_initialization(self):
        """Test default initialization."""
        skills = SkillsComponent()
        
        assert skills.charisma == 0.5
        assert skills.intelligence == 0.5
        assert skills.strength == 0.5
        assert skills.creativity == 0.5
        assert skills.work_ethic == 0.5
        assert skills.job_skills == {}
    
    def test_custom_initialization(self):
        """Test custom initialization."""
        skills = SkillsComponent(
            charisma=0.8,
            intelligence=0.9,
            strength=0.6,
            creativity=0.7,
            work_ethic=0.85,
            job_skills={'farming': 0.9, 'mining': 0.3}
        )
        
        assert skills.charisma == 0.8
        assert skills.intelligence == 0.9
        assert skills.strength == 0.6
        assert skills.creativity == 0.7
        assert skills.work_ethic == 0.85
        assert skills.job_skills['farming'] == 0.9
        assert skills.job_skills['mining'] == 0.3
    
    def test_trait_clamping(self):
        """Test that traits are clamped to 0.0-1.0 range."""
        skills = SkillsComponent(
            charisma=-0.5,  # Should clamp to 0.0
            intelligence=1.5,  # Should clamp to 1.0
            strength=0.3
        )
        
        assert skills.charisma == 0.0
        assert skills.intelligence == 1.0
        assert skills.strength == 0.3
    
    def test_job_skill_clamping(self):
        """Test that job skills are clamped to 0.0-1.0 range."""
        skills = SkillsComponent(
            job_skills={'farming': -0.2, 'mining': 1.5}
        )
        
        assert skills.job_skills['farming'] == 0.0
        assert skills.job_skills['mining'] == 1.0
    
    def test_get_core_trait_total(self):
        """Test getting sum of core traits."""
        skills = SkillsComponent(
            charisma=0.5,
            intelligence=0.6,
            strength=0.4,
            creativity=0.7,
            work_ethic=0.8
        )
        
        total = skills.get_core_trait_total()
        assert total == pytest.approx(3.0, abs=0.01)
    
    def test_get_job_skill(self):
        """Test getting job skill value."""
        skills = SkillsComponent(
            job_skills={'farming': 0.8, 'mining': 0.5}
        )
        
        assert skills.get_job_skill('farming') == 0.8
        assert skills.get_job_skill('mining') == 0.5
        assert skills.get_job_skill('teaching') == 0.0  # Default
        assert skills.get_job_skill('teaching', 0.3) == 0.3  # Custom default
    
    def test_set_job_skill(self):
        """Test setting job skill value."""
        skills = SkillsComponent()
        
        skills.set_job_skill('farming', 0.7)
        assert skills.job_skills['farming'] == 0.7
        
        skills.set_job_skill('mining', 1.5)  # Should clamp
        assert skills.job_skills['mining'] == 1.0
        
        skills.set_job_skill('teaching', -0.2)  # Should clamp
        assert skills.job_skills['teaching'] == 0.0
    
    def test_serialization(self):
        """Test component serialization."""
        skills = SkillsComponent(
            charisma=0.8,
            intelligence=0.9,
            strength=0.6,
            creativity=0.7,
            work_ethic=0.85,
            job_skills={'farming': 0.9, 'mining': 0.3}
        )
        
        data = skills.to_dict()
        assert data['charisma'] == 0.8
        assert data['intelligence'] == 0.9
        assert data['strength'] == 0.6
        assert data['creativity'] == 0.7
        assert data['work_ethic'] == 0.85
        assert data['job_skills']['farming'] == 0.9
        assert data['job_skills']['mining'] == 0.3
    
    def test_deserialization(self):
        """Test component deserialization."""
        data = {
            'charisma': 0.8,
            'intelligence': 0.9,
            'strength': 0.6,
            'creativity': 0.7,
            'work_ethic': 0.85,
            'job_skills': {'farming': 0.9, 'mining': 0.3}
        }
        
        skills = SkillsComponent.from_dict(data)
        
        assert skills.charisma == 0.8
        assert skills.intelligence == 0.9
        assert skills.strength == 0.6
        assert skills.creativity == 0.7
        assert skills.work_ethic == 0.85
        assert skills.job_skills['farming'] == 0.9
        assert skills.job_skills['mining'] == 0.3

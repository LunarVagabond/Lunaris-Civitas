"""Tests for job history system."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from src.systems.analytics.job_history import JobHistorySystem
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.entity import Entity
from src.models.components.employment import EmploymentComponent
from src.persistence.database import Database


def test_job_history_system_init():
    """Test system initializes correctly."""
    system = JobHistorySystem()
    
    assert system.system_id == "JobHistorySystem"
    assert system.enabled == True
    assert system.frequency == 'monthly'
    assert system.rate == 1


def test_job_history_system_saves_history():
    """Test system saves job history to database."""
    system = JobHistorySystem()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    try:
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        # Create some employed entities
        for i in range(5):
            entity = world_state.create_entity()
            employment = EmploymentComponent(
                job_type='farmer',
                payment_resources={'money': 100.0 + i * 10.0},
                hire_date=datetime(2024, 1, 1, 0, 0, 0),
                max_payment_cap={'money': 130.0}
            )
            entity.add_component(employment)
        
        config = {
            'enabled': True,
            'frequency': 'monthly',
            'rate': 1,
            'db_path': str(db_path)
        }
        
        system.init(world_state, config)
        
        # Run on monthly tick (1st of month)
        system.on_tick(world_state, datetime(2024, 1, 1, 0, 0, 0))
        
        # Check database
        with Database(db_path) as db:
            history = db.get_job_history()
            assert len(history) > 0
            
            latest = history[-1]
            assert latest['total_employed'] == 5
            assert latest['employment_rate'] == pytest.approx(100.0, abs=0.1)  # 5/5 = 100%
            assert latest['total_salary_paid'] > 0
            
            # Check JSON fields are parsed
            assert isinstance(latest['job_distribution'], dict)
            assert isinstance(latest['avg_salary_by_job'], dict)
            assert isinstance(latest['job_openings'], dict)
    
    finally:
        if db_path.exists():
            db_path.unlink()


def test_job_history_system_respects_frequency():
    """Test system only saves at configured frequency."""
    system = JobHistorySystem()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    try:
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={'simulation': {'db_path': str(db_path)}},
            rng_seed=42
        )
        
        entity = world_state.create_entity()
        entity.add_component(EmploymentComponent(
            job_type='farmer',
            payment_resources={'money': 100.0}
        ))
        
        config = {
            'enabled': True,
            'frequency': 'monthly',
            'rate': 1,
            'db_path': str(db_path)
        }
        
        system.init(world_state, config)
        
        # Run on non-monthly tick (not 1st of month)
        system.on_tick(world_state, datetime(2024, 1, 15, 12, 0, 0))
        
        # Should not save (not at month start)
        with Database(db_path) as db:
            history = db.get_job_history()
            assert len(history) == 0
        
        # Run on monthly tick (1st of month)
        system.on_tick(world_state, datetime(2024, 2, 1, 0, 0, 0))
        
        # Should save now
        with Database(db_path) as db:
            history = db.get_job_history()
            assert len(history) > 0
    
    finally:
        if db_path.exists():
            db_path.unlink()

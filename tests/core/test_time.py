"""Tests for time system."""

import pytest
from datetime import datetime, timedelta

from src.core.time import SimulationTime


def test_time_initialization():
    """Test time system initialization."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start, rng_seed=12345)
    
    assert time.current_datetime == start
    assert time.ticks_elapsed == 0
    assert time.rng_seed == 12345


def test_time_advance_tick():
    """Test advancing time by one tick."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    
    new_time = time.advance_tick()
    
    assert new_time == start + timedelta(hours=1)
    assert time.ticks_elapsed == 1
    assert time.current_datetime == start + timedelta(hours=1)


def test_time_serialization():
    """Test time serialization and deserialization."""
    start = datetime(2024, 1, 1, 12, 30, 0)
    time = SimulationTime(start, rng_seed=42)
    time.advance_tick()
    time.advance_tick()
    
    data = time.to_dict()
    restored = SimulationTime.from_dict(data)
    
    assert restored.current_datetime == time.current_datetime
    assert restored.ticks_elapsed == time.ticks_elapsed
    assert restored.rng_seed == time.rng_seed


def test_time_helpers():
    """Test time helper methods."""
    start = datetime(2024, 1, 1, 0, 0, 0)
    time = SimulationTime(start)
    
    assert time.get_year() == 2024
    assert time.get_month() == 1
    assert time.get_day() == 1
    assert time.get_hour() == 0
    
    assert time.is_new_day() == True
    assert time.is_new_month() == True
    assert time.is_new_year() == True
    
    # Advance to hour 1
    time.advance_tick()
    assert time.is_new_day() == False
    assert time.is_new_month() == False
    assert time.is_new_year() == False

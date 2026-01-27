"""Tests for database history methods."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.persistence.database import Database
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource


def test_save_resource_history():
    """Test saving history record correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            # Create a resource first (for foreign key)
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
                config_snapshot={},
                rng_seed=42
            )
            world_state.add_resource(Resource('food', 'Food', 1000.0, max_capacity=5000.0))
            db.save_world_state(world_state)
            
            # Save history
            timestamp = datetime(2024, 1, 1, 0, 0, 0).isoformat()
            db.save_resource_history(
                timestamp=timestamp,
                tick=100,
                resource_id='food',
                amount=1500.0,
                status_id='moderate',
                utilization_percent=30.0
            )
            
            # Verify it was saved
            history = db.get_resource_history('food')
            assert len(history) == 1
            assert history[0]['timestamp'] == timestamp
            assert history[0]['tick'] == 100
            assert history[0]['resource_id'] == 'food'
            assert history[0]['amount'] == 1500.0
            assert history[0]['status_id'] == 'moderate'
            assert history[0]['utilization_percent'] == 30.0


def test_get_resource_history_by_resource():
    """Test querying history by resource_id."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            # Create resources
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
                config_snapshot={},
                rng_seed=42
            )
            world_state.add_resource(Resource('food', 'Food', 1000.0))
            world_state.add_resource(Resource('water', 'Water', 2000.0))
            db.save_world_state(world_state)
            
            # Save history for both resources
            db.save_resource_history(
                timestamp=datetime(2024, 1, 1, 0, 0, 0).isoformat(),
                tick=100,
                resource_id='food',
                amount=1000.0,
                status_id='moderate'
            )
            db.save_resource_history(
                timestamp=datetime(2024, 1, 1, 0, 0, 0).isoformat(),
                tick=100,
                resource_id='water',
                amount=2000.0,
                status_id='moderate'
            )
            
            # Query only food
            history = db.get_resource_history('food')
            assert len(history) == 1
            assert history[0]['resource_id'] == 'food'
            
            # Query only water
            history = db.get_resource_history('water')
            assert len(history) == 1
            assert history[0]['resource_id'] == 'water'


def test_get_resource_history_by_tick_range():
    """Test querying history by tick range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            # Create resource
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
                config_snapshot={},
                rng_seed=42
            )
            world_state.add_resource(Resource('food', 'Food', 1000.0))
            db.save_world_state(world_state)
            
            # Save history at different ticks
            for tick in [50, 100, 150, 200]:
                db.save_resource_history(
                    timestamp=datetime(2024, 1, 1, tick // 24, tick % 24, 0).isoformat(),
                    tick=tick,
                    resource_id='food',
                    amount=1000.0 + tick,
                    status_id='moderate'
                )
            
            # Query range 100-150 (inclusive)
            history = db.get_resource_history('food', start_tick=100, end_tick=150)
            assert len(history) == 2  # Should be 100 and 150 (not 50, not 200)
            ticks = [h['tick'] for h in history]
            assert 50 not in ticks
            assert 100 in ticks
            assert 150 in ticks
            assert 200 not in ticks


def test_get_resource_history_by_datetime_range():
    """Test querying history by datetime range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            # Create resource
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
                config_snapshot={},
                rng_seed=42
            )
            world_state.add_resource(Resource('food', 'Food', 1000.0))
            db.save_world_state(world_state)
            
            # Save history at different times
            timestamps = [
                datetime(2024, 1, 1, 0, 0, 0).isoformat(),
                datetime(2024, 1, 2, 0, 0, 0).isoformat(),
                datetime(2024, 1, 3, 0, 0, 0).isoformat(),
                datetime(2024, 1, 4, 0, 0, 0).isoformat(),
            ]
            
            for i, timestamp in enumerate(timestamps):
                db.save_resource_history(
                    timestamp=timestamp,
                    tick=100 + i * 24,
                    resource_id='food',
                    amount=1000.0,
                    status_id='moderate'
                )
            
            # Query range Jan 2 - Jan 3 (inclusive)
            history = db.get_resource_history(
                'food',
                start_datetime=datetime(2024, 1, 2, 0, 0, 0).isoformat(),
                end_datetime=datetime(2024, 1, 3, 0, 0, 0).isoformat()
            )
            assert len(history) == 2
            timestamps_in_result = [h['timestamp'] for h in history]
            assert datetime(2024, 1, 1, 0, 0, 0).isoformat() not in timestamps_in_result
            assert datetime(2024, 1, 2, 0, 0, 0).isoformat() in timestamps_in_result
            assert datetime(2024, 1, 3, 0, 0, 0).isoformat() in timestamps_in_result
            assert datetime(2024, 1, 4, 0, 0, 0).isoformat() not in timestamps_in_result


def test_get_all_resource_history():
    """Test getting all resources' history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            # Create resources
            world_state = WorldState(
                simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
                config_snapshot={},
                rng_seed=42
            )
            world_state.add_resource(Resource('food', 'Food', 1000.0))
            world_state.add_resource(Resource('water', 'Water', 2000.0))
            db.save_world_state(world_state)
            
            # Save history for both resources
            timestamp = datetime(2024, 1, 1, 0, 0, 0).isoformat()
            db.save_resource_history(
                timestamp=timestamp,
                tick=100,
                resource_id='food',
                amount=1000.0,
                status_id='moderate'
            )
            db.save_resource_history(
                timestamp=timestamp,
                tick=100,
                resource_id='water',
                amount=2000.0,
                status_id='moderate'
            )
            
            # Get all history
            history = db.get_all_resource_history()
            assert len(history) == 2
            resource_ids = {h['resource_id'] for h in history}
            assert 'food' in resource_ids
            assert 'water' in resource_ids


def test_history_table_created():
    """Test history table is created on schema init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='resource_history'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == 'resource_history'


def test_history_indexes_created():
    """Test indexes are created for performance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        with Database(db_path) as db:
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_resource_history%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert 'idx_resource_history_timestamp_resource' in indexes
            assert 'idx_resource_history_tick' in indexes
            assert 'idx_resource_history_resource_id' in indexes

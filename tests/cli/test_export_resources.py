"""Tests for CSV export CLI tool."""

import pytest
import csv
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.persistence.database import Database
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource


def _create_test_database(db_path: Path) -> None:
    """Create a test database with resources and history."""
    with Database(db_path) as db:
        # Create world state with resources
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42),
            config_snapshot={},
            rng_seed=42
        )
        world_state.add_resource(Resource('food', 'Food', 1000.0, max_capacity=5000.0))
        world_state.add_resource(Resource('water', 'Water', 2000.0, max_capacity=5000.0))
        db.save_world_state(world_state)
        
        # Add history records
        timestamps = [
            datetime(2024, 1, 1, 0, 0, 0).isoformat(),
            datetime(2024, 1, 2, 0, 0, 0).isoformat(),
            datetime(2024, 1, 3, 0, 0, 0).isoformat(),
        ]
        
        for i, timestamp in enumerate(timestamps):
            tick = 100 + i * 24
            # Food history
            db.save_resource_history(
                timestamp=timestamp,
                tick=tick,
                resource_id='food',
                amount=1000.0 + i * 100,
                status_id='moderate',
                utilization_percent=20.0 + i * 2
            )
            # Water history
            db.save_resource_history(
                timestamp=timestamp,
                tick=tick,
                resource_id='water',
                amount=2000.0 + i * 200,
                status_id='moderate',
                utilization_percent=40.0 + i * 4
            )


def test_export_all_resources():
    """Test exporting all resources."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_path = Path(tmpdir) / "export.csv"
        
        _create_test_database(db_path)
        
        # Run export
        from src.cli.export_resources import main
        with patch('sys.argv', ['export_resources.py', '--db', str(db_path), '--output', str(output_path)]):
            main()
        
        # Verify CSV was created
        assert output_path.exists()
        
        # Read and verify CSV
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 6  # 3 timestamps * 2 resources
            assert all('timestamp' in row for row in rows)
            assert all('tick' in row for row in rows)
            assert all('resource_id' in row for row in rows)
            assert all('amount' in row for row in rows)
            
            # Check both resources are present
            resource_ids = {row['resource_id'] for row in rows}
            assert 'food' in resource_ids
            assert 'water' in resource_ids


def test_export_filtered_by_resource():
    """Test filtering by resource ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_path = Path(tmpdir) / "export.csv"
        
        _create_test_database(db_path)
        
        # Run export with filter
        from src.cli.export_resources import main
        with patch('sys.argv', [
            'export_resources.py',
            '--db', str(db_path),
            '--output', str(output_path),
            '--resource-id', 'food'
        ]):
            main()
        
        # Verify CSV
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3  # Only food, 3 timestamps
            assert all(row['resource_id'] == 'food' for row in rows)


def test_export_filtered_by_tick_range():
    """Test filtering by tick range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_path = Path(tmpdir) / "export.csv"
        
        _create_test_database(db_path)
        
        # Run export with tick range (100-124, should get first 2 timestamps)
        from src.cli.export_resources import main
        with patch('sys.argv', [
            'export_resources.py',
            '--db', str(db_path),
            '--output', str(output_path),
            '--start-tick', '100',
            '--end-tick', '124'
        ]):
            main()
        
        # Verify CSV
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 4  # 2 timestamps * 2 resources
            ticks = {int(row['tick']) for row in rows}
            assert 100 in ticks
            assert 124 in ticks
            assert 148 not in ticks


def test_export_filtered_by_datetime_range():
    """Test filtering by datetime range."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_path = Path(tmpdir) / "export.csv"
        
        _create_test_database(db_path)
        
        # Run export with datetime range (Jan 1 - Jan 2)
        from src.cli.export_resources import main
        with patch('sys.argv', [
            'export_resources.py',
            '--db', str(db_path),
            '--output', str(output_path),
            '--start-date', '2024-01-01T00:00:00',
            '--end-date', '2024-01-02T00:00:00'
        ]):
            main()
        
        # Verify CSV
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 4  # 2 timestamps * 2 resources
            timestamps = {row['timestamp'] for row in rows}
            assert '2024-01-01T00:00:00' in timestamps
            assert '2024-01-02T00:00:00' in timestamps
            assert '2024-01-03T00:00:00' not in timestamps


def test_export_pivot_format():
    """Test pivot format (one column per resource)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_path = Path(tmpdir) / "export.csv"
        
        _create_test_database(db_path)
        
        # Run export with pivot
        from src.cli.export_resources import main
        with patch('sys.argv', [
            'export_resources.py',
            '--db', str(db_path),
            '--output', str(output_path),
            '--pivot'
        ]):
            main()
        
        # Verify CSV
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3  # 3 timestamps, one row each
            
            # Check pivot columns exist
            assert 'food_amount' in rows[0]
            assert 'food_status' in rows[0]
            assert 'food_utilization' in rows[0]
            assert 'water_amount' in rows[0]
            assert 'water_status' in rows[0]
            assert 'water_utilization' in rows[0]
            
            # Verify data
            assert float(rows[0]['food_amount']) == 1000.0
            assert float(rows[1]['food_amount']) == 1100.0
            assert float(rows[2]['food_amount']) == 1200.0


def test_export_creates_output_directory():
    """Test export creates output directory if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        output_dir = Path(tmpdir) / "new_dir" / "subdir"
        output_path = output_dir / "export.csv"
        
        _create_test_database(db_path)
        
        # Ensure directory doesn't exist
        assert not output_dir.exists()
        
        # Run export
        from src.cli.export_resources import main
        with patch('sys.argv', [
            'export_resources.py',
            '--db', str(db_path),
            '--output', str(output_path)
        ]):
            main()
        
        # Verify directory was created and file exists
        assert output_dir.exists()
        assert output_path.exists()

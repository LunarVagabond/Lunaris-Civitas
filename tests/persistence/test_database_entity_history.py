"""Tests for database entity history methods."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.persistence.database import Database


class TestDatabaseEntityHistory:
    """Test database entity history methods."""
    
    def test_save_entity_history(self):
        """Test saving entity history."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 5, "Health": 4, "Pressure": 2})
            
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=0,
                total_entities=5,
                component_counts=component_counts,
                avg_hunger=0.5,
                avg_thirst=0.3,
                avg_rest=0.2,
                avg_pressure_level=0.1,
                entities_with_pressure=2,
                avg_health=0.8,
                entities_at_risk=1,
                avg_age_years=25.5,
                avg_wealth=100.0,
                employed_count=3
            )
            
            # Verify record was saved
            history = db.get_entity_history()
            assert len(history) == 1
            
            record = history[0]
            assert record['timestamp'] == "2024-01-01T00:00:00"
            assert record['tick'] == 0
            assert record['total_entities'] == 5
            assert record['component_counts'] == component_counts
            assert record['avg_hunger'] == 0.5
            assert record['avg_thirst'] == 0.3
            assert record['avg_rest'] == 0.2
            assert record['avg_pressure_level'] == 0.1
            assert record['entities_with_pressure'] == 2
            assert record['avg_health'] == 0.8
            assert record['entities_at_risk'] == 1
            assert record['avg_age_years'] == 25.5
            assert record['avg_wealth'] == 100.0
            assert record['employed_count'] == 3
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_get_entity_history_by_tick_range(self):
        """Test querying entity history by tick range."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            
            # Save multiple records
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=100,
                total_entities=1,
                component_counts=component_counts
            )
            db.save_entity_history(
                timestamp="2024-01-01T01:00:00",
                tick=150,
                total_entities=2,
                component_counts=component_counts
            )
            db.save_entity_history(
                timestamp="2024-01-01T02:00:00",
                tick=200,
                total_entities=3,
                component_counts=component_counts
            )
            
            # Query by tick range
            history = db.get_entity_history(start_tick=100, end_tick=150)
            assert len(history) == 2
            assert history[0]['tick'] == 100
            assert history[1]['tick'] == 150
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_get_entity_history_by_datetime_range(self):
        """Test querying entity history by datetime range."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            
            # Save multiple records
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=0,
                total_entities=1,
                component_counts=component_counts
            )
            db.save_entity_history(
                timestamp="2024-01-02T00:00:00",
                tick=24,
                total_entities=2,
                component_counts=component_counts
            )
            db.save_entity_history(
                timestamp="2024-01-03T00:00:00",
                tick=48,
                total_entities=3,
                component_counts=component_counts
            )
            
            # Query by datetime range
            history = db.get_entity_history(
                start_datetime="2024-01-01T00:00:00",
                end_datetime="2024-01-02T00:00:00"
            )
            assert len(history) == 2
            assert history[0]['timestamp'] == "2024-01-01T00:00:00"
            assert history[1]['timestamp'] == "2024-01-02T00:00:00"
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_get_all_entity_history(self):
        """Test getting all entity history."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            
            # Save multiple records
            for i in range(5):
                db.save_entity_history(
                    timestamp=f"2024-01-0{i+1}T00:00:00",
                    tick=i * 24,
                    total_entities=i + 1,
                    component_counts=component_counts
                )
            
            # Get all history
            history = db.get_entity_history()
            assert len(history) == 5
            
            # Verify ordering (by tick ASC)
            for i, record in enumerate(history):
                assert record['tick'] == i * 24
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()
    
    def test_entity_history_table_created(self):
        """Test that entity_history table is created."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)
        
        try:
            db = Database(db_path)
            db.connect()
            
            # Check table exists
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='entity_history'
            """)
            result = cursor.fetchone()
            assert result is not None
            
            # Check indexes exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_entity_history_timestamp'
            """)
            assert cursor.fetchone() is not None
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_entity_history_tick'
            """)
            assert cursor.fetchone() is not None
            
            db.close()
        finally:
            if db_path.exists():
                db_path.unlink()

"""Tests for export_entities CLI tool."""

import pytest
import tempfile
import csv
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.persistence.database import Database


class TestExportEntities:
    """Test export_entities CLI tool."""
    
    def test_export_all_entity_history(self):
        """Test exporting all entity history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            output_path = Path(tmpdir) / "entities.csv"
            
            # Create database and add history
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 2, "Health": 2})
            
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=0,
                total_entities=2,
                component_counts=component_counts,
                avg_hunger=0.5,
                avg_health=0.8
            )
            db.save_entity_history(
                timestamp="2024-01-02T00:00:00",
                tick=24,
                total_entities=3,
                component_counts=component_counts,
                avg_hunger=0.6,
                avg_health=0.7
            )
            
            db.close()
            
            # Run export command
            from src.cli.export_entities import main
            with patch('sys.argv', ['export_entities', '--db', str(db_path), '--output', str(output_path)]):
                main()
            
            # Verify CSV was created
            assert output_path.exists()
            
            # Verify CSV contents
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['timestamp'] == "2024-01-01T00:00:00"
                assert rows[0]['total_entities'] == '2'
                assert rows[0]['avg_hunger'] == '0.5'
                assert rows[1]['timestamp'] == "2024-01-02T00:00:00"
                assert rows[1]['total_entities'] == '3'
    
    def test_export_with_tick_range(self):
        """Test exporting with tick range filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            output_path = Path(tmpdir) / "entities.csv"
            
            # Create database and add history
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            
            for tick in [0, 24, 48]:
                db.save_entity_history(
                    timestamp=f"2024-01-0{tick//24+1}T00:00:00",
                    tick=tick,
                    total_entities=1,
                    component_counts=component_counts
                )
            
            db.close()
            
            # Run export with tick range
            from src.cli.export_entities import main
            with patch('sys.argv', [
                'export_entities', '--db', str(db_path), '--output', str(output_path),
                '--start-tick', '0', '--end-tick', '24'
            ]):
                main()
            
            # Verify CSV contents
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['tick'] == '0'
                assert rows[1]['tick'] == '24'
    
    def test_export_with_datetime_range(self):
        """Test exporting with datetime range filter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            output_path = Path(tmpdir) / "entities.csv"
            
            # Create database and add history
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            
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
            
            db.close()
            
            # Run export with datetime range
            from src.cli.export_entities import main
            with patch('sys.argv', [
                'export_entities', '--db', str(db_path), '--output', str(output_path),
                '--start-date', '2024-01-01T00:00:00', '--end-date', '2024-01-02T00:00:00'
            ]):
                main()
            
            # Verify CSV contents
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['timestamp'] == "2024-01-01T00:00:00"
                assert rows[1]['timestamp'] == "2024-01-02T00:00:00"
    
    def test_export_pivot_format(self):
        """Test exporting in pivot format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            output_path = Path(tmpdir) / "entities.csv"
            
            # Create database and add history
            db = Database(db_path)
            db.connect()
            
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=0,
                total_entities=2,
                component_counts=json.dumps({"Needs": 2, "Health": 1})
            )
            db.save_entity_history(
                timestamp="2024-01-02T00:00:00",
                tick=24,
                total_entities=3,
                component_counts=json.dumps({"Needs": 3, "Health": 2, "Pressure": 1})
            )
            
            db.close()
            
            # Run export with pivot format
            from src.cli.export_entities import main
            with patch('sys.argv', [
                'export_entities', '--db', str(db_path), '--output', str(output_path),
                '--pivot'
            ]):
                main()
            
            # Verify CSV contents
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                # Check that component count columns exist
                assert 'component_count_Needs' in rows[0]
                assert 'component_count_Health' in rows[0]
                assert 'component_count_Pressure' in rows[0]
                assert rows[0]['component_count_Needs'] == '2'
                assert rows[1]['component_count_Needs'] == '3'
    
    def test_export_creates_output_directory(self):
        """Test that export creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            output_dir = Path(tmpdir) / "exports" / "subdir"
            output_path = output_dir / "entities.csv"
            
            # Create database
            db = Database(db_path)
            db.connect()
            
            component_counts = json.dumps({"Needs": 1})
            db.save_entity_history(
                timestamp="2024-01-01T00:00:00",
                tick=0,
                total_entities=1,
                component_counts=component_counts
            )
            db.close()
            
            # Run export
            from src.cli.export_entities import main
            with patch('sys.argv', ['export_entities', '--db', str(db_path), '--output', str(output_path)]):
                main()
            
            # Verify directory was created and file exists
            assert output_dir.exists()
            assert output_path.exists()

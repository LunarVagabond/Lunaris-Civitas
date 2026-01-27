"""SQLite persistence layer for simulation state."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.models.modifier import Modifier
from src.core.system import System
from src.systems.generics.status import StatusLevel, get_all_status_levels, calculate_resource_status
from src.systems.generics.effect_type import EffectType, get_all_effect_types
from src.systems.generics.repeat_frequency import RepeatFrequency, get_all_repeat_frequencies


class Database:
    """SQLite database for persisting simulation state.
    
    The database stores:
    - World state (datetime, ticks, RNG seed, config snapshot)
    - Resources
    - Modifiers
    - System registry
    """
    
    def __init__(self, db_path: Path):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Open database connection and create schema if needed."""
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._create_schema()
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        cursor = self._connection.cursor()
        
        # Status enum table (reference table for status levels)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_enum (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                level INTEGER NOT NULL,
                UNIQUE(id)
            )
        """)
        
        # Initialize status enum values if table is empty
        cursor.execute("SELECT COUNT(*) FROM status_enum")
        if cursor.fetchone()[0] == 0:
            for status in get_all_status_levels():
                cursor.execute("""
                    INSERT INTO status_enum (id, name, color, level)
                    VALUES (?, ?, ?, ?)
                """, (status.label, status.label, status.color, status.level))
        
        # Effect type enum table (generic, may be used elsewhere)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS effect_type (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                UNIQUE(id)
            )
        """)
        
        # Initialize effect type enum values if table is empty
        cursor.execute("SELECT COUNT(*) FROM effect_type")
        if cursor.fetchone()[0] == 0:
            for effect_type in get_all_effect_types():
                cursor.execute("""
                    INSERT INTO effect_type (id, name, level)
                    VALUES (?, ?, ?)
                """, (effect_type.label, effect_type.label, effect_type.level))
        
        # Repeat frequency enum table (generic, may be used elsewhere)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repeat_frequency (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level INTEGER NOT NULL,
                UNIQUE(id)
            )
        """)
        
        # Initialize repeat frequency enum values if table is empty
        cursor.execute("SELECT COUNT(*) FROM repeat_frequency")
        if cursor.fetchone()[0] == 0:
            for frequency in get_all_repeat_frequencies():
                cursor.execute("""
                    INSERT INTO repeat_frequency (id, name, level)
                    VALUES (?, ?, ?)
                """, (frequency.label, frequency.label, frequency.level))
        
        # World state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS world_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                datetime TEXT NOT NULL,
                ticks_elapsed INTEGER NOT NULL,
                rng_seed INTEGER,
                config_snapshot TEXT NOT NULL,
                UNIQUE(id)
            )
        """)
        
        # Resources table (with status_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_amount REAL NOT NULL,
                max_capacity REAL,
                replenishment_rate REAL,
                finite INTEGER NOT NULL DEFAULT 0,
                replenishment_frequency TEXT NOT NULL DEFAULT 'hourly',
                status_id TEXT NOT NULL DEFAULT 'moderate',
                FOREIGN KEY (status_id) REFERENCES status_enum(id)
            )
        """)
        
        # Migrate existing resources table to add status_id column if it doesn't exist
        cursor.execute("PRAGMA table_info(resources)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'status_id' not in columns:
            cursor.execute("ALTER TABLE resources ADD COLUMN status_id TEXT NOT NULL DEFAULT 'moderate'")
            # Update existing rows with calculated status
            cursor.execute("SELECT id, current_amount, max_capacity FROM resources")
            for row in cursor.fetchall():
                status = calculate_resource_status(row[1], row[2])
                cursor.execute("UPDATE resources SET status_id = ? WHERE id = ?", (status.label, row[0]))
        
        # Check if old modifiers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='modifiers'
        """)
        old_table_exists = cursor.fetchone() is not None
        
        # Backup old modifiers table if it exists and has old schema
        if old_table_exists:
            cursor.execute("PRAGMA table_info(modifiers)")
            old_columns = [row[1] for row in cursor.fetchall()]
            if 'modifier_name' not in old_columns:
                # Old schema exists - backup it
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS modifiers_old_backup AS 
                    SELECT * FROM modifiers
                """)
        
        # New modifiers table (normalized: one row per resource)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modifier_name TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                effect_type TEXT NOT NULL,
                effect_value REAL NOT NULL,
                effect_direction TEXT NOT NULL CHECK(effect_direction IN ('increase', 'decrease')),
                start_year INTEGER NOT NULL,
                end_year INTEGER NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
                repeat_probability REAL NOT NULL DEFAULT 0.0 CHECK(repeat_probability >= 0.0 AND repeat_probability <= 1.0),
                repeat_frequency TEXT NOT NULL DEFAULT 'yearly',
                repeat_rate INTEGER NOT NULL DEFAULT 1,
                repeat_duration_years INTEGER,
                parent_modifier_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (effect_type) REFERENCES effect_type(id),
                FOREIGN KEY (repeat_frequency) REFERENCES repeat_frequency(id),
                FOREIGN KEY (parent_modifier_id) REFERENCES modifiers(id),
                FOREIGN KEY (resource_id) REFERENCES resources(id)
            )
        """)
        
        # Migrate old modifiers if they exist
        if old_table_exists:
            cursor.execute("PRAGMA table_info(modifiers)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'modifier_name' not in columns and 'modifiers_old_backup' in [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                # Migrate from old backup table
                cursor.execute("SELECT * FROM modifiers_old_backup")
                for row in cursor.fetchall():
                    old_modifier = dict(row)
                    # Extract resource from target_id if target_type is 'resource'
                    if old_modifier.get('target_type') == 'resource':
                        resource_id = old_modifier.get('target_id')
                        # Parse parameters
                        import json
                        params = json.loads(old_modifier.get('parameters', '{}'))
                        # Convert to new format
                        modifier_name = old_modifier.get('id', 'migrated_modifier')
                        effect_type = 'percentage'  # Default
                        effect_value = params.get('multiplier', 1.0)
                        effect_direction = 'decrease' if effect_value < 1.0 else 'increase'
                        # Parse dates
                        from datetime import datetime
                        start_dt = datetime.fromisoformat(old_modifier.get('start_datetime'))
                        end_dt = datetime.fromisoformat(old_modifier.get('end_datetime'))
                        start_year = start_dt.year
                        end_year = end_dt.year
                        
                        # Insert into new table
                        cursor.execute("""
                            INSERT INTO modifiers 
                            (modifier_name, resource_id, effect_type, effect_value, effect_direction,
                             start_year, end_year, is_active, repeat_probability, repeat_frequency, repeat_rate)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0.0, 'yearly', 1)
                        """, (modifier_name, resource_id, effect_type, effect_value, effect_direction,
                              start_year, end_year))
        
        # Systems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS systems (
                system_id TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        self._connection.commit()
    
    def save_world_state(self, world_state: WorldState) -> None:
        """Save world state to database.
        
        Args:
            world_state: WorldState instance to save
        """
        cursor = self._connection.cursor()
        
        # Save world state (replace if exists)
        time_dict = world_state.simulation_time.to_dict()
        cursor.execute("""
            INSERT OR REPLACE INTO world_state 
            (id, datetime, ticks_elapsed, rng_seed, config_snapshot)
            VALUES (1, ?, ?, ?, ?)
        """, (
            time_dict['datetime'],
            time_dict['ticks_elapsed'],
            time_dict['rng_seed'],
            json.dumps(world_state.config_snapshot)
        ))
        
        # Save resources
        cursor.execute("DELETE FROM resources")
        for resource in world_state.get_all_resources().values():
            # Get status_id from resource
            status_id = resource.status_id if hasattr(resource, 'status_id') else 'moderate'
            cursor.execute("""
                INSERT INTO resources 
                (id, name, current_amount, max_capacity, replenishment_rate, finite, replenishment_frequency, status_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource.id,
                resource.name,
                resource.current_amount,
                resource.max_capacity,
                resource.replenishment_rate,
                1 if resource.finite else 0,
                resource.replenishment_frequency,
                status_id
            ))
        
        # Save modifiers (one row per resource)
        # Don't delete all - we want to preserve modifiers added via CLI
        # Only save modifiers that are in world_state (newly created repeats, etc.)
        for modifier in world_state._modifiers.values():
            # Check if this modifier already exists in DB (by db_id)
            if modifier.db_id:
                # Update existing
                cursor.execute("""
                    UPDATE modifiers SET
                    modifier_name=?, resource_id=?, effect_type=?, effect_value=?, effect_direction=?,
                    start_year=?, end_year=?, is_active=?, repeat_probability=?, repeat_frequency=?,
                    repeat_rate=?, repeat_duration_years=?, parent_modifier_id=?
                    WHERE id=?
                """, (
                    modifier.modifier_name,
                    modifier.resource_id,
                    modifier.effect_type_str,
                    modifier.effect_value,
                    modifier.effect_direction,
                    modifier.start_year,
                    modifier.end_year,
                    1 if modifier._is_active_flag else 0,
                    modifier.repeat_probability,
                    modifier.repeat_frequency_str,
                    modifier.repeat_rate,
                    modifier.repeat_duration_years,
                    modifier.parent_modifier_id,
                    modifier.db_id
                ))
            else:
                # Insert new (repeats created during simulation)
                cursor.execute("""
                    INSERT INTO modifiers 
                    (modifier_name, resource_id, effect_type, effect_value, effect_direction,
                     start_year, end_year, is_active, repeat_probability, repeat_frequency, 
                     repeat_rate, repeat_duration_years, parent_modifier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    modifier.modifier_name,
                    modifier.resource_id,
                    modifier.effect_type_str,
                    modifier.effect_value,
                    modifier.effect_direction,
                    modifier.start_year,
                    modifier.end_year,
                    1 if modifier._is_active_flag else 0,
                    modifier.repeat_probability,
                    modifier.repeat_frequency_str,
                    modifier.repeat_rate,
                    modifier.repeat_duration_years,
                    modifier.parent_modifier_id
                ))
                # Update modifier with new db_id
                modifier.db_id = cursor.lastrowid
        
        # Save systems
        cursor.execute("DELETE FROM systems")
        for system_id in world_state._systems.keys():
            cursor.execute("""
                INSERT INTO systems (system_id, enabled)
                VALUES (?, 1)
            """, (system_id,))
        
        self._connection.commit()
    
    def load_world_state(
        self,
        systems_registry: Optional[Dict[str, System]] = None
    ) -> WorldState:
        """Load world state from database.
        
        Args:
            systems_registry: Optional dictionary of system_id -> System to restore systems
            
        Returns:
            WorldState instance restored from database
            
        Raises:
            ValueError: If no world state exists in database
        """
        cursor = self._connection.cursor()
        
        # Load world state
        cursor.execute("SELECT * FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            raise ValueError("No world state found in database")
        
        time_dict = {
            'datetime': row['datetime'],
            'ticks_elapsed': row['ticks_elapsed'],
            'rng_seed': row['rng_seed']
        }
        simulation_time = SimulationTime.from_dict(time_dict)
        config_snapshot = json.loads(row['config_snapshot'])
        
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot=config_snapshot,
            rng_seed=row['rng_seed']
        )
        
        # Load resources
        cursor.execute("SELECT * FROM resources")
        for row in cursor.fetchall():
            row_dict = dict(row)  # Convert Row to dict for easier access
            resource = Resource(
                resource_id=row_dict['id'],
                name=row_dict['name'],
                initial_amount=row_dict['current_amount'],
                max_capacity=row_dict['max_capacity'],
                replenishment_rate=row_dict['replenishment_rate'],
                finite=bool(row_dict['finite']),
                replenishment_frequency=row_dict.get('replenishment_frequency', 'hourly')
            )
            # Set status_id if column exists (for backward compatibility)
            if 'status_id' in row_dict and row_dict['status_id']:
                resource.status_id = row_dict['status_id']
            else:
                # Calculate status if not stored (backward compatibility)
                status = calculate_resource_status(resource.current_amount, resource.max_capacity)
                resource.status_id = status.label
            world_state._resources[resource.id] = resource
        
        # Load modifiers
        cursor.execute("SELECT * FROM modifiers")
        for row in cursor.fetchall():
            row_dict = dict(row)  # Convert Row to dict for easier access
            
            modifier = Modifier(
                modifier_name=row_dict['modifier_name'],
                resource_id=row_dict['resource_id'],
                start_year=row_dict['start_year'],
                end_year=row_dict['end_year'],
                effect_type=row_dict['effect_type'],
                effect_value=row_dict['effect_value'],
                effect_direction=row_dict['effect_direction'],
                is_active=bool(row_dict['is_active']),
                repeat_probability=row_dict['repeat_probability'],
                repeat_frequency=row_dict['repeat_frequency'],
                repeat_rate=row_dict['repeat_rate'],
                repeat_duration_years=row_dict.get('repeat_duration_years'),
                parent_modifier_id=row_dict.get('parent_modifier_id'),
                db_id=row_dict['id']
            )
            # Use composite ID for world_state dict
            modifier_id = f"{row_dict['modifier_name']}_{row_dict['resource_id']}_{row_dict['id']}"
            
            world_state._modifiers[modifier_id] = modifier
        
        # Load systems (if registry provided)
        if systems_registry:
            cursor.execute("SELECT system_id FROM systems WHERE enabled = 1")
            for row in cursor.fetchall():
                system_id = row['system_id']
                if system_id in systems_registry:
                    world_state._systems[system_id] = systems_registry[system_id]
        
        return world_state
    
    def has_world_state(self) -> bool:
        """Check if world state exists in database.
        
        Returns:
            True if world state exists, False otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM world_state WHERE id = 1")
        return cursor.fetchone()[0] > 0

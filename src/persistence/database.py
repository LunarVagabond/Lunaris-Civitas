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
from src.models.entity import Entity
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
        
        # New modifiers table (normalized: one row per target)
        # Note: target_type and target_id are nullable for migration compatibility
        # but should always be set in practice (enforced at application level)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modifiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modifier_name TEXT NOT NULL,
                resource_id TEXT,  -- NULL if targeting a system
                target_type TEXT CHECK(target_type IN ('resource', 'system')),
                target_id TEXT,  -- resource_id or system_id
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
        
        # Migration: Add target_type and target_id columns if they don't exist
        cursor.execute("PRAGMA table_info(modifiers)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'target_type' not in columns:
            # Add column as nullable first, then update, then make NOT NULL
            cursor.execute("ALTER TABLE modifiers ADD COLUMN target_type TEXT")
            # Set target_type based on existing resource_id
            cursor.execute("UPDATE modifiers SET target_type = 'resource' WHERE target_type IS NULL")
            # Note: SQLite doesn't support ALTER COLUMN, so we can't make it NOT NULL
            # The constraint is enforced at application level
        if 'target_id' not in columns:
            # Add column as nullable first, then update
            cursor.execute("ALTER TABLE modifiers ADD COLUMN target_id TEXT")
            # Migrate existing resource_id to target_id
            cursor.execute("UPDATE modifiers SET target_id = resource_id WHERE target_id IS NULL")
            # Note: SQLite doesn't support ALTER COLUMN, so we can't make it NOT NULL
            # The constraint is enforced at application level
        
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
        
        # Resource history table (time-series data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tick INTEGER NOT NULL,
                resource_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status_id TEXT NOT NULL,
                utilization_percent REAL,
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (status_id) REFERENCES status_enum(id)
            )
        """)
        
        # Create indexes for query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_history_timestamp_resource 
            ON resource_history(timestamp, resource_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_history_tick 
            ON resource_history(tick)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_history_resource_id 
            ON resource_history(resource_id)
        """)
        
        # Entity history table (time-series data for entity metrics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tick INTEGER NOT NULL,
                total_entities INTEGER NOT NULL,
                component_counts TEXT NOT NULL,
                avg_hunger REAL,
                avg_thirst REAL,
                avg_rest REAL,
                avg_pressure_level REAL,
                entities_with_pressure INTEGER,
                avg_health REAL,
                entities_at_risk INTEGER,
                avg_age_years REAL,
                avg_wealth REAL,
                employed_count INTEGER,
                birth_rate REAL,
                death_rate REAL
            )
        """)
        
        # Add birth_rate and death_rate columns if they don't exist (migration)
        cursor.execute("PRAGMA table_info(entity_history)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'birth_rate' not in columns:
            cursor.execute("ALTER TABLE entity_history ADD COLUMN birth_rate REAL")
        if 'death_rate' not in columns:
            cursor.execute("ALTER TABLE entity_history ADD COLUMN death_rate REAL")
        
        # Create indexes for query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_history_timestamp 
            ON entity_history(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_history_tick 
            ON entity_history(tick)
        """)
        
        # Job history table (time-series data for employment statistics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                tick INTEGER NOT NULL,
                total_employed INTEGER NOT NULL,
                employment_rate REAL NOT NULL,
                job_distribution TEXT NOT NULL,
                avg_salary_by_job TEXT NOT NULL,
                total_salary_paid REAL NOT NULL,
                job_openings TEXT NOT NULL
            )
        """)
        
        # Create indexes for query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_history_timestamp 
            ON job_history(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_history_tick 
            ON job_history(tick)
        """)
        
        # Entities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY
            )
        """)
        
        # Components table (one row per component)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                component_type TEXT NOT NULL,
                component_data TEXT NOT NULL,
                FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE CASCADE,
                UNIQUE(entity_id, component_type)
            )
        """)
        
        # Create indexes for query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_components_entity_id 
            ON components(entity_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_components_component_type 
            ON components(component_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_components_entity_type 
            ON components(entity_id, component_type)
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
                    modifier_name=?, resource_id=?, target_type=?, target_id=?, effect_type=?, effect_value=?, effect_direction=?,
                    start_year=?, end_year=?, is_active=?, repeat_probability=?, repeat_frequency=?,
                    repeat_rate=?, repeat_duration_years=?, parent_modifier_id=?
                    WHERE id=?
                """, (
                    modifier.modifier_name,
                    modifier.resource_id,
                    modifier.target_type,
                    modifier.target_id,
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
                    (modifier_name, resource_id, target_type, target_id, effect_type, effect_value, effect_direction,
                     start_year, end_year, is_active, repeat_probability, repeat_frequency, 
                     repeat_rate, repeat_duration_years, parent_modifier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    modifier.modifier_name,
                    modifier.resource_id,
                    modifier.target_type,
                    modifier.target_id,
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
        
        # Save entities and components
        cursor.execute("DELETE FROM components")
        cursor.execute("DELETE FROM entities")
        for entity in world_state._entities.values():
            # Save entity
            cursor.execute("""
                INSERT INTO entities (entity_id)
                VALUES (?)
            """, (entity.entity_id,))
            
            # Save components
            for comp_type, component in entity.get_all_components().items():
                component_data = json.dumps(component.to_dict())
                cursor.execute("""
                    INSERT INTO components (entity_id, component_type, component_data)
                    VALUES (?, ?, ?)
                """, (entity.entity_id, comp_type, component_data))
        
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
            
            # Support both old format (resource_id only) and new format (target_type/target_id)
            # If target_type doesn't exist, assume it's a resource modifier (backward compatibility)
            if 'target_type' in row_dict and row_dict.get('target_type'):
                target_type = row_dict['target_type']
                target_id = row_dict.get('target_id', row_dict.get('resource_id'))
            else:
                # Old format - resource_id only
                target_type = 'resource'
                target_id = row_dict.get('resource_id')
            
            modifier = Modifier(
                modifier_name=row_dict['modifier_name'],
                resource_id=row_dict.get('resource_id'),  # May be None for system modifiers
                start_year=row_dict['start_year'],
                end_year=row_dict['end_year'],
                effect_type=row_dict['effect_type'],
                effect_value=row_dict['effect_value'],
                effect_direction=row_dict['effect_direction'],
                is_active=bool(row_dict['is_active']),
                repeat_probability=row_dict['repeat_probability'],
                repeat_frequency=row_dict['repeat_frequency'],
                repeat_rate=row_dict['repeat_rate'],
                target_type=target_type,
                target_id=target_id,
                repeat_duration_years=row_dict.get('repeat_duration_years'),
                parent_modifier_id=row_dict.get('parent_modifier_id'),
                db_id=row_dict['id']
            )
            # Use composite ID for world_state dict (use target_id for new format)
            modifier_id = f"{row_dict['modifier_name']}_{target_id}_{row_dict['id']}"
            
            world_state._modifiers[modifier_id] = modifier
        
        # Load entities and components
        cursor.execute("SELECT entity_id FROM entities")
        entity_ids = {row['entity_id'] for row in cursor.fetchall()}
        
        for entity_id in entity_ids:
            entity = Entity(entity_id=entity_id)
            
            # Load components for this entity
            cursor.execute("""
                SELECT component_type, component_data 
                FROM components 
                WHERE entity_id = ?
            """, (entity_id,))
            
            for row in cursor.fetchall():
                comp_type = row['component_type']
                comp_data = json.loads(row['component_data'])
                
                # Create component from data
                from src.models.component import Component
                component = Component.create_component(comp_type, comp_data)
                if component is None:
                    # Skip unknown component types (for backward compatibility)
                    continue
                entity._components[comp_type] = component
            
            world_state._entities[entity_id] = entity
        
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
    
    def save_resource_history(
        self,
        timestamp: str,
        tick: int,
        resource_id: str,
        amount: float,
        status_id: str,
        utilization_percent: Optional[float] = None
    ) -> None:
        """Save resource history record to database.
        
        Args:
            timestamp: ISO format datetime string
            tick: Simulation tick number
            resource_id: Resource identifier
            amount: Resource amount at this timestamp
            status_id: Resource status ID
            utilization_percent: Utilization percentage (None if no max_capacity)
        """
        cursor = self._connection.cursor()
        cursor.execute("""
            INSERT INTO resource_history 
            (timestamp, tick, resource_id, amount, status_id, utilization_percent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, tick, resource_id, amount, status_id, utilization_percent))
        self._connection.commit()
    
    def get_resource_history(
        self,
        resource_id: str,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get resource history for a specific resource.
        
        Args:
            resource_id: Resource identifier
            start_tick: Optional start tick (inclusive)
            end_tick: Optional end tick (inclusive)
            start_datetime: Optional start datetime ISO string (inclusive)
            end_datetime: Optional end datetime ISO string (inclusive)
            
        Returns:
            List of history records as dictionaries
        """
        cursor = self._connection.cursor()
        
        query = "SELECT * FROM resource_history WHERE resource_id = ?"
        params = [resource_id]
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        if start_datetime is not None:
            query += " AND timestamp >= ?"
            params.append(start_datetime)
        
        if end_datetime is not None:
            query += " AND timestamp <= ?"
            params.append(end_datetime)
        
        query += " ORDER BY tick ASC, timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def save_entity_history(
        self,
        timestamp: str,
        tick: int,
        total_entities: int,
        component_counts: str,
        avg_hunger: Optional[float] = None,
        avg_thirst: Optional[float] = None,
        avg_rest: Optional[float] = None,
        avg_pressure_level: Optional[float] = None,
        entities_with_pressure: int = 0,
        avg_health: Optional[float] = None,
        entities_at_risk: int = 0,
        avg_age_years: Optional[float] = None,
        avg_wealth: Optional[float] = None,
        employed_count: int = 0,
        birth_rate: Optional[float] = None,
        death_rate: Optional[float] = None
    ) -> None:
        """Save entity history record to database.
        
        Args:
            timestamp: ISO format datetime string
            tick: Simulation tick number
            total_entities: Total number of entities
            component_counts: JSON string of component_type -> count
            avg_hunger: Average hunger level (0.0-1.0)
            avg_thirst: Average thirst level (0.0-1.0)
            avg_rest: Average rest level (0.0-1.0)
            avg_pressure_level: Average pressure level (0.0-1.0)
            entities_with_pressure: Count of entities with pressure > 0
            avg_health: Average health level (0.0-1.0)
            entities_at_risk: Count of entities with health < 0.5
            avg_age_years: Average age in years
            avg_wealth: Average wealth/money
            employed_count: Count of employed entities
            birth_rate: Births per 1000 population per period
            death_rate: Deaths per 1000 population per period
        """
        cursor = self._connection.cursor()
        cursor.execute("""
            INSERT INTO entity_history 
            (timestamp, tick, total_entities, component_counts, avg_hunger, avg_thirst, 
             avg_rest, avg_pressure_level, entities_with_pressure, avg_health, 
             entities_at_risk, avg_age_years, avg_wealth, employed_count, birth_rate, death_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, tick, total_entities, component_counts, avg_hunger, avg_thirst,
            avg_rest, avg_pressure_level, entities_with_pressure, avg_health,
            entities_at_risk, avg_age_years, avg_wealth, employed_count, birth_rate, death_rate
        ))
        self._connection.commit()
    
    def get_entity_history(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entity history records.
        
        Args:
            start_tick: Optional start tick (inclusive)
            end_tick: Optional end tick (inclusive)
            start_datetime: Optional start datetime ISO string (inclusive)
            end_datetime: Optional end datetime ISO string (inclusive)
            
        Returns:
            List of history records as dictionaries
        """
        cursor = self._connection.cursor()
        
        query = "SELECT * FROM entity_history WHERE 1=1"
        params = []
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        if start_datetime is not None:
            query += " AND timestamp >= ?"
            params.append(start_datetime)
        
        if end_datetime is not None:
            query += " AND timestamp <= ?"
            params.append(end_datetime)
        
        query += " ORDER BY tick ASC, timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def save_job_history(
        self,
        timestamp: str,
        tick: int,
        total_employed: int,
        employment_rate: float,
        job_distribution: Dict[str, int],
        avg_salary_by_job: Dict[str, float],
        total_salary_paid: float,
        job_openings: Dict[str, int],
        avg_payment_by_job: Optional[Dict[str, Dict[str, float]]] = None,
        total_payment_by_resource: Optional[Dict[str, float]] = None
    ) -> None:
        """Save job history record to database.
        
        Args:
            timestamp: ISO format datetime string
            tick: Simulation tick number
            total_employed: Total number of employed entities
            employment_rate: Employment rate as percentage (0-100)
            job_distribution: Dictionary mapping job_type -> count
            avg_salary_by_job: Dictionary mapping job_type -> average salary (backward compat)
            total_salary_paid: Total salary paid across all jobs (backward compat)
            job_openings: Dictionary mapping job_type -> open slots
            avg_payment_by_job: Dictionary mapping job_type -> {resource_id: avg_amount} (new format)
            total_payment_by_resource: Dictionary mapping resource_id -> total (new format)
        """
        import json
        cursor = self._connection.cursor()
        
        # Store new format in avg_salary_by_job JSON for now (can add new columns later if needed)
        # For now, we'll store the full payment data in the JSON
        payment_data = {
            'avg_payment_by_job': avg_payment_by_job or {},
            'total_payment_by_resource': total_payment_by_resource or {}
        }
        
        cursor.execute("""
            INSERT INTO job_history 
            (timestamp, tick, total_employed, employment_rate, job_distribution, 
             avg_salary_by_job, total_salary_paid, job_openings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            tick,
            total_employed,
            employment_rate,
            json.dumps(job_distribution),
            json.dumps(payment_data),  # Store full payment data in JSON
            total_salary_paid,
            json.dumps(job_openings)
        ))
        self._connection.commit()
    
    def get_job_history(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get job history records.
        
        Args:
            start_tick: Optional start tick (inclusive)
            end_tick: Optional end tick (inclusive)
            start_datetime: Optional start datetime ISO string (inclusive)
            end_datetime: Optional end datetime ISO string (inclusive)
            
        Returns:
            List of history records as dictionaries
        """
        import json
        cursor = self._connection.cursor()
        
        query = "SELECT * FROM job_history WHERE 1=1"
        params = []
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        if start_datetime is not None:
            query += " AND timestamp >= ?"
            params.append(start_datetime)
        
        if end_datetime is not None:
            query += " AND timestamp <= ?"
            params.append(end_datetime)
        
        query += " ORDER BY tick ASC, timestamp ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Parse JSON fields
        result = []
        for row in rows:
            record = dict(row)
            # Parse JSON strings back to dictionaries
            if 'job_distribution' in record and isinstance(record['job_distribution'], str):
                record['job_distribution'] = json.loads(record['job_distribution'])
            if 'avg_salary_by_job' in record and isinstance(record['avg_salary_by_job'], str):
                payment_data = json.loads(record['avg_salary_by_job'])
                # Handle both old format (just salary dict) and new format (payment_data dict)
                if isinstance(payment_data, dict) and 'avg_payment_by_job' in payment_data:
                    # New format
                    record['avg_payment_by_job'] = payment_data.get('avg_payment_by_job', {})
                    record['total_payment_by_resource'] = payment_data.get('total_payment_by_resource', {})
                    # Extract backward compat avg_salary_by_job (money only)
                    record['avg_salary_by_job'] = {
                        job: payments.get('money', 0.0) 
                        for job, payments in payment_data.get('avg_payment_by_job', {}).items()
                    }
                else:
                    # Old format (just salary dict)
                    record['avg_salary_by_job'] = payment_data
                    record['avg_payment_by_job'] = {job: {'money': amt} for job, amt in payment_data.items()}
                    record['total_payment_by_resource'] = {}
            if 'job_openings' in record and isinstance(record['job_openings'], str):
                record['job_openings'] = json.loads(record['job_openings'])
            result.append(record)
        
        return result
    
    def get_all_resource_history(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get history for all resources.
        
        Args:
            start_tick: Optional start tick (inclusive)
            end_tick: Optional end tick (inclusive)
            start_datetime: Optional start datetime ISO string (inclusive)
            end_datetime: Optional end datetime ISO string (inclusive)
            
        Returns:
            List of history records as dictionaries
        """
        cursor = self._connection.cursor()
        
        query = "SELECT * FROM resource_history WHERE 1=1"
        params = []
        
        if start_tick is not None:
            query += " AND tick >= ?"
            params.append(start_tick)
        
        if end_tick is not None:
            query += " AND tick <= ?"
            params.append(end_tick)
        
        if start_datetime is not None:
            query += " AND timestamp >= ?"
            params.append(start_datetime)
        
        if end_datetime is not None:
            query += " AND timestamp <= ?"
            params.append(end_datetime)
        
        query += " ORDER BY tick ASC, timestamp ASC, resource_id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]

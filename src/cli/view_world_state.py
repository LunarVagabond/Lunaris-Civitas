"""CLI tool for viewing world state summary."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database
from src.core.time import SimulationTime


def format_time_elapsed(start_datetime: datetime, current_datetime: datetime) -> str:
    """Format time elapsed."""
    years = current_datetime.year - start_datetime.year
    months = current_datetime.month - start_datetime.month
    days = current_datetime.day - start_datetime.day
    
    if days < 0:
        months -= 1
        from calendar import monthrange
        if current_datetime.month == 1:
            prev_month = 12
            prev_year = current_datetime.year - 1
        else:
            prev_month = current_datetime.month - 1
            prev_year = current_datetime.year
        days_in_prev_month = monthrange(prev_year, prev_month)[1]
        days += days_in_prev_month
    
    if months < 0:
        years -= 1
        months += 12
    
    parts = []
    if years > 0:
        parts.append(f"{years}y")
    if months > 0:
        parts.append(f"{months}m")
    if years == 0 and days > 0:
        parts.append(f"{days}d")
    
    return " ".join(parts) if parts else "0d"


def main():
    """Display world state summary."""
    db_path = Path("_running/simulation.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the simulation first to create the database.")
        sys.exit(1)
    
    db = Database(db_path)
    db.connect()
    
    try:
        cursor = db._connection.cursor()
        
        # Load world state
        cursor.execute("SELECT * FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        
        if not row:
            print("No world state found in database.")
            return
        
        import json
        time_dict = {
            'datetime': row['datetime'],
            'ticks_elapsed': row['ticks_elapsed'],
            'rng_seed': row['rng_seed']
        }
        simulation_time = SimulationTime.from_dict(time_dict)
        config_snapshot = json.loads(row['config_snapshot'])
        
        current_datetime = simulation_time.current_datetime
        ticks = simulation_time.ticks_elapsed
        
        # Get start datetime from config
        sim_config = config_snapshot.get('simulation', {})
        start_datetime_str = sim_config.get('start_datetime', time_dict['datetime'])
        start_datetime = datetime.fromisoformat(start_datetime_str)
        elapsed = format_time_elapsed(start_datetime, current_datetime)
        
        # Count resources
        cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = cursor.fetchone()[0]
        
        # Count systems
        cursor.execute("SELECT COUNT(*) FROM systems WHERE enabled = 1")
        system_count = cursor.fetchone()[0]
        
        # Count active modifiers
        cursor.execute("PRAGMA table_info(modifiers)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'modifier_name' in columns:
            cursor.execute("""
                SELECT COUNT(*) FROM modifiers 
                WHERE is_active = 1 
                AND ? >= start_year 
                AND ? < end_year
            """, (current_datetime.year, current_datetime.year))
        else:
            cursor.execute("SELECT COUNT(*) FROM modifiers")
        modifier_count = cursor.fetchone()[0]
        
        print("\n=== World State ===")
        print(f"Current Date: {current_datetime.strftime('%b %d, %Y %H:00')}")
        print(f"Ticks Elapsed: {ticks:,}")
        print(f"Time Elapsed: {elapsed}")
        print(f"RNG Seed: {simulation_time.rng_seed}")
        print(f"\nSystems: {system_count}")
        print(f"Resources: {resource_count}")
        print(f"Active Modifiers: {modifier_count}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

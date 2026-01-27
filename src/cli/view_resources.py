"""CLI tool for viewing resource states."""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database
from src.systems.generics.status import StatusLevel


def get_status_indicator(status_id: str) -> str:
    """Get status indicator symbol."""
    status_map = {
        'depleted': '[DEPLETED]',
        'at_risk': '[AT_RISK]',
        'moderate': '[MODERATE]',
        'sufficient': '[SUFFICIENT]',
        'abundant': '[ABUNDANT]'
    }
    return status_map.get(status_id, '[UNKNOWN]')


def main():
    """Display resource states."""
    db_path = Path("_running/simulation.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the simulation first to create the database.")
        sys.exit(1)
    
    db = Database(db_path)
    db.connect()
    
    try:
        cursor = db._connection.cursor()
        
        # Get current year for modifier checking
        cursor.execute("SELECT datetime FROM world_state WHERE id = 1")
        row = cursor.fetchone()
        current_year = datetime.fromisoformat(row['datetime']).year if row else None
        
        # Load resources
        cursor.execute("SELECT * FROM resources ORDER BY id")
        resources = cursor.fetchall()
        
        if not resources:
            print("No resources found in database.")
            return
        
        print("\n=== Resources ===\n")
        print(f"{'ID':<15} {'Name':<20} {'Amount':<15} {'Capacity':<12} {'Util %':<8} {'Status':<15} {'Modifiers'}")
        print("-" * 100)
        
        for row in resources:
            resource_id = row['id']
            name = row['name']
            current = row['current_amount']
            max_cap = row.get('max_capacity')
            status_id = row.get('status_id', 'moderate')
            
            if max_cap:
                utilization = (current / max_cap) * 100
                capacity_str = f"{current:.1f}/{max_cap:.0f}"
                util_str = f"{utilization:.1f}%"
            else:
                capacity_str = f"{current:.1f}/∞"
                util_str = "N/A"
            
            status = get_status_indicator(status_id)
            
            # Count active modifiers for this resource
            cursor.execute("PRAGMA table_info(modifiers)")
            mod_columns = [r[1] for r in cursor.fetchall()]
            if 'modifier_name' in mod_columns and current_year:
                cursor.execute("""
                    SELECT COUNT(*) FROM modifiers
                    WHERE resource_id = ?
                    AND is_active = 1
                    AND ? >= start_year
                    AND ? < end_year
                """, (resource_id, current_year, current_year))
                mod_count = cursor.fetchone()[0]
            else:
                mod_count = 0
            
            mod_str = f"{mod_count} active" if mod_count > 0 else "-"
            
            print(f"{resource_id:<15} {name:<20} {capacity_str:<15} {util_str:<8} {status:<15} {mod_str}")
        
        print()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

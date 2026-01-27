"""CLI tool for viewing modifiers from the database."""

import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database


def main():
    """Display all modifiers from database."""
    db_path = Path("_running/simulation.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the simulation first to create the database.")
        sys.exit(1)
    
    db = Database(db_path)
    db.connect()
    
    try:
        cursor = db._connection.cursor()
        
        # Check if new structure exists
        cursor.execute("PRAGMA table_info(modifiers)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'modifier_name' in columns:
            # New structure
            cursor.execute("""
                SELECT modifier_name, resource_id, effect_type, effect_value, effect_direction,
                       start_year, end_year, is_active, repeat_probability, repeat_frequency,
                       repeat_rate, repeat_duration_years, parent_modifier_id, id
                FROM modifiers
                ORDER BY modifier_name, resource_id, start_year
            """)
            
            modifiers_by_name = defaultdict(list)
            for row in cursor.fetchall():
                modifiers_by_name[row['modifier_name']].append(dict(row))
            
            if not modifiers_by_name:
                print("No modifiers found in database.")
                return
            
            print("\n=== Modifiers ===\n")
            
            for modifier_name, rows in sorted(modifiers_by_name.items()):
                print(f"Modifier: {modifier_name}")
                print("-" * 60)
                
                for row in rows:
                    status = "ACTIVE" if row['is_active'] else "INACTIVE"
                    effect_desc = f"{row['effect_type']} {row['effect_direction']} by {row['effect_value']}"
                    if row['effect_type'] == 'percentage':
                        effect_desc += f" ({row['effect_value']*100:.1f}%)"
                    
                    print(f"  Resource: {row['resource_id']}")
                    print(f"  Effect: {effect_desc}")
                    print(f"  Duration: {row['start_year']}-{row['end_year']} ({row['end_year'] - row['start_year']} years)")
                    print(f"  Status: {status}")
                    
                    if row['repeat_probability'] > 0.0:
                        print(f"  Repeat: {row['repeat_probability']*100:.1f}% chance, {row['repeat_frequency']}, every {row['repeat_rate']}")
                        if row['repeat_duration_years']:
                            print(f"  Repeat Duration: {row['repeat_duration_years']} years")
                    
                    if row['parent_modifier_id']:
                        print(f"  Parent: modifier ID {row['parent_modifier_id']} (repeat)")
                    
                    print()
                
                print()
        else:
            # Legacy structure
            cursor.execute("SELECT * FROM modifiers")
            rows = cursor.fetchall()
            
            if not rows:
                print("No modifiers found in database.")
                return
            
            print("\n=== Modifiers (Legacy) ===\n")
            for row in rows:
                print(f"ID: {row['id']}")
                print(f"  Target: {row['target_type']}:{row['target_id']}")
                print(f"  Duration: {row['start_datetime']} to {row['end_datetime']}")
                print()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

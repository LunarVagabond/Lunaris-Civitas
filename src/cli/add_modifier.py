"""Interactive CLI tool for adding modifiers to the simulation."""

import sys
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database
from src.systems.generics.effect_type import EffectType, get_effect_type_by_id
from src.systems.generics.repeat_frequency import RepeatFrequency, get_repeat_frequency_by_id


def get_input(prompt: str, default: str = None, validator=None) -> str:
    """Get user input with optional default and validation.
    
    Args:
        prompt: Prompt text
        default: Default value (shown in brackets)
        validator: Optional validation function that returns (is_valid, error_message)
        
    Returns:
        User input or default
    """
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        value = input(full_prompt).strip()
        if not value and default:
            value = default
        
        if not value:
            print("  Value is required")
            continue
        
        if validator:
            is_valid, error = validator(value)
            if not is_valid:
                print(f"  {error}")
                continue
        
        return value


def validate_year(value: str) -> tuple[bool, str]:
    """Validate year input."""
    try:
        year = int(value)
        if year < 1900 or year > 3000:
            return False, "Year must be between 1900 and 3000"
        return True, ""
    except ValueError:
        return False, "Year must be a number"


def validate_float(value: str, min_val: float = None, max_val: float = None) -> tuple[bool, str]:
    """Validate float input."""
    try:
        fval = float(value)
        if min_val is not None and fval < min_val:
            return False, f"Value must be >= {min_val}"
        if max_val is not None and fval > max_val:
            return False, f"Value must be <= {max_val}"
        return True, ""
    except ValueError:
        return False, "Value must be a number"


def validate_resource_ids(value: str, db: Database) -> tuple[bool, str]:
    """Validate resource IDs exist in database."""
    resource_ids = [r.strip() for r in value.split(',')]
    cursor = db._connection.cursor()
    for resource_id in resource_ids:
        cursor.execute("SELECT id FROM resources WHERE id = ?", (resource_id,))
        if not cursor.fetchone():
            return False, f"Resource '{resource_id}' not found in database"
    return True, ""


def validate_effect_type(value: str) -> tuple[bool, str]:
    """Validate effect type."""
    effect_type = get_effect_type_by_id(value)
    if not effect_type:
        return False, f"Effect type must be 'percentage' or 'direct'"
    return True, ""


def validate_repeat_frequency(value: str) -> tuple[bool, str]:
    """Validate repeat frequency."""
    frequency = get_repeat_frequency_by_id(value)
    if not frequency:
        return False, f"Repeat frequency must be 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'"
    return True, ""


def validate_direction(value: str) -> tuple[bool, str]:
    """Validate effect direction."""
    if value.lower() not in ('increase', 'decrease'):
        return False, "Direction must be 'increase' or 'decrease'"
    return True, ""


def main():
    """Main interactive CLI for adding modifiers."""
    db_path = Path("_running/simulation.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Please run the simulation first to create the database.")
        sys.exit(1)
    
    db = Database(db_path)
    db.connect()
    
    try:
        print("\n=== Add Modifier ===")
        print("This will create modifier entries for each resource affected.\n")
        
        # Get modifier name
        modifier_name = get_input("Modifier name")
        
        # Get resource IDs
        cursor = db._connection.cursor()
        cursor.execute("SELECT id FROM resources ORDER BY id")
        available_resources = [row[0] for row in cursor.fetchall()]
        print(f"\nAvailable resources: {', '.join(available_resources)}")
        resource_ids_str = get_input(
            "Resource IDs (comma-separated)",
            validator=lambda v: validate_resource_ids(v, db)
        )
        resource_ids = [r.strip() for r in resource_ids_str.split(',')]
        
        # Get effect type
        print("\nEffect types:")
        print("  percentage - Multiplier-based (e.g., 0.3 = 30% reduction)")
        print("  direct - Absolute value (e.g., 500 = remove 500 units)")
        effect_type_str = get_input(
            "Effect type",
            default="percentage",
            validator=validate_effect_type
        )
        
        # Get effect value
        if effect_type_str.lower() == 'percentage':
            effect_value = float(get_input(
                "Effect value (0.0-1.0, e.g., 0.3 for 30%)",
                validator=lambda v: validate_float(v, 0.0, 1.0)
            ))
        else:
            effect_value = float(get_input(
                "Effect value (absolute amount)",
                validator=lambda v: validate_float(v, 0.0)
            ))
        
        # Get direction
        effect_direction = get_input(
            "Effect direction (increase/decrease)",
            default="decrease",
            validator=validate_direction
        ).lower()
        
        # Get years
        start_year = int(get_input(
            "Start year",
            validator=validate_year
        ))
        end_year = int(get_input(
            "End year (exclusive)",
            validator=validate_year
        ))
        
        if end_year <= start_year:
            print("Error: End year must be after start year")
            sys.exit(1)
        
        # Get repeat settings
        print("\nRepeat settings:")
        repeat_probability = float(get_input(
            "Repeat probability (0.0-1.0, e.g., 0.5 for 50%)",
            default="0.0",
            validator=lambda v: validate_float(v, 0.0, 1.0)
        ))
        
        if repeat_probability > 0.0:
            repeat_frequency_str = get_input(
                "Repeat frequency (hourly/daily/weekly/monthly/yearly)",
                default="yearly",
                validator=validate_repeat_frequency
            )
            repeat_rate = int(get_input(
                "Repeat rate (every N periods)",
                default="1",
                validator=lambda v: validate_float(v, 1.0)
            ))
            repeat_duration_str = get_input(
                "Repeat duration in years (leave empty for same as original)",
                default=""
            )
            repeat_duration_years = int(repeat_duration_str) if repeat_duration_str else None
        else:
            repeat_frequency_str = 'yearly'
            repeat_rate = 1
            repeat_duration_years = None
        
        # Insert modifier rows (one per resource)
        cursor = db._connection.cursor()
        inserted_count = 0
        
        for resource_id in resource_ids:
            cursor.execute("""
                INSERT INTO modifiers 
                (modifier_name, resource_id, effect_type, effect_value, effect_direction,
                 start_year, end_year, is_active, repeat_probability, repeat_frequency, 
                 repeat_rate, repeat_duration_years, parent_modifier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, NULL)
            """, (
                modifier_name,
                resource_id,
                effect_type_str,
                effect_value,
                effect_direction,
                start_year,
                end_year,
                repeat_probability,
                repeat_frequency_str,
                repeat_rate,
                repeat_duration_years
            ))
            inserted_count += 1
        
        db._connection.commit()
        
        print(f"\n✓ Successfully created {inserted_count} modifier row(s)")
        print(f"  Modifier: {modifier_name}")
        print(f"  Resources: {', '.join(resource_ids)}")
        print(f"  Effect: {effect_type_str} {effect_direction} by {effect_value}")
        print(f"  Duration: {start_year}-{end_year}")
        if repeat_probability > 0.0:
            print(f"  Repeat: {repeat_probability*100:.1f}% chance, {repeat_frequency_str}, every {repeat_rate}")
        
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

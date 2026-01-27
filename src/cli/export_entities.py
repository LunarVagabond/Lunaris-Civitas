"""CLI tool for exporting entity history to CSV."""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database


def main():
    """Export entity history to CSV."""
    parser = argparse.ArgumentParser(
        description="Export entity history to CSV"
    )
    parser.add_argument(
        '--db',
        type=Path,
        default=Path("_running/simulation.db"),
        help='Path to SQLite database (default: _running/simulation.db)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output CSV file path (default: _running/exports/entities_YYYYMMDD_HHMMSS.csv)'
    )
    parser.add_argument(
        '--start-tick',
        type=int,
        help='Start from tick N (inclusive)'
    )
    parser.add_argument(
        '--end-tick',
        type=int,
        help='End at tick N (inclusive)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start from datetime (ISO format, inclusive)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End at datetime (ISO format, inclusive)'
    )
    parser.add_argument(
        '--pivot',
        action='store_true',
        help='Pivot format: expand component_counts JSON into columns'
    )
    
    args = parser.parse_args()
    
    # Validate database exists
    if not args.db.exists():
        print(f"Error: Database not found at {args.db}")
        print("Please run the simulation first to create the database.")
        sys.exit(1)
    
    # Generate output path if not provided
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("_running/exports")
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output = output_dir / f"entities_{timestamp}.csv"
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    db = Database(args.db)
    db.connect()
    
    try:
        # Get entity history data
        history = db.get_entity_history(
            start_tick=args.start_tick,
            end_tick=args.end_tick,
            start_datetime=args.start_date,
            end_datetime=args.end_date
        )
        
        if not history:
            print("No entity history data found matching the criteria.")
            sys.exit(0)
        
        # Write CSV
        if args.pivot:
            _write_pivot_csv(history, args.output)
        else:
            _write_standard_csv(history, args.output)
        
        print(f"Exported {len(history)} entity history records to {args.output}")
    
    finally:
        db.close()


def _write_standard_csv(history: list, output_path: Path) -> None:
    """Write history data in standard format (one row per timestamp).
    
    Args:
        history: List of history records
        output_path: Path to output CSV file
    """
    fieldnames = [
        'timestamp', 'tick', 'total_entities', 'component_counts',
        'avg_hunger', 'avg_thirst', 'avg_rest',
        'avg_pressure_level', 'entities_with_pressure',
        'avg_health', 'entities_at_risk',
        'avg_age_years', 'avg_wealth', 'employed_count'
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in history:
            writer.writerow({
                'timestamp': record['timestamp'],
                'tick': record['tick'],
                'total_entities': record['total_entities'],
                'component_counts': record['component_counts'],
                'avg_hunger': record.get('avg_hunger') or '',
                'avg_thirst': record.get('avg_thirst') or '',
                'avg_rest': record.get('avg_rest') or '',
                'avg_pressure_level': record.get('avg_pressure_level') or '',
                'entities_with_pressure': record.get('entities_with_pressure') or 0,
                'avg_health': record.get('avg_health') or '',
                'entities_at_risk': record.get('entities_at_risk') or 0,
                'avg_age_years': record.get('avg_age_years') or '',
                'avg_wealth': record.get('avg_wealth') or '',
                'employed_count': record.get('employed_count') or 0
            })


def _write_pivot_csv(history: list, output_path: Path) -> None:
    """Write history data in pivot format (component_counts expanded into columns).
    
    Args:
        history: List of history records
        output_path: Path to output CSV file
    """
    # Collect all component types from all records
    component_types = set()
    for record in history:
        try:
            counts = json.loads(record['component_counts'])
            component_types.update(counts.keys())
        except (json.JSONDecodeError, KeyError):
            pass
    
    component_types = sorted(component_types)
    
    # Build fieldnames
    fieldnames = [
        'timestamp', 'tick', 'total_entities',
        'avg_hunger', 'avg_thirst', 'avg_rest',
        'avg_pressure_level', 'entities_with_pressure',
        'avg_health', 'entities_at_risk',
        'avg_age_years', 'avg_wealth', 'employed_count'
    ]
    
    # Add component count columns
    for comp_type in component_types:
        fieldnames.append(f'component_count_{comp_type}')
    
    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in history:
            row = {
                'timestamp': record['timestamp'],
                'tick': record['tick'],
                'total_entities': record['total_entities'],
                'avg_hunger': record.get('avg_hunger') or '',
                'avg_thirst': record.get('avg_thirst') or '',
                'avg_rest': record.get('avg_rest') or '',
                'avg_pressure_level': record.get('avg_pressure_level') or '',
                'entities_with_pressure': record.get('entities_with_pressure') or 0,
                'avg_health': record.get('avg_health') or '',
                'entities_at_risk': record.get('entities_at_risk') or 0,
                'avg_age_years': record.get('avg_age_years') or '',
                'avg_wealth': record.get('avg_wealth') or '',
                'employed_count': record.get('employed_count') or 0
            }
            
            # Parse and add component counts
            try:
                counts = json.loads(record['component_counts'])
                for comp_type in component_types:
                    row[f'component_count_{comp_type}'] = counts.get(comp_type, 0)
            except (json.JSONDecodeError, KeyError):
                for comp_type in component_types:
                    row[f'component_count_{comp_type}'] = 0
            
            writer.writerow(row)


if __name__ == "__main__":
    main()

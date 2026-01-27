"""CLI tool for exporting resource history to CSV."""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.persistence.database import Database


def main():
    """Export resource history to CSV."""
    parser = argparse.ArgumentParser(
        description="Export resource history to CSV"
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
        help='Output CSV file path (default: _running/exports/resources_YYYYMMDD_HHMMSS.csv)'
    )
    parser.add_argument(
        '--resource-id',
        action='append',
        dest='resource_ids',
        help='Filter by specific resource ID (can specify multiple times)'
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
        help='Pivot format: one column per resource'
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
        args.output = output_dir / f"resources_{timestamp}.csv"
    
    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    db = Database(args.db)
    db.connect()
    
    try:
        # Get history data
        if args.resource_ids:
            # Get history for specific resources
            all_history = []
            for resource_id in args.resource_ids:
                history = db.get_resource_history(
                    resource_id=resource_id,
                    start_tick=args.start_tick,
                    end_tick=args.end_tick,
                    start_datetime=args.start_date,
                    end_datetime=args.end_date
                )
                all_history.extend(history)
            # Sort by tick, then timestamp, then resource_id
            all_history.sort(key=lambda x: (x['tick'], x['timestamp'], x['resource_id']))
        else:
            # Get history for all resources
            all_history = db.get_all_resource_history(
                start_tick=args.start_tick,
                end_tick=args.end_tick,
                start_datetime=args.start_date,
                end_datetime=args.end_date
            )
        
        if not all_history:
            print("No history data found matching the criteria.")
            sys.exit(0)
        
        # Write CSV
        if args.pivot:
            _write_pivot_csv(all_history, args.output)
        else:
            _write_standard_csv(all_history, args.output)
        
        print(f"Exported {len(all_history)} history records to {args.output}")
    
    finally:
        db.close()


def _write_standard_csv(history: list, output_path: Path) -> None:
    """Write history data in standard format (one row per resource per timestamp).
    
    Args:
        history: List of history records
        output_path: Path to output CSV file
    """
    fieldnames = ['timestamp', 'tick', 'resource_id', 'amount', 'status_id', 'utilization_percent']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in history:
            writer.writerow({
                'timestamp': record['timestamp'],
                'tick': record['tick'],
                'resource_id': record['resource_id'],
                'amount': record['amount'],
                'status_id': record['status_id'],
                'utilization_percent': record.get('utilization_percent') or ''
            })


def _write_pivot_csv(history: list, output_path: Path) -> None:
    """Write history data in pivot format (one column per resource).
    
    Args:
        history: List of history records
        output_path: Path to output CSV file
    """
    # Group by timestamp/tick
    grouped = {}
    resource_ids = set()
    
    for record in history:
        key = (record['timestamp'], record['tick'])
        if key not in grouped:
            grouped[key] = {}
        grouped[key][record['resource_id']] = record
        resource_ids.add(record['resource_id'])
    
    # Sort resource IDs for consistent column order
    resource_ids = sorted(resource_ids)
    
    # Build fieldnames
    fieldnames = ['timestamp', 'tick']
    for resource_id in resource_ids:
        fieldnames.extend([
            f'{resource_id}_amount',
            f'{resource_id}_status',
            f'{resource_id}_utilization'
        ])
    
    # Write CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Sort by tick, then timestamp
        sorted_keys = sorted(grouped.keys(), key=lambda x: (x[1], x[0]))
        
        for timestamp, tick in sorted_keys:
            row = {
                'timestamp': timestamp,
                'tick': tick
            }
            
            for resource_id in resource_ids:
                if resource_id in grouped[(timestamp, tick)]:
                    record = grouped[(timestamp, tick)][resource_id]
                    row[f'{resource_id}_amount'] = record['amount']
                    row[f'{resource_id}_status'] = record['status_id']
                    row[f'{resource_id}_utilization'] = record.get('utilization_percent') or ''
                else:
                    row[f'{resource_id}_amount'] = ''
                    row[f'{resource_id}_status'] = ''
                    row[f'{resource_id}_utilization'] = ''
            
            writer.writerow(row)


if __name__ == "__main__":
    main()

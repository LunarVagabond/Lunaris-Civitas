"""Main simulation engine and loop."""

import random
from calendar import monthrange
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from src.core.time import SimulationTime
from src.core.world_state import WorldState
from src.core.system import System
from src.core.logging import setup_logging, get_logger
from src.config.loader import load_config
from src.persistence.database import Database
from src.systems.generics.status import StatusLevel
from src.models.modifier import Modifier


logger = get_logger('engine')


class Simulation:
    """Main simulation engine.
    
    Manages the simulation loop, system registration, time progression,
    and persistence.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
        resume: bool = False
    ):
        """Initialize simulation.
        
        Args:
            config_path: Path to configuration file (required if not resuming)
            db_path: Path to SQLite database (defaults to _running/simulation.db)
            resume: If True, resume from database instead of creating new
        """
        self.db_path = db_path or Path("_running/simulation.db")
        self.resume = resume
        self.config_path = config_path
        
        self.world_state: Optional[WorldState] = None
        self.systems_registry: Dict[str, System] = {}
        self.running = False
        
        # Logging configuration
        self.logging_config: Dict[str, Any] = {}
        self.last_world_state_log: Optional[datetime] = None
        self.last_systems_log: Optional[datetime] = None
        
        # Change tracking for logging
        self.last_resource_values: Dict[str, float] = {}  # resource_id -> last logged amount
        self.last_log_ticks: int = 0  # Ticks at last log
        self.start_datetime: Optional[datetime] = None  # Simulation start datetime for elapsed time
    
    def register_system(self, system: System) -> None:
        """Register a system with the simulation.
        
        Args:
            system: System instance to register
        """
        if system.system_id in self.systems_registry:
            raise ValueError(f"System {system.system_id} is already registered")
        
        self.systems_registry[system.system_id] = system
        # Removed verbose debug logging for system registration
    
    def _initialize_new_simulation(self, config: Dict[str, Any]) -> None:
        """Initialize a new simulation from configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Extract simulation config
        sim_config = config.get('simulation', {})
        start_datetime_str = sim_config.get('start_datetime', '2024-01-01T00:00:00')
        rng_seed_config = sim_config.get('rng_seed')
        
        # Handle "RANDOM" seed or numeric seed
        if rng_seed_config == "RANDOM" or (isinstance(rng_seed_config, str) and rng_seed_config.upper() == "RANDOM"):
            # Generate random seed
            rng_seed = random.randint(0, 2**31 - 1)
            logger.info(f"Generated random RNG seed: {rng_seed}")
            # Update config snapshot to store actual seed (not "RANDOM")
            config = config.copy()
            config['simulation'] = config.get('simulation', {}).copy()
            config['simulation']['rng_seed'] = rng_seed
        elif rng_seed_config is not None:
            # Use provided numeric seed
            try:
                rng_seed = int(rng_seed_config)
            except (ValueError, TypeError):
                logger.warning(f"Invalid rng_seed value '{rng_seed_config}', using None (non-deterministic)")
                rng_seed = None
        else:
            # No seed provided
            rng_seed = None
        
        start_datetime = datetime.fromisoformat(start_datetime_str)
        self.start_datetime = start_datetime  # Store for elapsed time calculation
        simulation_time = SimulationTime(start_datetime, rng_seed)
        
        # Add db_path to config snapshot for systems that need it (e.g., HistorySystem)
        config_with_db = config.copy()
        if 'simulation' not in config_with_db:
            config_with_db['simulation'] = {}
        config_with_db['simulation']['db_path'] = str(self.db_path)
        
        # Create world state
        self.world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot=config_with_db,
            rng_seed=rng_seed
        )
        
        # Initialize resources
        resources_config = config.get('resources', [])
        for res_config in resources_config:
            from src.models.resource import Resource
            resource = Resource(
                resource_id=res_config['id'],
                name=res_config['name'],
                initial_amount=res_config['initial_amount'],
                max_capacity=res_config.get('max_capacity'),
                replenishment_rate=res_config.get('replenishment_rate'),
                finite=res_config.get('finite', False),
                replenishment_frequency=res_config.get('replenishment_frequency', 'hourly')
            )
            self.world_state.add_resource(resource)
        
        # Register and initialize systems
        systems_config = config.get('systems', [])
        for system_name in systems_config:
            if system_name not in self.systems_registry:
                logger.warning(f"System {system_name} not registered, skipping")
                continue
            
            system = self.systems_registry[system_name]
            self.world_state.register_system(system)
            
            # Get system-specific config
            system_config = config.get('systems_config', {}).get(system_name, {})
            system.init(self.world_state, system_config)
        
        # Store logging config
        self.logging_config = config.get('logging', {})
        
        # Initialize change tracking
        for resource_id, resource in self.world_state.get_all_resources().items():
            self.last_resource_values[resource_id] = resource.current_amount
        self.last_log_ticks = self.world_state.simulation_time.ticks_elapsed
        
        logger.debug(
            f"Initialized new simulation: {len(self.world_state.get_all_resources())} resources, "
            f"{len(self.world_state.get_all_systems())} systems"
        )
        
        # Log initial world state (get frequency/rate from config)
        world_state_config = self.logging_config.get('world_state', {})
        frequency = world_state_config.get('frequency', 'weekly')
        rate = world_state_config.get('rate', 1)
        self._log_world_state(frequency=frequency, rate=rate)
    
    def _resume_simulation(self) -> None:
        """Resume simulation from database."""
        with Database(self.db_path) as db:
            if not db.has_world_state():
                raise ValueError("No saved simulation found in database")
            
            self.world_state = db.load_world_state(
                systems_registry=self.systems_registry
            )
            
            # Re-initialize systems with their config
            config = self.world_state.config_snapshot
            systems_config = config.get('systems_config', {})
            
            for system in self.world_state.get_all_systems():
                system_config = systems_config.get(system.system_id, {})
                system.init(self.world_state, system_config)
        
        # Store logging config from snapshot
        self.logging_config = self.world_state.config_snapshot.get('logging', {})
        
        # Get start datetime from config snapshot
        sim_config = self.world_state.config_snapshot.get('simulation', {})
        start_datetime_str = sim_config.get('start_datetime', '2024-01-01T00:00:00')
        self.start_datetime = datetime.fromisoformat(start_datetime_str)
        
        # Initialize change tracking
        for resource_id, resource in self.world_state.get_all_resources().items():
            self.last_resource_values[resource_id] = resource.current_amount
        self.last_log_ticks = self.world_state.simulation_time.ticks_elapsed
        
        logger.debug(
            f"Resumed simulation: {self.world_state.simulation_time.current_datetime}, "
            f"{self.world_state.simulation_time.ticks_elapsed} ticks elapsed"
        )
        
        # Log current world state (get frequency/rate from config)
        world_state_config = self.logging_config.get('world_state', {})
        frequency = world_state_config.get('frequency', 'weekly')
        rate = world_state_config.get('rate', 1)
        self._log_world_state(frequency=frequency, rate=rate)
    
    def run(self, max_ticks: Optional[int] = None) -> None:
        """Run the simulation.
        
        Args:
            max_ticks: Maximum number of ticks to run (None = unlimited)
        """
        if self.running:
            raise RuntimeError("Simulation is already running")
        
        # Initialize or resume
        if self.resume:
            self._resume_simulation()
        else:
            # If world_state is already initialized (e.g., in tests), skip initialization
            if self.world_state is None:
                if not self.config_path:
                    raise ValueError("config_path required for new simulation")
                config = load_config(self.config_path)
                self._initialize_new_simulation(config)
        
        self.running = True
        logger.info("Starting simulation loop")
        
        try:
            tick_count = 0
            while True:
                if max_ticks and tick_count >= max_ticks:
                    logger.info(f"Reached max_ticks limit: {max_ticks}")
                    break
                
                # Advance time
                current_datetime = self.world_state.simulation_time.advance_tick()
                tick_count += 1
                
                # Check for modifier repeats (before cleanup)
                self._check_modifier_repeats(current_datetime)
                
                # Cleanup expired modifiers
                expired = self.world_state.cleanup_expired_modifiers()
                # Removed verbose debug logging for modifier cleanup
                
                # Call all systems
                for system in self.world_state.get_all_systems():
                    try:
                        system.on_tick(self.world_state, current_datetime)
                    except Exception as e:
                        logger.error(
                            f"Error in system {system.system_id} on tick {tick_count}: {e}",
                            exc_info=True
                        )
                
                # Periodic save (every 24 ticks = 1 day)
                if tick_count % 24 == 0:
                    self.save()
                
                # Configurable logging
                self._check_and_log(current_datetime)
        
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        finally:
            # Final save
            self.save()
            self.running = False
            logger.info("Simulation stopped")
    
    def _should_log(self, frequency: str, rate: int, last_log: Optional[datetime], current_datetime: datetime) -> bool:
        """Check if logging should happen based on frequency and rate.
        
        Args:
            frequency: 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
            rate: Log every N periods (e.g., rate=2 means every 2 weeks)
            last_log: Last time this was logged (None = never logged)
            current_datetime: Current simulation datetime
            
        Returns:
            True if logging should happen
        """
        # Check if we're at the start of a period boundary
        at_period_start = False
        
        if frequency == 'hourly':
            at_period_start = True  # Every hour is a period start
        elif frequency == 'daily':
            at_period_start = current_datetime.hour == 0
        elif frequency == 'weekly':
            at_period_start = current_datetime.weekday() == 0 and current_datetime.hour == 0
        elif frequency == 'monthly':
            at_period_start = current_datetime.day == 1 and current_datetime.hour == 0
        elif frequency == 'yearly':
            at_period_start = (current_datetime.month == 1 and 
                              current_datetime.day == 1 and 
                              current_datetime.hour == 0)
        else:
            return False
        
        if not at_period_start:
            return False
        
        if last_log is None:
            # First log - log immediately if at period start
            return True
        
        # Calculate periods since last log
        if frequency == 'hourly':
            hours_diff = int((current_datetime - last_log).total_seconds() / 3600)
            return hours_diff >= rate
        elif frequency == 'daily':
            days_diff = (current_datetime.date() - last_log.date()).days
            return days_diff >= rate
        elif frequency == 'weekly':
            # Calculate weeks difference
            weeks_diff = (current_datetime.date() - last_log.date()).days / 7
            return int(weeks_diff) >= rate
        elif frequency == 'monthly':
            months_diff = (current_datetime.year - last_log.year) * 12 + (current_datetime.month - last_log.month)
            return months_diff >= rate
        elif frequency == 'yearly':
            years_diff = current_datetime.year - last_log.year
            return years_diff >= rate
        
        return False
    
    def _format_readable_date(self, dt: datetime) -> str:
        """Format datetime to readable format.
        
        Args:
            dt: Datetime to format
            
        Returns:
            Formatted string like "Feb 1, 2030"
        """
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{month_names[dt.month - 1]} {dt.day}, {dt.year}"
    
    def _format_time_elapsed(self, start_datetime: datetime, current_datetime: datetime) -> str:
        """Format time elapsed since start.
        
        Args:
            start_datetime: Simulation start datetime
            current_datetime: Current simulation datetime
            
        Returns:
            Formatted string like "6y 2m" or "2y 5m 12d"
        """
        years = current_datetime.year - start_datetime.year
        months = current_datetime.month - start_datetime.month
        days = current_datetime.day - start_datetime.day
        
        # Adjust for negative days/months
        if days < 0:
            months -= 1
            # Get days in previous month
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
        
        # Format based on duration
        parts = []
        if years > 0:
            parts.append(f"{years}y")
        if months > 0:
            parts.append(f"{months}m")
        if years == 0 and days > 0:  # Only show days if less than a year
            parts.append(f"{days}d")
        
        return " ".join(parts) if parts else "0d"
    
    def _get_resource_status(self, resource: Any) -> str:
        """Get status indicator for a resource using status enum.
        
        Args:
            resource: Resource instance
            
        Returns:
            Status indicator string with color code
        """
        status = resource.status
        # Format as [STATUS_NAME] with color hint
        status_display = status.short_name
        return f"[{status_display}]"
    
    def _calculate_period_rate(
        self,
        delta: float,
        frequency: str,
        rate: int,
        last_datetime: datetime,
        current_datetime: datetime
    ) -> tuple[float, str]:
        """Calculate period-appropriate rate.
        
        Args:
            delta: Change in resource amount
            frequency: Logging frequency ('hourly', 'daily', 'weekly', 'monthly', 'yearly')
            rate: Logging rate (every N periods)
            last_datetime: Last log datetime
            current_datetime: Current datetime
            
        Returns:
            Tuple of (rate_value, rate_unit_string)
        """
        if frequency == 'hourly':
            hours = (current_datetime - last_datetime).total_seconds() / 3600
            if hours > 0:
                return (delta / hours, '/hr')
            return (0.0, '/hr')
        
        elif frequency == 'daily':
            days = (current_datetime.date() - last_datetime.date()).days
            if days > 0:
                if rate == 1:
                    return (delta / days, '/day')
                else:
                    period_days = days / rate
                    return (delta / period_days, f'/{rate}days')
            return (0.0, '/day')
        
        elif frequency == 'weekly':
            days = (current_datetime.date() - last_datetime.date()).days
            weeks = days / 7.0
            if weeks > 0:
                if rate == 1:
                    return (delta / weeks, '/week')
                else:
                    period_weeks = weeks / rate
                    return (delta / period_weeks, f'/{rate}weeks')
            return (0.0, '/week')
        
        elif frequency == 'monthly':
            # Calculate months difference
            years_diff = current_datetime.year - last_datetime.year
            months_diff = current_datetime.month - last_datetime.month
            total_months = years_diff * 12 + months_diff
            
            if total_months > 0:
                if rate == 1:
                    return (delta / total_months, '/month')
                else:
                    period_months = total_months / rate
                    return (delta / period_months, f'/{rate}months')
            return (0.0, '/month')
        
        elif frequency == 'yearly':
            years = current_datetime.year - last_datetime.year
            if years > 0:
                if rate == 1:
                    return (delta / years, '/year')
                else:
                    period_years = years / rate
                    return (delta / period_years, f'/{rate}years')
            return (0.0, '/year')
        
        return (0.0, '/period')
    
    def _check_modifier_repeats(self, current_datetime: datetime) -> None:
        """Check for modifier repeats and create new modifier entries if probability triggers.
        
        Modifiers never "fall off" - when they expire, if repeat triggers, a new record
        is created immediately to continue the effect seamlessly.
        
        Args:
            current_datetime: Current simulation datetime
        """
        if not self.world_state:
            return
        
        # Get all modifiers that have expired and should check for repeat
        expired_modifiers = []
        for modifier in self.world_state._modifiers.values():
            # Check if modifier expires at this datetime boundary
            if modifier.has_expired(current_datetime) and modifier.repeat_probability > 0.0:
                if modifier.should_check_repeat(current_datetime):
                    expired_modifiers.append(modifier)
        
        # Check each expired modifier for repeat
        for modifier in expired_modifiers:
            # Roll probability die
            roll = self.world_state.rng.random()
            if roll < modifier.repeat_probability:
                # Repeat triggered - create new modifier entry immediately
                # This ensures the modifier never "falls off" - seamless continuation
                self._create_modifier_repeat(modifier, current_datetime)
    
    def _create_modifier_repeat(self, parent_modifier: Modifier, current_datetime: datetime) -> None:
        """Create a repeat of a modifier.
        
        Args:
            parent_modifier: The modifier that is repeating
            current_datetime: Current simulation datetime
        """
        if not self.world_state:
            return
        
        # Calculate new duration
        if parent_modifier.repeat_duration_years:
            duration_years = parent_modifier.repeat_duration_years
        else:
            # Use same duration as original
            duration_years = parent_modifier.end_year - parent_modifier.start_year
        
        # New start/end years - start in the year after expiration
        # If modifier expires at start of 2025, repeat starts at start of 2026
        new_start_year = parent_modifier.end_year
        # If we're checking at the end of the expiration year, start next year
        if current_datetime.year == parent_modifier.end_year:
            new_start_year = parent_modifier.end_year + 1
        new_end_year = new_start_year + duration_years
        
        # Create new modifier entry (same resource, inherits all properties)
        new_modifier = Modifier(
            modifier_name=parent_modifier.modifier_name,
            resource_id=parent_modifier.resource_id,
            start_year=new_start_year,
            end_year=new_end_year,
            effect_type=parent_modifier.effect_type_str,
            effect_value=parent_modifier.effect_value,
            effect_direction=parent_modifier.effect_direction,
            is_active=True,
            repeat_probability=parent_modifier.repeat_probability,
            repeat_frequency=parent_modifier.repeat_frequency_str,
            repeat_rate=parent_modifier.repeat_rate,
            repeat_duration_years=parent_modifier.repeat_duration_years,
            parent_modifier_id=parent_modifier.db_id
        )
        
        # Add to world state
        modifier_id = f"{new_modifier.modifier_name}_{new_modifier.resource_id}_{new_start_year}"
        self.world_state._modifiers[modifier_id] = new_modifier
        
        # Also save to database immediately
        from src.persistence.database import Database
        db = Database(self.db_path)
        db.connect()
        try:
            cursor = db._connection.cursor()
            cursor.execute("""
                INSERT INTO modifiers 
                (modifier_name, resource_id, effect_type, effect_value, effect_direction,
                 start_year, end_year, is_active, repeat_probability, repeat_frequency, 
                 repeat_rate, repeat_duration_years, parent_modifier_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_modifier.modifier_name,
                new_modifier.resource_id,
                new_modifier.effect_type_str,
                new_modifier.effect_value,
                new_modifier.effect_direction,
                new_modifier.start_year,
                new_modifier.end_year,
                1,
                new_modifier.repeat_probability,
                new_modifier.repeat_frequency_str,
                new_modifier.repeat_rate,
                new_modifier.repeat_duration_years,
                new_modifier.parent_modifier_id
            ))
            db._connection.commit()
            logger.info(
                f"Modifier '{new_modifier.modifier_name}' repeated for resource '{new_modifier.resource_id}' "
                f"({new_start_year}-{new_end_year})"
            )
        finally:
            db.close()
    
    def _log_world_state(self, frequency: str = 'weekly', rate: int = 1) -> None:
        """Log world state summary including enabled systems and resource states with changes.
        
        Args:
            frequency: Logging frequency for period-appropriate rate calculation
            rate: Logging rate (every N periods)
        """
        if not self.world_state:
            return
        
        current_datetime = self.world_state.simulation_time.current_datetime
        ticks = self.world_state.simulation_time.ticks_elapsed
        
        # Format readable date
        readable_date = self._format_readable_date(current_datetime)
        
        # Calculate time elapsed
        elapsed_str = ""
        if self.start_datetime:
            elapsed_str = f", Elapsed: {self._format_time_elapsed(self.start_datetime, current_datetime)}"
        
        # System status
        systems = self.world_state.get_all_systems()
        system_ids = [s.system_id for s in systems]
        
        # Calculate resource changes and rates
        resources = self.world_state.get_all_resources()
        
        resource_changes = []
        resource_rates = []
        
        for resource_id, resource in resources.items():
            current_amount = resource.current_amount
            
            # Format with capacity and percentage
            if resource.max_capacity is not None:
                utilization = (current_amount / resource.max_capacity) * 100
                capacity_str = f"{current_amount:.1f}/{resource.max_capacity:.0f} ({utilization:.1f}%)"
            else:
                capacity_str = f"{current_amount:.1f}"
            
            # Get status indicator
            status = self._get_resource_status(resource)
            
            # Calculate delta and rate
            if resource_id in self.last_resource_values:
                last_amount = self.last_resource_values[resource_id]
                delta = current_amount - last_amount
                
                # Calculate period-appropriate rate
                if self.last_world_state_log:
                    rate_value, rate_unit = self._calculate_period_rate(
                        delta, frequency, rate, self.last_world_state_log, current_datetime
                    )
                    resource_changes.append(
                        f"{resource_id}: {capacity_str} {status} ({delta:+.1f})"
                    )
                    resource_rates.append(f"{resource_id}: {rate_value:+.2f}{rate_unit}")
                else:
                    resource_changes.append(f"{resource_id}: {capacity_str} {status}")
            else:
                # First log - no change
                resource_changes.append(f"{resource_id}: {capacity_str} {status}")
            
            # Update tracking
            self.last_resource_values[resource_id] = current_amount
        
        # Modifiers summary
        active_modifiers = self.world_state.get_active_modifiers()
        modifier_count = len(active_modifiers)
        
        # Format summary
        changes_summary = ", ".join(resource_changes)
        rates_summary = ", ".join(resource_rates) if resource_rates else "N/A"
        
        # Enhanced log line with all information
        logger.info(
            f"World State | {readable_date} (Tick {ticks}{elapsed_str}) | "
            f"Systems: {len(system_ids)} [{', '.join(system_ids)}] | "
            f"Resources: {changes_summary} | "
            f"Rates: {rates_summary} | "
            f"Modifiers: {modifier_count}"
        )
        
        # Update last log ticks and datetime
        self.last_log_ticks = ticks
        self.last_world_state_log = current_datetime
    
    def _log_systems_metrics(self) -> None:
        """Log system-specific metrics (disabled by default - too verbose)."""
        # System metrics logging disabled - not useful at daily frequency
        # Systems don't change frequently enough to warrant daily logging
        pass
    
    def _check_and_log(self, current_datetime: datetime) -> None:
        """Check logging configuration and log if needed.
        
        Args:
            current_datetime: Current simulation datetime
        """
        # World state logging
        world_state_config = self.logging_config.get('world_state', {})
        if world_state_config.get('enabled', False):
            frequency = world_state_config.get('frequency', 'weekly')
            rate = world_state_config.get('rate', 1)
            
            if self._should_log(frequency, rate, self.last_world_state_log, current_datetime):
                self._log_world_state(frequency=frequency, rate=rate)
        
        # Systems metrics logging
        systems_config = self.logging_config.get('systems', {})
        if systems_config.get('enabled', False):
            frequency = systems_config.get('frequency', 'daily')
            rate = systems_config.get('rate', 1)
            
            if self._should_log(frequency, rate, self.last_systems_log, current_datetime):
                self._log_systems_metrics()
                self.last_systems_log = current_datetime
    
    def _format_resources_summary(self) -> str:
        """Format a summary of resource states.
        
        Returns:
            String summary of resources
        """
        resources = self.world_state.get_all_resources()
        summaries = []
        for resource_id, resource in resources.items():
            summaries.append(
                f"{resource_id}: {resource.current_amount:.1f}"
            )
        return ", ".join(summaries)
    
    def save(self) -> None:
        """Save simulation state to database."""
        with Database(self.db_path) as db:
            db.save_world_state(self.world_state)
        # Removed verbose debug logging - saves happen frequently (daily)
    
    def shutdown(self) -> None:
        """Shutdown the simulation and all systems."""
        if not self.world_state:
            return
        
        for system in self.world_state.get_all_systems():
            try:
                system.shutdown(self.world_state)
            except Exception as e:
                logger.error(
                    f"Error shutting down system {system.system_id}: {e}",
                    exc_info=True
                )
        
        self.save()
        logger.info("Simulation shutdown complete")

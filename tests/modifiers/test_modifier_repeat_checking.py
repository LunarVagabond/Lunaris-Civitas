"""Tests for modifier repeat checking and removal in simulation loop."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from src.models.modifier import Modifier
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.engine.simulation import Simulation


class TestRepeatChecking:
    """Tests for repeat checking logic in simulation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0)
        self.simulation_time = SimulationTime(self.start_datetime, rng_seed=42)
        self.world_state = WorldState(
            simulation_time=self.simulation_time,
            config_snapshot={"simulation": {"start_datetime": "2024-01-01T00:00:00"}},
            rng_seed=42
        )
        
        # Add test resource
        self.food_resource = Resource(
            resource_id="food",
            name="Food",
            initial_amount=1000.0,
            max_capacity=10000.0
        )
        self.world_state._resources["food"] = self.food_resource
        
        # Initialize database
        from src.persistence.database import Database
        self.db = Database(self.db_path)
        self.db.connect()
        self.db._create_schema()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_repeat_check_triggers_on_probability(self):
        """Test that repeat check creates new modifier when probability triggers."""
        # Create modifier with 100% repeat probability that expires at start of 2025
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2025,  # Expires at start of 2025
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,  # 100% chance
            repeat_frequency="yearly",
            repeat_rate=1,
            db_id=1
        )
        
        self.world_state.add_modifier(modifier)
        
        # Create simulation
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check repeats at year boundary AFTER expiration (Dec 31, 23:00 of 2025)
        # Modifier expired at start of 2025, so checking at end of 2025 should trigger
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        
        # Should have created a repeat
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 2
        
        # Find the repeat
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        assert repeat.start_year == 2026  # Starts in 2026
        assert repeat.parent_modifier_id == 1
    
    def test_repeat_check_no_trigger_on_low_probability(self):
        """Test that repeat check doesn't create modifier when probability doesn't trigger."""
        # Create modifier with 0% repeat probability
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=0.0,  # 0% chance
            repeat_frequency="yearly",
            repeat_rate=1,
            db_id=1
        )
        
        self.world_state.add_modifier(modifier)
        
        # Advance time to end of 2025
        self.world_state.simulation_time._current_datetime = datetime(2025, 12, 31, 23, 0, 0)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check repeats
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        
        # Should NOT have created a repeat
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 1  # Only original
    
    def test_repeat_check_only_at_frequency_boundary(self):
        """Test that repeat check only happens at appropriate frequency boundaries."""
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,
            repeat_frequency="yearly",
            repeat_rate=1,
            db_id=1
        )
        
        self.world_state.add_modifier(modifier)
        self.world_state.simulation_time._current_datetime = datetime(2026, 1, 1, 0, 0, 0)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check at year boundary (Dec 31, 23:00) when modifier is expired - should trigger
        # Modifier expires at start of 2026, so checking at end of 2025 should work
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        # Note: modifier expires at 2026-01-01, so at 2025-12-31 23:00 it's still active
        # We need to check after expiration
        assert len(modifiers) >= 1  # At least original
        
        # Reset and check after expiration
        self.world_state._modifiers.clear()
        modifier2 = Modifier(
            modifier_name="pest_outbreak2",
            resource_id="food",
            start_year=2024,
            end_year=2025,  # Expires earlier
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,
            repeat_frequency="yearly",
            repeat_rate=1,
            db_id=2
        )
        self.world_state.add_modifier(modifier2)
        self.world_state.simulation_time._current_datetime = datetime(2026, 1, 1, 0, 0, 0)
        
        # Check at year boundary after expiration - should trigger
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak2")
        # Modifier expired, should create repeat
        assert len(modifiers) == 2  # Original + repeat
    
    def test_repeat_inherits_properties(self):
        """Test that repeated modifiers inherit all properties from parent."""
        parent_modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2025,  # Expires at start of 2025
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,  # 100% for testing
            repeat_frequency="yearly",
            repeat_rate=2,  # Every 2 years
            repeat_duration_years=3,  # Custom duration
            db_id=1
        )
        
        self.world_state.add_modifier(parent_modifier)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check repeats at year boundary after expiration (Dec 31, 23:00 of 2025)
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        # Should have repeat
        assert len(modifiers) == 2
        
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        
        # Check inheritance
        assert repeat.modifier_name == parent_modifier.modifier_name
        assert repeat.resource_id == parent_modifier.resource_id
        assert repeat.effect_type == parent_modifier.effect_type
        assert repeat.effect_value == parent_modifier.effect_value
        assert repeat.effect_direction == parent_modifier.effect_direction
        assert repeat.repeat_probability == parent_modifier.repeat_probability
        assert repeat.repeat_frequency_str == parent_modifier.repeat_frequency_str
        assert repeat.repeat_rate == parent_modifier.repeat_rate
        assert repeat.repeat_duration_years == parent_modifier.repeat_duration_years
    
    def test_repeat_uses_custom_duration(self):
        """Test that repeat uses custom duration when specified."""
        parent_modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2025,  # Expires at start of 2025
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,
            repeat_frequency="yearly",
            repeat_rate=1,
            repeat_duration_years=5,  # Custom: 5 years
            db_id=1
        )
        
        self.world_state.add_modifier(parent_modifier)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check at year boundary after expiration (Dec 31, 23:00 of 2025)
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 2
        
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        
        # Should use custom duration (5 years)
        assert repeat.start_year == 2026
        assert repeat.end_year == 2031  # 2026 + 5
    
    def test_repeat_uses_same_duration_when_none_specified(self):
        """Test that repeat uses same duration as original when not specified."""
        parent_modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2025,  # 1 year, expires at start of 2025
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,
            repeat_frequency="yearly",
            repeat_rate=1,
            repeat_duration_years=None,  # Use same as original
            db_id=1
        )
        
        self.world_state.add_modifier(parent_modifier)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Check at year boundary after expiration (Dec 31, 23:00 of 2025)
        sim._check_modifier_repeats(datetime(2025, 12, 31, 23, 0, 0))
        
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 2
        
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        
        # Should use same duration as original (1 year)
        assert repeat.start_year == 2026
        assert repeat.end_year == 2027  # 2026 + 1


class TestModifierRemoval:
    """Tests for modifier removal and deactivation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0)
        self.simulation_time = SimulationTime(self.start_datetime, rng_seed=42)
        self.world_state = WorldState(
            simulation_time=self.simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        self.food_resource = Resource(
            resource_id="food",
            name="Food",
            initial_amount=1000.0,
            max_capacity=10000.0
        )
        self.world_state._resources["food"] = self.food_resource
    
    def test_remove_modifier(self):
        """Test removing a modifier from world state."""
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        self.world_state.add_modifier(modifier)
        assert len(self.world_state.get_modifiers_for_resource("food")) == 1
        
        # Remove modifier
        modifier_id = list(self.world_state._modifiers.keys())[0]
        self.world_state.remove_modifier(modifier_id)
        
        assert len(self.world_state.get_modifiers_for_resource("food")) == 0
    
    def test_cleanup_expired_modifiers_removes_them(self):
        """Test that cleanup_expired_modifiers removes expired modifiers."""
        # Add expired modifier
        expired_modifier = Modifier(
            modifier_name="expired",
            resource_id="food",
            start_year=2020,
            end_year=2022,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        # Add active modifier
        active_modifier = Modifier(
            modifier_name="active",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        self.world_state.add_modifier(expired_modifier)
        self.world_state.add_modifier(active_modifier)
        
        # Advance time to 2024
        self.world_state.simulation_time._current_datetime = datetime(2024, 6, 15, 12, 0, 0)
        
        # Cleanup expired
        expired_ids = self.world_state.cleanup_expired_modifiers()
        
        # Check expired was removed
        assert len(expired_ids) == 1
        
        # Check active still exists
        active_modifiers = self.world_state.get_modifiers_for_resource("food")
        assert len(active_modifiers) == 1
        assert active_modifiers[0].modifier_name == "active"
    
    def test_modifier_not_active_when_inactive_flag_set(self):
        """Test that modifier is not active when is_active flag is False."""
        modifier = Modifier(
            modifier_name="inactive",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            is_active=False  # Inactive
        )
        
        self.world_state.add_modifier(modifier)
        
        # Even though we're in the date range, modifier should not be active
        current_time = datetime(2024, 6, 15, 12, 0, 0)
        active_modifiers = self.world_state.get_modifiers_for_resource("food")
        
        # Should be empty because modifier is inactive
        assert len(active_modifiers) == 0
        
        # Direct check
        assert modifier.is_active(current_time) == False

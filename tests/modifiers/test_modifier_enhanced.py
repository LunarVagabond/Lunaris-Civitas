"""Tests for enhanced modifier system with repeat mechanics and effect types."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from src.models.modifier import Modifier
from src.core.world_state import WorldState
from src.core.time import SimulationTime
from src.models.resource import Resource
from src.systems.generics.effect_type import EffectType
from src.systems.generics.repeat_frequency import RepeatFrequency
from src.persistence.database import Database


class TestNewStructureModifier:
    """Tests for new structure modifiers."""
    
    def test_modifier_creation_new_structure(self):
        """Test creating a modifier with new structure."""
        modifier = Modifier(
            modifier_name="pest_outbreak_2024",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        assert modifier.modifier_name == "pest_outbreak_2024"
        assert modifier.resource_id == "food"
        assert modifier.start_year == 2024
        assert modifier.end_year == 2026
        assert modifier.effect_type == EffectType.PERCENTAGE
        assert modifier.effect_value == 0.3
        assert modifier.effect_direction == "decrease"
        assert modifier._is_new_structure == True
    
    def test_modifier_validation_new_structure(self):
        """Test validation for new structure modifiers."""
        # Missing required fields (now raises ValueError for missing start_year/end_year)
        with pytest.raises(ValueError, match="start_year and end_year required"):
            Modifier(
                modifier_name="test",
                resource_id="food",
                start_year=None,
                end_year=None,
                effect_type="percentage",
                effect_value=0.3,
                effect_direction="decrease"
            )
        
        # End year before start year
        with pytest.raises(ValueError, match="end_year.*must be after start_year"):
            Modifier(
                modifier_name="test",
                resource_id="food",
                start_year=2026,
                end_year=2024,
                effect_type="percentage",
                effect_value=0.3,
                effect_direction="decrease"
            )
        
        # Invalid effect direction
        with pytest.raises(ValueError, match="effect_direction must be"):
            Modifier(
                modifier_name="test",
                resource_id="food",
                start_year=2024,
                end_year=2026,
                effect_type="percentage",
                effect_value=0.3,
                effect_direction="invalid"
            )
    
    def test_modifier_is_active_new_structure(self):
        """Test is_active for new structure modifiers."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        # Before start year
        assert modifier.is_active(datetime(2023, 12, 31, 23, 0, 0)) == False
        
        # During active period
        assert modifier.is_active(datetime(2024, 6, 15, 12, 0, 0)) == True
        assert modifier.is_active(datetime(2025, 1, 1, 0, 0, 0)) == True
        
        # At end year (exclusive)
        assert modifier.is_active(datetime(2026, 1, 1, 0, 0, 0)) == False
        
        # After end year
        assert modifier.is_active(datetime(2026, 6, 15, 12, 0, 0)) == False
    
    def test_modifier_has_expired_new_structure(self):
        """Test has_expired for new structure modifiers."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        assert modifier.has_expired(datetime(2025, 12, 31, 23, 0, 0)) == False
        assert modifier.has_expired(datetime(2026, 1, 1, 0, 0, 0)) == True
        assert modifier.has_expired(datetime(2027, 1, 1, 0, 0, 0)) == True
    
    def test_modifier_calculate_effect_percentage(self):
        """Test effect calculation for percentage modifiers."""
        # Decrease by 30%
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        assert modifier.calculate_effect(100.0) == 70.0  # 100 * (1 - 0.3)
        assert modifier.calculate_effect(200.0) == 140.0
        
        # Increase by 50%
        modifier2 = Modifier(
            modifier_name="test2",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.5,
            effect_direction="increase"
        )
        
        assert modifier2.calculate_effect(100.0) == 150.0  # 100 * (1 + 0.5)
    
    def test_modifier_calculate_effect_direct(self):
        """Test effect calculation for direct modifiers."""
        # Decrease by 50 units
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="direct",
            effect_value=50.0,
            effect_direction="decrease"
        )
        
        assert modifier.calculate_effect(100.0) == 50.0  # 100 - 50
        assert modifier.calculate_effect(200.0) == 150.0
        
        # Increase by 25 units
        modifier2 = Modifier(
            modifier_name="test2",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="direct",
            effect_value=25.0,
            effect_direction="increase"
        )
        
        assert modifier2.calculate_effect(100.0) == 125.0  # 100 + 25
    
    def test_modifier_targets_resource_new_structure(self):
        """Test resource targeting for new structure."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        assert modifier.targets_resource("food") == True
        assert modifier.targets_resource("water") == False


class TestRepeatMechanics:
    """Tests for modifier repeat mechanics."""
    
    def test_should_check_repeat_yearly(self):
        """Test repeat check timing for yearly frequency."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_frequency="yearly"
        )
        
        # End of year (Dec 31, 23:00)
        assert modifier.should_check_repeat(datetime(2025, 12, 31, 23, 0, 0)) == True
        
        # Not end of year
        assert modifier.should_check_repeat(datetime(2025, 6, 15, 12, 0, 0)) == False
        assert modifier.should_check_repeat(datetime(2025, 12, 30, 23, 0, 0)) == False
    
    def test_should_check_repeat_monthly(self):
        """Test repeat check timing for monthly frequency."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_frequency="monthly"
        )
        
        # End of month (last day, 23:00)
        assert modifier.should_check_repeat(datetime(2025, 1, 31, 23, 0, 0)) == True
        assert modifier.should_check_repeat(datetime(2025, 2, 28, 23, 0, 0)) == True  # Non-leap year
        
        # Not end of month
        assert modifier.should_check_repeat(datetime(2025, 1, 30, 23, 0, 0)) == False
    
    def test_should_check_repeat_daily(self):
        """Test repeat check timing for daily frequency."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_frequency="daily"
        )
        
        # End of day (23:00)
        assert modifier.should_check_repeat(datetime(2025, 6, 15, 23, 0, 0)) == True
        
        # Not end of day
        assert modifier.should_check_repeat(datetime(2025, 6, 15, 22, 0, 0)) == False
    
    def test_should_check_repeat_hourly(self):
        """Test repeat check timing for hourly frequency."""
        modifier = Modifier(
            modifier_name="test",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_frequency="hourly"
        )
        
        # Should check every hour
        assert modifier.should_check_repeat(datetime(2025, 6, 15, 12, 0, 0)) == True
        assert modifier.should_check_repeat(datetime(2025, 6, 15, 13, 0, 0)) == True


class TestModifierInWorldState:
    """Tests for modifiers in WorldState."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0)
        self.simulation_time = SimulationTime(self.start_datetime, rng_seed=42)
        self.world_state = WorldState(
            simulation_time=self.simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        # Add a test resource
        self.food_resource = Resource(
            resource_id="food",
            name="Food",
            initial_amount=1000.0,
            max_capacity=10000.0
        )
        self.world_state._resources["food"] = self.food_resource
    
    def test_add_modifier_new_structure(self):
        """Test adding a new structure modifier to world state."""
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
        
        # Check modifier is in world state
        modifiers = self.world_state.get_modifiers_for_resource("food")
        assert len(modifiers) == 1
        assert modifiers[0].modifier_name == "pest_outbreak"
    
    def test_get_modifiers_for_resource(self):
        """Test getting modifiers for a specific resource."""
        # Add modifiers for different resources
        modifier1 = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        modifier2 = Modifier(
            modifier_name="drought",
            resource_id="water",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.5,
            effect_direction="decrease"
        )
        
        self.world_state.add_modifier(modifier1)
        self.world_state.add_modifier(modifier2)
        
        # Get modifiers for food
        food_modifiers = self.world_state.get_modifiers_for_resource("food")
        assert len(food_modifiers) == 1
        assert food_modifiers[0].resource_id == "food"
        
        # Get modifiers for water
        water_modifiers = self.world_state.get_modifiers_for_resource("water")
        assert len(water_modifiers) == 1
        assert water_modifiers[0].resource_id == "water"
    
    def test_get_modifiers_by_name(self):
        """Test getting modifiers grouped by name."""
        # Add multiple rows for same modifier name
        modifier1 = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        modifier2 = Modifier(
            modifier_name="pest_outbreak",
            resource_id="water",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
        
        self.world_state.add_modifier(modifier1)
        self.world_state.add_modifier(modifier2)
        
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 2
        assert all(m.modifier_name == "pest_outbreak" for m in modifiers)
    
    def test_cleanup_expired_modifiers(self):
        """Test cleanup of expired modifiers."""
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
        
        self.world_state.add_modifier(active_modifier)
        self.world_state.add_modifier(expired_modifier)
        
        # Advance time to 2024
        self.world_state.simulation_time._current_datetime = datetime(2024, 6, 15, 12, 0, 0)
        
        # Cleanup expired
        expired_ids = self.world_state.cleanup_expired_modifiers()
        
        # Check expired modifier was removed
        assert len(expired_ids) == 1
        assert "expired" in expired_ids[0] or expired_modifier.modifier_name in expired_ids[0]
        
        # Check active modifier still exists
        active_modifiers = self.world_state.get_modifiers_for_resource("food")
        assert len(active_modifiers) == 1
        assert active_modifiers[0].modifier_name == "active"


class TestModifierRepeatCreation:
    """Tests for creating modifier repeats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0)
        self.simulation_time = SimulationTime(self.start_datetime, rng_seed=42)
        self.world_state = WorldState(
            simulation_time=self.simulation_time,
            config_snapshot={},
            rng_seed=42
        )
        
        # Initialize database
        self.db = Database(self.db_path)
        self.db.connect()
        self.db._create_schema()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_create_modifier_repeat_same_duration(self):
        """Test creating a modifier repeat with same duration."""
        from src.engine.simulation import Simulation
        
        # Create parent modifier
        parent_modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=1.0,  # 100% chance for testing
            repeat_frequency="yearly",
            repeat_rate=1,
            db_id=1
        )
        
        # Set world state time to end of 2025 (modifier expires at start of 2026)
        self.world_state.simulation_time._current_datetime = datetime(2025, 12, 31, 23, 0, 0)
        self.world_state.add_modifier(parent_modifier)
        
        # Create simulation instance to access _create_modifier_repeat
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Create repeat at year boundary after expiration
        sim._create_modifier_repeat(parent_modifier, datetime(2025, 12, 31, 23, 0, 0))
        
        # Check new modifier was created
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        assert len(modifiers) == 2
        
        # Find the repeat
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        assert repeat.start_year == 2026  # Starts in 2026 (next year after expiration)
        assert repeat.end_year == 2028  # Same duration (2 years)
        assert repeat.parent_modifier_id == 1
        assert repeat.effect_value == 0.3  # Inherited
    
    def test_create_modifier_repeat_custom_duration(self):
        """Test creating a modifier repeat with custom duration."""
        from src.engine.simulation import Simulation
        
        # Create parent modifier with custom repeat duration
        parent_modifier = Modifier(
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
            repeat_duration_years=3,  # Custom duration
            db_id=1
        )
        
        self.world_state.simulation_time._current_datetime = datetime(2025, 12, 31, 23, 0, 0)
        self.world_state.add_modifier(parent_modifier)
        
        sim = Simulation(db_path=self.db_path)
        sim.world_state = self.world_state
        
        # Create repeat at year boundary after expiration
        sim._create_modifier_repeat(parent_modifier, datetime(2025, 12, 31, 23, 0, 0))
        
        # Check repeat has custom duration
        modifiers = self.world_state.get_modifiers_by_name("pest_outbreak")
        repeat = [m for m in modifiers if m.parent_modifier_id == 1][0]
        assert repeat.start_year == 2026  # Starts in 2026 (next year after expiration)
        assert repeat.end_year == 2029  # Custom duration (3 years)


class TestModifierInSystems:
    """Tests for modifier application in resource systems."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.start_datetime = datetime(2024, 1, 1, 0, 0, 0)
        self.simulation_time = SimulationTime(self.start_datetime, rng_seed=42)
        self.world_state = WorldState(
            simulation_time=self.simulation_time,
            config_snapshot={},
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
    
    def test_production_system_with_percentage_modifier(self):
        """Test production system applying percentage modifier."""
        from src.systems.resource.production import ResourceProductionSystem
        
        # Add percentage modifier (30% reduction)
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
        
        # Create production system
        system = ResourceProductionSystem()
        system.production_rates = {"food": 100.0}
        system.production_frequencies = {"food": "hourly"}
        system.last_production_hour = {}
        
        # Calculate production rate
        rate = system._calculate_production_rate(self.world_state, "food", 100.0)
        
        # Should be reduced by 30%
        assert rate == 70.0  # 100 * (1 - 0.3)
    
    def test_production_system_with_direct_modifier(self):
        """Test production system applying direct modifier."""
        from src.systems.resource.production import ResourceProductionSystem
        
        # Add direct modifier (remove 50 units)
        modifier = Modifier(
            modifier_name="equipment_failure",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="direct",
            effect_value=50.0,
            effect_direction="decrease"
        )
        self.world_state.add_modifier(modifier)
        
        system = ResourceProductionSystem()
        system.production_rates = {"food": 100.0}
        system.production_frequencies = {"food": "hourly"}
        system.last_production_hour = {}
        
        rate = system._calculate_production_rate(self.world_state, "food", 100.0)
        
        # Should be reduced by 50 units
        assert rate == 50.0  # 100 - 50
    
    def test_consumption_system_with_modifier(self):
        """Test consumption system applying modifier."""
        from src.systems.resource.consumption import ResourceConsumptionSystem
        
        # Add modifier (reduce consumption by 20%)
        modifier = Modifier(
            modifier_name="rationing",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.2,
            effect_direction="decrease"
        )
        self.world_state.add_modifier(modifier)
        
        system = ResourceConsumptionSystem()
        system.consumption_rates = {"food": 100.0}
        system.consumption_frequencies = {"food": "hourly"}
        system.last_consumption_hour = {}
        
        rate = system._calculate_consumption_rate(self.world_state, "food", 100.0)
        
        # Should be reduced by 20%
        assert rate == 80.0  # 100 * (1 - 0.2)
    
    def test_replenishment_system_with_modifier(self):
        """Test replenishment system applying modifier."""
        from src.systems.resource.replenishment import ResourceReplenishmentSystem
        
        # Add modifier (reduce replenishment by 50%)
        modifier = Modifier(
            modifier_name="drought",
            resource_id="water",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.5,
            effect_direction="decrease"
        )
        
        # Add water resource
        water_resource = Resource(
            resource_id="water",
            name="Water",
            initial_amount=5000.0,
            max_capacity=10000.0
        )
        self.world_state._resources["water"] = water_resource
        self.world_state.add_modifier(modifier)
        
        system = ResourceReplenishmentSystem()
        system.replenishment_rates = {"water": 100.0}
        system.replenishment_frequencies = {"water": "hourly"}
        system.last_replenishment_hour = {}
        
        rate = system._calculate_replenishment_rate(self.world_state, "water", 100.0)
        
        # Should be reduced by 50%
        assert rate == 50.0  # 100 * (1 - 0.5)
    
    def test_multiple_modifiers_stack(self):
        """Test that multiple modifiers stack correctly."""
        from src.systems.resource.production import ResourceProductionSystem
        
        # Add two percentage modifiers
        modifier1 = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.2,  # 20% reduction
            effect_direction="decrease"
        )
        modifier2 = Modifier(
            modifier_name="equipment_failure",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,  # 30% reduction
            effect_direction="decrease"
        )
        
        self.world_state.add_modifier(modifier1)
        self.world_state.add_modifier(modifier2)
        
        system = ResourceProductionSystem()
        system.production_rates = {"food": 100.0}
        system.production_frequencies = {"food": "hourly"}
        system.last_production_hour = {}
        
        rate = system._calculate_production_rate(self.world_state, "food", 100.0)
        
        # First modifier: 100 * 0.8 = 80
        # Second modifier: 80 * 0.7 = 56
        assert rate == pytest.approx(56.0, rel=0.01)


class TestModifierDatabase:
    """Tests for modifier database operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        
        self.db = Database(self.db_path)
        self.db.connect()
        self.db._create_schema()
        
        # Add a test resource
        cursor = self.db._connection.cursor()
        cursor.execute("""
            INSERT INTO resources 
            (id, name, current_amount, max_capacity, replenishment_rate, finite, replenishment_frequency, status_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("food", "Food", 1000.0, 10000.0, None, 0, "hourly", "moderate"))
        self.db._connection.commit()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_modifier(self):
        """Test saving and loading modifiers from database."""
        from src.core.time import SimulationTime
        from src.core.world_state import WorldState
        import json
        
        # Create modifier
        modifier = Modifier(
            modifier_name="pest_outbreak",
            resource_id="food",
            start_year=2024,
            end_year=2026,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease",
            repeat_probability=0.5,
            repeat_frequency="yearly",
            repeat_rate=1
        )
        
        # Create world state and add modifier
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={"simulation": {"start_datetime": "2024-01-01T00:00:00"}},
            rng_seed=42
        )
        
        # Add resource
        food_resource = Resource(
            resource_id="food",
            name="Food",
            initial_amount=1000.0,
            max_capacity=10000.0
        )
        world_state._resources["food"] = food_resource
        
        world_state.add_modifier(modifier)
        
        # Save to database
        self.db.save_world_state(world_state)
        
        # Load from database
        loaded_world_state = self.db.load_world_state()
        
        # Check modifier was loaded
        loaded_modifiers = loaded_world_state.get_modifiers_for_resource("food")
        assert len(loaded_modifiers) == 1
        assert loaded_modifiers[0].modifier_name == "pest_outbreak"
        assert loaded_modifiers[0].effect_value == 0.3
        assert loaded_modifiers[0].repeat_probability == 0.5
    
    def test_modifier_repeat_inheritance(self):
        """Test that repeated modifiers inherit properties correctly."""
        from src.core.time import SimulationTime
        from src.core.world_state import WorldState
        import json
        
        # Create world state first (required for load_world_state)
        simulation_time = SimulationTime(datetime(2024, 1, 1, 0, 0, 0), rng_seed=42)
        world_state = WorldState(
            simulation_time=simulation_time,
            config_snapshot={"simulation": {"start_datetime": "2024-01-01T00:00:00"}},
            rng_seed=42
        )
        
        # Add resource
        food_resource = Resource(
            resource_id="food",
            name="Food",
            initial_amount=1000.0,
            max_capacity=10000.0
        )
        world_state._resources["food"] = food_resource
        
        # Save world state
        self.db.save_world_state(world_state)
        
        cursor = self.db._connection.cursor()
        
        # Insert parent modifier
        cursor.execute("""
            INSERT INTO modifiers 
            (modifier_name, resource_id, target_type, target_id, effect_type, effect_value, effect_direction,
             start_year, end_year, is_active, repeat_probability, repeat_frequency, 
             repeat_rate, repeat_duration_years, parent_modifier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "pest_outbreak", "food", "resource", "food", "percentage", 0.3, "decrease",
            2024, 2026, 1, 0.5, "yearly", 1, 2, None
        ))
        parent_id = cursor.lastrowid
        
        # Insert repeat modifier
        cursor.execute("""
            INSERT INTO modifiers 
            (modifier_name, resource_id, target_type, target_id, effect_type, effect_value, effect_direction,
             start_year, end_year, is_active, repeat_probability, repeat_frequency, 
             repeat_rate, repeat_duration_years, parent_modifier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "pest_outbreak", "food", "resource", "food", "percentage", 0.3, "decrease",
            2026, 2028, 1, 0.5, "yearly", 1, 2, parent_id
        ))
        
        self.db._connection.commit()
        
        # Load modifiers
        loaded_world_state = self.db.load_world_state()
        modifiers = loaded_world_state.get_modifiers_by_name("pest_outbreak")
        
        assert len(modifiers) == 2
        
        # Find parent and repeat
        parent = [m for m in modifiers if m.parent_modifier_id is None][0]
        repeat = [m for m in modifiers if m.parent_modifier_id == parent_id][0]
        
        # Check inheritance
        assert repeat.effect_type == parent.effect_type
        assert repeat.effect_value == parent.effect_value
        assert repeat.effect_direction == parent.effect_direction
        assert repeat.repeat_probability == parent.repeat_probability
        assert repeat.repeat_frequency_str == parent.repeat_frequency_str
        assert repeat.repeat_rate == parent.repeat_rate

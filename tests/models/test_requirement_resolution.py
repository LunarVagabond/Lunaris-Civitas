"""Unit tests for requirement resolution system."""

import pytest
from datetime import datetime

from src.models.entity import Entity
from src.models.requirement_source import RequirementSource
from src.models.requirement_resolution import RequirementResolution
from src.models.components.needs import NeedsComponent
from src.models.components.inventory import InventoryComponent
from src.models.components.wealth import WealthComponent
from src.core.world_state import WorldState
from src.core.time import SimulationTime


class TestRequirementResolution:
    """Test RequirementResolution dataclass."""
    
    def test_requirement_resolution_success(self):
        """Test successful resolution."""
        resolution = RequirementResolution(
            success=True,
            source_id="inventory",
            amount_fulfilled=10.0,
            amount_requested=10.0
        )
        assert resolution.success
        assert resolution.unmet_pressure == 0.0
    
    def test_requirement_resolution_failure(self):
        """Test failed resolution."""
        resolution = RequirementResolution(
            success=False,
            source_id=None,
            amount_fulfilled=0.0,
            amount_requested=10.0
        )
        assert not resolution.success
        assert resolution.unmet_pressure == 10.0


class TestRequirementSource:
    """Test RequirementSource class."""
    
    def test_source_is_available_with_component(self):
        """Test source availability check with component condition."""
        entity = Entity()
        entity.add_component(InventoryComponent())
        
        source = RequirementSource(
            source_id="inventory",
            source_type="inventory",
            priority=1,
            conditions={"has_component": "Inventory"},
            requirements={},
            fulfillment_method="consume"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        assert source.is_available(entity, world_state)
    
    def test_source_not_available_without_component(self):
        """Test source not available without required component."""
        entity = Entity()
        
        source = RequirementSource(
            source_id="inventory",
            source_type="inventory",
            priority=1,
            conditions={"has_component": "Inventory"},
            requirements={},
            fulfillment_method="consume"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        assert not source.is_available(entity, world_state)
    
    def test_source_can_fulfill_from_inventory(self):
        """Test fulfillment check from inventory."""
        entity = Entity()
        inventory = InventoryComponent(resources={'food': 10.0})
        entity.add_component(inventory)
        
        source = RequirementSource(
            source_id="inventory",
            source_type="inventory",
            priority=1,
            conditions={"has_component": "Inventory"},
            requirements={},
            fulfillment_method="consume"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        can_fulfill, reason = source.can_fulfill(entity, "food", 5.0, world_state)
        assert can_fulfill
        assert reason is None
    
    def test_source_cannot_fulfill_insufficient_inventory(self):
        """Test fulfillment check fails with insufficient inventory."""
        entity = Entity()
        inventory = InventoryComponent(resources={'food': 2.0})
        entity.add_component(inventory)
        
        source = RequirementSource(
            source_id="inventory",
            source_type="inventory",
            priority=1,
            conditions={"has_component": "Inventory"},
            requirements={},
            fulfillment_method="consume"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        can_fulfill, reason = source.can_fulfill(entity, "food", 5.0, world_state)
        assert not can_fulfill
        assert reason is not None
    
    def test_source_can_fulfill_from_market(self):
        """Test fulfillment check from market with money."""
        entity = Entity()
        wealth = WealthComponent(money=100.0)
        entity.add_component(wealth)
        
        source = RequirementSource(
            source_id="market",
            source_type="market",
            priority=2,
            conditions={"has_component": "Wealth"},
            requirements={"money": 5.0},
            fulfillment_method="purchase"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        # Need 5.0 * 10 = 50.0 money for 10 units
        can_fulfill, reason = source.can_fulfill(entity, "food", 10.0, world_state)
        assert can_fulfill
        assert reason is None
    
    def test_source_cannot_fulfill_insufficient_money(self):
        """Test fulfillment check fails with insufficient money."""
        entity = Entity()
        wealth = WealthComponent(money=10.0)
        entity.add_component(wealth)
        
        source = RequirementSource(
            source_id="market",
            source_type="market",
            priority=2,
            conditions={"has_component": "Wealth"},
            requirements={"money": 5.0},
            fulfillment_method="purchase"
        )
        
        world_state = WorldState(
            simulation_time=SimulationTime(datetime(2020, 1, 1)),
            config_snapshot={}
        )
        
        # Need 5.0 * 10 = 50.0 money for 10 units, only have 10.0
        can_fulfill, reason = source.can_fulfill(entity, "food", 10.0, world_state)
        assert not can_fulfill
        assert reason is not None

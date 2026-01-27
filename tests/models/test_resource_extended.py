"""Extended tests for Resource model."""

import pytest
from datetime import datetime

from src.models.resource import Resource
from src.systems.generics.status import StatusLevel


def test_resource_add():
    """Test adding to resource."""
    resource = Resource("water", "Water", 100.0, max_capacity=200.0)
    
    added = resource.add(50.0)
    assert added == 50.0
    assert resource.current_amount == 150.0


def test_resource_add_exceeds_capacity():
    """Test adding that exceeds capacity."""
    resource = Resource("water", "Water", 100.0, max_capacity=150.0)
    
    added = resource.add(100.0)
    assert added == 50.0  # Only 50 can be added
    assert resource.current_amount == 150.0
    assert resource.is_at_capacity()


def test_resource_add_no_capacity_limit():
    """Test adding to resource without capacity limit."""
    resource = Resource("water", "Water", 100.0, max_capacity=None)
    
    added = resource.add(1000.0)
    assert added == 1000.0
    assert resource.current_amount == 1100.0


def test_resource_add_negative():
    """Test adding negative amount raises error."""
    resource = Resource("water", "Water", 100.0)
    
    with pytest.raises(ValueError, match="Cannot add negative amount"):
        resource.add(-10.0)


def test_resource_consume():
    """Test consuming from resource."""
    resource = Resource("water", "Water", 100.0)
    
    consumed = resource.consume(30.0)
    assert consumed == 30.0
    assert resource.current_amount == 70.0


def test_resource_consume_exceeds_amount():
    """Test consuming more than available."""
    resource = Resource("water", "Water", 50.0)
    
    consumed = resource.consume(100.0)
    assert consumed == 50.0  # Only 50 available
    assert resource.current_amount == 0.0
    assert resource.is_depleted()


def test_resource_consume_negative():
    """Test consuming negative amount raises error."""
    resource = Resource("water", "Water", 100.0)
    
    with pytest.raises(ValueError, match="Cannot consume negative amount"):
        resource.consume(-10.0)


def test_resource_set_amount():
    """Test setting resource amount directly."""
    resource = Resource("water", "Water", 100.0, max_capacity=200.0)
    
    resource.set_amount(150.0)
    assert resource.current_amount == 150.0


def test_resource_set_amount_exceeds_capacity():
    """Test setting amount that exceeds capacity raises error."""
    resource = Resource("water", "Water", 100.0, max_capacity=150.0)
    
    with pytest.raises(ValueError, match="exceeds max_capacity"):
        resource.set_amount(200.0)


def test_resource_set_amount_negative():
    """Test setting negative amount raises error."""
    resource = Resource("water", "Water", 100.0)
    
    with pytest.raises(ValueError, match="cannot be negative"):
        resource.set_amount(-10.0)


def test_resource_is_depleted():
    """Test checking if resource is depleted."""
    resource = Resource("water", "Water", 0.0)
    assert resource.is_depleted()
    
    resource.add(10.0)
    assert not resource.is_depleted()
    
    resource.consume(10.0)
    assert resource.is_depleted()


def test_resource_is_at_capacity():
    """Test checking if resource is at capacity."""
    resource = Resource("water", "Water", 100.0, max_capacity=100.0)
    assert resource.is_at_capacity()
    
    resource.consume(10.0)
    assert not resource.is_at_capacity()
    
    resource.add(10.0)
    assert resource.is_at_capacity()


def test_resource_is_at_capacity_no_limit():
    """Test checking capacity when no limit."""
    resource = Resource("water", "Water", 100.0, max_capacity=None)
    assert not resource.is_at_capacity()


def test_resource_should_replenish_hourly():
    """Test should_replenish for hourly frequency."""
    resource = Resource("water", "Water", 100.0, replenishment_rate=10.0, replenishment_frequency='hourly')
    
    # Should always replenish hourly
    assert resource.should_replenish(datetime(2024, 1, 1, 0, 0, 0))
    assert resource.should_replenish(datetime(2024, 1, 1, 12, 30, 0))
    assert resource.should_replenish(datetime(2024, 1, 1, 23, 59, 0))


def test_resource_should_replenish_daily():
    """Test should_replenish for daily frequency."""
    resource = Resource("water", "Water", 100.0, replenishment_rate=10.0, replenishment_frequency='daily')
    
    # Should only replenish at midnight
    assert resource.should_replenish(datetime(2024, 1, 1, 0, 0, 0))
    assert not resource.should_replenish(datetime(2024, 1, 1, 12, 0, 0))
    assert not resource.should_replenish(datetime(2024, 1, 1, 23, 59, 0))


def test_resource_should_replenish_weekly():
    """Test should_replenish for weekly frequency."""
    resource = Resource("water", "Water", 100.0, replenishment_rate=10.0, replenishment_frequency='weekly')
    
    # Monday (weekday 0) at midnight
    monday = datetime(2024, 1, 1, 0, 0, 0)  # Jan 1, 2024 is a Monday
    assert resource.should_replenish(monday)
    
    # Tuesday at midnight
    tuesday = datetime(2024, 1, 2, 0, 0, 0)
    assert not resource.should_replenish(tuesday)
    
    # Monday at noon
    monday_noon = datetime(2024, 1, 1, 12, 0, 0)
    assert not resource.should_replenish(monday_noon)


def test_resource_should_replenish_monthly():
    """Test should_replenish for monthly frequency."""
    resource = Resource("water", "Water", 100.0, replenishment_rate=10.0, replenishment_frequency='monthly')
    
    # 1st of month at midnight
    assert resource.should_replenish(datetime(2024, 1, 1, 0, 0, 0))
    assert resource.should_replenish(datetime(2024, 2, 1, 0, 0, 0))
    
    # 2nd of month
    assert not resource.should_replenish(datetime(2024, 1, 2, 0, 0, 0))
    
    # 1st at noon
    assert not resource.should_replenish(datetime(2024, 1, 1, 12, 0, 0))


def test_resource_should_replenish_yearly():
    """Test should_replenish for yearly frequency."""
    resource = Resource("water", "Water", 100.0, replenishment_rate=10.0, replenishment_frequency='yearly')
    
    # January 1st at midnight
    assert resource.should_replenish(datetime(2024, 1, 1, 0, 0, 0))
    assert resource.should_replenish(datetime(2025, 1, 1, 0, 0, 0))
    
    # January 2nd
    assert not resource.should_replenish(datetime(2024, 1, 2, 0, 0, 0))
    
    # January 1st at noon
    assert not resource.should_replenish(datetime(2024, 1, 1, 12, 0, 0))


def test_resource_status_updates_on_add():
    """Test that status updates when adding to resource."""
    resource = Resource("water", "Water", 100.0, max_capacity=1000.0)
    initial_status = resource.status_id
    
    # Add significant amount
    resource.add(500.0)
    assert resource.status_id != initial_status


def test_resource_status_updates_on_consume():
    """Test that status updates when consuming from resource."""
    resource = Resource("water", "Water", 800.0, max_capacity=1000.0)
    initial_status = resource.status_id
    
    # Consume significant amount
    resource.consume(600.0)
    assert resource.status_id != initial_status


def test_resource_status_updates_on_set_amount():
    """Test that status updates when setting amount."""
    resource = Resource("water", "Water", 100.0, max_capacity=1000.0)
    initial_status = resource.status_id
    
    resource.set_amount(900.0)
    assert resource.status_id != initial_status


def test_resource_finite_no_replenishment_rate():
    """Test that finite resources have no replenishment rate."""
    resource = Resource("oil", "Oil", 1000.0, finite=True)
    
    assert resource.finite
    assert resource.replenishment_rate is None


def test_resource_invalid_replenishment_frequency():
    """Test that invalid replenishment frequency raises error."""
    with pytest.raises(ValueError, match="replenishment_frequency must be one of"):
        Resource("water", "Water", 100.0, replenishment_frequency='invalid')

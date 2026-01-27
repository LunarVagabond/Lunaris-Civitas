"""Tests for resource model."""

import pytest

from src.models.resource import Resource


def test_resource_initialization():
    """Test resource initialization."""
    resource = Resource(
        resource_id="food",
        name="Food",
        initial_amount=1000.0,
        max_capacity=5000.0,
        replenishment_rate=50.0,
        finite=False
    )
    
    assert resource.id == "food"
    assert resource.name == "Food"
    assert resource.current_amount == 1000.0
    assert resource.max_capacity == 5000.0
    assert resource.replenishment_rate == 50.0
    assert resource.finite == False


def test_resource_add():
    """Test adding to resource."""
    resource = Resource("food", "Food", 1000.0, max_capacity=2000.0)
    
    added = resource.add(500.0)
    assert added == 500.0
    assert resource.current_amount == 1500.0
    
    # Test capacity limit
    added = resource.add(1000.0)
    assert added == 500.0  # Only 500 fits
    assert resource.current_amount == 2000.0


def test_resource_consume():
    """Test consuming from resource."""
    resource = Resource("food", "Food", 1000.0)
    
    consumed = resource.consume(300.0)
    assert consumed == 300.0
    assert resource.current_amount == 700.0
    
    # Test insufficient amount
    consumed = resource.consume(1000.0)
    assert consumed == 700.0  # Only 700 available
    assert resource.current_amount == 0.0
    assert resource.is_depleted() == True


def test_resource_validation():
    """Test resource validation."""
    # Negative initial amount
    with pytest.raises(ValueError):
        Resource("food", "Food", -100.0)
    
    # Initial amount exceeds capacity
    with pytest.raises(ValueError):
        Resource("food", "Food", 1000.0, max_capacity=500.0)
    
    # Finite resource with replenishment rate
    with pytest.raises(ValueError):
        Resource("oil", "Oil", 500.0, finite=True, replenishment_rate=10.0)


def test_resource_serialization():
    """Test resource serialization."""
    resource = Resource(
        resource_id="food",
        name="Food",
        initial_amount=1000.0,
        max_capacity=5000.0,
        replenishment_rate=50.0,
        finite=False
    )
    
    data = resource.to_dict()
    restored = Resource.from_dict(data)
    
    assert restored.id == resource.id
    assert restored.name == resource.name
    assert restored.current_amount == resource.current_amount
    assert restored.max_capacity == resource.max_capacity
    assert restored.replenishment_rate == resource.replenishment_rate
    assert restored.finite == resource.finite

"""Tests for modifier model (basic functionality)."""

import pytest
from datetime import datetime

from src.models.modifier import Modifier


def test_modifier_initialization():
    """Test modifier initialization."""
    modifier = Modifier(
        modifier_name="drought",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    
    assert modifier.modifier_name == "drought"
    assert modifier.resource_id == "water"
    assert modifier.start_year == 2024
    assert modifier.end_year == 2025
    assert modifier.effect_type_str == "percentage"
    assert modifier.effect_value == 0.3
    assert modifier.effect_direction == "decrease"


def test_modifier_validation():
    """Test modifier validation."""
    # End before start
    with pytest.raises(ValueError, match="end_year.*must be after start_year"):
        Modifier(
            modifier_name="test",
            resource_id="water",
            start_year=2025,
            end_year=2024,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="decrease"
        )
    
    # Invalid effect direction
    with pytest.raises(ValueError, match="effect_direction must be"):
        Modifier(
            modifier_name="test",
            resource_id="water",
            start_year=2024,
            end_year=2025,
            effect_type="percentage",
            effect_value=0.3,
            effect_direction="invalid"
        )
    
    # Missing required fields (Python raises TypeError before our validation)
    with pytest.raises(TypeError):
        Modifier(
            modifier_name="test",
            resource_id="water",
            start_year=2024
        )


def test_modifier_active():
    """Test modifier active status."""
    modifier = Modifier(
        modifier_name="test",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    
    # Before start year
    assert modifier.is_active(datetime(2023, 12, 31, 23, 0, 0)) == False
    
    # At start year
    assert modifier.is_active(datetime(2024, 6, 15, 12, 0, 0)) == True
    
    # At end year (exclusive)
    assert modifier.is_active(datetime(2025, 1, 1, 0, 0, 0)) == False
    
    # After end year
    assert modifier.is_active(datetime(2025, 6, 15, 12, 0, 0)) == False


def test_modifier_targeting():
    """Test modifier targeting methods."""
    modifier = Modifier(
        modifier_name="test",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease"
    )
    
    assert modifier.targets_resource("water") == True
    assert modifier.targets_resource("food") == False


def test_modifier_serialization():
    """Test modifier serialization."""
    modifier = Modifier(
        modifier_name="drought",
        resource_id="water",
        start_year=2024,
        end_year=2025,
        effect_type="percentage",
        effect_value=0.3,
        effect_direction="decrease",
        repeat_probability=0.5
    )
    
    data = modifier.to_dict()
    restored = Modifier.from_dict(data)
    
    assert restored.modifier_name == modifier.modifier_name
    assert restored.resource_id == modifier.resource_id
    assert restored.start_year == modifier.start_year
    assert restored.end_year == modifier.end_year
    assert restored.effect_type_str == modifier.effect_type_str
    assert restored.effect_value == modifier.effect_value
    assert restored.repeat_probability == modifier.repeat_probability

"""Tests for repeat frequency enum and helpers."""

import pytest
from datetime import timedelta

from src.systems.generics.repeat_frequency import (
    RepeatFrequency,
    get_repeat_frequency_by_id,
    get_all_repeat_frequencies
)


def test_repeat_frequency_enum_values():
    """Test RepeatFrequency enum values."""
    assert RepeatFrequency.HOURLY.label == 'hourly'
    assert RepeatFrequency.DAILY.label == 'daily'
    assert RepeatFrequency.WEEKLY.label == 'weekly'
    assert RepeatFrequency.MONTHLY.label == 'monthly'
    assert RepeatFrequency.YEARLY.label == 'yearly'


def test_repeat_frequency_to_timedelta():
    """Test converting repeat frequency to timedelta."""
    assert RepeatFrequency.HOURLY.to_timedelta() == timedelta(hours=1)
    assert RepeatFrequency.DAILY.to_timedelta() == timedelta(days=1)
    assert RepeatFrequency.WEEKLY.to_timedelta() == timedelta(weeks=1)
    assert RepeatFrequency.MONTHLY.to_timedelta() == timedelta(days=30)
    assert RepeatFrequency.YEARLY.to_timedelta() == timedelta(days=365)


def test_get_repeat_frequency_by_id():
    """Test getting repeat frequency by ID."""
    assert get_repeat_frequency_by_id('hourly') == RepeatFrequency.HOURLY
    assert get_repeat_frequency_by_id('daily') == RepeatFrequency.DAILY
    assert get_repeat_frequency_by_id('weekly') == RepeatFrequency.WEEKLY
    assert get_repeat_frequency_by_id('monthly') == RepeatFrequency.MONTHLY
    assert get_repeat_frequency_by_id('yearly') == RepeatFrequency.YEARLY


def test_get_repeat_frequency_by_id_case_insensitive():
    """Test getting repeat frequency is case insensitive."""
    assert get_repeat_frequency_by_id('HOURLY') == RepeatFrequency.HOURLY
    assert get_repeat_frequency_by_id('Daily') == RepeatFrequency.DAILY
    assert get_repeat_frequency_by_id('WEEKLY') == RepeatFrequency.WEEKLY


def test_get_repeat_frequency_by_id_invalid():
    """Test getting repeat frequency with invalid ID returns None."""
    assert get_repeat_frequency_by_id('invalid') is None
    assert get_repeat_frequency_by_id('') is None
    # None should be handled gracefully
    try:
        result = get_repeat_frequency_by_id(None)
        assert result is None
    except (AttributeError, TypeError):
        pass  # Expected behavior


def test_get_all_repeat_frequencies():
    """Test getting all repeat frequencies."""
    all_freqs = get_all_repeat_frequencies()
    
    assert len(all_freqs) == 5
    assert RepeatFrequency.HOURLY in all_freqs
    assert RepeatFrequency.DAILY in all_freqs
    assert RepeatFrequency.WEEKLY in all_freqs
    assert RepeatFrequency.MONTHLY in all_freqs
    assert RepeatFrequency.YEARLY in all_freqs

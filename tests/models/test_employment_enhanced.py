"""Unit tests for enhanced EmploymentComponent."""

import pytest
from datetime import datetime

from src.models.components.employment import EmploymentComponent


class TestEmploymentComponentEnhanced:
    """Test enhanced EmploymentComponent with salary and dates."""
    
    def test_component_type(self):
        """Test component_type property."""
        assert EmploymentComponent.component_type() == "Employment"
    
    def test_default_initialization(self):
        """Test default initialization."""
        employment = EmploymentComponent()
        
        assert employment.job_type is None
        assert employment.employer_id is None
        assert employment.payment_resources == {}
        assert employment.hire_date is None
        assert employment.last_raise_date is None
        assert employment.max_payment_cap == {}
        # Backward compat
        assert employment.salary == 0.0
        assert employment.max_salary_cap == 0.0
    
    def test_custom_initialization(self):
        """Test custom initialization with all fields."""
        hire_date = datetime(2024, 1, 1, 0, 0, 0)
        raise_date = datetime(2024, 6, 1, 0, 0, 0)
        
        employment = EmploymentComponent(
            job_type='farmer',
            employer_id=None,
            payment_resources={'money': 100.0},
            hire_date=hire_date,
            last_raise_date=raise_date,
            max_payment_cap={'money': 130.0}
        )
        
        assert employment.job_type == 'farmer'
        assert employment.employer_id is None
        assert employment.payment_resources == {'money': 100.0}
        assert employment.hire_date == hire_date
        assert employment.last_raise_date == raise_date
        assert employment.max_payment_cap == {'money': 130.0}
        # Test backward compat properties
        assert employment.salary == 100.0
        assert employment.max_salary_cap == 130.0
    
    def test_is_employed(self):
        """Test is_employed method."""
        employment = EmploymentComponent()
        assert not employment.is_employed()
        
        employment.job_type = 'farmer'
        assert employment.is_employed()
        
        employment.job_type = None
        assert not employment.is_employed()
    
    def test_negative_payment_clamping(self):
        """Test that negative payment amounts are clamped to 0."""
        employment = EmploymentComponent(payment_resources={'money': -10.0})
        assert employment.payment_resources['money'] == 0.0
    
    def test_negative_max_payment_cap_clamping(self):
        """Test that negative max_payment_cap amounts are clamped to 0."""
        employment = EmploymentComponent(max_payment_cap={'money': -10.0})
        assert employment.max_payment_cap['money'] == 0.0
    
    def test_serialization(self):
        """Test component serialization."""
        hire_date = datetime(2024, 1, 1, 0, 0, 0)
        raise_date = datetime(2024, 6, 1, 0, 0, 0)
        
        employment = EmploymentComponent(
            job_type='farmer',
            employer_id='employer_1',
            payment_resources={'money': 100.0},
            hire_date=hire_date,
            last_raise_date=raise_date,
            max_payment_cap={'money': 130.0}
        )
        
        data = employment.to_dict()
        
        assert data['job_type'] == 'farmer'
        assert data['employer_id'] == 'employer_1'
        assert data['payment_resources'] == {'money': 100.0}
        assert data['hire_date'] == hire_date.isoformat()
        assert data['last_raise_date'] == raise_date.isoformat()
        assert data['max_payment_cap'] == {'money': 130.0}
    
    def test_serialization_without_dates(self):
        """Test serialization when dates are None."""
        employment = EmploymentComponent(
            job_type='farmer',
            payment_resources={'money': 100.0}
        )
        
        data = employment.to_dict()
        
        assert data['payment_resources'] == {'money': 100.0}
        assert 'hire_date' not in data or data.get('hire_date') is None
        assert 'last_raise_date' not in data or data.get('last_raise_date') is None
    
    def test_deserialization(self):
        """Test component deserialization."""
        hire_date_str = "2024-01-01T00:00:00"
        raise_date_str = "2024-06-01T00:00:00"
        
        data = {
            'job_type': 'farmer',
            'employer_id': 'employer_1',
            'payment_resources': {'money': 100.0},
            'hire_date': hire_date_str,
            'last_raise_date': raise_date_str,
            'max_payment_cap': {'money': 130.0}
        }
        
        employment = EmploymentComponent.from_dict(data)
        
        assert employment.job_type == 'farmer'
        assert employment.employer_id == 'employer_1'
        assert employment.payment_resources == {'money': 100.0}
        assert employment.hire_date == datetime.fromisoformat(hire_date_str)
        assert employment.last_raise_date == datetime.fromisoformat(raise_date_str)
        assert employment.max_payment_cap == {'money': 130.0}
    
    def test_deserialization_with_datetime_objects(self):
        """Test deserialization when dates are already datetime objects."""
        hire_date = datetime(2024, 1, 1, 0, 0, 0)
        raise_date = datetime(2024, 6, 1, 0, 0, 0)
        
        data = {
            'job_type': 'farmer',
            'salary': 100.0,
            'hire_date': hire_date,
            'last_raise_date': raise_date,
            'max_salary_cap': 130.0
        }
        
        employment = EmploymentComponent.from_dict(data)
        
        assert employment.hire_date == hire_date
        assert employment.last_raise_date == raise_date
    
    def test_deserialization_without_dates(self):
        """Test deserialization when dates are missing."""
        data = {
            'job_type': 'farmer',
            'payment_resources': {'money': 100.0}
        }
        
        employment = EmploymentComponent.from_dict(data)
        
        assert employment.job_type == 'farmer'
        assert employment.payment_resources == {'money': 100.0}
        assert employment.hire_date is None
        assert employment.last_raise_date is None
    
    def test_multiple_payment_resources(self):
        """Test employment with multiple payment resource types."""
        employment = EmploymentComponent(
            job_type='crypto_trader',
            payment_resources={'money': 100.0, 'crypto': 2.0},
            max_payment_cap={'money': 150.0, 'crypto': 3.0}
        )
        
        assert employment.payment_resources == {'money': 100.0, 'crypto': 2.0}
        assert employment.max_payment_cap == {'money': 150.0, 'crypto': 3.0}
        assert employment.get_total_payment_value() == 102.0
    
    def test_backward_compatibility_deserialization(self):
        """Test deserialization from old salary format."""
        data = {
            'job_type': 'farmer',
            'salary': 100.0,
            'max_salary_cap': 130.0
        }
        
        employment = EmploymentComponent.from_dict(data)
        
        # Should convert to new format
        assert employment.payment_resources == {'money': 100.0}
        assert employment.max_payment_cap == {'money': 130.0}
        # Backward compat properties should work
        assert employment.salary == 100.0
        assert employment.max_salary_cap == 130.0

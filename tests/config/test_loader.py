"""Tests for configuration loader."""

import pytest
import json
import tempfile
from pathlib import Path

from src.config.loader import load_config, _load_yaml, _load_json


def test_load_yaml_config():
    """Test loading YAML configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
simulation:
  start_datetime: "2024-01-01T00:00:00"
  rng_seed: 42
resources:
  water:
    initial_amount: 1000.0
    max_capacity: 5000.0
""")
        config_path = Path(f.name)
    
    try:
        config = load_config(config_path)
        assert config['simulation']['start_datetime'] == "2024-01-01T00:00:00"
        assert config['simulation']['rng_seed'] == 42
        assert config['resources']['water']['initial_amount'] == 1000.0
    finally:
        config_path.unlink()


def test_load_yaml_config_yml_extension():
    """Test loading YAML configuration with .yml extension."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("simulation:\n  rng_seed: 42\n")
        config_path = Path(f.name)
    
    try:
        config = load_config(config_path)
        assert config['simulation']['rng_seed'] == 42
    finally:
        config_path.unlink()


def test_load_json_config():
    """Test loading JSON configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            'simulation': {
                'start_datetime': '2024-01-01T00:00:00',
                'rng_seed': 42
            }
        }, f)
        config_path = Path(f.name)
    
    try:
        config = load_config(config_path)
        assert config['simulation']['start_datetime'] == '2024-01-01T00:00:00'
        assert config['simulation']['rng_seed'] == 42
    finally:
        config_path.unlink()


def test_load_config_file_not_found():
    """Test loading non-existent config file."""
    config_path = Path("nonexistent_config.yaml")
    
    with pytest.raises(FileNotFoundError):
        load_config(config_path)


def test_load_config_unsupported_format():
    """Test loading unsupported file format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("some content")
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_yaml_invalid_content():
    """Test loading invalid YAML content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Failed to parse YAML"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_yaml_not_dict():
    """Test loading YAML that's not a dictionary."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("- item1\n- item2")
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="must contain a dictionary"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_json_invalid_content():
    """Test loading invalid JSON content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_json_not_dict():
    """Test loading JSON that's not a dictionary."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([1, 2, 3], f)
        config_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError, match="must contain a dictionary"):
            load_config(config_path)
    finally:
        config_path.unlink()


def test_load_yaml_empty_file():
    """Test loading empty YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        config_path = Path(f.name)
    
    try:
        # Empty YAML file raises ValueError (not a dict)
        with pytest.raises(ValueError, match="must contain a dictionary"):
            load_config(config_path)
    finally:
        config_path.unlink()

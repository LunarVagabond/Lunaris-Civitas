"""Configuration loader for YAML and JSON config files."""

import json
from pathlib import Path
from typing import Dict, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to configuration file (.yml, .yaml, or .json)
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If file format is not supported or invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    suffix = config_path.suffix.lower()
    
    if suffix in ('.yml', '.yaml'):
        if not YAML_AVAILABLE:
            raise ValueError(
                "YAML support not available. Install PyYAML: pip install pyyaml"
            )
        return _load_yaml(config_path)
    elif suffix == '.json':
        return _load_json(config_path)
    else:
        raise ValueError(
            f"Unsupported config file format: {suffix}. "
            "Supported formats: .yml, .yaml, .json"
        )


def _load_yaml(config_path: Path) -> Dict[str, Any]:
    """Load YAML configuration file.
    
    Args:
        config_path: Path to YAML file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        ValueError: If YAML parsing fails
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a dictionary/mapping")
        
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML config: {e}")


def _load_json(config_path: Path) -> Dict[str, Any]:
    """Load JSON configuration file.
    
    Args:
        config_path: Path to JSON file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise ValueError("Config file must contain a dictionary/object")
        
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON config: {e}")

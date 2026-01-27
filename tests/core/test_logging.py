"""Tests for logging system."""

import logging
import sys
from pathlib import Path

from src.core.logging import setup_logging, get_logger


def test_setup_logging_default():
    """Test setting up logging with default parameters."""
    logger = setup_logging()
    
    assert logger.name == 'lunaris_civitas'
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logging_custom_level():
    """Test setting up logging with custom level."""
    logger = setup_logging(log_level="DEBUG")
    
    assert logger.level == logging.DEBUG
    assert logger.handlers[0].level == logging.DEBUG


def test_setup_logging_detailed():
    """Test setting up logging with detailed format."""
    logger = setup_logging(detailed=True)
    
    handler = logger.handlers[0]
    formatter = handler.formatter
    assert formatter is not None
    assert '%(asctime)s' in formatter._fmt


def test_setup_logging_simple():
    """Test setting up logging with simple format."""
    logger = setup_logging(detailed=False)
    
    handler = logger.handlers[0]
    formatter = handler.formatter
    assert formatter is not None
    assert '%(asctime)s' not in formatter._fmt


def test_setup_logging_multiple_calls():
    """Test that multiple setup calls don't duplicate handlers."""
    logger1 = setup_logging()
    initial_handlers = len(logger1.handlers)
    
    logger2 = setup_logging()
    assert len(logger2.handlers) == initial_handlers


def test_get_logger_default():
    """Test getting default logger."""
    logger = get_logger()
    
    assert logger.name == 'lunaris_civitas'


def test_get_logger_named():
    """Test getting named logger."""
    logger = get_logger('test_module')
    
    assert logger.name == 'lunaris_civitas.test_module'


def test_get_logger_different_names():
    """Test getting loggers with different names."""
    logger1 = get_logger('module1')
    logger2 = get_logger('module2')
    
    assert logger1.name == 'lunaris_civitas.module1'
    assert logger2.name == 'lunaris_civitas.module2'
    assert logger1 is not logger2

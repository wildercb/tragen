"""
Logging utilities for NQ Trading Agent
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    max_size: str = "10MB",
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration for the NQ Trading Agent.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, logs only to console
        format_string: Custom log format string
        max_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Convert level string to logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if log_file is provided
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse max_size
        max_bytes = _parse_size(max_size)
        
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured - Level: {level}, File: {log_file}")


def _parse_size(size_str: str) -> int:
    """
    Parse size string (e.g., '10MB', '1GB') to bytes.
    
    Args:
        size_str: Size string
        
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    multipliers = {
        'GB': 1024 * 1024 * 1024,
        'MB': 1024 * 1024,
        'KB': 1024,
        'B': 1,
    }
    
    # Check suffixes in order of length (longest first)
    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number_str = size_str[:-len(suffix)].strip()
            if number_str:  # Make sure we have a number
                try:
                    number = float(number_str)
                    return int(number * multiplier)
                except ValueError:
                    raise ValueError(f"Invalid size format: '{size_str}' - could not parse number '{number_str}'")
    
    # If no suffix, assume bytes
    try:
        return int(float(size_str))
    except ValueError:
        raise ValueError(f"Invalid size format: '{size_str}' - expected format like '10MB', '1GB', or plain bytes")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
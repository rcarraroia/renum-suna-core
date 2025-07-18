"""
Logger module for the Renum backend.

This module provides logging functionality for the Renum backend.
"""

import logging
import sys
from typing import Optional

# Configure logger
logger = logging.getLogger("renum")
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger.
    
    Args:
        name: Name of the logger.
        
    Returns:
        Logger.
    """
    if name is None:
        return logger
    
    return logging.getLogger(f"renum.{name}")
"""
Trading platforms module for NQ Trading Agent
"""

from .tradovate import TradovatePlatform
from .mock_platform import MockPlatform

__all__ = ["TradovatePlatform", "MockPlatform"]
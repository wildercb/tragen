"""
Market Hours Utility
===================

Utility functions for checking NQ futures market hours and trading sessions.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import pytz

logger = logging.getLogger(__name__)

class MarketHours:
    """Utility class for market hours calculations."""
    
    @staticmethod
    def is_market_open(check_time: Optional[datetime] = None) -> bool:
        """
        Check if NQ futures market is currently open.
        
        Args:
            check_time: Time to check (defaults to current time)
            
        Returns:
            True if market is open, False otherwise
        """
        if check_time is None:
            check_time = datetime.now(pytz.timezone('US/Eastern'))
        elif check_time.tzinfo is None:
            # Assume local time, convert to ET
            check_time = check_time.replace(tzinfo=pytz.timezone('US/Eastern'))
        else:
            # Convert to ET
            check_time = check_time.astimezone(pytz.timezone('US/Eastern'))
        
        weekday = check_time.weekday()  # 0=Monday, 6=Sunday
        hour = check_time.hour
        minute = check_time.minute
        
        # NQ trades nearly 24/5 with brief maintenance breaks
        # Sunday 6:00 PM ET to Friday 5:00 PM ET
        # Daily maintenance: 5:00 PM - 6:00 PM ET
        
        if weekday == 6:  # Sunday
            return hour >= 18  # 6 PM ET or later
        elif weekday < 5:  # Monday-Friday
            if hour < 17:  # Before 5 PM ET
                return True
            elif hour == 17:  # 5 PM ET maintenance hour
                return False
            elif hour >= 18:  # 6 PM ET or later
                return True
            else:
                return False
        elif weekday == 5:  # Saturday (Friday trading continues until 5 PM)
            return hour < 17  # Before 5 PM ET Friday close
        
        return False
    
    @staticmethod
    def get_market_status(check_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get comprehensive market status information.
        
        Args:
            check_time: Time to check (defaults to current time)
            
        Returns:
            Dictionary with market status, hours, and timing info
        """
        if check_time is None:
            check_time = datetime.now(pytz.timezone('US/Eastern'))
        elif check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=pytz.timezone('US/Eastern'))
        else:
            check_time = check_time.astimezone(pytz.timezone('US/Eastern'))
        
        is_open = MarketHours.is_market_open(check_time)
        weekday = check_time.weekday()
        hour = check_time.hour
        
        # Determine session status
        session_status = "closed"
        if is_open:
            session_status = "open"
        elif weekday < 5 and hour == 17:  # Daily maintenance
            session_status = "maintenance"
        
        return {
            "is_market_open": is_open,
            "session_status": session_status,
            "current_time": check_time.isoformat(),
            "timezone": "US/Eastern",
            "trading_hours": {
                "sunday_open": "18:00 ET",
                "friday_close": "17:00 ET", 
                "daily_maintenance": "17:00-18:00 ET",
                "nearly_24_hours": True
            },
            "next_open": MarketHours._get_next_market_open(check_time),
            "next_close": MarketHours._get_next_market_close(check_time),
            "minutes_until_next_change": MarketHours._minutes_until_next_change(check_time)
        }
    
    @staticmethod
    def should_agents_trade(check_time: Optional[datetime] = None) -> bool:
        """
        Determine if agents should be actively trading.
        
        This can be more restrictive than market hours to avoid
        low-liquidity periods or other conditions.
        
        Args:
            check_time: Time to check (defaults to current time)
            
        Returns:
            True if agents should be trading, False otherwise
        """
        market_status = MarketHours.get_market_status(check_time)
        
        # Don't trade during maintenance
        if market_status["session_status"] == "maintenance":
            return False
        
        # Don't trade if market is closed
        if not market_status["is_market_open"]:
            return False
        
        # Additional trading restrictions can be added here
        # For example: avoid first/last 30 minutes, holidays, etc.
        
        return True
    
    @staticmethod
    def _get_next_market_open(current_time: datetime) -> str:
        """Calculate next market open time."""
        weekday = current_time.weekday()
        hour = current_time.hour
        
        if MarketHours.is_market_open(current_time):
            return "Market is currently open"
        
        if weekday == 6 and hour < 18:  # Sunday before 6 PM
            next_open = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
        elif weekday < 5 and hour >= 17 and hour < 18:  # Weekday maintenance
            next_open = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
        elif weekday == 5 and hour >= 17:  # Friday after close
            # Next Sunday 6 PM
            days_to_add = 2  # Friday to Sunday
            next_open = (current_time + timedelta(days=days_to_add)).replace(
                hour=18, minute=0, second=0, microsecond=0
            )
        elif weekday == 6 and hour < 18:  # Saturday
            # Sunday 6 PM
            next_open = (current_time + timedelta(days=1)).replace(
                hour=18, minute=0, second=0, microsecond=0
            )
        else:
            # Default case
            next_open = current_time.replace(hour=18, minute=0, second=0, microsecond=0)
            if next_open <= current_time:
                next_open += timedelta(days=1)
        
        return next_open.isoformat()
    
    @staticmethod
    def _get_next_market_close(current_time: datetime) -> str:
        """Calculate next market close time."""
        weekday = current_time.weekday()
        hour = current_time.hour
        
        if not MarketHours.is_market_open(current_time):
            return "Market is currently closed"
        
        if weekday < 5:  # Monday-Friday
            if hour < 17:
                next_close = current_time.replace(hour=17, minute=0, second=0, microsecond=0)
            else:
                # Next weekday at 5 PM
                if weekday == 4:  # Thursday -> Friday close
                    next_close = (current_time + timedelta(days=1)).replace(
                        hour=17, minute=0, second=0, microsecond=0
                    )
                else:  # Other weekdays -> tomorrow at 5 PM (maintenance)
                    next_close = (current_time + timedelta(days=1)).replace(
                        hour=17, minute=0, second=0, microsecond=0
                    )
        else:
            # Weekend - should be Friday close
            days_to_friday = (4 - weekday) % 7
            next_close = (current_time + timedelta(days=days_to_friday)).replace(
                hour=17, minute=0, second=0, microsecond=0
            )
        
        return next_close.isoformat()
    
    @staticmethod
    def _minutes_until_next_change(current_time: datetime) -> int:
        """Calculate minutes until next market open/close."""
        try:
            if MarketHours.is_market_open(current_time):
                next_close_str = MarketHours._get_next_market_close(current_time)
                if next_close_str == "Market is currently closed":
                    return 0
                next_close = datetime.fromisoformat(next_close_str.replace('Z', '+00:00'))
                if next_close.tzinfo is None:
                    next_close = next_close.replace(tzinfo=current_time.tzinfo)
                delta = next_close - current_time
                return max(0, int(delta.total_seconds() / 60))
            else:
                next_open_str = MarketHours._get_next_market_open(current_time)
                if next_open_str == "Market is currently open":
                    return 0
                next_open = datetime.fromisoformat(next_open_str.replace('Z', '+00:00'))
                if next_open.tzinfo is None:
                    next_open = next_open.replace(tzinfo=current_time.tzinfo)
                delta = next_open - current_time
                return max(0, int(delta.total_seconds() / 60))
        except Exception as e:
            logger.error(f"Error calculating minutes until next change: {e}")
            return 0
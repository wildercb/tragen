"""
Data Ingestion MCP Tools
========================

MCP tools for fetching and managing market data for NQ futures trading.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

def register_data_tools(mcp_server, config):
    """Register data ingestion tools with the MCP server."""
    
    async def get_nq_price(symbol: str = "NQ=F") -> Dict[str, Any]:
        """
        Get current NQ futures price and basic info.
        
        Args:
            symbol: NQ futures symbol (default: NQ=F)
            
        Returns:
            Current price, session high/low, volume, and timestamp
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent data for more accurate current price
            recent_data = ticker.history(period="1d", interval="1m")
            
            if recent_data.empty:
                return {"error": "No data available for symbol"}
            
            current_price = recent_data['Close'].iloc[-1]
            session_high = recent_data['High'].max()
            session_low = recent_data['Low'].min()
            volume = recent_data['Volume'].sum()
            
            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "session_high": float(session_high),
                "session_low": float(session_low),
                "volume": int(volume),
                "timestamp": recent_data.index[-1].isoformat(),
                "range_pct": float((session_high - session_low) / current_price * 100),
                "position_in_range": float((current_price - session_low) / (session_high - session_low) * 100)
            }
            
        except Exception as e:
            logger.error(f"Error getting NQ price: {e}")
            return {"error": str(e)}
    
    async def get_historical_data(
        symbol: str = "NQ=F",
        period: str = "1d", 
        interval: str = "5m",
        max_points: int = 100
    ) -> Dict[str, Any]:
        """
        Get historical OHLCV data for NQ futures.
        
        Args:
            symbol: Futures symbol (default: NQ=F)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            max_points: Maximum data points to return
            
        Returns:
            OHLCV data with metadata
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return {"error": "No historical data available"}
            
            # Limit data points
            if len(data) > max_points:
                data = data.tail(max_points)
            
            # Convert to records for JSON serialization
            ohlcv_data = []
            for timestamp, row in data.iterrows():
                ohlcv_data.append({
                    "timestamp": timestamp.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data_points": len(ohlcv_data),
                "start_time": data.index[0].isoformat(),
                "end_time": data.index[-1].isoformat(),
                "data": ohlcv_data,
                "summary": {
                    "current_price": float(data['Close'].iloc[-1]),
                    "period_high": float(data['High'].max()),
                    "period_low": float(data['Low'].min()),
                    "total_volume": int(data['Volume'].sum()),
                    "price_change": float(data['Close'].iloc[-1] - data['Open'].iloc[0]),
                    "price_change_pct": float((data['Close'].iloc[-1] - data['Open'].iloc[0]) / data['Open'].iloc[0] * 100)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return {"error": str(e)}
    
    async def get_market_hours() -> Dict[str, Any]:
        """
        Get NQ futures market hours and trading session info.
        
        Returns:
            Market hours, session status, and time zones
        """
        try:
            now = datetime.now()
            
            # NQ trades nearly 24/5 with brief maintenance breaks
            # Sunday 6:00 PM ET to Friday 5:00 PM ET
            # Daily maintenance: 5:00 PM - 6:00 PM ET
            
            weekday = now.weekday()  # 0=Monday, 6=Sunday
            hour = now.hour
            
            # Determine if market is open
            is_open = False
            session_status = "closed"
            
            if weekday == 6:  # Sunday
                if hour >= 18:  # 6 PM ET or later
                    is_open = True
                    session_status = "open"
            elif weekday < 5:  # Monday-Friday
                if hour < 17:  # Before 5 PM ET
                    is_open = True
                    session_status = "open"
                elif hour == 17:  # 5 PM ET maintenance hour
                    session_status = "maintenance"
                elif hour >= 18:  # 6 PM ET or later
                    is_open = True
                    session_status = "open"
            elif weekday == 5:  # Saturday
                if hour < 17:  # Before 5 PM ET Friday close
                    is_open = True
                    session_status = "open"
            
            return {
                "is_market_open": is_open,
                "session_status": session_status,
                "current_time": now.isoformat(),
                "timezone": "US/Eastern",
                "trading_hours": {
                    "sunday_open": "18:00 ET",
                    "friday_close": "17:00 ET",
                    "daily_maintenance": "17:00-18:00 ET",
                    "nearly_24_hours": True
                },
                "next_open": _get_next_market_open(now),
                "next_close": _get_next_market_close(now)
            }
            
        except Exception as e:
            logger.error(f"Error getting market hours: {e}")
            return {"error": str(e)}
    
def _get_next_market_open(now: datetime) -> str:
    """Calculate next market open time."""
    # Simplified calculation - would need more robust implementation
    weekday = now.weekday()
    
    if weekday == 6 and now.hour < 18:  # Sunday before 6 PM
        next_open = now.replace(hour=18, minute=0, second=0, microsecond=0)
    elif weekday < 5 and now.hour >= 17:  # Weekday after close
        next_open = now.replace(hour=18, minute=0, second=0, microsecond=0)
    elif weekday == 5 and now.hour >= 17:  # Friday after close
        # Next Sunday 6 PM
        days_to_add = (6 - weekday) % 7 + 1
        next_open = (now + timedelta(days=days_to_add)).replace(hour=18, minute=0, second=0, microsecond=0)
    else:
        next_open = now  # Market is open now
    
    return next_open.isoformat()
    
def _get_next_market_close(now: datetime) -> str:
    """Calculate next market close time."""
    weekday = now.weekday()
    
    if weekday < 5:  # Monday-Friday
        if now.hour < 17:
            next_close = now.replace(hour=17, minute=0, second=0, microsecond=0)
        else:
            # Next day at 5 PM (or Friday if it's Thursday)
            if weekday == 4:  # Thursday
                next_close = (now + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
            else:
                next_close = (now + timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    else:
        # Weekend - next close is Friday 5 PM
        days_to_friday = (4 - weekday) % 7
        if days_to_friday == 0 and now.hour >= 17:
            days_to_friday = 7
        next_close = (now + timedelta(days=days_to_friday)).replace(hour=17, minute=0, second=0, microsecond=0)
    
    return next_close.isoformat()
    
    async def get_contract_info() -> Dict[str, Any]:
        """
        Get NQ futures contract specifications.
        
        Returns:
            Contract specifications, margin requirements, and trading details
        """
        return {
            "symbol": "NQ",
            "name": "E-mini NASDAQ-100 Futures",
            "exchange": "CME",
            "contract_specs": {
                "tick_size": 0.25,
                "tick_value": 5.00,
                "contract_size": "$20 × NASDAQ-100 Index",
                "minimum_fluctuation": "0.25 index points",
                "currency": "USD"
            },
            "margin_requirements": {
                "initial_margin": 16500,  # Approximate, varies by broker
                "maintenance_margin": 15000,  # Approximate
                "day_trading_margin": 8250,  # Approximate
                "note": "Margin requirements vary by broker and market conditions"
            },
            "trading_details": {
                "trading_hours": "Nearly 24 hours, Sunday 6 PM - Friday 5 PM ET",
                "last_trading_day": "Third Friday of contract month",
                "settlement": "Cash settled to NASDAQ-100 Index",
                "position_limits": "Check with exchange for current limits"
            },
            "contract_months": [
                "March (H)", "June (M)", "September (U)", "December (Z)"
            ]
        }
    
    # Register tools manually
    mcp_server.register_tool("get_nq_price", get_nq_price)
    mcp_server.register_tool("get_historical_data", get_historical_data)
    mcp_server.register_tool("get_market_hours", get_market_hours)
    mcp_server.register_tool("get_contract_info", get_contract_info)
    
    logger.info("Data ingestion tools registered with MCP server")
    logger.info(f"Registered tools: get_nq_price, get_historical_data, get_market_hours, get_contract_info")
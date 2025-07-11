"""
Execution Agent for NQ futures trading
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL = "partial"


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "long"
    SHORT = "short"


class ExecutionAgent:
    """
    Execution agent for managing NQ futures trades.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize execution agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trading_config = config.get('trading', {})
        self.account_config = self.trading_config.get('account', {})
        self.risk_config = self.trading_config.get('risk', {})
        self.execution_config = config.get('execution', {})
        
        # Trading state
        self.positions = {}
        self.open_orders = {}
        self.order_history = []
        self.trade_history = []
        self.account_balance = self.account_config.get('initial_balance', 100000.0)
        self.available_balance = self.account_balance
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.last_trade_date = None
        
        # Risk management
        self.max_position_size = self.account_config.get('max_position_size', 0.02)
        self.max_daily_loss = self.account_config.get('max_daily_loss', 0.05)
        self.max_drawdown = self.risk_config.get('max_drawdown', 0.10)
        self.stop_loss_pct = self.risk_config.get('stop_loss_pct', 0.005)
        self.take_profit_pct = self.risk_config.get('take_profit_pct', 0.015)
        
        # Execution parameters
        self.max_positions = self.execution_config.get('positions', {}).get('max_positions', 3)
        self.default_quantity = self.execution_config.get('orders', {}).get('default_quantity', 1)
        self.order_timeout = self.execution_config.get('orders', {}).get('timeout', 30)
        
        # Platform connection
        self.platform = None
        self.is_connected = False
        
    async def connect_platform(self, platform):
        """
        Connect to trading platform.
        
        Args:
            platform: Trading platform instance
        """
        try:
            self.platform = platform
            await platform.connect()
            self.is_connected = True
            logger.info("Connected to trading platform")
            
        except Exception as e:
            logger.error(f"Failed to connect to platform: {e}")
            raise
            
    async def disconnect_platform(self):
        """Disconnect from trading platform."""
        try:
            if self.platform:
                await self.platform.disconnect()
                self.is_connected = False
                logger.info("Disconnected from trading platform")
                
        except Exception as e:
            logger.error(f"Error disconnecting from platform: {e}")
            
    async def execute_signal(self, signal: Dict[str, Any], current_price: float, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a trading signal.
        
        Args:
            signal: Trading signal from LLM
            current_price: Current market price
            nq_config: NQ contract configuration
            
        Returns:
            Execution result
        """
        try:
            # Validate signal
            if not self._validate_signal(signal):
                return {
                    'success': False,
                    'reason': 'Invalid signal',
                    'signal': signal
                }
                
            # Check risk management
            risk_check = self._check_risk_management(signal, current_price)
            if not risk_check['allowed']:
                return {
                    'success': False,
                    'reason': risk_check['reason'],
                    'signal': signal
                }
                
            # Execute based on action
            if signal['action'] == 'BUY':
                result = await self._execute_buy_signal(signal, current_price, nq_config)
            elif signal['action'] == 'SELL':
                result = await self._execute_sell_signal(signal, current_price, nq_config)
            else:  # HOLD
                result = {
                    'success': True,
                    'action': 'HOLD',
                    'reason': 'No action taken',
                    'signal': signal
                }
                
            # Update trading statistics
            self._update_trade_statistics(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {
                'success': False,
                'reason': f'Execution error: {e}',
                'signal': signal
            }
            
    async def _execute_buy_signal(self, signal: Dict[str, Any], current_price: float, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a buy signal."""
        try:
            # Calculate position size
            position_size = self._calculate_position_size(signal, current_price, nq_config)
            
            # Determine entry price
            entry_price = signal.get('entry_price', current_price)
            
            # Create order
            order = {
                'id': f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'symbol': nq_config.get('symbol', 'NQ'),
                'side': 'BUY',
                'quantity': position_size,
                'price': entry_price,
                'order_type': 'MARKET' if entry_price == current_price else 'LIMIT',
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'timestamp': datetime.now(),
                'status': OrderStatus.PENDING,
                'signal': signal
            }
            
            # Execute order
            execution_result = await self._execute_order(order, nq_config)
            
            if execution_result['success']:
                # Create position
                position = {
                    'id': f"pos_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'symbol': order['symbol'],
                    'side': PositionSide.LONG,
                    'quantity': position_size,
                    'entry_price': execution_result['fill_price'],
                    'current_price': execution_result['fill_price'],
                    'unrealized_pnl': 0.0,
                    'stop_loss': order['stop_loss'],
                    'take_profit': order['take_profit'],
                    'timestamp': datetime.now(),
                    'order_id': order['id']
                }
                
                self.positions[position['id']] = position
                
                # Place stop loss and take profit orders
                await self._place_exit_orders(position, nq_config)
                
                return {
                    'success': True,
                    'action': 'BUY',
                    'order_id': order['id'],
                    'position_id': position['id'],
                    'quantity': position_size,
                    'entry_price': execution_result['fill_price'],
                    'signal': signal
                }
            else:
                return {
                    'success': False,
                    'reason': execution_result['reason'],
                    'signal': signal
                }
                
        except Exception as e:
            logger.error(f"Error executing buy signal: {e}")
            return {
                'success': False,
                'reason': f'Buy execution error: {e}',
                'signal': signal
            }
            
    async def _execute_sell_signal(self, signal: Dict[str, Any], current_price: float, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sell signal."""
        try:
            # Calculate position size
            position_size = self._calculate_position_size(signal, current_price, nq_config)
            
            # Determine entry price
            entry_price = signal.get('entry_price', current_price)
            
            # Create order
            order = {
                'id': f"order_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'symbol': nq_config.get('symbol', 'NQ'),
                'side': 'SELL',
                'quantity': position_size,
                'price': entry_price,
                'order_type': 'MARKET' if entry_price == current_price else 'LIMIT',
                'stop_loss': signal.get('stop_loss'),
                'take_profit': signal.get('take_profit'),
                'timestamp': datetime.now(),
                'status': OrderStatus.PENDING,
                'signal': signal
            }
            
            # Execute order
            execution_result = await self._execute_order(order, nq_config)
            
            if execution_result['success']:
                # Create position
                position = {
                    'id': f"pos_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'symbol': order['symbol'],
                    'side': PositionSide.SHORT,
                    'quantity': position_size,
                    'entry_price': execution_result['fill_price'],
                    'current_price': execution_result['fill_price'],
                    'unrealized_pnl': 0.0,
                    'stop_loss': order['stop_loss'],
                    'take_profit': order['take_profit'],
                    'timestamp': datetime.now(),
                    'order_id': order['id']
                }
                
                self.positions[position['id']] = position
                
                # Place stop loss and take profit orders
                await self._place_exit_orders(position, nq_config)
                
                return {
                    'success': True,
                    'action': 'SELL',
                    'order_id': order['id'],
                    'position_id': position['id'],
                    'quantity': position_size,
                    'entry_price': execution_result['fill_price'],
                    'signal': signal
                }
            else:
                return {
                    'success': False,
                    'reason': execution_result['reason'],
                    'signal': signal
                }
                
        except Exception as e:
            logger.error(f"Error executing sell signal: {e}")
            return {
                'success': False,
                'reason': f'Sell execution error: {e}',
                'signal': signal
            }
            
    async def _execute_order(self, order: Dict[str, Any], nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an order through the platform."""
        try:
            if not self.is_connected or not self.platform:
                return {
                    'success': False,
                    'reason': 'Platform not connected'
                }
                
            # Add order to tracking
            self.open_orders[order['id']] = order
            
            # Execute through platform
            result = await self.platform.place_order(order)
            
            if result['success']:
                # Update order status
                order['status'] = OrderStatus.FILLED
                order['fill_price'] = result['fill_price']
                order['fill_time'] = datetime.now()
                
                # Move to history
                self.order_history.append(order)
                del self.open_orders[order['id']]
                
                # Update account balance
                self._update_account_balance(order, nq_config)
                
                return {
                    'success': True,
                    'fill_price': result['fill_price'],
                    'order_id': order['id']
                }
            else:
                order['status'] = OrderStatus.REJECTED
                order['reject_reason'] = result['reason']
                
                return {
                    'success': False,
                    'reason': result['reason']
                }
                
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            if order['id'] in self.open_orders:
                self.open_orders[order['id']]['status'] = OrderStatus.REJECTED
                
            return {
                'success': False,
                'reason': f'Order execution error: {e}'
            }
            
    async def _place_exit_orders(self, position: Dict[str, Any], nq_config: Dict[str, Any]):
        """Place stop loss and take profit orders for a position."""
        try:
            if position['stop_loss']:
                stop_order = {
                    'id': f"stop_{position['id']}",
                    'symbol': position['symbol'],
                    'side': 'SELL' if position['side'] == PositionSide.LONG else 'BUY',
                    'quantity': position['quantity'],
                    'price': position['stop_loss'],
                    'order_type': 'STOP',
                    'timestamp': datetime.now(),
                    'status': OrderStatus.PENDING,
                    'position_id': position['id']
                }
                
                await self._execute_order(stop_order, nq_config)
                
            if position['take_profit']:
                profit_order = {
                    'id': f"profit_{position['id']}",
                    'symbol': position['symbol'],
                    'side': 'SELL' if position['side'] == PositionSide.LONG else 'BUY',
                    'quantity': position['quantity'],
                    'price': position['take_profit'],
                    'order_type': 'LIMIT',
                    'timestamp': datetime.now(),
                    'status': OrderStatus.PENDING,
                    'position_id': position['id']
                }
                
                await self._execute_order(profit_order, nq_config)
                
        except Exception as e:
            logger.error(f"Error placing exit orders: {e}")
            
    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """Validate trading signal."""
        try:
            # Check required fields
            required_fields = ['action', 'confidence']
            for field in required_fields:
                if field not in signal:
                    return False
                    
            # Check valid action
            if signal['action'] not in ['BUY', 'SELL', 'HOLD']:
                return False
                
            # Check confidence range
            if not (0 <= signal['confidence'] <= 10):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return False
            
    def _check_risk_management(self, signal: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """Check risk management constraints."""
        try:
            # Check if trading is allowed
            if not self._is_trading_allowed():
                return {
                    'allowed': False,
                    'reason': 'Trading not allowed due to risk limits'
                }
                
            # Check maximum positions
            if len(self.positions) >= self.max_positions:
                return {
                    'allowed': False,
                    'reason': 'Maximum positions reached'
                }
                
            # Check daily loss limit
            if self.daily_pnl < -self.max_daily_loss * self.account_balance:
                return {
                    'allowed': False,
                    'reason': 'Daily loss limit exceeded'
                }
                
            # Check available balance
            required_margin = self._calculate_required_margin(signal, current_price)
            if required_margin > self.available_balance:
                return {
                    'allowed': False,
                    'reason': 'Insufficient available balance'
                }
                
            # Check confidence threshold
            min_confidence = self.trading_config.get('min_confidence', 6)
            if signal['confidence'] < min_confidence:
                return {
                    'allowed': False,
                    'reason': 'Signal confidence below threshold'
                }
                
            return {
                'allowed': True,
                'reason': 'All risk checks passed'
            }
            
        except Exception as e:
            logger.error(f"Error checking risk management: {e}")
            return {
                'allowed': False,
                'reason': f'Risk check error: {e}'
            }
            
    def _is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed."""
        try:
            # Check if it's a new trading day
            today = datetime.now().date()
            if self.last_trade_date != today:
                self.daily_pnl = 0.0
                self.daily_trades = 0
                self.last_trade_date = today
                
            # Check maximum daily trades
            max_daily_trades = self.trading_config.get('max_daily_trades', 10)
            if self.daily_trades >= max_daily_trades:
                return False
                
            # Check maximum drawdown
            current_drawdown = (self.account_balance - self.total_pnl) / self.account_balance
            if current_drawdown > self.max_drawdown:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking if trading allowed: {e}")
            return False
            
    def _calculate_position_size(self, signal: Dict[str, Any], current_price: float, nq_config: Dict[str, Any]) -> int:
        """Calculate position size based on risk management."""
        try:
            # Get suggested position size from signal
            suggested_size = signal.get('position_size', self.default_quantity)
            
            # Calculate maximum position size based on account balance
            max_risk_per_trade = self.max_position_size * self.account_balance
            contract_value = current_price * nq_config.get('contract_size', 20)
            max_contracts = int(max_risk_per_trade / contract_value)
            
            # Use the smaller of suggested size or max allowed
            position_size = min(suggested_size, max_contracts, 5)  # Cap at 5 contracts
            
            return max(1, position_size)  # Minimum 1 contract
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 1
            
    def _calculate_required_margin(self, signal: Dict[str, Any], current_price: float) -> float:
        """Calculate required margin for a trade."""
        try:
            position_size = signal.get('position_size', 1)
            margin_per_contract = 16500  # NQ margin requirement
            return position_size * margin_per_contract
            
        except Exception as e:
            logger.error(f"Error calculating required margin: {e}")
            return 16500  # Default margin
            
    def _update_account_balance(self, order: Dict[str, Any], nq_config: Dict[str, Any]):
        """Update account balance after order execution."""
        try:
            # Calculate transaction cost
            commission = 2.50  # Per contract
            total_commission = order['quantity'] * commission
            
            # Update available balance (margin requirement)
            margin_per_contract = nq_config.get('margin_requirement', 16500)
            margin_used = order['quantity'] * margin_per_contract
            
            if order['side'] == 'BUY' or order['side'] == 'SELL':
                self.available_balance -= margin_used + total_commission
                
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            
    def _update_trade_statistics(self, result: Dict[str, Any]):
        """Update trading statistics."""
        try:
            if result['success'] and result['action'] in ['BUY', 'SELL']:
                self.daily_trades += 1
                
        except Exception as e:
            logger.error(f"Error updating trade statistics: {e}")
            
    async def update_positions(self, current_prices: Dict[str, float]):
        """Update positions with current market prices."""
        try:
            for position_id, position in self.positions.items():
                symbol = position['symbol']
                if symbol in current_prices:
                    current_price = current_prices[symbol]
                    position['current_price'] = current_price
                    
                    # Calculate unrealized PnL
                    if position['side'] == PositionSide.LONG:
                        position['unrealized_pnl'] = (current_price - position['entry_price']) * position['quantity'] * 20
                    else:  # SHORT
                        position['unrealized_pnl'] = (position['entry_price'] - current_price) * position['quantity'] * 20
                        
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            
    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary."""
        try:
            # Calculate total unrealized PnL
            total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in self.positions.values())
            
            # Calculate total account value
            total_account_value = self.account_balance + self.total_pnl + total_unrealized_pnl
            
            return {
                'account_balance': self.account_balance,
                'available_balance': self.available_balance,
                'total_pnl': self.total_pnl,
                'unrealized_pnl': total_unrealized_pnl,
                'total_account_value': total_account_value,
                'daily_pnl': self.daily_pnl,
                'daily_trades': self.daily_trades,
                'open_positions': len(self.positions),
                'max_positions': self.max_positions,
                'positions': list(self.positions.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting account summary: {e}")
            return {'error': str(e)}
            
    async def close_position(self, position_id: str, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Close a specific position."""
        try:
            if position_id not in self.positions:
                return {
                    'success': False,
                    'reason': 'Position not found'
                }
                
            position = self.positions[position_id]
            
            # Create closing order
            close_order = {
                'id': f"close_{position_id}",
                'symbol': position['symbol'],
                'side': 'SELL' if position['side'] == PositionSide.LONG else 'BUY',
                'quantity': position['quantity'],
                'price': position['current_price'],
                'order_type': 'MARKET',
                'timestamp': datetime.now(),
                'status': OrderStatus.PENDING,
                'position_id': position_id
            }
            
            # Execute closing order
            result = await self._execute_order(close_order, nq_config)
            
            if result['success']:
                # Calculate realized PnL
                realized_pnl = position['unrealized_pnl']
                
                # Update account
                self.total_pnl += realized_pnl
                self.daily_pnl += realized_pnl
                
                # Remove position
                del self.positions[position_id]
                
                # Add to trade history
                trade = {
                    'position_id': position_id,
                    'symbol': position['symbol'],
                    'side': position['side'].value,
                    'quantity': position['quantity'],
                    'entry_price': position['entry_price'],
                    'exit_price': result['fill_price'],
                    'realized_pnl': realized_pnl,
                    'entry_time': position['timestamp'],
                    'exit_time': datetime.now()
                }
                
                self.trade_history.append(trade)
                
                return {
                    'success': True,
                    'realized_pnl': realized_pnl,
                    'trade': trade
                }
            else:
                return {
                    'success': False,
                    'reason': result['reason']
                }
                
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {
                'success': False,
                'reason': f'Close position error: {e}'
            }
            
    async def close_all_positions(self, nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Close all open positions."""
        try:
            results = []
            
            for position_id in list(self.positions.keys()):
                result = await self.close_position(position_id, nq_config)
                results.append(result)
                
            return {
                'success': True,
                'results': results,
                'total_positions_closed': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return {
                'success': False,
                'reason': f'Close all positions error: {e}'
            }
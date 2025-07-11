"""
Mock trading platform for testing NQ futures trading
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import random

logger = logging.getLogger(__name__)


class MockPlatform:
    """
    Mock trading platform for testing and development.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock platform.
        
        Args:
            config: Mock platform configuration
        """
        self.config = config
        self.is_connected = False
        
        # Mock account info
        self.account_info = {
            'id': 'mock_account_123',
            'name': 'Mock Trading Account',
            'currency': 'USD',
            'balance': 100000.0,
            'available_balance': 100000.0
        }
        
        # Trading state
        self.orders = {}
        self.positions = {}
        self.fills = []
        self.next_order_id = 1
        self.next_fill_id = 1
        
        # Mock market data
        self.current_price = 15000.0
        self.bid_price = 14999.75
        self.ask_price = 15000.25
        self.last_price = 15000.0
        self.volume = 1000
        
        # Simulation parameters
        self.fill_probability = 0.95  # 95% chance of order fill
        self.slippage_range = 0.25    # NQ tick size
        self.latency_ms = 50          # Simulated latency
        
    async def connect(self) -> None:
        """Connect to mock platform."""
        try:
            # Simulate connection delay
            await asyncio.sleep(0.1)
            
            self.is_connected = True
            logger.info("Connected to mock trading platform")
            
            # Start market data simulation
            asyncio.create_task(self._simulate_market_data())
            
        except Exception as e:
            logger.error(f"Failed to connect to mock platform: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from mock platform."""
        try:
            self.is_connected = False
            logger.info("Disconnected from mock trading platform")
            
        except Exception as e:
            logger.error(f"Error disconnecting from mock platform: {e}")
            
    async def _simulate_market_data(self) -> None:
        """Simulate market data updates."""
        try:
            while self.is_connected:
                # Simulate price movement
                change = random.uniform(-0.5, 0.5)  # Random price change
                self.current_price += change
                
                # Update bid/ask
                spread = 0.25  # NQ tick size
                self.bid_price = self.current_price - spread/2
                self.ask_price = self.current_price + spread/2
                self.last_price = self.current_price
                
                # Simulate volume
                self.volume = random.randint(100, 2000)
                
                # Sleep for a bit
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in market data simulation: {e}")
            
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order on mock platform.
        
        Args:
            order: Order details
            
        Returns:
            Order placement result
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'reason': 'Not connected to mock platform'
                }
                
            # Simulate order processing delay
            await asyncio.sleep(self.latency_ms / 1000.0)
            
            # Generate order ID
            order_id = f"mock_order_{self.next_order_id}"
            self.next_order_id += 1
            
            # Create order record
            mock_order = {
                'id': order_id,
                'original_order': order,
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['quantity'],
                'price': order.get('price', self.current_price),
                'order_type': order.get('order_type', 'MARKET'),
                'status': 'PENDING',
                'timestamp': datetime.now(),
                'fill_price': None,
                'fill_quantity': 0,
                'remaining_quantity': order['quantity']
            }
            
            # Store order
            self.orders[order_id] = mock_order
            
            # Simulate order execution
            execution_result = await self._simulate_order_execution(mock_order)
            
            if execution_result['success']:
                return {
                    'success': True,
                    'order_id': order_id,
                    'fill_price': execution_result['fill_price'],
                    'fill_quantity': execution_result['fill_quantity']
                }
            else:
                return {
                    'success': False,
                    'reason': execution_result['reason']
                }
                
        except Exception as e:
            logger.error(f"Error placing mock order: {e}")
            return {
                'success': False,
                'reason': f"Mock order placement error: {e}"
            }
            
    async def _simulate_order_execution(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate order execution."""
        try:
            # Simulate execution delay
            await asyncio.sleep(random.uniform(0.01, 0.1))
            
            # Check if order should fill
            if random.random() > self.fill_probability:
                order['status'] = 'REJECTED'
                return {
                    'success': False,
                    'reason': 'Order rejected by mock exchange'
                }
                
            # Calculate fill price
            if order['order_type'] == 'MARKET':
                if order['side'] == 'BUY':
                    fill_price = self.ask_price
                else:
                    fill_price = self.bid_price
                    
                # Add some slippage
                slippage = random.uniform(-self.slippage_range, self.slippage_range)
                fill_price += slippage
                
            else:  # LIMIT order
                fill_price = order['price']
                
            # Create fill record
            fill_id = f"mock_fill_{self.next_fill_id}"
            self.next_fill_id += 1
            
            fill = {
                'id': fill_id,
                'order_id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'],
                'quantity': order['quantity'],
                'price': fill_price,
                'timestamp': datetime.now(),
                'commission': 2.50 * order['quantity']  # $2.50 per contract
            }
            
            self.fills.append(fill)
            
            # Update order
            order['status'] = 'FILLED'
            order['fill_price'] = fill_price
            order['fill_quantity'] = order['quantity']
            order['remaining_quantity'] = 0
            order['fill_time'] = datetime.now()
            
            # Update account balance
            self._update_account_balance(fill)
            
            # Create or update position
            await self._update_position(fill)
            
            logger.info(f"Mock order filled: {order['id']} at {fill_price}")
            
            return {
                'success': True,
                'fill_price': fill_price,
                'fill_quantity': order['quantity']
            }
            
        except Exception as e:
            logger.error(f"Error simulating order execution: {e}")
            return {
                'success': False,
                'reason': f"Order execution simulation error: {e}"
            }
            
    def _update_account_balance(self, fill: Dict[str, Any]) -> None:
        """Update account balance after fill."""
        try:
            # Deduct commission
            self.account_info['balance'] -= fill['commission']
            self.account_info['available_balance'] -= fill['commission']
            
            # For futures, we don't exchange cash for positions
            # Just reserve margin and pay commission
            
        except Exception as e:
            logger.error(f"Error updating account balance: {e}")
            
    async def _update_position(self, fill: Dict[str, Any]) -> None:
        """Update position after fill."""
        try:
            symbol = fill['symbol']
            side = fill['side']
            quantity = fill['quantity']
            price = fill['price']
            
            if symbol not in self.positions:
                # Create new position
                self.positions[symbol] = {
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity if side == 'BUY' else -quantity,
                    'entry_price': price,
                    'current_price': price,
                    'unrealized_pnl': 0.0,
                    'timestamp': datetime.now()
                }
            else:
                # Update existing position
                position = self.positions[symbol]
                current_quantity = position['quantity']
                
                if side == 'BUY':
                    new_quantity = current_quantity + quantity
                else:
                    new_quantity = current_quantity - quantity
                    
                if new_quantity == 0:
                    # Position closed
                    del self.positions[symbol]
                else:
                    # Update position
                    position['quantity'] = new_quantity
                    position['current_price'] = price
                    
                    # Update average entry price
                    if (current_quantity > 0 and new_quantity > 0) or (current_quantity < 0 and new_quantity < 0):
                        # Adding to position
                        total_cost = (abs(current_quantity) * position['entry_price'] + 
                                    abs(quantity) * price)
                        position['entry_price'] = total_cost / abs(new_quantity)
                        
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            if order_id not in self.orders:
                return {
                    'success': False,
                    'reason': 'Order not found'
                }
                
            order = self.orders[order_id]
            
            if order['status'] == 'FILLED':
                return {
                    'success': False,
                    'reason': 'Order already filled'
                }
                
            # Cancel order
            order['status'] = 'CANCELLED'
            order['cancel_time'] = datetime.now()
            
            logger.info(f"Mock order cancelled: {order_id}")
            
            return {
                'success': True,
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Error cancelling mock order: {e}")
            return {
                'success': False,
                'reason': f"Mock order cancellation error: {e}"
            }
            
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        try:
            # Update unrealized PnL
            for symbol, position in self.positions.items():
                current_price = self.current_price  # Use current market price
                entry_price = position['entry_price']
                quantity = position['quantity']
                
                # Calculate unrealized PnL
                if quantity > 0:  # Long position
                    position['unrealized_pnl'] = (current_price - entry_price) * quantity * 20  # NQ multiplier
                else:  # Short position
                    position['unrealized_pnl'] = (entry_price - current_price) * abs(quantity) * 20
                    
                position['current_price'] = current_price
                
            return {
                'success': True,
                'positions': list(self.positions.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                'success': False,
                'reason': f"Get positions error: {e}"
            }
            
    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        try:
            # Calculate total unrealized PnL
            total_unrealized_pnl = 0.0
            for position in self.positions.values():
                total_unrealized_pnl += position.get('unrealized_pnl', 0.0)
                
            balance_info = {
                'balance': self.account_info['balance'],
                'available_balance': self.account_info['available_balance'],
                'unrealized_pnl': total_unrealized_pnl,
                'total_equity': self.account_info['balance'] + total_unrealized_pnl,
                'currency': self.account_info['currency']
            }
            
            return {
                'success': True,
                'balance': balance_info
            }
            
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {
                'success': False,
                'reason': f"Get balance error: {e}"
            }
            
    async def get_orders(self) -> Dict[str, Any]:
        """Get order history."""
        try:
            return {
                'success': True,
                'orders': list(self.orders.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {
                'success': False,
                'reason': f"Get orders error: {e}"
            }
            
    async def get_fills(self) -> Dict[str, Any]:
        """Get fill history."""
        try:
            return {
                'success': True,
                'fills': self.fills
            }
            
        except Exception as e:
            logger.error(f"Error getting fills: {e}")
            return {
                'success': False,
                'reason': f"Get fills error: {e}"
            }
            
    async def subscribe_to_quotes(self, symbol: str) -> Dict[str, Any]:
        """Subscribe to quotes (mock implementation)."""
        try:
            logger.info(f"Subscribed to mock quotes for {symbol}")
            return {
                'success': True,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to mock quotes: {e}")
            return {
                'success': False,
                'reason': f"Subscription error: {e}"
            }
            
    async def unsubscribe_from_quotes(self, symbol: str) -> Dict[str, Any]:
        """Unsubscribe from quotes (mock implementation)."""
        try:
            logger.info(f"Unsubscribed from mock quotes for {symbol}")
            return {
                'success': True,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from mock quotes: {e}")
            return {
                'success': False,
                'reason': f"Unsubscription error: {e}"
            }
            
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        return self.current_price
        
    def get_bid_ask(self, symbol: str) -> Dict[str, float]:
        """Get bid/ask prices."""
        return {
            'bid': self.bid_price,
            'ask': self.ask_price,
            'last': self.last_price
        }
        
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return {
            'account_info': self.account_info,
            'is_connected': self.is_connected,
            'orders_count': len(self.orders),
            'positions_count': len(self.positions),
            'fills_count': len(self.fills)
        }
        
    def set_market_price(self, price: float) -> None:
        """Set market price for testing."""
        self.current_price = price
        self.bid_price = price - 0.125
        self.ask_price = price + 0.125
        self.last_price = price
        
    def set_fill_probability(self, probability: float) -> None:
        """Set fill probability for testing."""
        self.fill_probability = max(0.0, min(1.0, probability))
        
    def set_slippage_range(self, slippage: float) -> None:
        """Set slippage range for testing."""
        self.slippage_range = max(0.0, slippage)
        
    def reset_account(self) -> None:
        """Reset account to initial state."""
        self.account_info = {
            'id': 'mock_account_123',
            'name': 'Mock Trading Account',
            'currency': 'USD',
            'balance': 100000.0,
            'available_balance': 100000.0
        }
        
        self.orders = {}
        self.positions = {}
        self.fills = []
        self.next_order_id = 1
        self.next_fill_id = 1
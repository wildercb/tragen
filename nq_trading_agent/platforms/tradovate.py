"""
Tradovate trading platform connector for NQ futures
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import websockets

logger = logging.getLogger(__name__)


class TradovatePlatform:
    """
    Tradovate platform connector for NQ futures trading.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Tradovate platform.
        
        Args:
            config: Tradovate configuration
        """
        self.config = config
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        self.account_id = config.get('account_id')
        self.demo = config.get('demo', True)
        
        # URLs
        base_url = "https://demo.tradovateapi.com/v1" if self.demo else "https://live.tradovateapi.com/v1"
        self.rest_url = config.get('rest_url', base_url)
        self.websocket_url = config.get('websocket_url', 
                                       "wss://demo.tradovateapi.com/v1/websocket" if self.demo 
                                       else "wss://live.tradovateapi.com/v1/websocket")
        
        # Connection state
        self.session = None
        self.websocket = None
        self.access_token = None
        self.is_connected = False
        
        # Account info
        self.account_info = None
        self.margin_info = None
        
    async def connect(self) -> None:
        """Connect to Tradovate API."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Authenticate
            await self._authenticate()
            
            # Get account information
            await self._get_account_info()
            
            # Connect WebSocket
            await self._connect_websocket()
            
            self.is_connected = True
            logger.info(f"Connected to Tradovate API (demo: {self.demo})")
            
        except Exception as e:
            logger.error(f"Failed to connect to Tradovate: {e}")
            await self.disconnect()
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from Tradovate API."""
        try:
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
                
            if self.session:
                await self.session.close()
                self.session = None
                
            self.is_connected = False
            logger.info("Disconnected from Tradovate API")
            
        except Exception as e:
            logger.error(f"Error disconnecting from Tradovate: {e}")
            
    async def _authenticate(self) -> None:
        """Authenticate with Tradovate API."""
        auth_data = {
            "name": self.api_key,
            "password": self.api_secret,
            "appId": "NQTradingAgent",
            "appVersion": "1.0.0",
            "cid": 1
        }
        
        try:
            async with self.session.post(
                f"{self.rest_url}/auth/accesstokenrequest",
                json=auth_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result.get('accessToken')
                    logger.info("Authenticated with Tradovate API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Authentication failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise
            
    async def _get_account_info(self) -> None:
        """Get account information."""
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Get account info
            async with self.session.get(
                f"{self.rest_url}/account/list",
                headers=headers
            ) as response:
                if response.status == 200:
                    accounts = await response.json()
                    if accounts:
                        self.account_info = accounts[0]  # Use first account
                        logger.info(f"Account info loaded: {self.account_info.get('name', 'Unknown')}")
                    else:
                        raise Exception("No accounts found")
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get account info: {response.status} - {error_text}")
                    
            # Get margin info
            account_id = self.account_info.get('id')
            async with self.session.get(
                f"{self.rest_url}/cashBalance/getcashbalancesnapshot",
                headers=headers,
                params={"accountId": account_id}
            ) as response:
                if response.status == 200:
                    self.margin_info = await response.json()
                    logger.info("Margin info loaded")
                else:
                    logger.warning(f"Failed to get margin info: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise
            
    async def _connect_websocket(self) -> None:
        """Connect to Tradovate WebSocket."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            
            # Start WebSocket message handler
            asyncio.create_task(self._handle_websocket_messages())
            
            logger.info("Connected to Tradovate WebSocket")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
            
    async def _handle_websocket_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_websocket_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
            
    async def _process_websocket_message(self, data: Dict[str, Any]) -> None:
        """Process WebSocket message."""
        try:
            msg_type = data.get('e')
            
            if msg_type == 'md':  # Market data
                await self._handle_market_data(data)
            elif msg_type == 'order':  # Order updates
                await self._handle_order_update(data)
            elif msg_type == 'position':  # Position updates
                await self._handle_position_update(data)
            elif msg_type == 'fill':  # Fill updates
                await self._handle_fill_update(data)
            else:
                logger.debug(f"Unhandled message type: {msg_type}")
                
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            
    async def _handle_market_data(self, data: Dict[str, Any]) -> None:
        """Handle market data updates."""
        try:
            # Process market data
            market_data = data.get('d', {})
            logger.debug(f"Market data received: {market_data}")
            
        except Exception as e:
            logger.error(f"Error handling market data: {e}")
            
    async def _handle_order_update(self, data: Dict[str, Any]) -> None:
        """Handle order updates."""
        try:
            order_data = data.get('d', {})
            logger.info(f"Order update: {order_data}")
            
        except Exception as e:
            logger.error(f"Error handling order update: {e}")
            
    async def _handle_position_update(self, data: Dict[str, Any]) -> None:
        """Handle position updates."""
        try:
            position_data = data.get('d', {})
            logger.info(f"Position update: {position_data}")
            
        except Exception as e:
            logger.error(f"Error handling position update: {e}")
            
    async def _handle_fill_update(self, data: Dict[str, Any]) -> None:
        """Handle fill updates."""
        try:
            fill_data = data.get('d', {})
            logger.info(f"Fill update: {fill_data}")
            
        except Exception as e:
            logger.error(f"Error handling fill update: {e}")
            
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order on Tradovate.
        
        Args:
            order: Order details
            
        Returns:
            Order placement result
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'reason': 'Not connected to Tradovate'
                }
                
            # Convert order to Tradovate format
            tradovate_order = self._convert_order_to_tradovate(order)
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Submit order
            async with self.session.post(
                f"{self.rest_url}/order/placeorder",
                headers=headers,
                json=tradovate_order
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract order ID and fill price
                    order_id = result.get('orderId')
                    fill_price = result.get('fillPrice', order.get('price'))
                    
                    return {
                        'success': True,
                        'order_id': order_id,
                        'fill_price': fill_price,
                        'result': result
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'reason': f"Order placement failed: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {
                'success': False,
                'reason': f"Order placement error: {e}"
            }
            
    def _convert_order_to_tradovate(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Convert order to Tradovate format."""
        try:
            # Get contract ID for NQ
            contract_id = self._get_nq_contract_id()
            
            # Map order side
            side_mapping = {
                'BUY': 'Buy',
                'SELL': 'Sell'
            }
            
            # Map order type
            type_mapping = {
                'MARKET': 'Market',
                'LIMIT': 'Limit',
                'STOP': 'Stop'
            }
            
            tradovate_order = {
                'accountId': self.account_info.get('id'),
                'contractId': contract_id,
                'action': side_mapping.get(order['side'], 'Buy'),
                'orderType': type_mapping.get(order['order_type'], 'Market'),
                'qty': order['quantity'],
                'timeInForce': 'Day'
            }
            
            # Add price for limit orders
            if order['order_type'] == 'LIMIT':
                tradovate_order['price'] = order['price']
                
            # Add stop price for stop orders
            if order['order_type'] == 'STOP':
                tradovate_order['stopPrice'] = order['price']
                
            return tradovate_order
            
        except Exception as e:
            logger.error(f"Error converting order: {e}")
            raise
            
    def _get_nq_contract_id(self) -> int:
        """Get NQ contract ID."""
        # This would typically be retrieved from Tradovate's contract list
        # For now, using a placeholder
        return 3930  # NQ contract ID (this needs to be actual contract ID)
        
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'reason': 'Not connected to Tradovate'
                }
                
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{self.rest_url}/order/cancelorder",
                headers=headers,
                json={'orderId': order_id}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        'success': True,
                        'result': result
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'reason': f"Order cancellation failed: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {
                'success': False,
                'reason': f"Order cancellation error: {e}"
            }
            
    async def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions.
        
        Returns:
            Positions data
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'reason': 'Not connected to Tradovate'
                }
                
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            account_id = self.account_info.get('id')
            async with self.session.get(
                f"{self.rest_url}/position/list",
                headers=headers,
                params={'accountId': account_id}
            ) as response:
                if response.status == 200:
                    positions = await response.json()
                    return {
                        'success': True,
                        'positions': positions
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'reason': f"Failed to get positions: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {
                'success': False,
                'reason': f"Get positions error: {e}"
            }
            
    async def get_account_balance(self) -> Dict[str, Any]:
        """
        Get account balance.
        
        Returns:
            Account balance data
        """
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'reason': 'Not connected to Tradovate'
                }
                
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            account_id = self.account_info.get('id')
            async with self.session.get(
                f"{self.rest_url}/cashBalance/getcashbalancesnapshot",
                headers=headers,
                params={'accountId': account_id}
            ) as response:
                if response.status == 200:
                    balance = await response.json()
                    return {
                        'success': True,
                        'balance': balance
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'reason': f"Failed to get balance: {response.status} - {error_text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting account balance: {e}")
            return {
                'success': False,
                'reason': f"Get balance error: {e}"
            }
            
    async def subscribe_to_quotes(self, symbol: str) -> Dict[str, Any]:
        """
        Subscribe to real-time quotes.
        
        Args:
            symbol: Symbol to subscribe to
            
        Returns:
            Subscription result
        """
        try:
            if not self.websocket:
                return {
                    'success': False,
                    'reason': 'WebSocket not connected'
                }
                
            subscribe_msg = {
                "url": "md/subscribeQuote",
                "body": {
                    "symbol": symbol
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            
            return {
                'success': True,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to quotes: {e}")
            return {
                'success': False,
                'reason': f"Subscription error: {e}"
            }
            
    async def unsubscribe_from_quotes(self, symbol: str) -> Dict[str, Any]:
        """
        Unsubscribe from real-time quotes.
        
        Args:
            symbol: Symbol to unsubscribe from
            
        Returns:
            Unsubscription result
        """
        try:
            if not self.websocket:
                return {
                    'success': False,
                    'reason': 'WebSocket not connected'
                }
                
            unsubscribe_msg = {
                "url": "md/unsubscribeQuote",
                "body": {
                    "symbol": symbol
                }
            }
            
            await self.websocket.send(json.dumps(unsubscribe_msg))
            
            return {
                'success': True,
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error unsubscribing from quotes: {e}")
            return {
                'success': False,
                'reason': f"Unsubscription error: {e}"
            }
            
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return {
            'account_info': self.account_info,
            'margin_info': self.margin_info,
            'is_connected': self.is_connected
        }
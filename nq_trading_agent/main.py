"""
Main entry point for NQ Trading Agent
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from .utils.config_loader import ConfigLoader
from .utils.logging import setup_logging
from .utils.llm_factory import LLMFactory
from .data.ingestion import DataIngestion
from .agents.llm_agent import LLMAnalysisAgent
from .agents.execution_agent import ExecutionAgent
from .platforms.tradovate import TradovatePlatform
from .platforms.mock_platform import MockPlatform

logger = logging.getLogger(__name__)


class NQTradingAgent:
    """
    Main NQ Trading Agent class that coordinates all components.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize NQ Trading Agent.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        
        # Initialize components
        self.data_ingestion = None
        self.llm_agent = None
        self.execution_agent = None
        self.platform = None
        
        # Runtime state
        self.running = False
        self.last_analysis_time = None
        self.analysis_count = 0
        
        # Setup logging
        logging_config = self.config.get('logging', {})
        setup_logging(
            level=logging_config.get('level', 'INFO'),
            log_file=logging_config.get('file'),
            format_string=logging_config.get('format'),
            max_size=logging_config.get('max_size', '10MB'),
            backup_count=logging_config.get('backup_count', 5)
        )
        
        logger.info("NQ Trading Agent initialized")
        
    async def start(self) -> None:
        """Start the trading agent."""
        try:
            logger.info("Starting NQ Trading Agent...")
            
            # Initialize components
            await self._initialize_components()
            
            # Connect to data source
            await self.data_ingestion.connect()
            
            # Connect to trading platform
            await self.execution_agent.connect_platform(self.platform)
            
            # Set running flag
            self.running = True
            
            # Start main trading loop
            await self._run_trading_loop()
            
        except Exception as e:
            logger.error(f"Error starting trading agent: {e}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop the trading agent."""
        try:
            logger.info("Stopping NQ Trading Agent...")
            
            self.running = False
            
            # Disconnect from data source
            if self.data_ingestion:
                await self.data_ingestion.disconnect()
                
            # Disconnect from trading platform
            if self.execution_agent:
                await self.execution_agent.disconnect_platform()
                
            # Close LLM agent
            if self.llm_agent:
                await self.llm_agent.close()
                
            logger.info("NQ Trading Agent stopped")
            
        except Exception as e:
            logger.error(f"Error stopping trading agent: {e}")
            
    async def _initialize_components(self) -> None:
        """Initialize all components."""
        try:
            # Initialize data ingestion
            data_config = self.config_loader.get_data_config()
            self.data_ingestion = DataIngestion(data_config)
            
            # Initialize LLM agent
            self.llm_agent = LLMAnalysisAgent(self.config)
            
            # Initialize execution agent
            self.execution_agent = ExecutionAgent(self.config)
            
            # Initialize trading platform
            self.platform = self._create_platform()
            
            logger.info("All components initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
            
    def _create_platform(self):
        """Create the appropriate trading platform."""
        data_config = self.config_loader.get_data_config()
        source = data_config.get('source', 'mock')
        
        if source == 'tradovate':
            return TradovatePlatform(data_config)
        else:
            return MockPlatform(data_config)
            
    async def _run_trading_loop(self) -> None:
        """Main trading loop."""
        try:
            logger.info("Starting main trading loop")
            
            # Get NQ configuration
            nq_config = self.data_ingestion.get_nq_config()
            
            # Start data stream
            symbol = nq_config.get('symbol', 'NQ')
            data_stream = self.data_ingestion.stream_live_data(symbol)
            
            # Process data stream
            data_buffer = []
            last_analysis = datetime.now()
            analysis_interval = 60  # Analyze every 60 seconds
            
            async for market_data in data_stream:
                if not self.running:
                    break
                    
                # Add to buffer
                data_buffer.append(market_data)
                
                # Keep only last 1000 data points
                if len(data_buffer) > 1000:
                    data_buffer = data_buffer[-1000:]
                    
                # Check if it's time for analysis
                now = datetime.now()
                if (now - last_analysis).total_seconds() >= analysis_interval:
                    if len(data_buffer) >= 50:  # Minimum data points
                        await self._process_market_data(data_buffer, nq_config)
                        last_analysis = now
                        
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            
    async def _process_market_data(self, data_buffer: list, nq_config: Dict[str, Any]) -> None:
        """Process market data and execute trades."""
        try:
            # Convert buffer to DataFrame
            import pandas as pd
            df = pd.DataFrame(data_buffer)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Check if we should analyze
            trigger_conditions = {
                'min_analysis_interval': 60,
                'price_change_threshold': 0.005,
                'volume_spike_threshold': 2.0,
                'max_analysis_interval': 300
            }
            
            if self.llm_agent.should_analyze(trigger_conditions):
                # Analyze market
                analysis_result = await self.llm_agent.analyze_market(df, nq_config)
                
                # Execute signal
                signal = analysis_result.get('signal', {})
                if signal.get('action') in ['BUY', 'SELL']:
                    execution_result = await self.execution_agent.execute_signal(
                        signal, current_price, nq_config
                    )
                    
                    # Log execution result
                    if execution_result['success']:
                        logger.info(f"Trade executed: {execution_result['action']} at {current_price}")
                    else:
                        logger.warning(f"Trade execution failed: {execution_result['reason']}")
                        
                self.analysis_count += 1
                self.last_analysis_time = datetime.now()
                
            # Update positions
            await self.execution_agent.update_positions({nq_config.get('symbol', 'NQ'): current_price})
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            
    async def run_backtest(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Run backtest on historical data.
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            
        Returns:
            Backtest results
        """
        try:
            logger.info(f"Starting backtest from {start_date} to {end_date}")
            
            # Initialize components for backtest
            await self._initialize_components()
            
            # Get historical data
            nq_config = self.data_ingestion.get_nq_config()
            symbol = nq_config.get('symbol', 'NQ')
            
            historical_data = await self.data_ingestion.get_historical_data(
                symbol, start_date, end_date, "1h"
            )
            
            if historical_data.empty:
                raise ValueError("No historical data available for backtest")
                
            # Run backtest
            backtest_results = await self._run_backtest_simulation(historical_data, nq_config)
            
            logger.info(f"Backtest completed: {backtest_results}")
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            raise
            
    async def _run_backtest_simulation(self, data: 'pd.DataFrame', nq_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run backtest simulation."""
        try:
            # Initialize mock platform for backtest
            mock_platform = MockPlatform({})
            await mock_platform.connect()
            await self.execution_agent.connect_platform(mock_platform)
            
            # Process data in chunks
            window_size = 50
            total_trades = 0
            successful_trades = 0
            
            for i in range(window_size, len(data)):
                # Get data window
                window_data = data.iloc[i-window_size:i]
                current_price = window_data['close'].iloc[-1]
                
                # Analyze
                analysis_result = await self.llm_agent.analyze_market(window_data, nq_config)
                
                # Execute signal
                signal = analysis_result.get('signal', {})
                if signal.get('action') in ['BUY', 'SELL']:
                    execution_result = await self.execution_agent.execute_signal(
                        signal, current_price, nq_config
                    )
                    
                    total_trades += 1
                    if execution_result['success']:
                        successful_trades += 1
                        
                # Update positions
                await self.execution_agent.update_positions({nq_config.get('symbol', 'NQ'): current_price})
                
            # Get final results
            account_summary = self.execution_agent.get_account_summary()
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'success_rate': successful_trades / total_trades if total_trades > 0 else 0,
                'final_balance': account_summary['total_account_value'],
                'total_pnl': account_summary['total_pnl'],
                'unrealized_pnl': account_summary['unrealized_pnl'],
                'open_positions': account_summary['open_positions']
            }
            
        except Exception as e:
            logger.error(f"Error running backtest simulation: {e}")
            raise
            
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the trading agent."""
        try:
            status = {
                'running': self.running,
                'analysis_count': self.analysis_count,
                'last_analysis_time': self.last_analysis_time,
                'config_loaded': self.config is not None,
                'components_initialized': all([
                    self.data_ingestion is not None,
                    self.llm_agent is not None,
                    self.execution_agent is not None,
                    self.platform is not None
                ])
            }
            
            # Add component status
            if self.data_ingestion:
                status['data_connection'] = self.data_ingestion.data_source.is_connected
                
            if self.execution_agent:
                status['platform_connection'] = self.execution_agent.is_connected
                status['account_summary'] = self.execution_agent.get_account_summary()
                
            if self.llm_agent:
                status['llm_summary'] = self.llm_agent.get_analysis_summary()
                
            return status
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'error': str(e)}
            
    async def manual_analysis(self) -> Dict[str, Any]:
        """Manually trigger market analysis."""
        try:
            if not self.running:
                return {'error': 'Agent not running'}
                
            # Get recent data
            nq_config = self.data_ingestion.get_nq_config()
            symbol = nq_config.get('symbol', 'NQ')
            
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            data = await self.data_ingestion.get_historical_data(
                symbol, start_date, end_date, "1m"
            )
            
            if data.empty:
                return {'error': 'No data available'}
                
            # Analyze
            analysis_result = await self.llm_agent.analyze_market(data, nq_config)
            
            return {
                'success': True,
                'analysis': analysis_result,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error in manual analysis: {e}")
            return {'error': str(e)}


async def main():
    """Main function."""
    agent = None
    
    try:
        # Handle shutdown signals
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            if agent:
                asyncio.create_task(agent.stop())
                
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Create and start agent
        agent = NQTradingAgent()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == 'backtest':
                # Run backtest
                start_date = datetime.now() - timedelta(days=30)
                end_date = datetime.now()
                results = await agent.run_backtest(start_date, end_date)
                print(f"Backtest results: {results}")
                
            elif command == 'status':
                # Show status
                await agent._initialize_components()
                status = agent.get_status()
                print(f"Status: {status}")
                
            elif command == 'test':
                # Run tests
                await agent._initialize_components()
                analysis = await agent.manual_analysis()
                print(f"Test analysis: {analysis}")
                
            else:
                print(f"Unknown command: {command}")
                print("Available commands: backtest, status, test")
                
        else:
            # Run normal trading
            await agent.start()
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        if agent:
            await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
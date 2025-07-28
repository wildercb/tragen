/**
 * ChartExamples - Usage examples for TradingChart V2
 * 
 * This file contains comprehensive examples showing how to use the new
 * TradingChart V2 component with different configurations and features.
 */

import React, { useState, useEffect, useCallback } from 'react';
import TradingChartV2 from '../components/TradingChartV2';
import MarketDataProvider from '../services/MarketDataProvider';
import ChartAgentInterface from '../services/ChartAgentInterface';
import TechnicalIndicators from '../utils/TechnicalIndicators';

// Example 1: Basic Chart Usage
export const BasicChartExample = () => {
  const [symbol, setSymbol] = useState('NQ=F');
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Basic Chart Example</h2>
      <TradingChartV2
        symbol={symbol}
        displaySymbol={symbol.replace('=F', '')}
        height={350}
        onSymbolChange={(newSymbol, displaySymbol) => {
          setSymbol(newSymbol);
          console.log(`Symbol changed to: ${newSymbol}`);
        }}
      />
    </div>
  );
};

// Example 2: Chart with Custom Indicators
export const CustomIndicatorExample = () => {
  const [indicators, setIndicators] = useState({
    sma20: { enabled: true, visible: true, color: '#f59e0b', period: 20 },
    rsi: { enabled: true, visible: true, color: '#8b5cf6', period: 14 },
    bollinger: { enabled: true, visible: true, color: '#ef4444', period: 20, stdDev: 2 },
    superTrend: { enabled: true, visible: true, color: '#10b981', period: 10, multiplier: 3 }
  });
  
  const toggleIndicator = (indicator) => {
    setIndicators(prev => ({
      ...prev,
      [indicator]: {
        ...prev[indicator],
        enabled: !prev[indicator].enabled
      }
    }));
  };
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Custom Indicators Example</h2>
      
      {/* Indicator Controls */}
      <div className="mb-4 flex flex-wrap gap-2">
        {Object.entries(indicators).map(([key, config]) => (
          <button
            key={key}
            onClick={() => toggleIndicator(key)}
            className={`px-3 py-1 text-xs rounded-full border ${
              config.enabled 
                ? 'bg-blue-600 border-blue-600 text-white' 
                : 'bg-transparent border-gray-600 text-gray-400'
            }`}
          >
            {key.toUpperCase()}
          </button>
        ))}
      </div>
      
      <TradingChartV2
        symbol="NQ=F"
        displaySymbol="NQ"
        height={300}
        customIndicators={indicators}
      />
    </div>
  );
};

// Example 3: Multi-Timeframe Chart
export const MultiTimeframeExample = () => {
  const [timeframes] = useState(['1m', '5m', '15m', '1h', '1d']);
  const [activeTimeframe, setActiveTimeframe] = useState('5m');
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Multi-Timeframe Example</h2>
      
      {/* Timeframe Selector */}
      <div className="mb-4 flex gap-2">
        {timeframes.map(tf => (
          <button
            key={tf}
            onClick={() => setActiveTimeframe(tf)}
            className={`px-3 py-1 text-xs rounded ${
              activeTimeframe === tf
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {tf}
          </button>
        ))}
      </div>
      
      <TradingChartV2
        symbol="NQ=F"
        displaySymbol="NQ"
        height={300}
        timeframe={activeTimeframe}
        period="1d"
      />
    </div>
  );
};

// Example 4: Chart with AI Agent Integration
export const AIAgentExample = () => {
  const [dataProvider] = useState(new MarketDataProvider());
  const [agentInterface] = useState(new ChartAgentInterface(dataProvider));
  const [agentId, setAgentId] = useState(null);
  const [signals, setSignals] = useState([]);
  const [analysisData, setAnalysisData] = useState(null);
  
  useEffect(() => {
    // Register AI agent
    const id = agentInterface.registerAgent('demo-agent', {
      name: 'Demo Trading Agent',
      type: 'trading',
      permissions: ['read', 'analyze'],
      indicators: ['sma20', 'rsi', 'macd'],
      updateFrequency: 'realtime'
    });
    
    setAgentId(id);
    
    // Subscribe to real-time data
    agentInterface.subscribeToSymbol(id, 'NQ=F', handleAgentUpdate);
    
    return () => {
      agentInterface.unregisterAgent(id);
    };
  }, []);
  
  const handleAgentUpdate = useCallback((update) => {
    console.log('Agent update:', update);
    
    if (update.type === 'price_update') {
      // Update analysis data
      setAnalysisData(prev => ({
        ...prev,
        currentPrice: update.data.price,
        lastUpdate: new Date()
      }));
    }
  }, []);
  
  const generateSignals = async () => {
    if (!agentId) return;
    
    try {
      const newSignals = await agentInterface.generateSignals(agentId, 'NQ=F', {
        strategy: 'momentum',
        lookback: '1d',
        timeframe: '5m'
      });
      
      setSignals(newSignals);
    } catch (error) {
      console.error('Error generating signals:', error);
    }
  };
  
  const getAnalysis = async () => {
    if (!agentId) return;
    
    try {
      const analysis = await agentInterface.getRealTimeAnalysis(agentId, 'NQ=F');
      setAnalysisData(analysis);
    } catch (error) {
      console.error('Error getting analysis:', error);
    }
  };
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">AI Agent Integration Example</h2>
      
      {/* Agent Controls */}
      <div className="mb-4 flex gap-2">
        <button
          onClick={generateSignals}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Generate Signals
        </button>
        <button
          onClick={getAnalysis}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Get Analysis
        </button>
      </div>
      
      {/* Analysis Display */}
      {analysisData && (
        <div className="mb-4 p-3 bg-gray-800 rounded">
          <h3 className="text-white text-sm font-semibold mb-2">Real-time Analysis</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-400">Current Price:</span>
              <span className="text-white ml-2">${analysisData.currentPrice?.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-400">Market Condition:</span>
              <span className="text-white ml-2">{analysisData.marketCondition?.condition}</span>
            </div>
            <div>
              <span className="text-gray-400">Volatility:</span>
              <span className="text-white ml-2">{(analysisData.analysis?.volatility * 100)?.toFixed(2)}%</span>
            </div>
            <div>
              <span className="text-gray-400">Signals:</span>
              <span className="text-white ml-2">{signals.length}</span>
            </div>
          </div>
        </div>
      )}
      
      {/* Chart */}
      <TradingChartV2
        symbol="NQ=F"
        displaySymbol="NQ"
        height={250}
        onSignalReceived={(signal) => {
          console.log('Chart signal:', signal);
          setSignals(prev => [...prev, signal]);
        }}
        agentConfig={{
          enabled: true,
          agentInterface: agentInterface,
          agentId: agentId
        }}
      />
    </div>
  );
};

// Example 5: Chart with Custom Pattern Detection
export const PatternDetectionExample = () => {
  const [patterns, setPatterns] = useState([]);
  const [detectedPatterns, setDetectedPatterns] = useState([]);
  
  useEffect(() => {
    // Register custom pattern detectors
    const indicators = new TechnicalIndicators();
    
    // Double Bottom Pattern
    indicators.registerCustomIndicator('doubleBottom', (data, params = {}) => {
      const { minDistance = 20, tolerance = 0.02 } = params;
      const patterns = [];
      
      for (let i = minDistance; i < data.length - minDistance; i++) {
        const leftLow = Math.min(...data.slice(i - minDistance, i).map(d => d.low));
        const rightLow = Math.min(...data.slice(i, i + minDistance).map(d => d.low));
        const currentLow = data[i].low;
        
        if (Math.abs(leftLow - currentLow) / currentLow < tolerance &&
            Math.abs(rightLow - currentLow) / currentLow < tolerance) {
          patterns.push({
            time: data[i].time,
            type: 'double_bottom',
            price: currentLow,
            confidence: 0.8
          });
        }
      }
      
      return patterns;
    });
    
    // Support/Resistance Levels
    indicators.registerCustomIndicator('supportResistance', (data, params = {}) => {
      const { touchCount = 3, tolerance = 0.01 } = params;
      const levels = [];
      
      // Simple support/resistance detection
      const prices = data.map(d => d.close);
      const highs = data.map(d => d.high);
      const lows = data.map(d => d.low);
      
      // Find potential levels
      const potentialLevels = [...new Set([...highs, ...lows])];
      
      for (const level of potentialLevels) {
        let touchCount = 0;
        
        for (const price of prices) {
          if (Math.abs(price - level) / level < tolerance) {
            touchCount++;
          }
        }
        
        if (touchCount >= touchCount) {
          levels.push({
            price: level,
            type: level > prices[prices.length - 1] ? 'resistance' : 'support',
            strength: touchCount,
            confidence: Math.min(touchCount / 5, 1)
          });
        }
      }
      
      return levels;
    });
    
  }, []);
  
  const handleChartDataUpdate = useCallback((data) => {
    // Run pattern detection on new data
    const indicators = new TechnicalIndicators();
    
    try {
      const doubleBottoms = indicators.calculateCustom('doubleBottom', data, {
        minDistance: 20,
        tolerance: 0.02
      });
      
      const srLevels = indicators.calculateCustom('supportResistance', data, {
        touchCount: 3,
        tolerance: 0.01
      });
      
      setDetectedPatterns([...doubleBottoms, ...srLevels]);
    } catch (error) {
      console.error('Pattern detection error:', error);
    }
  }, []);
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Pattern Detection Example</h2>
      
      {/* Pattern List */}
      {detectedPatterns.length > 0 && (
        <div className="mb-4 p-3 bg-gray-800 rounded">
          <h3 className="text-white text-sm font-semibold mb-2">Detected Patterns</h3>
          <div className="space-y-1">
            {detectedPatterns.slice(-5).map((pattern, index) => (
              <div key={index} className="text-xs text-gray-400">
                <span className="text-white">{pattern.type.replace('_', ' ').toUpperCase()}</span>
                {pattern.price && <span className="ml-2">@ ${pattern.price.toFixed(2)}</span>}
                {pattern.confidence && (
                  <span className="ml-2 text-green-400">
                    {(pattern.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <TradingChartV2
        symbol="NQ=F"
        displaySymbol="NQ"
        height={280}
        onChartDataUpdate={handleChartDataUpdate}
        enablePatternDetection={true}
      />
    </div>
  );
};

// Example 6: Performance Comparison Dashboard
export const PerformanceComparisonExample = () => {
  const [symbols] = useState(['NQ=F', 'ES=F', 'YM=F', 'RTY=F']);
  const [activeSymbol, setActiveSymbol] = useState('NQ=F');
  const [performanceData, setPerformanceData] = useState({});
  
  useEffect(() => {
    // Simulate performance data
    const mockData = {
      'NQ=F': { change: 2.5, volume: 1250000, volatility: 0.018 },
      'ES=F': { change: 1.2, volume: 2100000, volatility: 0.015 },
      'YM=F': { change: 0.8, volume: 180000, volatility: 0.012 },
      'RTY=F': { change: -0.3, volume: 420000, volatility: 0.022 }
    };
    setPerformanceData(mockData);
  }, []);
  
  return (
    <div className="w-full h-96 bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Performance Comparison</h2>
      
      {/* Symbol Selector with Performance */}
      <div className="mb-4 grid grid-cols-4 gap-2">
        {symbols.map(symbol => {
          const data = performanceData[symbol];
          return (
            <button
              key={symbol}
              onClick={() => setActiveSymbol(symbol)}
              className={`p-2 rounded text-xs ${
                activeSymbol === symbol
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <div className="font-semibold">{symbol.replace('=F', '')}</div>
              {data && (
                <div className={`text-xs ${
                  data.change > 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {data.change > 0 ? '+' : ''}{data.change.toFixed(2)}%
                </div>
              )}
            </button>
          );
        })}
      </div>
      
      {/* Performance Metrics */}
      {performanceData[activeSymbol] && (
        <div className="mb-4 p-3 bg-gray-800 rounded">
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-gray-400">Change:</span>
              <span className={`ml-2 ${
                performanceData[activeSymbol].change > 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {performanceData[activeSymbol].change > 0 ? '+' : ''}
                {performanceData[activeSymbol].change.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-gray-400">Volume:</span>
              <span className="text-white ml-2">
                {(performanceData[activeSymbol].volume / 1000000).toFixed(2)}M
              </span>
            </div>
            <div>
              <span className="text-gray-400">Volatility:</span>
              <span className="text-white ml-2">
                {(performanceData[activeSymbol].volatility * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}
      
      <TradingChartV2
        symbol={activeSymbol}
        displaySymbol={activeSymbol.replace('=F', '')}
        height={250}
        key={activeSymbol} // Force re-render on symbol change
      />
    </div>
  );
};

// Example 7: Complete Trading Dashboard
export const TradingDashboardExample = () => {
  const [dataProvider] = useState(new MarketDataProvider());
  const [agentInterface] = useState(new ChartAgentInterface(dataProvider));
  const [symbol, setSymbol] = useState('NQ=F');
  const [signals, setSignals] = useState([]);
  const [positions, setPositions] = useState([]);
  const [pnl, setPnl] = useState(0);
  
  const handleSignalReceived = useCallback((signal) => {
    setSignals(prev => [...prev.slice(-9), signal]);
    
    // Simulate position management
    if (signal.type === 'buy') {
      setPositions(prev => [...prev, {
        symbol: signal.symbol,
        type: 'long',
        price: signal.price,
        size: 1,
        timestamp: signal.timestamp
      }]);
    } else if (signal.type === 'sell' && positions.length > 0) {
      const position = positions[positions.length - 1];
      const profit = (signal.price - position.price) * position.size;
      setPnl(prev => prev + profit);
      setPositions(prev => prev.slice(0, -1));
    }
  }, [positions]);
  
  return (
    <div className="w-full h-[600px] bg-gray-900 rounded-lg p-4">
      <h2 className="text-white text-xl mb-4">Complete Trading Dashboard</h2>
      
      <div className="grid grid-cols-3 gap-4 h-full">
        {/* Chart Area */}
        <div className="col-span-2">
          <TradingChartV2
            symbol={symbol}
            displaySymbol={symbol.replace('=F', '')}
            height={550}
            onSignalReceived={handleSignalReceived}
            onSymbolChange={setSymbol}
            agentConfig={{
              enabled: true,
              agentInterface: agentInterface
            }}
          />
        </div>
        
        {/* Sidebar */}
        <div className="space-y-4">
          {/* P&L */}
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-white text-sm font-semibold mb-2">P&L</h3>
            <div className={`text-2xl font-bold ${
              pnl > 0 ? 'text-green-400' : pnl < 0 ? 'text-red-400' : 'text-white'
            }`}>
              {pnl > 0 ? '+' : ''}${pnl.toFixed(2)}
            </div>
          </div>
          
          {/* Positions */}
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-white text-sm font-semibold mb-2">Positions</h3>
            <div className="space-y-2">
              {positions.map((position, index) => (
                <div key={index} className="text-xs">
                  <div className="text-white">
                    {position.type.toUpperCase()} {position.symbol}
                  </div>
                  <div className="text-gray-400">
                    ${position.price.toFixed(2)} x {position.size}
                  </div>
                </div>
              ))}
              {positions.length === 0 && (
                <div className="text-gray-400 text-xs">No open positions</div>
              )}
            </div>
          </div>
          
          {/* Recent Signals */}
          <div className="bg-gray-800 p-4 rounded">
            <h3 className="text-white text-sm font-semibold mb-2">Recent Signals</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {signals.map((signal, index) => (
                <div key={index} className="text-xs">
                  <div className={`font-semibold ${
                    signal.type === 'buy' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {signal.type.toUpperCase()}
                  </div>
                  <div className="text-gray-400">
                    ${signal.price?.toFixed(2)} • {signal.reason || 'Signal'}
                  </div>
                </div>
              ))}
              {signals.length === 0 && (
                <div className="text-gray-400 text-xs">No signals yet</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Export all examples
export const ChartExamples = {
  BasicChartExample,
  CustomIndicatorExample,
  MultiTimeframeExample,
  AIAgentExample,
  PatternDetectionExample,
  PerformanceComparisonExample,
  TradingDashboardExample
};

export default ChartExamples;
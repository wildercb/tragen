import React, { useState, useCallback } from 'react';
import { 
  PlusIcon, 
  EyeIcon, 
  EyeSlashIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';

const TradingIndicators = ({ onIndicatorChange }) => {
  const [indicators, setIndicators] = useState({
    // Moving Averages
    sma20: { enabled: true, visible: true, color: '#f59e0b', period: 20, name: 'SMA 20' },
    sma50: { enabled: false, visible: true, color: '#8b5cf6', period: 50, name: 'SMA 50' },
    sma200: { enabled: false, visible: true, color: '#dc2626', period: 200, name: 'SMA 200' },
    ema12: { enabled: false, visible: true, color: '#06b6d4', period: 12, name: 'EMA 12' },
    ema26: { enabled: false, visible: true, color: '#84cc16', period: 26, name: 'EMA 26' },
    ema50: { enabled: false, visible: true, color: '#f97316', period: 50, name: 'EMA 50' },
    
    // Oscillators
    rsi: { enabled: false, visible: true, color: '#a855f7', period: 14, name: 'RSI' },
    stoch: { enabled: false, visible: true, color: '#ec4899', period: 14, name: 'Stochastic' },
    cci: { enabled: false, visible: true, color: '#06b6d4', period: 20, name: 'CCI' },
    williams: { enabled: false, visible: true, color: '#65a30d', period: 14, name: 'Williams %R' },
    
    // Momentum
    macd: { enabled: false, visible: true, color: '#10b981', name: 'MACD' },
    momentum: { enabled: false, visible: true, color: '#f59e0b', period: 10, name: 'Momentum' },
    roc: { enabled: false, visible: true, color: '#ef4444', period: 12, name: 'Rate of Change' },
    
    // Volatility
    bollinger: { enabled: false, visible: true, color: '#8b5cf6', period: 20, name: 'Bollinger Bands' },
    atr: { enabled: false, visible: true, color: '#f97316', period: 14, name: 'ATR' },
    keltner: { enabled: false, visible: true, color: '#06b6d4', period: 20, name: 'Keltner Channels' },
    
    // Volume
    volume: { enabled: true, visible: true, color: '#6b7280', name: 'Volume' },
    obv: { enabled: false, visible: true, color: '#84cc16', name: 'On Balance Volume' },
    vwap: { enabled: false, visible: true, color: '#f59e0b', name: 'VWAP' },
    
    // Trend
    adx: { enabled: false, visible: true, color: '#a855f7', period: 14, name: 'ADX' },
    supertrend: { enabled: false, visible: true, color: '#ef4444', period: 10, name: 'SuperTrend' },
    ichimoku: { enabled: false, visible: true, color: '#06b6d4', name: 'Ichimoku Cloud' },
    parabolic: { enabled: false, visible: true, color: '#f97316', name: 'Parabolic SAR' },
  });

  const [showIndicatorList, setShowIndicatorList] = useState(false);

  const availableIndicators = [
    // Moving Averages
    { key: 'sma20', name: 'Simple Moving Average (20)', category: 'Moving Averages' },
    { key: 'sma50', name: 'Simple Moving Average (50)', category: 'Moving Averages' },
    { key: 'sma200', name: 'Simple Moving Average (200)', category: 'Moving Averages' },
    { key: 'ema12', name: 'Exponential Moving Average (12)', category: 'Moving Averages' },
    { key: 'ema26', name: 'Exponential Moving Average (26)', category: 'Moving Averages' },
    { key: 'ema50', name: 'Exponential Moving Average (50)', category: 'Moving Averages' },
    
    // Oscillators  
    { key: 'rsi', name: 'Relative Strength Index', category: 'Oscillators' },
    { key: 'stoch', name: 'Stochastic Oscillator', category: 'Oscillators' },
    { key: 'cci', name: 'Commodity Channel Index', category: 'Oscillators' },
    { key: 'williams', name: 'Williams %R', category: 'Oscillators' },
    
    // Momentum
    { key: 'macd', name: 'MACD', category: 'Momentum' },
    { key: 'momentum', name: 'Momentum', category: 'Momentum' },
    { key: 'roc', name: 'Rate of Change', category: 'Momentum' },
    
    // Volatility
    { key: 'bollinger', name: 'Bollinger Bands', category: 'Volatility' },
    { key: 'atr', name: 'Average True Range', category: 'Volatility' },
    { key: 'keltner', name: 'Keltner Channels', category: 'Volatility' },
    
    // Volume
    { key: 'volume', name: 'Volume', category: 'Volume' },
    { key: 'obv', name: 'On Balance Volume', category: 'Volume' },
    { key: 'vwap', name: 'Volume Weighted Average Price', category: 'Volume' },
    
    // Trend
    { key: 'adx', name: 'Average Directional Index', category: 'Trend' },
    { key: 'supertrend', name: 'SuperTrend', category: 'Trend' },
    { key: 'ichimoku', name: 'Ichimoku Cloud', category: 'Trend' },
    { key: 'parabolic', name: 'Parabolic SAR', category: 'Trend' },
  ];

  const toggleIndicator = useCallback((key) => {
    setIndicators(prev => {
      const updated = {
        ...prev,
        [key]: {
          ...prev[key],
          enabled: !prev[key]?.enabled,
          visible: !prev[key]?.enabled ? true : prev[key]?.visible,
        }
      };
      
      if (onIndicatorChange) {
        onIndicatorChange(updated);
      }
      
      return updated;
    });
  }, [onIndicatorChange]);

  const toggleVisibility = useCallback((key) => {
    setIndicators(prev => {
      const updated = {
        ...prev,
        [key]: {
          ...prev[key],
          visible: !prev[key]?.visible,
        }
      };
      
      if (onIndicatorChange) {
        onIndicatorChange(updated);
      }
      
      return updated;
    });
  }, [onIndicatorChange]);

  const addIndicator = useCallback((key) => {
    const indicator = availableIndicators.find(ind => ind.key === key);
    if (!indicator) return;

    setIndicators(prev => {
      const updated = {
        ...prev,
        [key]: {
          enabled: true,
          visible: true,
          color: `#${Math.floor(Math.random()*16777215).toString(16)}`, // Random color
          name: indicator.name,
          period: key.includes('sma') || key.includes('ema') ? parseInt(key.match(/\d+/)?.[0] || 20) : 14,
        }
      };
      
      if (onIndicatorChange) {
        onIndicatorChange(updated);
      }
      
      return updated;
    });
    
    setShowIndicatorList(false);
  }, [availableIndicators, onIndicatorChange]);

  return (
    <div className="relative">
      {/* Indicators Bar */}
      <div className="flex items-center space-x-2 p-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center space-x-2 flex-wrap">
          {Object.entries(indicators).map(([key, config]) => (
            config.enabled && (
              <div key={key} className="flex items-center space-x-1">
                <button
                  onClick={() => toggleIndicator(key)}
                  className={`px-2 py-1 text-xs rounded-full border transition-colors ${
                    config.visible
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'bg-transparent border-gray-600 text-gray-400'
                  }`}
                  style={{ borderColor: config.visible ? config.color : undefined }}
                >
                  <span 
                    className="inline-block w-2 h-2 rounded-full mr-1" 
                    style={{ backgroundColor: config.color }}
                  />
                  {config.name || key.toUpperCase()}
                </button>
                <button
                  onClick={() => toggleVisibility(key)}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                  title={config.visible ? 'Hide' : 'Show'}
                >
                  {config.visible ? (
                    <EyeIcon className="w-3 h-3" />
                  ) : (
                    <EyeSlashIcon className="w-3 h-3" />
                  )}
                </button>
              </div>
            )
          ))}
        </div>
        
        {/* Add Indicator Button */}
        <button
          onClick={() => setShowIndicatorList(!showIndicatorList)}
          className="p-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          title="Add Indicator"
        >
          <PlusIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Indicator Selection Modal */}
      {showIndicatorList && (
        <div className="absolute top-full left-0 z-50 bg-gray-800 border border-gray-600 rounded-lg shadow-xl w-80 max-h-96 overflow-y-auto">
          <div className="p-3 border-b border-gray-700 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-white">Add Indicators</h4>
            <button
              onClick={() => setShowIndicatorList(false)}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          </div>
          
          <div className="p-2">
            {availableIndicators.map((indicator) => (
              <button
                key={indicator.key}
                onClick={() => addIndicator(indicator.key)}
                disabled={indicators[indicator.key]?.enabled}
                className={`w-full text-left p-2 rounded hover:bg-gray-700 transition-colors mb-1 ${
                  indicators[indicator.key]?.enabled 
                    ? 'opacity-50 cursor-not-allowed' 
                    : 'cursor-pointer'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-white">{indicator.name}</div>
                    <div className="text-xs text-gray-400">{indicator.category}</div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {indicators[indicator.key]?.enabled ? '✓ Added' : '+ Add'}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingIndicators;
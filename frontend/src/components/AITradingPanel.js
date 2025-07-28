import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CpuChipIcon,
  ChartBarIcon,
  PlayIcon,
  PauseIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon,
  StarIcon,
} from '@heroicons/react/24/outline';

const AITradingPanel = ({ 
  symbol, 
  chartData, 
  onSignalReceived, 
  apiBaseUrl = 'http://localhost:8001' 
}) => {
  const [selectedModel, setSelectedModel] = useState('ollama:phi3:mini');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [tradingSignals, setTradingSignals] = useState([]);
  const [autoAnalysis, setAutoAnalysis] = useState(false);
  const [confidence, setConfidence] = useState(75);
  const [riskLevel, setRiskLevel] = useState('medium');
  const [wsConnection, setWsConnection] = useState(null);

  // Available model providers and models
  const modelProviders = {
    ollama: [
      'phi3:mini',
      'llama3:8b',
      'mistral:7b',
      'codellama:7b',
      'neural-chat:7b'
    ],
    openai: [
      'gpt-4-turbo',
      'gpt-4',
      'gpt-3.5-turbo'
    ],
    anthropic: [
      'claude-3-opus',
      'claude-3-sonnet',
      'claude-3-haiku'
    ],
    groq: [
      'llama3-70b',
      'llama3-8b',
      'mixtral-8x7b'
    ]
  };


  // WebSocket connection for real-time signals
  useEffect(() => {
    if (symbol) {
      const wsUrl = `ws://localhost:8001/api/ws/market/${encodeURIComponent(symbol)}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'trading_signal') {
          addTradingSignal(data.signal);
          if (onSignalReceived) {
            onSignalReceived(data.signal);
          }
        } else if (data.type === 'model_analysis_result') {
          setAnalysisResult(data);
          setIsAnalyzing(false);
        }
      };
      
      setWsConnection(ws);
      
      return () => {
        ws.close();
      };
    }
  }, [symbol, onSignalReceived]);

  // Reset analysis state when symbol changes
  useEffect(() => {
    setAnalysisResult(null);
    setIsAnalyzing(false);
    setTradingSignals([]);
  }, [symbol]);


  const analyzeWithAI = useCallback(async () => {
    if (!chartData || chartData.length === 0) {
      console.warn('No chart data available for analysis');
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const [provider, model] = selectedModel.split(':');
      
      // Send chart data via WebSocket for real-time analysis
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify({
          type: 'send_chart_data',
          chart_data: chartData.slice(-50), // Send last 50 candles
          model_provider: provider,
          model_name: model
        }));
      } else {
        // Fallback to HTTP API
        const response = await fetch(`${apiBaseUrl}/api/models/analyze-chart`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            symbol,
            chart_data: chartData.slice(-50),
            model_provider: provider,
            model_name: model
          })
        });
        
        if (response.ok) {
          const result = await response.json();
          setAnalysisResult(result);
        }
        setIsAnalyzing(false);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      setIsAnalyzing(false);
    }
  }, [chartData, selectedModel, symbol, wsConnection, apiBaseUrl]);

  const createManualSignal = useCallback(async (action) => {
    if (!chartData || chartData.length === 0) return;
    
    const currentPrice = chartData[chartData.length - 1]?.close || 0;
    
    const signal = {
      symbol,
      action,
      price: currentPrice,
      confidence: confidence / 100,
      reason: `Manual ${action} signal at $${currentPrice}`
    };

    try {
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.send(JSON.stringify({
          type: 'create_signal',
          signal
        }));
      } else {
        // Fallback to HTTP API
        const response = await fetch(`${apiBaseUrl}/api/trading/manual-signal`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: signal
        });
        
        if (response.ok) {
          const result = await response.json();
          addTradingSignal(result.signal);
        }
      }
    } catch (error) {
      console.error('Failed to create signal:', error);
    }
  }, [chartData, symbol, confidence, wsConnection, apiBaseUrl]);

  const addTradingSignal = useCallback((signal) => {
    setTradingSignals(prev => {
      const newSignals = [signal, ...prev].slice(0, 20); // Keep last 20 signals
      return newSignals;
    });
  }, []);

  const getSignalIcon = (action) => {
    switch (action) {
      case 'buy':
        return <ArrowTrendingUpIcon className="w-5 h-5" />;
      case 'sell':
        return <ArrowTrendingDownIcon className="w-5 h-5" />;
      default:
        return <MinusIcon className="w-5 h-5" />;
    }
  };

  const getSignalColor = (action) => {
    switch (action) {
      case 'buy':
        return 'text-green-400 bg-green-400 bg-opacity-10 border-green-400';
      case 'sell':
        return 'text-red-400 bg-red-400 bg-opacity-10 border-red-400';
      default:
        return 'text-gray-400 bg-gray-400 bg-opacity-10 border-gray-400';
    }
  };

  return (
    <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <StarIcon className="w-6 h-6 text-robin-egg-500" />
          <h3 className="text-lg font-semibold text-white">AI Trading Assistant</h3>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoAnalysis(!autoAnalysis)}
            className={`p-2 rounded-lg transition-colors ${
              autoAnalysis 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title={autoAnalysis ? 'Disable Auto Analysis' : 'Enable Auto Analysis'}
          >
            {autoAnalysis ? <PauseIcon className="w-4 h-4" /> : <PlayIcon className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Model Selection */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <CpuChipIcon className="w-4 h-4 text-gray-400" />
          <label className="text-sm text-gray-300">AI Model:</label>
        </div>
        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="w-full bg-eerie-black-secondary border border-dim-grey-600 rounded-lg px-3 py-2 text-white text-sm focus:border-robin-egg-500 focus:outline-none"
        >
          {Object.entries(modelProviders).map(([provider, models]) => (
            <optgroup key={provider} label={provider.toUpperCase()}>
              {models.map(model => (
                <option key={`${provider}:${model}`} value={`${provider}:${model}`}>
                  {model}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Analysis Controls */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Confidence Level</label>
          <input
            type="range"
            min="50"
            max="95"
            value={confidence}
            onChange={(e) => setConfidence(e.target.value)}
            className="w-full"
          />
          <span className="text-xs text-robin-egg-400">{confidence}%</span>
        </div>
        <div>
          <label className="text-xs text-gray-400 mb-1 block">Risk Level</label>
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="w-full bg-eerie-black-secondary border border-dim-grey-600 rounded px-2 py-1 text-white text-xs"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-4 gap-2">
        <button
          onClick={analyzeWithAI}
          disabled={isAnalyzing}
          className="flex items-center justify-center space-x-1 px-3 py-2 bg-robin-egg-600 hover:bg-robin-egg-700 rounded-lg text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <ChartBarIcon className="w-4 h-4" />
          <span>{isAnalyzing ? 'Analyzing...' : 'Analyze'}</span>
        </button>
        
        <button
          onClick={() => createManualSignal('buy')}
          className="flex items-center justify-center space-x-1 px-3 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white text-sm transition-colors"
        >
          <ArrowTrendingUpIcon className="w-4 h-4" />
          <span>Buy</span>
        </button>
        
        <button
          onClick={() => createManualSignal('sell')}
          className="flex items-center justify-center space-x-1 px-3 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white text-sm transition-colors"
        >
          <ArrowTrendingDownIcon className="w-4 h-4" />
          <span>Sell</span>
        </button>
        
        <button
          onClick={() => createManualSignal('hold')}
          className="flex items-center justify-center space-x-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white text-sm transition-colors"
        >
          <MinusIcon className="w-4 h-4" />
          <span>Hold</span>
        </button>
      </div>

      {/* Analysis Result */}
      {analysisResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-eerie-black-secondary rounded-lg p-3 border border-dim-grey-600"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-white">AI Analysis</span>
            <span className="text-xs text-gray-400">{analysisResult.model_used}</span>
          </div>
          
          {analysisResult.analysis && (
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">Recommendation:</span>
                <span className={`font-medium ${
                  analysisResult.analysis.recommendation === 'BUY' ? 'text-green-400' :
                  analysisResult.analysis.recommendation === 'SELL' ? 'text-red-400' :
                  'text-gray-400'
                }`}>
                  {analysisResult.analysis.recommendation}
                </span>
              </div>
              
              {analysisResult.analysis.confidence && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-300">Confidence:</span>
                  <span className="text-robin-egg-400">{analysisResult.analysis.confidence}%</span>
                </div>
              )}
              
              {analysisResult.analysis.reasoning && (
                <div className="text-xs text-gray-400 mt-2">
                  {analysisResult.analysis.reasoning}
                </div>
              )}
            </div>
          )}
        </motion.div>
      )}

      {/* Trading Signals */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-white">Live Trading Signals</span>
          <span className="text-xs text-gray-400">{tradingSignals.length} signals</span>
        </div>
        
        <div className="space-y-2 max-h-48 overflow-y-auto">
          <AnimatePresence>
            {tradingSignals.map((signal, index) => (
              <motion.div
                key={signal.id || index}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className={`flex items-center justify-between p-2 rounded-lg border ${getSignalColor(signal.action)}`}
              >
                <div className="flex items-center space-x-2">
                  {getSignalIcon(signal.action)}
                  <div>
                    <div className="text-sm font-medium">
                      {signal.action.toUpperCase()} @ ${signal.price?.toFixed(2)}
                    </div>
                    <div className="text-xs opacity-75">
                      {signal.confidence && `${(signal.confidence * 100).toFixed(0)}% confidence`}
                    </div>
                  </div>
                </div>
                
                <div className="text-right text-xs opacity-75">
                  <div>{signal.agent_id || 'Unknown'}</div>
                  <div>{new Date(signal.timestamp).toLocaleTimeString()}</div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {tradingSignals.length === 0 && (
            <div className="text-center py-4 text-gray-500 text-sm">
              No trading signals yet. Start analysis to generate signals.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AITradingPanel;
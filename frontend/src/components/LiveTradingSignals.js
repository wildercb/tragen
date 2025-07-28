import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BoltIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  MinusIcon,
} from '@heroicons/react/24/outline';

const LiveTradingSignals = ({ symbol = 'NQ=F' }) => {
  const [liveSignals, setLiveSignals] = useState([]);
  const [marketStatus, setMarketStatus] = useState(null);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [isConnected, setIsConnected] = useState(false);

  // Check if market is open for NQ futures
  const checkMarketStatus = useCallback(() => {
    const now = new Date();
    const et = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
    const day = et.getDay(); // 0=Sunday, 6=Saturday
    const hour = et.getHours();
    const minute = et.getMinutes();
    
    // Crypto trades 24/7
    let isOpen = true;
    let sessionStatus = 'open';
    
    const nextChange = getNextMarketChange(et, day, hour);
    
    return {
      is_market_open: isOpen,
      session_status: sessionStatus,
      current_time: et.toISOString(),
      timezone: 'US/Eastern',
      next_change: nextChange,
      trading_hours: {
        regular_hours: '24/7 Trading',
        market_type: 'Cryptocurrency'
      }
    };
  }, []);

  const getNextMarketChange = (et, day, hour) => {
    if (day === 0 && hour < 18) { // Sunday before open
      const nextOpen = new Date(et);
      nextOpen.setHours(18, 0, 0, 0);
      return { type: 'open', time: nextOpen.toISOString() };
    } else if (day >= 1 && day <= 4 && hour >= 17 && hour < 18) { // Maintenance
      const nextOpen = new Date(et);
      nextOpen.setHours(18, 0, 0, 0);
      return { type: 'open', time: nextOpen.toISOString() };
    } else if (day === 5 && hour >= 17) { // Friday after close
      const nextOpen = new Date(et);
      nextOpen.setDate(nextOpen.getDate() + 2); // Sunday
      nextOpen.setHours(18, 0, 0, 0);
      return { type: 'open', time: nextOpen.toISOString() };
    } else if (day === 6) { // Saturday
      const nextOpen = new Date(et);
      nextOpen.setDate(nextOpen.getDate() + 1); // Sunday
      nextOpen.setHours(18, 0, 0, 0);
      return { type: 'open', time: nextOpen.toISOString() };
    }
    // Market is open, find next close
    const nextClose = new Date(et);
    if (day < 5) {
      nextClose.setDate(nextClose.getDate() + (day === 4 ? 1 : 0)); // Friday close
      nextClose.setHours(17, 0, 0, 0);
    }
    return { type: 'close', time: nextClose.toISOString() };
  };

  // Fetch live signals from agents
  const fetchLiveSignals = useCallback(async () => {
    try {
      const response = await fetch('/api/agents');
      const agentsData = await response.json();
      
      if (agentsData.agents && agentsData.agents.length > 0) {
        // Simulate getting analysis from agents
        for (const agent of agentsData.agents) {
          try {
            const analysisResponse = await fetch(`/api/agents/${agent.id}/tasks`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                type: 'market_analysis',
                parameters: { symbol: symbol, timeframe: '5m' }
              })
            });
            
            if (analysisResponse.ok) {
              const analysis = await analysisResponse.json();
              
              // Update agent status
              setAgentStatuses(prev => ({
                ...prev,
                [agent.id]: {
                  ...agent,
                  last_analysis: new Date(),
                  status: analysis.result?.signal_status?.should_trade ? 'active' : 'monitoring'
                }
              }));
              
              // Check if analysis contains actionable signals
              if (analysis.result?.signal_status?.should_trade && analysis.result?.analysis) {
                const confidence = extractConfidence(analysis.result.analysis);
                const recommendation = extractRecommendation(analysis.result.analysis);
                
                if (recommendation && confidence > 0.6) {
                  const signal = {
                    id: `${agent.id}_${Date.now()}`,
                    agent_id: agent.id,
                    agent_name: analysis.result.agent_config?.name || `${agent.type} Agent`,
                    type: recommendation.toLowerCase(),
                    confidence: confidence,
                    price: analysis.result.market_data?.current_price || 0,
                    reason: extractReason(analysis.result.analysis),
                    timestamp: new Date(),
                    timeframe: analysis.result.timeframe || '5m'
                  };
                  
                  setLiveSignals(prev => {
                    // Avoid duplicate signals from same agent within 5 minutes
                    const recentSignals = prev.filter(s => 
                      s.agent_id === agent.id && 
                      new Date() - new Date(s.timestamp) < 5 * 60 * 1000
                    );
                    
                    if (recentSignals.length === 0) {
                      return [signal, ...prev.slice(0, 19)]; // Keep last 20 signals
                    }
                    return prev;
                  });
                }
              }
            }
          } catch (error) {
            console.error(`Failed to get analysis from agent ${agent.id}:`, error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch live signals:', error);
    }
  }, []);

  // Extract confidence from analysis text
  const extractConfidence = (analysisText) => {
    const confidenceMatch = analysisText.match(/confidence[:\s]+(\d+(?:\.\d+)?)/i);
    if (confidenceMatch) {
      return parseFloat(confidenceMatch[1]);
    }
    // Default confidence based on keywords
    const highConfidenceWords = ['strong', 'clear', 'definitive', 'confirmed'];
    const lowConfidenceWords = ['weak', 'uncertain', 'mixed', 'unclear'];
    
    const hasHighConfidence = highConfidenceWords.some(word => 
      analysisText.toLowerCase().includes(word)
    );
    const hasLowConfidence = lowConfidenceWords.some(word => 
      analysisText.toLowerCase().includes(word)
    );
    
    if (hasHighConfidence && !hasLowConfidence) return 0.8;
    if (hasLowConfidence && !hasHighConfidence) return 0.4;
    return 0.6;
  };

  // Extract recommendation from analysis text
  const extractRecommendation = (analysisText) => {
    const buyWords = ['buy', 'long', 'bullish', 'upside'];
    const sellWords = ['sell', 'short', 'bearish', 'downside'];
    
    const lowerText = analysisText.toLowerCase();
    const hasBuy = buyWords.some(word => lowerText.includes(word));
    const hasSell = sellWords.some(word => lowerText.includes(word));
    
    if (hasBuy && !hasSell) return 'BUY';
    if (hasSell && !hasBuy) return 'SELL';
    return 'HOLD';
  };

  // Extract reason from analysis text
  const extractReason = (analysisText) => {
    // Extract first sentence or first 100 characters
    const firstSentence = analysisText.split('.')[0];
    return firstSentence.length > 100 ? 
      firstSentence.substring(0, 100) + '...' : 
      firstSentence;
  };

  // Update market status
  useEffect(() => {
    const updateMarketStatus = () => {
      setMarketStatus(checkMarketStatus());
    };
    
    updateMarketStatus();
    const statusInterval = setInterval(updateMarketStatus, 60000); // Update every minute
    
    return () => clearInterval(statusInterval);
  }, [checkMarketStatus]);

  // Fetch signals periodically
  useEffect(() => {
    if (marketStatus?.is_market_open) {
      fetchLiveSignals();
      const signalsInterval = setInterval(fetchLiveSignals, 30000); // Every 30 seconds during market hours
      
      return () => clearInterval(signalsInterval);
    } else {
      // Less frequent updates when market is closed
      const signalsInterval = setInterval(fetchLiveSignals, 5 * 60000); // Every 5 minutes
      return () => clearInterval(signalsInterval);
    }
  }, [marketStatus?.is_market_open, fetchLiveSignals]);

  const getSignalIcon = (type) => {
    switch (type) {
      case 'buy':
        return <TrendingUpIcon className="w-5 h-5" />;
      case 'sell':
        return <TrendingDownIcon className="w-5 h-5" />;
      default:
        return <MinusIcon className="w-5 h-5" />;
    }
  };

  const getSignalColor = (type) => {
    switch (type) {
      case 'buy':
        return 'text-trading-buy border-trading-buy bg-trading-buy bg-opacity-10';
      case 'sell':
        return 'text-trading-sell border-trading-sell bg-trading-sell bg-opacity-10';
      default:
        return 'text-dim-grey-400 border-dim-grey-600 bg-dim-grey-600 bg-opacity-10';
    }
  };

  const getMarketStatusColor = () => {
    if (!marketStatus) return 'text-dim-grey-400';
    
    switch (marketStatus.session_status) {
      case 'open':
        return 'text-trading-buy';
      case 'maintenance':
        return 'text-yellow-500';
      default:
        return 'text-trading-sell';
    }
  };

  const formatTimeUntilChange = () => {
    if (!marketStatus?.next_change) return '';
    
    const now = new Date();
    const changeTime = new Date(marketStatus.next_change.time);
    const diffMs = changeTime - now;
    
    if (diffMs <= 0) return 'Now';
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <div className="space-y-6">
      {/* Market Status */}
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${
              marketStatus?.is_market_open ? 'bg-trading-buy animate-pulse' : 'bg-trading-sell'
            }`} />
            <h2 className="text-xl font-semibold text-white">Market Status</h2>
          </div>
          
          <div className="text-right">
            <p className={`font-medium capitalize ${getMarketStatusColor()}`}>
              {marketStatus?.session_status || 'Loading...'}
            </p>
            {marketStatus?.next_change && (
              <p className="text-sm text-dim-grey-400">
                Next {marketStatus.next_change.type} in {formatTimeUntilChange()}
              </p>
            )}
          </div>
        </div>
        
        {marketStatus && (
          <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-dim-grey-400">Trading Hours</p>
              <p className="text-white">{marketStatus.trading_hours.sunday_open} - {marketStatus.trading_hours.friday_close}</p>
            </div>
            <div>
              <p className="text-dim-grey-400">Daily Maintenance</p>
              <p className="text-white">{marketStatus.trading_hours.daily_maintenance}</p>
            </div>
            <div>
              <p className="text-dim-grey-400">Current Time</p>
              <p className="text-white">
                {new Date(marketStatus.current_time).toLocaleTimeString('en-US', {
                  timeZone: 'America/New_York',
                  hour12: true
                })} ET
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Live Trading Signals */}
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700">
        <div className="p-4 border-b border-dim-grey-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
              <BoltIcon className="w-5 h-5 text-robin-egg-500" />
              <span>Live Trading Signals</span>
            </h3>
            <div className="flex items-center space-x-2 text-sm">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-trading-buy' : 'bg-trading-sell'}`} />
              <span className="text-dim-grey-400">
                {isConnected ? 'Connected' : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
          <AnimatePresence>
            {liveSignals.map((signal) => (
              <motion.div
                key={signal.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className={`rounded-lg p-4 border ${getSignalColor(signal.type)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getSignalIcon(signal.type)}
                    <span className="font-semibold uppercase">
                      {signal.type}
                    </span>
                    <span className="text-sm opacity-75">
                      ${signal.price?.toFixed(2) || 'N/A'}
                    </span>
                  </div>
                  <div className="text-sm opacity-75">
                    {Math.round(signal.confidence * 100)}% confidence
                  </div>
                </div>
                
                <p className="text-sm opacity-90 mb-2">
                  {signal.reason}
                </p>
                
                <div className="flex items-center justify-between text-xs opacity-60">
                  <span>{signal.agent_name} • {signal.timeframe}</span>
                  <span>{signal.timestamp.toLocaleTimeString()}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {liveSignals.length === 0 && (
            <div className="text-center py-8 text-dim-grey-400">
              <BoltIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No live signals yet</p>
              <p className="text-sm mt-1">
                {marketStatus?.is_market_open 
                  ? 'Agents are analyzing market conditions...'
                  : 'Market is closed - agents in monitoring mode'
                }
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Active Agents Status */}
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700">
        <div className="p-4 border-b border-dim-grey-700">
          <h3 className="text-lg font-semibold text-white">Agent Status</h3>
        </div>
        
        <div className="p-4">
          {Object.keys(agentStatuses).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.values(agentStatuses).map((agent) => (
                <div key={agent.id} className="bg-eerie-black-secondary rounded-lg p-3 border border-dim-grey-600">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white capitalize">
                      {agent.type} Agent
                    </span>
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'active' ? 'bg-trading-buy' : 'bg-yellow-500'
                    }`} />
                  </div>
                  <p className="text-xs text-dim-grey-400">
                    Last analysis: {agent.last_analysis ? 
                      new Date(agent.last_analysis).toLocaleTimeString() : 
                      'Never'
                    }
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-dim-grey-400">
              <p>No active agents</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LiveTradingSignals;
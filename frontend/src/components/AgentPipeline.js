import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayIcon,
  PauseIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  BoltIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';

const AgentPipeline = () => {
  const [agents, setAgents] = useState([]);
  const [agentThoughts, setAgentThoughts] = useState({});
  const [tradeSignals, setTradeSignals] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedModel, setSelectedModel] = useState('ollama:phi3:mini');
  const [availableModels, setAvailableModels] = useState([]);

  // Fetch agents and models on component mount
  useEffect(() => {
    fetchAgents();
    fetchAvailableModels();
  }, []);

  // Start live agent monitoring when running
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      // Simulate agent thoughts and analysis
      simulateAgentActivity();
    }, 3000);

    return () => clearInterval(interval);
  }, [isRunning, simulateAgentActivity]);

  const fetchAgents = async () => {
    try {
      const response = await fetch('/api/agents');
      const data = await response.json();
      setAgents(data.agents || []);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  };

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('/api/providers/models');
      const data = await response.json();
      setAvailableModels(data.models || []);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const createAgent = async (agentType) => {
    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: agentType,
          config: {
            symbol: 'NQ=F',
            model: selectedModel,
            temperature: agentType === 'risk' ? 0.0 : 0.1,
          },
        }),
      });
      
      if (response.ok) {
        fetchAgents();
      }
    } catch (error) {
      console.error('Failed to create agent:', error);
    }
  };

  const switchModel = async (provider, model) => {
    try {
      const response = await fetch('/api/providers/switch-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, model }),
      });
      
      if (response.ok) {
        setSelectedModel(`${provider}:${model}`);
      }
    } catch (error) {
      console.error('Failed to switch model:', error);
    }
  };

  const simulateAgentActivity = useCallback(() => {
    const thoughts = [
      'Analyzing price action and volume trends...',
      'RSI showing oversold conditions at 28.4',
      'Bollinger Bands suggesting potential breakout',
      'Volume spike detected - confirming momentum',
      'Risk assessment: Position size within limits',
      'Support level holding at 22,850',
      'MACD showing bullish divergence',
      'Monitoring for entry signal...',
      'Market sentiment analysis complete',
      'Pattern recognition: Double bottom forming',
    ];

    const signals = [
      { type: 'buy', confidence: 0.85, price: 22875, reason: 'Bullish breakout pattern' },
      { type: 'sell', confidence: 0.78, price: 22925, reason: 'Resistance level reached' },
      { type: 'hold', confidence: 0.65, price: 22900, reason: 'Consolidation phase' },
    ];

    // Update agent thoughts
    agents.forEach(agent => {
      const randomThought = thoughts[Math.floor(Math.random() * thoughts.length)];
      setAgentThoughts(prev => ({
        ...prev,
        [agent.id]: {
          ...prev[agent.id],
          currentThought: randomThought,
          timestamp: new Date(),
          status: Math.random() > 0.8 ? 'analyzing' : 'active',
        }
      }));
    });

    // Occasionally generate trade signals
    if (Math.random() > 0.7) {
      const signal = signals[Math.floor(Math.random() * signals.length)];
      setTradeSignals(prev => [
        {
          ...signal,
          id: Date.now(),
          timestamp: new Date(),
          agent: agents[Math.floor(Math.random() * agents.length)]?.id || 'unknown',
        },
        ...prev.slice(0, 9) // Keep last 10 signals
      ]);
    }
  }, [agents]);

  const getAgentIcon = (type) => {
    switch (type) {
      case 'analysis':
        return <ChartBarIcon className="w-6 h-6" />;
      case 'execution':
        return <BoltIcon className="w-6 h-6" />;
      case 'risk':
        return <ShieldCheckIcon className="w-6 h-6" />;
      default:
        return <CpuChipIcon className="w-6 h-6" />;
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

  return (
    <div className="space-y-6">
      {/* Control Panel */}
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
            <CpuChipIcon className="w-6 h-6 text-robin-egg-500" />
            <span>AI Agent Pipeline</span>
          </h2>
          
          <div className="flex items-center space-x-4">
            {/* Model Selector */}
            <select
              value={selectedModel}
              onChange={(e) => {
                const [provider, model] = e.target.value.split(':');
                switchModel(provider, model);
              }}
              className="bg-eerie-black-secondary border border-dim-grey-600 rounded-lg px-3 py-2 text-white text-sm focus:border-robin-egg-500 focus:outline-none"
            >
              {availableModels.map((model) => (
                <option key={`${model.provider}:${model.name}`} value={`${model.provider}:${model.name}`}>
                  {model.provider}: {model.name}
                </option>
              ))}
            </select>
            
            {/* Start/Stop Button */}
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isRunning
                  ? 'bg-trading-sell hover:bg-red-600 text-white'
                  : 'bg-trading-buy hover:bg-green-600 text-white'
              }`}
            >
              {isRunning ? (
                <>
                  <PauseIcon className="w-4 h-4" />
                  <span>Stop Pipeline</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>Start Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Agent Creation */}
        <div className="flex flex-wrap gap-2">
          {['analysis', 'execution', 'risk'].map((type) => (
            <button
              key={type}
              onClick={() => createAgent(type)}
              className="flex items-center space-x-2 px-3 py-2 bg-robin-egg-500 hover:bg-robin-egg-600 rounded-lg text-white text-sm transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
              <span>Create {type} Agent</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Agents */}
        <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700">
          <div className="p-4 border-b border-dim-grey-700">
            <h3 className="text-lg font-semibold text-white">Active Agents ({agents.length})</h3>
          </div>
          
          <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {agents.map((agent, index) => (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="text-robin-egg-500">
                        {getAgentIcon(agent.type)}
                      </div>
                      <div>
                        <h4 className="font-medium text-white capitalize">
                          {agent.type} Agent
                        </h4>
                        <p className="text-xs text-dim-grey-400">
                          ID: {agent.id}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        agentThoughts[agent.id]?.status === 'analyzing' 
                          ? 'bg-yellow-500 animate-pulse' 
                          : 'bg-trading-buy'
                      }`} />
                      <span className="text-xs text-dim-grey-400">
                        {agentThoughts[agent.id]?.status || 'idle'}
                      </span>
                    </div>
                  </div>
                  
                  {agentThoughts[agent.id]?.currentThought && (
                    <motion.div
                      key={agentThoughts[agent.id].timestamp}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="bg-eerie-black-primary rounded-lg p-3 border border-dim-grey-700"
                    >
                      <p className="text-sm text-dim-grey-300">
                        {agentThoughts[agent.id].currentThought}
                      </p>
                      <p className="text-xs text-dim-grey-500 mt-1">
                        {agentThoughts[agent.id].timestamp?.toLocaleTimeString()}
                      </p>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {agents.length === 0 && (
              <div className="text-center py-8 text-dim-grey-400">
                <CpuChipIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No active agents</p>
                <p className="text-sm mt-1">Create agents to start analysis</p>
              </div>
            )}
          </div>
        </div>

        {/* Trade Signals */}
        <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700">
          <div className="p-4 border-b border-dim-grey-700">
            <h3 className="text-lg font-semibold text-white">Live Trade Signals</h3>
          </div>
          
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            <AnimatePresence>
              {tradeSignals.map((signal) => (
                <motion.div
                  key={signal.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className={`rounded-lg p-4 border ${getSignalColor(signal.type)}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold uppercase">
                        {signal.type}
                      </span>
                      <span className="text-sm opacity-75">
                        ${signal.price}
                      </span>
                    </div>
                    <div className="text-sm opacity-75">
                      {(signal.confidence * 100).toFixed(0)}% confidence
                    </div>
                  </div>
                  
                  <p className="text-sm opacity-90 mb-2">
                    {signal.reason}
                  </p>
                  
                  <div className="flex items-center justify-between text-xs opacity-60">
                    <span>Agent: {signal.agent}</span>
                    <span>{signal.timestamp.toLocaleTimeString()}</span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {tradeSignals.length === 0 && (
              <div className="text-center py-8 text-dim-grey-400">
                <BoltIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No trade signals yet</p>
                <p className="text-sm mt-1">Start the pipeline to see signals</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentPipeline;
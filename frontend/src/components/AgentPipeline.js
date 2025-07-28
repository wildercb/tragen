import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlayIcon,
  PauseIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  BoltIcon,
  PlusIcon,
  ChatBubbleLeftRightIcon,
  PaperAirplaneIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

const AgentPipeline = ({ currentSymbol = 'NQ=F', chartData = [], onSignalCreated }) => {
  const [agents, setAgents] = useState([]);
  const [agentThoughts, setAgentThoughts] = useState({});
  const [tradeSignals, setTradeSignals] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [selectedModel, setSelectedModel] = useState('ollama:phi3:mini');
  const [availableModels, setAvailableModels] = useState([]);
  const [chatHistory, setChatHistory] = useState({});
  const [activeChat, setActiveChat] = useState(null);
  const [chatMessage, setChatMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  // Fetch agents and models on component mount
  useEffect(() => {
    fetchAgents();
    fetchAvailableModels();
  }, []);

  // Check if market is open for NQ futures
  const isMarketOpen = () => {
    const now = new Date();
    const et = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
    const day = et.getDay(); // 0=Sunday, 6=Saturday
    const hour = et.getHours();
    
    // NQ trades nearly 24/5: Sunday 6 PM - Friday 5 PM ET
    // Daily maintenance: 5-6 PM ET
    
    if (day === 0) { // Sunday
      return hour >= 18; // 6 PM or later
    } else if (day >= 1 && day <= 4) { // Monday-Thursday
      return hour < 17 || hour >= 18; // Before 5 PM or after 6 PM
    } else if (day === 5) { // Friday
      return hour < 17; // Before 5 PM
    }
    return false; // Saturday
  };

  // Real agent analysis using current chart data
  const triggerAgentAnalysis = useCallback(async (agentId, symbol, chartData) => {
    if (!chartData || chartData.length === 0) return;
    
    try {
      // Get the last 20 candles for analysis
      const recentData = chartData.slice(-20);
      const currentPrice = recentData[recentData.length - 1]?.close;
      
      const response = await fetch('/api/agents/analyze-chart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          symbol: symbol,
          chart_data: recentData,
          current_price: currentPrice,
          model_provider: selectedModel.split(':')[0] || 'ollama',
          model_name: selectedModel.split(':')[1] || 'phi3:mini'
        })
      });
      
      if (response.ok) {
        const analysis = await response.json();
        
        // Update agent thoughts with real analysis
        setAgentThoughts(prev => ({
          ...prev,
          [agentId]: {
            ...prev[agentId],
            currentThought: analysis.reasoning || 'Analysis complete',
            timestamp: new Date(),
            status: 'active',
            lastAnalysis: analysis
          }
        }));
        
        // If analysis includes a trading signal, add it
        if (analysis.recommendation && analysis.recommendation !== 'HOLD') {
          const signal = {
            id: Date.now(),
            type: analysis.recommendation.toLowerCase(),
            confidence: analysis.confidence / 100,
            price: currentPrice,
            reason: analysis.reasoning,
            timestamp: new Date(),
            agent: agentId,
            symbol: symbol
          };
          
          setTradeSignals(prev => [signal, ...prev.slice(0, 9)]);
          
          // Notify parent component to add signal to chart
          if (onSignalCreated) {
            onSignalCreated(signal);
          }
        }
      }
    } catch (error) {
      console.error('Failed to trigger agent analysis:', error);
      setAgentThoughts(prev => ({
        ...prev,
        [agentId]: {
          ...prev[agentId],
          currentThought: 'Analysis failed - connection error',
          timestamp: new Date(),
          status: 'error'
        }
      }));
    }
  }, [selectedModel, onSignalCreated]);

  // Start real agent monitoring when running
  useEffect(() => {
    if (!isRunning || agents.length === 0 || chartData.length === 0) return;

    const interval = setInterval(() => {
      // Trigger real analysis for each agent
      agents.forEach(agent => {
        triggerAgentAnalysis(agent.id, currentSymbol, chartData);
      });
    }, 30000); // Analyze every 30 seconds to avoid rate limiting

    return () => clearInterval(interval);
  }, [isRunning, agents, chartData, currentSymbol, triggerAgentAnalysis]);

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
            symbol: currentSymbol,
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
  
  // Chat functionality
  const sendMessage = async (agentId, message) => {
    if (!message.trim()) return;
    
    setIsTyping(true);
    
    // Add user message to chat history
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      message: message.trim(),
      timestamp: new Date()
    };
    
    setChatHistory(prev => ({
      ...prev,
      [agentId]: [...(prev[agentId] || []), userMessage]
    }));
    
    setChatMessage('');
    
    try {
      // Send message to agent for response
      const response = await fetch('/api/agents/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          message: message,
          symbol: currentSymbol,
          chart_data: chartData.slice(-20), // Last 20 candles for context
          chat_history: chatHistory[agentId] || []
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        
        // Add agent response to chat history
        const agentMessage = {
          id: Date.now() + 1,
          sender: 'agent',
          message: result.response,
          timestamp: new Date(),
          analysis: result.analysis,
          signal: result.signal
        };
        
        setChatHistory(prev => ({
          ...prev,
          [agentId]: [...(prev[agentId] || []), agentMessage]
        }));
        
        // If agent created a signal, add it to the chart
        if (result.signal && onSignalCreated) {
          onSignalCreated({
            ...result.signal,
            agent: agentId,
            symbol: currentSymbol,
            timestamp: new Date()
          });
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'agent',
        message: 'Sorry, I\'m having trouble connecting right now. Please try again.',
        timestamp: new Date(),
        error: true
      };
      
      setChatHistory(prev => ({
        ...prev,
        [agentId]: [...(prev[agentId] || []), errorMessage]
      }));
    } finally {
      setIsTyping(false);
    }
  };
  
  // Scroll to bottom of chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, activeChat]);
  
  // Quick action to request analysis
  const requestAnalysis = async (agentId) => {
    await sendMessage(agentId, `Please analyze the current ${currentSymbol} chart and provide your trading recommendation with reasoning.`);
  };
  
  // Quick action to place signal
  const requestSignal = async (agentId, signalType) => {
    const currentPrice = chartData.length > 0 ? chartData[chartData.length - 1].close : 0;
    await sendMessage(agentId, `Based on the current ${currentSymbol} chart analysis, please place a ${signalType.toUpperCase()} signal at the current price of $${currentPrice}. Explain your reasoning.`);
  };

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
        return 'text-green-400 border-green-500 bg-green-500 bg-opacity-10';
      case 'sell':
        return 'text-red-400 border-red-500 bg-red-500 bg-opacity-10';
      default:
        return 'text-gray-400 border-gray-600 bg-gray-600 bg-opacity-10';
    }
  };
  
  const getAgentStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'analyzing':
        return 'bg-yellow-500 animate-pulse';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
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
            {/* Current Symbol Display */}
            <div className="text-sm text-gray-300">
              <span className="text-gray-500">Trading:</span>
              <span className="font-semibold text-blue-400 ml-1">{currentSymbol}</span>
            </div>
            
            {/* Model Selector */}
            <select
              value={selectedModel}
              onChange={(e) => {
                const [provider, model] = e.target.value.split(':');
                switchModel(provider, model);
              }}
              className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
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
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isRunning ? (
                <>
                  <PauseIcon className="w-4 h-4" />
                  <span>Stop Analysis</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-4 h-4" />
                  <span>Start Analysis</span>
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
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
              <span>Create {type} Agent</span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Agents */}
        <div className="lg:col-span-2 bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">AI Trading Agents ({agents.length})</h3>
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
                  className="bg-gray-700 rounded-lg p-4 border border-gray-600"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="text-blue-400">
                        {getAgentIcon(agent.type)}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-white capitalize">
                          {agent.type} Agent
                        </h4>
                        <p className="text-xs text-gray-400">
                          {currentSymbol} • {selectedModel.split(':')[1] || 'AI Model'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        getAgentStatusColor(agentThoughts[agent.id]?.status || 'idle')
                      }`} />
                      <span className="text-xs text-gray-400">
                        {agentThoughts[agent.id]?.status || 'idle'}
                      </span>
                      <button
                        onClick={() => setActiveChat(agent.id)}
                        className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                        title="Chat with agent"
                      >
                        <ChatBubbleLeftRightIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Agent Actions */}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      onClick={() => requestAnalysis(agent.id)}
                      className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                    >
                      Analyze Chart
                    </button>
                    <button
                      onClick={() => requestSignal(agent.id, 'buy')}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                    >
                      Buy Signal
                    </button>
                    <button
                      onClick={() => requestSignal(agent.id, 'sell')}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
                    >
                      Sell Signal
                    </button>
                  </div>
                  
                  {/* Last Analysis */}
                  {agentThoughts[agent.id]?.currentThought && (
                    <motion.div
                      key={agentThoughts[agent.id].timestamp}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="bg-gray-800 rounded-lg p-3 border border-gray-600 mt-3"
                    >
                      <p className="text-sm text-gray-300">
                        {agentThoughts[agent.id].currentThought}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {agentThoughts[agent.id].timestamp?.toLocaleTimeString()}
                      </p>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>
            
            {agents.length === 0 && (
              <div className="text-center py-8 text-gray-400">
                <CpuChipIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No active agents</p>
                <p className="text-sm mt-1">Create agents to start real-time analysis</p>
              </div>
            )}
          </div>
        </div>

        {/* Agent Chat Interface */}
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">Agent Chat</h3>
              {activeChat && (
                <button
                  onClick={() => setActiveChat(null)}
                  className="text-gray-400 hover:text-white p-1"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
          
          {activeChat ? (
            <div className="flex flex-col h-96">
              {/* Chat Messages */}
              <div className="flex-1 p-4 overflow-y-auto space-y-3">
                {(chatHistory[activeChat] || []).map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.sender === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.error
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-700 text-gray-100'
                      }`}
                    >
                      <p className="text-sm">{message.message}</p>
                      <p className="text-xs opacity-75 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                      {message.signal && (
                        <div className="mt-2 p-2 bg-gray-800 rounded text-xs">
                          <strong>Signal:</strong> {message.signal.type.toUpperCase()} at ${message.signal.price}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-gray-700 text-gray-100 px-4 py-2 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              
              {/* Chat Input */}
              <div className="p-4 border-t border-gray-700">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage(activeChat, chatMessage);
                      }
                    }}
                    placeholder="Ask about the chart, request analysis, or place signals..."
                    className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
                    disabled={isTyping}
                  />
                  <button
                    onClick={() => sendMessage(activeChat, chatMessage)}
                    disabled={!chatMessage.trim() || isTyping}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    <PaperAirplaneIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-gray-400">
              <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Select an agent to start chatting</p>
              <p className="text-sm mt-1">Ask about market analysis, request signals, or get trading insights</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentPipeline;
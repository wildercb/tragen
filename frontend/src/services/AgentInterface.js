/**
 * AgentInterface - Professional Agent Communication Service
 * ========================================================
 * 
 * High-performance service for real-time communication between frontend
 * and AI trading agents with advanced features:
 * - WebSocket-based real-time communication
 * - Agent registration and management
 * - Signal processing and validation
 * - Performance monitoring
 * - Automatic reconnection
 */

import EventEmitter from 'eventemitter3';

class AgentInterface extends EventEmitter {
  constructor(wsBaseUrl = 'ws://localhost:8000') {
    super();
    
    this.wsBaseUrl = wsBaseUrl;
    this.ws = null;
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectDelay = 1000;
    this.heartbeatInterval = null;
    this.reconnectTimeout = null;
    
    // Agent management
    this.registeredAgents = new Map();
    this.agentPerformance = new Map();
    this.pendingRequests = new Map();
    
    // Message queue for offline scenarios
    this.messageQueue = [];
    this.maxQueueSize = 1000;
    
    // Performance metrics
    this.metrics = {
      messagesReceived: 0,
      messagesSent: 0,
      avgLatency: 0,
      connectionUptime: 0,
      lastActivity: Date.now()
    };
    
    // Connection options
    this.options = {
      heartbeatInterval: 30000, // 30 seconds
      maxMessageSize: 1024 * 1024, // 1MB
      enableCompression: true,
      enableBinaryMessages: false
    };
    
    console.log('🤖 AgentInterface initialized');
  }
  
  /**
   * Connect to the agent WebSocket server
   */
  async connect() {
    if (this.isConnected || this.isConnecting) {
      console.log('🤖 Already connected or connecting to agent server');
      return;
    }
    
    this.isConnecting = true;
    
    try {
      const wsUrl = `${this.wsBaseUrl}/api/ws/agents`;
      console.log(`🤖 Connecting to agent server: ${wsUrl}`);
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('🤖 ✅ Connected to agent server');
        this.isConnected = true;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Process queued messages
        this.processMessageQueue();
        
        // Send connection info
        this.send({
          type: 'client_connected',
          clientInfo: {
            type: 'trading_chart',
            version: '4.0',
            capabilities: [
              'real_time_data',
              'signal_display',
              'chart_interaction',
              'technical_analysis'
            ],
            timestamp: Date.now()
          }
        });
        
        this.emit('connected');
      };
      
      this.ws.onmessage = (event) => {
        this.handleMessage(event.data);
      };
      
      this.ws.onerror = (error) => {
        console.error('🤖 ❌ Agent WebSocket error:', error);
        this.emit('error', error);
      };
      
      this.ws.onclose = (event) => {
        console.log(`🤖 🔌 Agent WebSocket closed: ${event.code} ${event.reason}`);
        this.isConnected = false;
        this.isConnecting = false;
        
        this.stopHeartbeat();
        
        // Clear registered agents
        this.registeredAgents.clear();
        this.emit('disconnected');
        
        // Attempt reconnection
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        } else {
          console.error('🤖 ❌ Max reconnection attempts reached');
          this.emit('maxReconnectAttemptsReached');
        }
      };
      
    } catch (error) {
      console.error('🤖 ❌ Failed to connect to agent server:', error);
      this.isConnecting = false;
      this.emit('connectionFailed', error);
      this.scheduleReconnect();
    }
  }
  
  /**
   * Disconnect from the agent server
   */
  disconnect() {
    console.log('🤖 Disconnecting from agent server');
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.registeredAgents.clear();
    
    this.emit('disconnected');
  }
  
  /**
   * Send message to agent server
   */
  send(message) {
    if (!this.isConnected || !this.ws) {
      // Queue message for later
      if (this.messageQueue.length < this.maxQueueSize) {
        this.messageQueue.push({
          message,
          timestamp: Date.now()
        });
        console.log('🤖 📦 Message queued (not connected)');
      } else {
        console.warn('🤖 ⚠️ Message queue full, dropping message');
      }
      return false;
    }
    
    try {
      const messageStr = JSON.stringify(message);
      
      // Check message size
      if (messageStr.length > this.options.maxMessageSize) {
        console.error('🤖 ❌ Message too large:', messageStr.length);
        return false;
      }
      
      this.ws.send(messageStr);
      this.metrics.messagesSent++;
      this.metrics.lastActivity = Date.now();
      
      return true;
    } catch (error) {
      console.error('🤖 ❌ Failed to send message:', error);
      return false;
    }
  }
  
  /**
   * Register a new AI agent
   */
  async registerAgent(agentConfig) {
    const requestId = this.generateRequestId();
    
    const success = this.send({
      type: 'register_agent',
      requestId,
      config: {
        name: agentConfig.name,
        type: agentConfig.type || 'trading',
        strategy: agentConfig.strategy || '',
        symbols: agentConfig.symbols || ['NQ=F'],
        timeframes: agentConfig.timeframes || ['5m'],
        indicators: agentConfig.indicators || [],
        permissions: agentConfig.permissions || ['read_data', 'send_signals'],
        riskTolerance: agentConfig.riskTolerance || 0.02,
        maxSignalsPerHour: agentConfig.maxSignalsPerHour || 10,
        ...agentConfig
      }
    });
    
    if (!success) {
      throw new Error('Failed to send agent registration');
    }
    
    // Return promise that resolves when registration completes
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error('Agent registration timeout'));
      }, 30000);
      
      this.pendingRequests.set(requestId, {
        type: 'register_agent',
        resolve: (result) => {
          clearTimeout(timeout);
          resolve(result);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        }
      });
    });
  }
  
  /**
   * Unregister an AI agent
   */
  async unregisterAgent(agentId) {
    const success = this.send({
      type: 'unregister_agent',
      agentId
    });
    
    if (success) {
      this.registeredAgents.delete(agentId);
      this.agentPerformance.delete(agentId);
      this.emit('agentUnregistered', agentId);
    }
    
    return success;
  }
  
  /**
   * Send trading signal from agent
   */
  sendTradingSignal(agentId, signal) {
    return this.send({
      type: 'trading_signal',
      agentId,
      signal: {
        symbol: signal.symbol,
        type: signal.type, // 'buy', 'sell', 'hold'
        price: signal.price,
        confidence: signal.confidence,
        timeframe: signal.timeframe,
        rationale: signal.rationale,
        stopLoss: signal.stopLoss,
        takeProfit: signal.takeProfit,
        positionSize: signal.positionSize,
        timestamp: Date.now(),
        ...signal
      }
    });
  }
  
  /**
   * Request chart data analysis from agent
   */
  async requestAnalysis(agentId, analysisType, chartData) {
    const requestId = this.generateRequestId();
    
    const success = this.send({
      type: 'analysis_request',
      requestId,
      agentId,
      analysisType,
      chartData: {
        symbol: chartData.symbol,
        timeframe: chartData.timeframe,
        data: chartData.data.slice(-1000), // Send last 1000 points
        indicators: chartData.indicators
      }
    });
    
    if (!success) {
      throw new Error('Failed to send analysis request');
    }
    
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error('Analysis request timeout'));
      }, 60000); // 1 minute timeout
      
      this.pendingRequests.set(requestId, {
        type: 'analysis_request',
        resolve: (result) => {
          clearTimeout(timeout);
          resolve(result);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        }
      });
    });
  }
  
  /**
   * Send command to agent
   */
  sendAgentCommand(agentId, command, params = {}) {
    return this.send({
      type: 'agent_command',
      agentId,
      command,
      params,
      timestamp: Date.now()
    });
  }
  
  /**
   * Subscribe to chart data updates for agent
   */
  subscribeToChartData(agentId, symbols, timeframes) {
    return this.send({
      type: 'subscribe_chart_data',
      agentId,
      symbols: Array.isArray(symbols) ? symbols : [symbols],
      timeframes: Array.isArray(timeframes) ? timeframes : [timeframes]
    });
  }
  
  /**
   * Get agent performance metrics
   */
  getAgentPerformance(agentId) {
    return this.agentPerformance.get(agentId) || {
      totalSignals: 0,
      successfulSignals: 0,
      winRate: 0,
      avgReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      lastActivity: null
    };
  }
  
  /**
   * Get all registered agents
   */
  getRegisteredAgents() {
    return Array.from(this.registeredAgents.values());
  }
  
  /**
   * Get connection metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      isConnected: this.isConnected,
      registeredAgents: this.registeredAgents.size,
      queuedMessages: this.messageQueue.length,
      uptime: this.isConnected ? Date.now() - this.metrics.connectionStart : 0
    };
  }
  
  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data);
      this.metrics.messagesReceived++;
      this.metrics.lastActivity = Date.now();
      
      // Calculate message latency if timestamp provided
      if (message.timestamp) {
        const latency = Date.now() - message.timestamp;
        this.metrics.avgLatency = this.metrics.avgLatency * 0.9 + latency * 0.1;
      }
      
      console.log('🤖 📨 Message received:', message.type);
      
      switch (message.type) {
        case 'agent_registered':
          this.handleAgentRegistered(message);
          break;
          
        case 'agent_unregistered':
          this.handleAgentUnregistered(message);
          break;
          
        case 'trading_signal':
          this.handleTradingSignal(message);
          break;
          
        case 'analysis_result':
          this.handleAnalysisResult(message);
          break;
          
        case 'agent_status_update':
          this.handleAgentStatusUpdate(message);
          break;
          
        case 'chart_data_update':
          this.handleChartDataUpdate(message);
          break;
          
        case 'performance_update':
          this.handlePerformanceUpdate(message);
          break;
          
        case 'heartbeat_response':
          this.handleHeartbeatResponse(message);
          break;
          
        case 'error':
          this.handleError(message);
          break;
          
        case 'request_response':
          this.handleRequestResponse(message);
          break;
          
        default:
          console.warn('🤖 ⚠️ Unknown message type:', message.type);
          this.emit('unknownMessage', message);
      }
      
    } catch (error) {
      console.error('🤖 ❌ Failed to parse message:', error);
      this.emit('messageError', error);
    }
  }
  
  /**
   * Handle agent registration response
   */
  handleAgentRegistered(message) {
    const agent = {
      id: message.agentId,
      name: message.agentInfo.name,
      type: message.agentInfo.type,
      strategy: message.agentInfo.strategy,
      status: 'active',
      registeredAt: Date.now(),
      ...message.agentInfo
    };
    
    this.registeredAgents.set(agent.id, agent);
    
    // Initialize performance tracking
    this.agentPerformance.set(agent.id, {
      totalSignals: 0,
      successfulSignals: 0,
      winRate: 0,
      avgReturn: 0,
      sharpeRatio: 0,
      maxDrawdown: 0,
      lastActivity: Date.now()
    });
    
    console.log(`🤖 ✅ Agent registered: ${agent.name} (${agent.id})`);
    this.emit('agentRegistered', agent);
    
    // Handle pending request
    if (message.requestId && this.pendingRequests.has(message.requestId)) {
      const request = this.pendingRequests.get(message.requestId);
      request.resolve(agent);
      this.pendingRequests.delete(message.requestId);
    }
  }
  
  /**
   * Handle agent unregistration
   */
  handleAgentUnregistered(message) {
    const agentId = message.agentId;
    
    if (this.registeredAgents.has(agentId)) {
      this.registeredAgents.delete(agentId);
      this.agentPerformance.delete(agentId);
      
      console.log(`🤖 👋 Agent unregistered: ${agentId}`);
      this.emit('agentUnregistered', agentId);
    }
  }
  
  /**
   * Handle trading signal from agent
   */
  handleTradingSignal(message) {
    const signal = {
      id: message.signalId || this.generateRequestId(),
      agentId: message.agentId,
      agentName: this.getAgentName(message.agentId),
      timestamp: message.timestamp || Date.now(),
      ...message.signal
    };
    
    // Update agent performance
    const performance = this.agentPerformance.get(message.agentId);
    if (performance) {
      performance.totalSignals++;
      performance.lastActivity = Date.now();
    }
    
    console.log(`🤖 📈 Trading signal: ${signal.type} ${signal.symbol} by ${signal.agentName}`);
    this.emit('signalReceived', signal);
  }
  
  /**
   * Handle analysis result from agent
   */
  handleAnalysisResult(message) {
    const result = {
      requestId: message.requestId,
      agentId: message.agentId,
      analysisType: message.analysisType,
      result: message.result,
      confidence: message.confidence,
      timestamp: message.timestamp || Date.now()
    };
    
    console.log(`🤖 📊 Analysis result: ${result.analysisType} from ${this.getAgentName(result.agentId)}`);
    this.emit('analysisResult', result);
    
    // Handle pending request
    if (message.requestId && this.pendingRequests.has(message.requestId)) {
      const request = this.pendingRequests.get(message.requestId);
      request.resolve(result);
      this.pendingRequests.delete(message.requestId);
    }
  }
  
  /**
   * Handle agent status update
   */
  handleAgentStatusUpdate(message) {
    const agentId = message.agentId;
    const agent = this.registeredAgents.get(agentId);
    
    if (agent) {
      Object.assign(agent, message.status);
      
      console.log(`🤖 📊 Agent status update: ${agent.name} - ${message.status.status}`);
      this.emit('agentStatusUpdate', agent);
    }
  }
  
  /**
   * Handle chart data update
   */
  handleChartDataUpdate(message) {
    console.log(`🤖 📊 Chart data update: ${message.symbol} ${message.timeframe}`);
    this.emit('chartDataUpdate', message.data);
  }
  
  /**
   * Handle performance update
   */
  handlePerformanceUpdate(message) {
    const agentId = message.agentId;
    const performance = message.performance;
    
    if (this.agentPerformance.has(agentId)) {
      Object.assign(this.agentPerformance.get(agentId), performance);
      
      console.log(`🤖 📈 Performance update: ${this.getAgentName(agentId)}`);
      this.emit('performanceUpdate', agentId, performance);
    }
  }
  
  /**
   * Handle heartbeat response
   */
  handleHeartbeatResponse(message) {
    // Connection is healthy
    console.log('🤖 💓 Heartbeat response received');
  }
  
  /**
   * Handle error message
   */
  handleError(message) {
    console.error('🤖 ❌ Server error:', message.error);
    this.emit('serverError', message.error);
    
    // Handle pending request error
    if (message.requestId && this.pendingRequests.has(message.requestId)) {
      const request = this.pendingRequests.get(message.requestId);
      request.reject(new Error(message.error));
      this.pendingRequests.delete(message.requestId);
    }
  }
  
  /**
   * Handle request response
   */
  handleRequestResponse(message) {
    if (message.requestId && this.pendingRequests.has(message.requestId)) {
      const request = this.pendingRequests.get(message.requestId);
      
      if (message.success) {
        request.resolve(message.result);
      } else {
        request.reject(new Error(message.error));
      }
      
      this.pendingRequests.delete(message.requestId);
    }
  }
  
  /**
   * Start heartbeat to keep connection alive
   */
  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'heartbeat',
          timestamp: Date.now()
        });
      }
    }, this.options.heartbeatInterval);
  }
  
  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
  
  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );
    
    console.log(`🤖 ⏰ Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
  
  /**
   * Process queued messages after reconnection
   */
  processMessageQueue() {
    if (this.messageQueue.length === 0) return;
    
    console.log(`🤖 📦 Processing ${this.messageQueue.length} queued messages`);
    
    const messages = [...this.messageQueue];
    this.messageQueue = [];
    
    for (const { message } of messages) {
      this.send(message);
    }
  }
  
  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  /**
   * Get agent name by ID
   */
  getAgentName(agentId) {
    const agent = this.registeredAgents.get(agentId);
    return agent ? agent.name : agentId;
  }
  
  /**
   * Cleanup resources
   */
  destroy() {
    console.log('🤖 🧹 Destroying AgentInterface');
    
    this.disconnect();
    this.removeAllListeners();
    this.registeredAgents.clear();
    this.agentPerformance.clear();
    this.pendingRequests.clear();
    this.messageQueue = [];
  }
}

export default AgentInterface;
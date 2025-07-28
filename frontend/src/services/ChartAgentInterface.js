/**
 * ChartAgentInterface - AI Agent Integration API for Trading Charts
 * 
 * This service provides a comprehensive API for AI agents to interact with
 * trading charts. Designed to enable agents to read chart data, analyze
 * patterns, and make trading decisions efficiently.
 * 
 * Features:
 * - Chart data access and analysis
 * - Technical indicator calculations
 * - Pattern recognition utilities
 * - Signal generation and validation
 * - Real-time data streaming for agents
 * - Performance optimization for AI models
 * - Structured data formats for ML processing
 */

import TechnicalIndicators from '../utils/TechnicalIndicators';

class ChartAgentInterface {
  constructor(marketDataProvider, config = {}) {
    this.dataProvider = marketDataProvider;
    this.indicators = new TechnicalIndicators();
    
    this.config = {
      maxDataPoints: config.maxDataPoints || 10000,
      refreshInterval: config.refreshInterval || 1000,
      enableCaching: config.enableCaching !== false,
      agentTimeout: config.agentTimeout || 30000,
      ...config
    };
    
    // Agent subscriptions and callbacks
    this.agentSubscriptions = new Map();
    this.patternDetectors = new Map();
    this.signalGenerators = new Map();
    
    // Data caches for efficient agent access
    this.dataCache = new Map();
    this.indicatorCache = new Map();
    this.patternCache = new Map();
    
    // Performance monitoring
    this.metrics = {
      requestCount: 0,
      averageResponseTime: 0,
      cacheHitRate: 0,
      errorCount: 0
    };
    
    console.log('🤖 ChartAgentInterface initialized');
  }

  /**
   * Register an AI agent for chart data access
   * @param {string} agentId - Unique agent identifier
   * @param {Object} config - Agent configuration
   * @returns {string} Registration ID
   */
  registerAgent(agentId, config = {}) {
    const registration = {
      id: agentId,
      name: config.name || agentId,
      type: config.type || 'trading',
      permissions: config.permissions || ['read', 'analyze'],
      subscriptions: new Set(),
      lastActivity: Date.now(),
      metrics: {
        requestCount: 0,
        dataRequests: 0,
        signalsGenerated: 0,
        errors: 0
      },
      config: {
        maxDataPoints: config.maxDataPoints || this.config.maxDataPoints,
        updateFrequency: config.updateFrequency || 'realtime',
        dataFormat: config.dataFormat || 'ohlcv',
        indicators: config.indicators || [],
        patterns: config.patterns || [],
        ...config
      }
    };
    
    this.agentSubscriptions.set(agentId, registration);
    
    console.log(`🤖 Registered agent: ${agentId} (${registration.name})`);
    return agentId;
  }

  /**
   * Unregister an AI agent
   * @param {string} agentId - Agent identifier
   */
  unregisterAgent(agentId) {
    const registration = this.agentSubscriptions.get(agentId);
    if (registration) {
      // Clean up subscriptions
      registration.subscriptions.forEach(symbol => {
        this._unsubscribeAgentFromSymbol(agentId, symbol);
      });
      
      this.agentSubscriptions.delete(agentId);
      console.log(`🤖 Unregistered agent: ${agentId}`);
    }
  }

  /**
   * Subscribe agent to real-time data for a symbol
   * @param {string} agentId - Agent identifier
   * @param {string} symbol - Symbol to subscribe to
   * @param {function} callback - Callback for data updates
   * @returns {boolean} Success status
   */
  subscribeToSymbol(agentId, symbol, callback) {
    const registration = this.agentSubscriptions.get(agentId);
    if (!registration) {
      throw new Error(`Agent ${agentId} not registered`);
    }
    
    if (!this._hasPermission(agentId, 'read')) {
      throw new Error(`Agent ${agentId} does not have read permission`);
    }
    
    // Subscribe to market data if not already subscribed
    if (!registration.subscriptions.has(symbol)) {
      const subscription = this.dataProvider.subscribe(
        symbol,
        {
          timeframe: registration.config.updateFrequency === 'realtime' ? '1m' : '5m',
          includeHistorical: true
        },
        (update) => this._handleAgentDataUpdate(agentId, symbol, update, callback)
      );
      
      registration.subscriptions.add(symbol);
      registration.subscriptionIds = registration.subscriptionIds || new Map();
      registration.subscriptionIds.set(symbol, subscription);
    }
    
    console.log(`🤖 Agent ${agentId} subscribed to ${symbol}`);
    return true;
  }

  /**
   * Get historical chart data for analysis
   * @param {string} agentId - Agent identifier
   * @param {string} symbol - Symbol to get data for
   * @param {Object} options - Data options
   * @returns {Promise<Object>} Chart data in agent-friendly format
   */
  async getChartData(agentId, symbol, options = {}) {
    this._validateAgent(agentId);
    this._updateAgentActivity(agentId);
    
    const startTime = Date.now();
    
    try {
      const {
        period = '1d',
        interval = '5m',
        maxPoints = this.agentSubscriptions.get(agentId).config.maxDataPoints,
        includeIndicators = true,
        includePatterns = false,
        format = 'structured'
      } = options;
      
      // Check cache first
      const cacheKey = `${agentId}_${symbol}_${period}_${interval}_${maxPoints}`;
      if (this.config.enableCaching) {
        const cached = this._getCachedData(cacheKey);
        if (cached) {
          this._updateMetrics('cache_hit', Date.now() - startTime);
          return cached;
        }
      }
      
      // Fetch historical data
      const rawData = await this.dataProvider.getHistoricalData(symbol, {
        period,
        interval,
        maxPoints
      });
      
      // Format data for agent consumption
      const formattedData = this._formatDataForAgent(rawData, format);
      
      // Add technical indicators if requested
      let indicators = {};
      if (includeIndicators) {
        indicators = await this._calculateIndicatorsForAgent(agentId, rawData);
      }
      
      // Add pattern analysis if requested
      let patterns = {};
      if (includePatterns) {
        patterns = await this._detectPatternsForAgent(agentId, rawData);
      }
      
      const result = {
        symbol,
        timeframe: interval,
        period,
        dataPoints: formattedData.length,
        timestamp: Date.now(),
        data: formattedData,
        indicators,
        patterns,
        metadata: {
          source: 'historical',
          agentId,
          format,
          processingTime: Date.now() - startTime
        }
      };
      
      // Cache the result
      if (this.config.enableCaching) {
        this._setCachedData(cacheKey, result);
      }
      
      this._updateMetrics('request', Date.now() - startTime);
      this._updateAgentMetrics(agentId, 'dataRequests');
      
      return result;
      
    } catch (error) {
      this._updateMetrics('error', Date.now() - startTime);
      this._updateAgentMetrics(agentId, 'errors');
      throw error;
    }
  }

  /**
   * Get real-time market analysis
   * @param {string} agentId - Agent identifier
   * @param {string} symbol - Symbol to analyze
   * @returns {Promise<Object>} Real-time analysis
   */
  async getRealTimeAnalysis(agentId, symbol) {
    this._validateAgent(agentId);
    this._updateAgentActivity(agentId);
    
    try {
      // Get current price
      const currentPrice = await this.dataProvider.getCurrentPrice(symbol);
      
      // Get recent data for analysis
      const recentData = await this.getChartData(agentId, symbol, {
        period: '1d',
        interval: '1m',
        maxPoints: 100,
        includeIndicators: true,
        includePatterns: true
      });
      
      // Calculate momentum and volatility
      const analysis = this._calculateRealTimeMetrics(recentData.data, currentPrice);
      
      return {
        symbol,
        currentPrice: currentPrice.price,
        timestamp: Date.now(),
        analysis,
        signals: this._generateSignals(agentId, recentData),
        riskMetrics: this._calculateRiskMetrics(recentData.data),
        marketCondition: this._assessMarketCondition(recentData),
        metadata: {
          agentId,
          analysisType: 'realtime',
          dataPoints: recentData.dataPoints
        }
      };
      
    } catch (error) {
      console.error(`❌ Error in real-time analysis for agent ${agentId}:`, error);
      throw error;
    }
  }

  /**
   * Generate trading signals based on chart data
   * @param {string} agentId - Agent identifier
   * @param {string} symbol - Symbol to analyze
   * @param {Object} strategy - Signal generation strategy
   * @returns {Promise<Array>} Generated signals
   */
  async generateSignals(agentId, symbol, strategy = {}) {
    this._validateAgent(agentId);
    
    if (!this._hasPermission(agentId, 'analyze')) {
      throw new Error(`Agent ${agentId} does not have analyze permission`);
    }
    
    try {
      const chartData = await this.getChartData(agentId, symbol, {
        period: strategy.lookback || '1d',
        interval: strategy.timeframe || '5m',
        includeIndicators: true,
        includePatterns: true
      });
      
      const signals = this._generateSignals(agentId, chartData, strategy);
      
      this._updateAgentMetrics(agentId, 'signalsGenerated', signals.length);
      
      return signals;
      
    } catch (error) {
      console.error(`❌ Error generating signals for agent ${agentId}:`, error);
      throw error;
    }
  }

  /**
   * Backtest a trading strategy
   * @param {string} agentId - Agent identifier
   * @param {string} symbol - Symbol to test
   * @param {Object} strategy - Strategy configuration
   * @param {Object} options - Backtest options
   * @returns {Promise<Object>} Backtest results
   */
  async backtestStrategy(agentId, symbol, strategy, options = {}) {
    this._validateAgent(agentId);
    
    try {
      const {
        startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
        endDate = new Date(),
        initialCapital = 10000,
        commission = 0.001
      } = options;
      
      // Get historical data for backtesting
      const chartData = await this.getChartData(agentId, symbol, {
        period: '1mo',
        interval: strategy.timeframe || '5m',
        includeIndicators: true
      });
      
      // Run backtest simulation
      const results = this._runBacktest(chartData, strategy, {
        initialCapital,
        commission
      });
      
      return {
        symbol,
        strategy: strategy.name || 'Unnamed Strategy',
        period: { startDate, endDate },
        results,
        metadata: {
          agentId,
          dataPoints: chartData.dataPoints,
          processingTime: Date.now()
        }
      };
      
    } catch (error) {
      console.error(`❌ Error in backtest for agent ${agentId}:`, error);
      throw error;
    }
  }

  /**
   * Get agent performance metrics
   * @param {string} agentId - Agent identifier
   * @returns {Object} Performance metrics
   */
  getAgentMetrics(agentId) {
    const registration = this.agentSubscriptions.get(agentId);
    if (!registration) {
      throw new Error(`Agent ${agentId} not registered`);
    }
    
    return {
      agentId,
      name: registration.name,
      type: registration.type,
      registrationTime: registration.lastActivity,
      metrics: { ...registration.metrics },
      subscriptions: Array.from(registration.subscriptions),
      performance: {
        averageResponseTime: this.metrics.averageResponseTime,
        cacheHitRate: this.metrics.cacheHitRate,
        errorRate: registration.metrics.errors / (registration.metrics.requestCount || 1)
      }
    };
  }

  /**
   * Register a custom pattern detector
   * @param {string} name - Pattern name
   * @param {function} detector - Pattern detection function
   */
  registerPatternDetector(name, detector) {
    if (typeof detector !== 'function') {
      throw new Error('Pattern detector must be a function');
    }
    
    this.patternDetectors.set(name, detector);
    console.log(`🔍 Registered pattern detector: ${name}`);
  }

  /**
   * Register a custom signal generator
   * @param {string} name - Signal generator name
   * @param {function} generator - Signal generation function
   */
  registerSignalGenerator(name, generator) {
    if (typeof generator !== 'function') {
      throw new Error('Signal generator must be a function');
    }
    
    this.signalGenerators.set(name, generator);
    console.log(`📈 Registered signal generator: ${name}`);
  }

  /**
   * Handle data updates for subscribed agents
   * @private
   */
  _handleAgentDataUpdate(agentId, symbol, update, callback) {
    try {
      const registration = this.agentSubscriptions.get(agentId);
      if (!registration || !registration.subscriptions.has(symbol)) {
        return;
      }
      
      // Format update for agent
      const formattedUpdate = {
        symbol,
        type: update.type,
        timestamp: Date.now(),
        data: update.data,
        agentId
      };
      
      // Add real-time analysis if enabled
      if (registration.config.includeRealTimeAnalysis && update.type === 'price_update') {
        formattedUpdate.analysis = this._calculateRealTimeMetrics([update.data], update.data);
      }
      
      callback(formattedUpdate);
      this._updateAgentActivity(agentId);
      
    } catch (error) {
      console.error(`❌ Error handling agent data update:`, error);
    }
  }

  /**
   * Format data for agent consumption
   * @private
   */
  _formatDataForAgent(data, format) {
    switch (format) {
      case 'ohlcv':
        return data.map(item => ({
          timestamp: item.time,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          volume: item.volume
        }));
      
      case 'structured':
        return {
          timestamps: data.map(d => d.time),
          opens: data.map(d => d.open),
          highs: data.map(d => d.high),
          lows: data.map(d => d.low),
          closes: data.map(d => d.close),
          volumes: data.map(d => d.volume)
        };
      
      case 'ml_ready':
        // Format optimized for machine learning models
        return data.map((item, index) => ({
          features: [
            item.open, item.high, item.low, item.close, item.volume,
            index > 0 ? item.close - data[index - 1].close : 0, // price change
            index > 0 ? (item.close - data[index - 1].close) / data[index - 1].close : 0 // returns
          ],
          target: item.close,
          metadata: { timestamp: item.time, index }
        }));
      
      default:
        return data;
    }
  }

  /**
   * Calculate indicators for agent
   * @private
   */
  async _calculateIndicatorsForAgent(agentId, data) {
    const registration = this.agentSubscriptions.get(agentId);
    const requestedIndicators = registration.config.indicators;
    
    if (!requestedIndicators.length) {
      // Default indicators for trading agents
      return {
        sma20: this.indicators.sma(data, 20),
        sma50: this.indicators.sma(data, 50),
        rsi: this.indicators.rsi(data, 14),
        macd: this.indicators.macd(data)
      };
    }
    
    const results = {};
    for (const indicator of requestedIndicators) {
      try {
        if (typeof indicator === 'string') {
          results[indicator] = this.indicators[indicator](data);
        } else if (typeof indicator === 'object') {
          const { name, params } = indicator;
          results[name] = this.indicators[name](data, ...Object.values(params || {}));
        }
      } catch (error) {
        console.error(`❌ Error calculating indicator ${indicator}:`, error);
      }
    }
    
    return results;
  }

  /**
   * Detect patterns for agent
   * @private
   */
  async _detectPatternsForAgent(agentId, data) {
    const registration = this.agentSubscriptions.get(agentId);
    const requestedPatterns = registration.config.patterns;
    
    const results = {};
    for (const patternName of requestedPatterns) {
      const detector = this.patternDetectors.get(patternName);
      if (detector) {
        try {
          results[patternName] = detector(data);
        } catch (error) {
          console.error(`❌ Error detecting pattern ${patternName}:`, error);
        }
      }
    }
    
    return results;
  }

  /**
   * Generate trading signals
   * @private
   */
  _generateSignals(agentId, chartData, strategy = {}) {
    const signals = [];
    
    // Use registered signal generators or default logic
    const generatorName = strategy.generator || 'default';
    const generator = this.signalGenerators.get(generatorName);
    
    if (generator) {
      return generator(chartData, strategy);
    }
    
    // Default signal generation logic
    const { data, indicators } = chartData;
    
    if (indicators.rsi && indicators.sma20) {
      for (let i = 1; i < data.length; i++) {
        const currentRSI = indicators.rsi[i]?.value;
        const prevPrice = data[i - 1].close;
        const currentPrice = data[i].close;
        
        // Simple RSI + price momentum signals
        if (currentRSI < 30 && currentPrice > prevPrice) {
          signals.push({
            type: 'buy',
            timestamp: data[i].time,
            price: currentPrice,
            confidence: 0.7,
            reason: 'RSI oversold + price momentum',
            strength: 1
          });
        } else if (currentRSI > 70 && currentPrice < prevPrice) {
          signals.push({
            type: 'sell',
            timestamp: data[i].time,
            price: currentPrice,
            confidence: 0.7,
            reason: 'RSI overbought + price momentum',
            strength: 1
          });
        }
      }
    }
    
    return signals;
  }

  /**
   * Calculate real-time metrics
   * @private
   */
  _calculateRealTimeMetrics(data, currentPrice) {
    if (!data.length) return {};
    
    const prices = data.map(d => d.close);
    const volumes = data.map(d => d.volume);
    
    return {
      momentum: this._calculateMomentum(prices),
      volatility: this._calculateVolatility(prices),
      volume: {
        current: volumes[volumes.length - 1],
        average: volumes.reduce((a, b) => a + b, 0) / volumes.length,
        trend: volumes[volumes.length - 1] > volumes.reduce((a, b) => a + b, 0) / volumes.length ? 'increasing' : 'decreasing'
      },
      priceAction: {
        trend: prices[prices.length - 1] > prices[0] ? 'bullish' : 'bearish',
        strength: Math.abs(prices[prices.length - 1] - prices[0]) / prices[0]
      }
    };
  }

  /**
   * Calculate momentum
   * @private
   */
  _calculateMomentum(prices) {
    if (prices.length < 2) return 0;
    return (prices[prices.length - 1] - prices[prices.length - 2]) / prices[prices.length - 2];
  }

  /**
   * Calculate volatility
   * @private
   */
  _calculateVolatility(prices) {
    if (prices.length < 2) return 0;
    
    const returns = [];
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
    
    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;
    
    return Math.sqrt(variance);
  }

  /**
   * Calculate risk metrics
   * @private
   */
  _calculateRiskMetrics(data) {
    const prices = data.map(d => d.close);
    const returns = [];
    
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
    
    const sortedReturns = returns.sort((a, b) => a - b);
    const var95 = sortedReturns[Math.floor(sortedReturns.length * 0.05)];
    const maxDrawdown = this._calculateMaxDrawdown(prices);
    
    return {
      volatility: this._calculateVolatility(prices),
      valueAtRisk95: var95,
      maxDrawdown: maxDrawdown,
      sharpeRatio: this._calculateSharpeRatio(returns)
    };
  }

  /**
   * Calculate maximum drawdown
   * @private
   */
  _calculateMaxDrawdown(prices) {
    let maxDrawdown = 0;
    let peak = prices[0];
    
    for (const price of prices) {
      if (price > peak) {
        peak = price;
      } else {
        const drawdown = (peak - price) / peak;
        maxDrawdown = Math.max(maxDrawdown, drawdown);
      }
    }
    
    return maxDrawdown;
  }

  /**
   * Calculate Sharpe ratio
   * @private
   */
  _calculateSharpeRatio(returns, riskFreeRate = 0.02) {
    if (returns.length === 0) return 0;
    
    const meanReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const stdReturn = Math.sqrt(returns.reduce((a, b) => a + Math.pow(b - meanReturn, 2), 0) / returns.length);
    
    return stdReturn === 0 ? 0 : (meanReturn - riskFreeRate) / stdReturn;
  }

  /**
   * Assess market condition
   * @private
   */
  _assessMarketCondition(chartData) {
    const { data, indicators } = chartData;
    
    // Simple market condition assessment
    const recentPrices = data.slice(-20).map(d => d.close);
    const priceChange = (recentPrices[recentPrices.length - 1] - recentPrices[0]) / recentPrices[0];
    const volatility = this._calculateVolatility(recentPrices);
    
    let condition = 'neutral';
    let confidence = 0.5;
    
    if (Math.abs(priceChange) > 0.02) {
      condition = priceChange > 0 ? 'bullish' : 'bearish';
      confidence = Math.min(Math.abs(priceChange) * 10, 0.9);
    }
    
    if (volatility > 0.05) {
      condition += '_volatile';
    }
    
    return { condition, confidence, priceChange, volatility };
  }

  /**
   * Run backtest simulation
   * @private
   */
  _runBacktest(chartData, strategy, options) {
    // Simplified backtesting logic
    const { data } = chartData;
    const { initialCapital, commission } = options;
    
    let capital = initialCapital;
    let position = 0;
    let trades = [];
    let equity = [initialCapital];
    
    const signals = this._generateSignals(null, chartData, strategy);
    
    for (const signal of signals) {
      const price = signal.price;
      
      if (signal.type === 'buy' && position <= 0) {
        const shares = Math.floor(capital / price);
        const cost = shares * price * (1 + commission);
        
        if (cost <= capital) {
          capital -= cost;
          position = shares;
          trades.push({
            type: 'buy',
            timestamp: signal.timestamp,
            price: price,
            shares: shares,
            cost: cost
          });
        }
      } else if (signal.type === 'sell' && position > 0) {
        const proceeds = position * price * (1 - commission);
        capital += proceeds;
        
        trades.push({
          type: 'sell',
          timestamp: signal.timestamp,
          price: price,
          shares: position,
          proceeds: proceeds
        });
        
        position = 0;
      }
      
      equity.push(capital + (position * price));
    }
    
    const finalValue = capital + (position * data[data.length - 1].close);
    const totalReturn = (finalValue - initialCapital) / initialCapital;
    
    return {
      initialCapital,
      finalValue,
      totalReturn,
      totalTrades: trades.length,
      winRate: this._calculateWinRate(trades),
      maxDrawdown: this._calculateMaxDrawdown(equity),
      trades: trades.slice(-10) // Return last 10 trades
    };
  }

  /**
   * Calculate win rate from trades
   * @private
   */
  _calculateWinRate(trades) {
    const completedTrades = [];
    let buyTrade = null;
    
    for (const trade of trades) {
      if (trade.type === 'buy') {
        buyTrade = trade;
      } else if (trade.type === 'sell' && buyTrade) {
        completedTrades.push({
          profit: trade.proceeds - buyTrade.cost
        });
        buyTrade = null;
      }
    }
    
    if (completedTrades.length === 0) return 0;
    
    const winningTrades = completedTrades.filter(trade => trade.profit > 0);
    return winningTrades.length / completedTrades.length;
  }

  // Utility methods
  _validateAgent(agentId) {
    if (!this.agentSubscriptions.has(agentId)) {
      throw new Error(`Agent ${agentId} not registered`);
    }
  }

  _hasPermission(agentId, permission) {
    const registration = this.agentSubscriptions.get(agentId);
    return registration && registration.permissions.includes(permission);
  }

  _updateAgentActivity(agentId) {
    const registration = this.agentSubscriptions.get(agentId);
    if (registration) {
      registration.lastActivity = Date.now();
      registration.metrics.requestCount++;
    }
  }

  _updateAgentMetrics(agentId, metric, value = 1) {
    const registration = this.agentSubscriptions.get(agentId);
    if (registration) {
      registration.metrics[metric] = (registration.metrics[metric] || 0) + value;
    }
  }

  _updateMetrics(type, duration) {
    this.metrics.requestCount++;
    
    if (type === 'request') {
      this.metrics.averageResponseTime = 
        (this.metrics.averageResponseTime * (this.metrics.requestCount - 1) + duration) / 
        this.metrics.requestCount;
    } else if (type === 'cache_hit') {
      this.metrics.cacheHitRate = 
        (this.metrics.cacheHitRate * (this.metrics.requestCount - 1) + 1) / 
        this.metrics.requestCount;
    } else if (type === 'error') {
      this.metrics.errorCount++;
    }
  }

  _getCachedData(key) {
    const cached = this.dataCache.get(key);
    if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
      return cached.data;
    }
    if (cached) {
      this.dataCache.delete(key);
    }
    return null;
  }

  _setCachedData(key, data) {
    this.dataCache.set(key, {
      data: data,
      timestamp: Date.now()
    });
  }

  /**
   * Cleanup resources
   */
  cleanup() {
    console.log('🧹 Cleaning up ChartAgentInterface...');
    
    // Unsubscribe all agents
    for (const [agentId, registration] of this.agentSubscriptions) {
      registration.subscriptions.forEach(symbol => {
        this._unsubscribeAgentFromSymbol(agentId, symbol);
      });
    }
    
    // Clear caches
    this.dataCache.clear();
    this.indicatorCache.clear();
    this.patternCache.clear();
    this.agentSubscriptions.clear();
    
    console.log('✅ ChartAgentInterface cleanup complete');
  }

  _unsubscribeAgentFromSymbol(agentId, symbol) {
    const registration = this.agentSubscriptions.get(agentId);
    if (registration && registration.subscriptionIds) {
      const subscriptionId = registration.subscriptionIds.get(symbol);
      if (subscriptionId) {
        this.dataProvider.unsubscribe(subscriptionId);
        registration.subscriptionIds.delete(symbol);
      }
    }
  }
}

export default ChartAgentInterface;
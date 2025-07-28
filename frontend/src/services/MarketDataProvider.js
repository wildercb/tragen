/**
 * MarketDataProvider - Unified data service for consistent market data
 * 
 * This service provides a single source of truth for market data, eliminating
 * the inconsistencies caused by multiple data sources and caching issues.
 * 
 * Features:
 * - Unified WebSocket and HTTP data handling
 * - Proper cache isolation by symbol and timeframe
 * - Consistent data format and validation
 * - Agent-friendly API for AI model integration
 * - Real-time price updates with proper candle building
 * - Comprehensive error handling and fallback strategies
 */

class MarketDataProvider {
  constructor(config = {}) {
    this.config = {
      apiBaseUrl: config.apiBaseUrl || process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
      wsBaseUrl: config.wsBaseUrl || process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000',
      reconnectInterval: config.reconnectInterval || 3000,
      maxReconnectAttempts: config.maxReconnectAttempts || 5,
      cacheTimeout: config.cacheTimeout || 30000, // 30 seconds
      ...config
    };
    
    // Data management
    this.cache = new Map();
    this.subscriptions = new Map();
    this.websockets = new Map();
    this.reconnectAttempts = new Map();
    
    // Event system
    this.listeners = new Map();
    
    // Current state
    this.connectionStatus = new Map();
    this.currentPrices = new Map();
    this.lastUpdateTimes = new Map();
    
    // Data validation
    this.dataValidators = {
      price: (price) => typeof price === 'number' && price > 0 && price < 1000000,
      ohlc: (ohlc) => {
        return ohlc.open > 0 && ohlc.high > 0 && ohlc.low > 0 && ohlc.close > 0 &&
               ohlc.high >= Math.max(ohlc.open, ohlc.close) &&
               ohlc.low <= Math.min(ohlc.open, ohlc.close);
      },
      volume: (volume) => typeof volume === 'number' && volume >= 0
    };
    
    console.log('🚀 MarketDataProvider initialized with config:', this.config);
  }

  /**
   * Subscribe to real-time market data for a symbol
   * @param {string} symbol - The symbol to subscribe to
   * @param {Object} options - Subscription options
   * @param {function} callback - Callback function for data updates
   * @returns {string} - Subscription ID
   */
  subscribe(symbol, options = {}, callback) {
    const subscriptionId = `${symbol}_${Date.now()}_${Math.random()}`;
    
    const subscription = {
      id: subscriptionId,
      symbol: symbol,
      options: {
        timeframe: options.timeframe || '1m',
        includeHistorical: options.includeHistorical !== false,
        ...options
      },
      callback: callback,
      active: true,
      createdAt: Date.now()
    };
    
    this.subscriptions.set(subscriptionId, subscription);
    
    console.log(`📊 Subscribed to ${symbol} with ID: ${subscriptionId}`);
    
    // Initialize WebSocket connection for this symbol
    this._initializeWebSocket(symbol, subscription);
    
    // Load initial historical data if requested
    if (subscription.options.includeHistorical) {
      this._loadHistoricalData(symbol, subscription);
    }
    
    return subscriptionId;
  }

  /**
   * Unsubscribe from market data
   * @param {string} subscriptionId - The subscription ID to unsubscribe
   */
  unsubscribe(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) return;
    
    subscription.active = false;
    this.subscriptions.delete(subscriptionId);
    
    const symbol = subscription.symbol;
    
    // Check if there are other active subscriptions for this symbol
    const activeSubscriptions = Array.from(this.subscriptions.values())
      .filter(sub => sub.symbol === symbol && sub.active);
    
    if (activeSubscriptions.length === 0) {
      // No more subscriptions for this symbol, close WebSocket
      this._closeWebSocket(symbol);
    }
    
    console.log(`📊 Unsubscribed from ${symbol} (ID: ${subscriptionId})`);
  }

  /**
   * Get current price for a symbol
   * @param {string} symbol - The symbol to get price for
   * @returns {Promise<Object>} - Current price data
   */
  async getCurrentPrice(symbol) {
    try {
      // Check cache first
      const cacheKey = `price_${symbol}`;
      const cached = this._getCachedData(cacheKey);
      if (cached) {
        return cached;
      }
      
      const response = await fetch(`${this.config.apiBaseUrl}/api/market/price?symbol=${symbol}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate data
      if (!this._validatePriceData(data)) {
        throw new Error('Invalid price data received');
      }
      
      // Normalize data format
      const normalizedData = this._normalizePriceData(data);
      
      // Cache the data
      this._setCachedData(cacheKey, normalizedData);
      
      // Update internal state
      this.currentPrices.set(symbol, normalizedData.price);
      this.lastUpdateTimes.set(symbol, Date.now());
      
      console.log(`💰 Current price for ${symbol}: $${normalizedData.price}`);
      
      return normalizedData;
      
    } catch (error) {
      console.error(`❌ Failed to get current price for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get historical data for a symbol
   * @param {string} symbol - The symbol to get data for
   * @param {Object} options - Historical data options
   * @returns {Promise<Array>} - Historical OHLCV data
   */
  async getHistoricalData(symbol, options = {}) {
    try {
      const {
        period = '1y',
        interval = '1d',
        maxPoints = 2000
      } = options;
      
      // Check cache first
      const cacheKey = `historical_${symbol}_${period}_${interval}_${maxPoints}`;
      const cached = this._getCachedData(cacheKey);
      if (cached) {
        console.log(`📊 Using cached historical data for ${symbol}`);
        return cached;
      }
      
      const url = `${this.config.apiBaseUrl}/api/market/historical?symbol=${symbol}&period=${period}&interval=${interval}&max_points=${maxPoints}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (!data.data || !Array.isArray(data.data)) {
        throw new Error('Invalid historical data format');
      }
      
      // Normalize and validate data
      const normalizedData = this._normalizeHistoricalData(data.data);
      
      // Cache the data
      this._setCachedData(cacheKey, normalizedData, this.config.cacheTimeout * 5); // Cache historical data longer
      
      console.log(`📊 Retrieved ${normalizedData.length} historical data points for ${symbol}`);
      
      return normalizedData;
      
    } catch (error) {
      console.error(`❌ Failed to get historical data for ${symbol}:`, error);
      throw error;
    }
  }

  /**
   * Get connection status for a symbol
   * @param {string} symbol - The symbol to check
   * @returns {Object} - Connection status
   */
  getConnectionStatus(symbol) {
    return this.connectionStatus.get(symbol) || { connected: false, lastUpdate: null };
  }

  /**
   * Clear cache for a specific symbol or all symbols
   * @param {string} symbol - Symbol to clear cache for (optional)
   */
  clearCache(symbol = null) {
    if (symbol) {
      // Clear cache for specific symbol
      const keysToDelete = [];
      for (const key of this.cache.keys()) {
        if (key.includes(symbol)) {
          keysToDelete.push(key);
        }
      }
      keysToDelete.forEach(key => this.cache.delete(key));
      console.log(`🗑️ Cleared cache for ${symbol} (${keysToDelete.length} entries)`);
    } else {
      // Clear all cache
      this.cache.clear();
      console.log('🗑️ Cleared all cache');
    }
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {function} listener - Event listener function
   */
  addEventListener(event, listener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(listener);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {function} listener - Event listener function
   */
  removeEventListener(event, listener) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(listener);
    }
  }

  /**
   * Initialize WebSocket connection for a symbol
   * @private
   */
  async _initializeWebSocket(symbol, subscription) {
    try {
      const wsUrl = `${this.config.wsBaseUrl}/api/ws/market/${encodeURIComponent(symbol)}`;
      
      console.log(`🔄 Initializing WebSocket for ${symbol}: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log(`🔗 WebSocket connected for ${symbol}`);
        this.connectionStatus.set(symbol, { connected: true, lastUpdate: Date.now() });
        this.reconnectAttempts.set(symbol, 0);
        this._emit('connection', { symbol, status: 'connected' });
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this._handleWebSocketMessage(symbol, data);
        } catch (error) {
          console.error(`❌ Error parsing WebSocket message for ${symbol}:`, error);
        }
      };
      
      ws.onerror = (error) => {
        console.error(`❌ WebSocket error for ${symbol}:`, error);
        this._emit('error', { symbol, error });
      };
      
      ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed for ${symbol} (code: ${event.code})`);
        this.connectionStatus.set(symbol, { connected: false, lastUpdate: Date.now() });
        this._emit('connection', { symbol, status: 'disconnected' });
        
        // Attempt to reconnect if subscription is still active
        if (subscription.active) {
          this._attemptReconnect(symbol, subscription);
        }
      };
      
      this.websockets.set(symbol, ws);
      
    } catch (error) {
      console.error(`❌ Failed to initialize WebSocket for ${symbol}:`, error);
      this._emit('error', { symbol, error });
    }
  }

  /**
   * Handle WebSocket message
   * @private
   */
  _handleWebSocketMessage(symbol, data) {
    // Validate that the data is for the correct symbol
    if (data.symbol && data.symbol !== symbol) {
      console.warn(`⚠️ Received data for ${data.symbol} but expected ${symbol}`);
      return;
    }
    
    // Update last update time
    this.lastUpdateTimes.set(symbol, Date.now());
    
    // Process different message types
    switch (data.type) {
      case 'price_update':
        this._handlePriceUpdate(symbol, data);
        break;
      case 'historical_data':
        this._handleHistoricalData(symbol, data);
        break;
      case 'trading_signal':
        this._handleTradingSignal(symbol, data);
        break;
      case 'error':
        console.error(`❌ WebSocket error for ${symbol}:`, data.message);
        this._emit('error', { symbol, error: data.message });
        break;
      default:
        console.log(`📨 Unknown message type for ${symbol}:`, data.type);
    }
  }

  /**
   * Handle price update from WebSocket
   * @private
   */
  _handlePriceUpdate(symbol, data) {
    // Validate price data
    if (!this._validatePriceData(data)) {
      console.warn(`⚠️ Invalid price data for ${symbol}:`, data);
      return;
    }
    
    // Normalize price data
    const normalizedData = this._normalizePriceData(data);
    
    // Update internal state
    this.currentPrices.set(symbol, normalizedData.price);
    
    // Notify all active subscriptions for this symbol
    const activeSubscriptions = Array.from(this.subscriptions.values())
      .filter(sub => sub.symbol === symbol && sub.active);
    
    activeSubscriptions.forEach(subscription => {
      if (subscription.callback) {
        subscription.callback({
          type: 'price_update',
          symbol: symbol,
          data: normalizedData
        });
      }
    });
    
    this._emit('price_update', { symbol, data: normalizedData });
  }

  /**
   * Handle historical data from WebSocket
   * @private
   */
  _handleHistoricalData(symbol, data) {
    if (!data.data || !Array.isArray(data.data.data)) {
      console.warn(`⚠️ Invalid historical data format for ${symbol}:`, data);
      return;
    }
    
    // Normalize historical data
    const normalizedData = this._normalizeHistoricalData(data.data.data);
    
    // Notify all active subscriptions for this symbol
    const activeSubscriptions = Array.from(this.subscriptions.values())
      .filter(sub => sub.symbol === symbol && sub.active);
    
    activeSubscriptions.forEach(subscription => {
      if (subscription.callback) {
        subscription.callback({
          type: 'historical_data',
          symbol: symbol,
          data: normalizedData
        });
      }
    });
    
    this._emit('historical_data', { symbol, data: normalizedData });
  }

  /**
   * Handle trading signal from WebSocket
   * @private
   */
  _handleTradingSignal(symbol, data) {
    const activeSubscriptions = Array.from(this.subscriptions.values())
      .filter(sub => sub.symbol === symbol && sub.active);
    
    activeSubscriptions.forEach(subscription => {
      if (subscription.callback) {
        subscription.callback({
          type: 'trading_signal',
          symbol: symbol,
          data: data.signal
        });
      }
    });
    
    this._emit('trading_signal', { symbol, signal: data.signal });
  }

  /**
   * Attempt to reconnect WebSocket
   * @private
   */
  _attemptReconnect(symbol, subscription) {
    const currentAttempts = this.reconnectAttempts.get(symbol) || 0;
    
    if (currentAttempts >= this.config.maxReconnectAttempts) {
      console.error(`❌ Max reconnect attempts reached for ${symbol}`);
      this._emit('error', { symbol, error: 'Max reconnect attempts reached' });
      return;
    }
    
    setTimeout(() => {
      if (subscription.active) {
        console.log(`🔄 Attempting to reconnect WebSocket for ${symbol} (attempt ${currentAttempts + 1})`);
        this.reconnectAttempts.set(symbol, currentAttempts + 1);
        this._initializeWebSocket(symbol, subscription);
      }
    }, this.config.reconnectInterval);
  }

  /**
   * Close WebSocket connection
   * @private
   */
  _closeWebSocket(symbol) {
    const ws = this.websockets.get(symbol);
    if (ws) {
      ws.close();
      this.websockets.delete(symbol);
      this.connectionStatus.delete(symbol);
      this.reconnectAttempts.delete(symbol);
      console.log(`🔌 Closed WebSocket for ${symbol}`);
    }
  }

  /**
   * Load historical data for a subscription
   * @private
   */
  async _loadHistoricalData(symbol, subscription) {
    try {
      const historicalData = await this.getHistoricalData(symbol, {
        period: subscription.options.period || '1y',
        interval: subscription.options.timeframe || '1d',
        maxPoints: subscription.options.maxPoints || 2000
      });
      
      if (subscription.active && subscription.callback) {
        subscription.callback({
          type: 'historical_data',
          symbol: symbol,
          data: historicalData
        });
      }
      
    } catch (error) {
      console.error(`❌ Failed to load historical data for ${symbol}:`, error);
      if (subscription.active && subscription.callback) {
        subscription.callback({
          type: 'error',
          symbol: symbol,
          error: error.message
        });
      }
    }
  }

  /**
   * Validate price data
   * @private
   */
  _validatePriceData(data) {
    if (!data || typeof data !== 'object') return false;
    
    const price = parseFloat(data.close || data.current_price || data.price);
    return this.dataValidators.price(price);
  }

  /**
   * Normalize price data to consistent format
   * @private
   */
  _normalizePriceData(data) {
    const price = parseFloat(data.close || data.current_price || data.price);
    return {
      symbol: data.symbol,
      price: price,
      open: parseFloat(data.open || price),
      high: parseFloat(data.high || price),
      low: parseFloat(data.low || price),
      close: price,
      volume: parseFloat(data.volume || 0),
      change: parseFloat(data.change || 0),
      changePercent: parseFloat(data.changePercent || 0),
      timestamp: data.timestamp || data.current_time || Math.floor(Date.now() / 1000),
      source: data.source || 'api'
    };
  }

  /**
   * Normalize historical data to consistent format
   * @private
   */
  _normalizeHistoricalData(data) {
    return data
      .map(item => ({
        time: Math.floor(new Date(item.date).getTime() / 1000),
        open: parseFloat(item.open),
        high: parseFloat(item.high),
        low: parseFloat(item.low),
        close: parseFloat(item.close),
        volume: parseFloat(item.volume || 0)
      }))
      .filter(item => this.dataValidators.ohlc(item) && this.dataValidators.volume(item.volume))
      .sort((a, b) => a.time - b.time);
  }

  /**
   * Get cached data
   * @private
   */
  _getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }
    if (cached) {
      this.cache.delete(key);
    }
    return null;
  }

  /**
   * Set cached data
   * @private
   */
  _setCachedData(key, data, ttl = null) {
    this.cache.set(key, {
      data: data,
      timestamp: Date.now(),
      ttl: ttl || this.config.cacheTimeout
    });
  }

  /**
   * Emit event to listeners
   * @private
   */
  _emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`❌ Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup all connections and subscriptions
   */
  cleanup() {
    console.log('🧹 Cleaning up MarketDataProvider...');
    
    // Close all WebSocket connections
    for (const [symbol, ws] of this.websockets) {
      ws.close();
    }
    
    // Clear all data
    this.websockets.clear();
    this.subscriptions.clear();
    this.connectionStatus.clear();
    this.currentPrices.clear();
    this.lastUpdateTimes.clear();
    this.cache.clear();
    this.listeners.clear();
    
    console.log('✅ MarketDataProvider cleanup complete');
  }
}

export default MarketDataProvider;
/**
 * Application Constants
 * =====================
 * 
 * Centralized constants for the trading application
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8001',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8001',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};

// Trading Constants
export const TRADING = {
  DEFAULT_SYMBOL: 'NQ=F',
  DEFAULT_TIMEFRAME: '5m',
  DEFAULT_CHART_HEIGHT: 600,
  MAX_CHART_POINTS: 500,
  UPDATE_INTERVAL: 2000, // 2 seconds
  
  // Timeframes
  TIMEFRAMES: [
    { value: '1m', label: '1m', seconds: 60 },
    { value: '5m', label: '5m', seconds: 300 },
    { value: '15m', label: '15m', seconds: 900 },
    { value: '30m', label: '30m', seconds: 1800 },
    { value: '1h', label: '1H', seconds: 3600 },
    { value: '4h', label: '4H', seconds: 14400 },
    { value: '1d', label: '1D', seconds: 86400 },
  ],
  
  // Chart Types
  CHART_TYPES: [
    { value: 'candlestick', label: 'Candlestick' },
    { value: 'line', label: 'Line' },
    { value: 'area', label: 'Area' },
  ],
  
  // Indicators
  INDICATORS: {
    sma20: { name: 'SMA 20', color: '#f59e0b', period: 20 },
    sma50: { name: 'SMA 50', color: '#8b5cf6', period: 50 },
    ema12: { name: 'EMA 12', color: '#06b6d4', period: 12 },
    ema26: { name: 'EMA 26', color: '#f97316', period: 26 },
    rsi: { name: 'RSI', color: '#a855f7', period: 14 },
    macd: { name: 'MACD', color: '#10b981' },
    bollinger: { name: 'Bollinger Bands', color: '#ef4444', period: 20 },
    volume: { name: 'Volume', color: '#6b7280' },
  },
};

// UI Constants
export const UI = {
  ANIMATIONS: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
  },
  
  BREAKPOINTS: {
    xs: '475px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  
  Z_INDEX: {
    DROPDOWN: 1000,
    STICKY: 1020,
    FIXED: 1030,
    MODAL_BACKDROP: 1040,
    MODAL: 1050,
    POPOVER: 1060,
    TOOLTIP: 1070,
    NOTIFICATION: 1080,
  },
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network connection failed. Please check your connection.',
  API_ERROR: 'API request failed. Please try again.',
  WEBSOCKET_ERROR: 'Real-time connection lost. Attempting to reconnect...',
  DATA_FETCH_ERROR: 'Failed to fetch market data. Using cached data.',
  CHART_ERROR: 'Chart rendering failed. Please refresh the page.',
  AGENT_ERROR: 'Agent execution failed. Please check configuration.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  AGENT_CREATED: 'Agent created successfully',
  TRADE_EXECUTED: 'Trade executed successfully',
  CONFIG_UPDATED: 'Configuration updated successfully',
  CONNECTION_ESTABLISHED: 'Real-time connection established',
};

// Status Constants
export const STATUS = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
};

// Agent Types
export const AGENT_TYPES = {
  ANALYSIS: 'analysis',
  EXECUTION: 'execution',
  RISK: 'risk',
  CUSTOM: 'custom',
};

// Market States
export const MARKET_STATES = {
  OPEN: 'open',
  CLOSED: 'closed',
  PRE_MARKET: 'pre_market',
  AFTER_HOURS: 'after_hours',
  MAINTENANCE: 'maintenance',
};

// Local Storage Keys
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'trading_app_preferences',
  CHART_SETTINGS: 'chart_settings',
  AGENT_CONFIGS: 'agent_configs',
  RECENT_SYMBOLS: 'recent_symbols',
  DASHBOARD_LAYOUT: 'dashboard_layout',
};

// Default Settings
export const DEFAULT_SETTINGS = {
  theme: 'dark',
  notifications: true,
  autoRefresh: true,
  soundEnabled: false,
  chartType: 'candlestick',
  timeframe: '5m',
  indicators: ['sma20', 'volume'],
  riskSettings: {
    maxPositionSize: 1,
    stopLoss: 0.5,
    takeProfit: 1.0,
  },
};

export default {
  API_CONFIG,
  TRADING,
  UI,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  STATUS,
  AGENT_TYPES,
  MARKET_STATES,
  STORAGE_KEYS,
  DEFAULT_SETTINGS,
};
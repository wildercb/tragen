/**
 * Formatting Utilities
 * ====================
 * 
 * Utility functions for formatting data display
 */

/**
 * Format price values with proper currency formatting
 */
export const formatPrice = (price, options = {}) => {
  const {
    currency = 'USD',
    minimumFractionDigits = 2,
    maximumFractionDigits = 2,
    showSymbol = true,
  } = options;
  
  if (price === null || price === undefined || isNaN(price)) {
    return showSymbol ? '$--' : '--';
  }
  
  const formatter = new Intl.NumberFormat('en-US', {
    style: showSymbol ? 'currency' : 'decimal',
    currency,
    minimumFractionDigits,
    maximumFractionDigits,
  });
  
  return formatter.format(price);
};

/**
 * Format large numbers with appropriate suffixes (K, M, B)
 */
export const formatLargeNumber = (num, options = {}) => {
  const { precision = 1 } = options;
  
  if (num === null || num === undefined || isNaN(num)) {
    return '--';
  }
  
  const abs = Math.abs(num);
  const sign = num < 0 ? '-' : '';
  
  if (abs >= 1e9) {
    return `${sign}${(abs / 1e9).toFixed(precision)}B`;
  } else if (abs >= 1e6) {
    return `${sign}${(abs / 1e6).toFixed(precision)}M`;
  } else if (abs >= 1e3) {
    return `${sign}${(abs / 1e3).toFixed(precision)}K`;
  }
  
  return `${sign}${abs.toLocaleString()}`;
};

/**
 * Format percentage values
 */
export const formatPercentage = (value, options = {}) => {
  const { precision = 2, showSign = true } = options;
  
  if (value === null || value === undefined || isNaN(value)) {
    return '--';
  }
  
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(precision)}%`;
};

/**
 * Format time and dates
 */
export const formatTime = (date, options = {}) => {
  const {
    format = 'time', // 'time', 'date', 'datetime', 'relative'
    includeSeconds = false,
    use24Hour = false,
  } = options;
  
  if (!date) return '--';
  
  const dateObj = date instanceof Date ? date : new Date(date);
  
  if (isNaN(dateObj.getTime())) return '--';
  
  switch (format) {
    case 'time':
      return dateObj.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: includeSeconds ? '2-digit' : undefined,
        hour12: !use24Hour,
      });
    
    case 'date':
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    
    case 'datetime':
      return dateObj.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: !use24Hour,
      });
    
    case 'relative':
      return formatRelativeTime(dateObj);
    
    default:
      return dateObj.toISOString();
  }
};

/**
 * Format relative time (e.g., "2 minutes ago")
 */
export const formatRelativeTime = (date) => {
  const now = new Date();
  const diffMs = now - date;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) {
    return 'just now';
  } else if (diffMins < 60) {
    return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  } else if (diffHours < 24) {
    return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  } else if (diffDays < 7) {
    return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
};

/**
 * Format trading signals
 */
export const formatSignal = (signal) => {
  if (!signal) return null;
  
  return {
    type: signal.type?.toUpperCase() || 'UNKNOWN',
    strength: signal.strength || 0,
    confidence: formatPercentage(signal.confidence * 100, { precision: 1 }),
    price: formatPrice(signal.price),
    timestamp: formatTime(signal.timestamp, { format: 'datetime' }),
  };
};

/**
 * Format volume with appropriate scaling
 */
export const formatVolume = (volume) => {
  if (volume === null || volume === undefined || isNaN(volume)) {
    return '--';
  }
  
  return formatLargeNumber(volume, { precision: 1 });
};

/**
 * Format price change with colors
 */
export const formatPriceChange = (change, options = {}) => {
  const { showSign = true, precision = 2 } = options;
  
  if (change === null || change === undefined || isNaN(change)) {
    return { value: '--', color: 'neutral', isPositive: null };
  }
  
  const isPositive = change > 0;
  const sign = showSign && isPositive ? '+' : '';
  const value = `${sign}${change.toFixed(precision)}`;
  const color = isPositive ? 'profit' : change < 0 ? 'loss' : 'neutral';
  
  return { value, color, isPositive };
};

/**
 * Format market status
 */
export const formatMarketStatus = (status) => {
  const statusMap = {
    open: { label: 'Market Open', color: 'success' },
    closed: { label: 'Market Closed', color: 'neutral' },
    pre_market: { label: 'Pre-Market', color: 'warning' },
    after_hours: { label: 'After Hours', color: 'warning' },
    maintenance: { label: 'Maintenance', color: 'danger' },
  };
  
  return statusMap[status] || { label: 'Unknown', color: 'neutral' };
};

/**
 * Format agent status
 */
export const formatAgentStatus = (status) => {
  const statusMap = {
    idle: { label: 'Idle', color: 'neutral', icon: 'pause' },
    running: { label: 'Running', color: 'success', icon: 'play' },
    error: { label: 'Error', color: 'danger', icon: 'exclamation' },
    connecting: { label: 'Connecting', color: 'warning', icon: 'loading' },
  };
  
  return statusMap[status] || { label: 'Unknown', color: 'neutral', icon: 'question' };
};

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text || text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};

/**
 * Format file size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * Format duration (milliseconds to human readable)
 */
export const formatDuration = (ms) => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
};

export default {
  formatPrice,
  formatLargeNumber,
  formatPercentage,
  formatTime,
  formatRelativeTime,
  formatSignal,
  formatVolume,
  formatPriceChange,
  formatMarketStatus,
  formatAgentStatus,
  truncateText,
  formatFileSize,
  formatDuration,
};
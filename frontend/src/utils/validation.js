/**
 * Validation Utilities
 * ====================
 * 
 * Utility functions for data validation and sanitization
 */

/**
 * Validate price values
 */
export const validatePrice = (price) => {
  const numPrice = parseFloat(price);
  
  return {
    isValid: !isNaN(numPrice) && numPrice > 0 && isFinite(numPrice),
    value: numPrice,
    error: isNaN(numPrice) ? 'Invalid price format' : 
           numPrice <= 0 ? 'Price must be greater than zero' :
           !isFinite(numPrice) ? 'Price must be a finite number' : null
  };
};

/**
 * Validate percentage values
 */
export const validatePercentage = (percentage, options = {}) => {
  const { min = 0, max = 100, allowNegative = true } = options;
  const numPercentage = parseFloat(percentage);
  
  const isValid = !isNaN(numPercentage) && 
                  isFinite(numPercentage) &&
                  (allowNegative || numPercentage >= 0) &&
                  numPercentage >= min &&
                  numPercentage <= max;
  
  return {
    isValid,
    value: numPercentage,
    error: isNaN(numPercentage) ? 'Invalid percentage format' :
           !isFinite(numPercentage) ? 'Percentage must be a finite number' :
           (!allowNegative && numPercentage < 0) ? 'Percentage cannot be negative' :
           numPercentage < min ? `Percentage must be at least ${min}%` :
           numPercentage > max ? `Percentage cannot exceed ${max}%` : null
  };
};

/**
 * Validate symbol format
 */
export const validateSymbol = (symbol) => {
  const symbolRegex = /^[A-Z]{1,5}(=F)?$/; // Supports futures symbols like NQ=F
  const isValid = symbolRegex.test(symbol);
  
  return {
    isValid,
    value: symbol?.toUpperCase(),
    error: !isValid ? 'Invalid symbol format. Use format like NQ=F for futures' : null
  };
};

/**
 * Validate timeframe
 */
export const validateTimeframe = (timeframe, validTimeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']) => {
  const isValid = validTimeframes.includes(timeframe);
  
  return {
    isValid,
    value: timeframe,
    error: !isValid ? `Invalid timeframe. Must be one of: ${validTimeframes.join(', ')}` : null
  };
};

/**
 * Validate quantity/position size
 */
export const validateQuantity = (quantity, options = {}) => {
  const { min = 1, max = 100, allowDecimals = false } = options;
  const numQuantity = parseFloat(quantity);
  
  const isValid = !isNaN(numQuantity) &&
                  isFinite(numQuantity) &&
                  numQuantity >= min &&
                  numQuantity <= max &&
                  (allowDecimals || Number.isInteger(numQuantity));
  
  return {
    isValid,
    value: numQuantity,
    error: isNaN(numQuantity) ? 'Invalid quantity format' :
           !isFinite(numQuantity) ? 'Quantity must be a finite number' :
           numQuantity < min ? `Quantity must be at least ${min}` :
           numQuantity > max ? `Quantity cannot exceed ${max}` :
           (!allowDecimals && !Number.isInteger(numQuantity)) ? 'Quantity must be a whole number' : null
  };
};

/**
 * Validate email format
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const isValid = emailRegex.test(email);
  
  return {
    isValid,
    value: email?.toLowerCase(),
    error: !isValid ? 'Invalid email format' : null
  };
};

/**
 * Validate password strength
 */
export const validatePassword = (password, options = {}) => {
  const {
    minLength = 8,
    requireUppercase = true,
    requireLowercase = true,
    requireNumbers = true,
    requireSpecialChars = false
  } = options;
  
  const errors = [];
  
  if (password.length < minLength) {
    errors.push(`Password must be at least ${minLength} characters long`);
  }
  
  if (requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  if (requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  if (requireNumbers && !/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  if (requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  return {
    isValid: errors.length === 0,
    value: password,
    errors,
    error: errors.length > 0 ? errors[0] : null
  };
};

/**
 * Validate API key format
 */
export const validateApiKey = (apiKey, options = {}) => {
  const { minLength = 10, maxLength = 100 } = options;
  
  const isValid = typeof apiKey === 'string' &&
                  apiKey.length >= minLength &&
                  apiKey.length <= maxLength &&
                  /^[a-zA-Z0-9_-]+$/.test(apiKey);
  
  return {
    isValid,
    value: apiKey,
    error: !isValid ? 'Invalid API key format' : null
  };
};

/**
 * Validate configuration object
 */
export const validateConfig = (config, schema) => {
  const errors = [];
  const validatedConfig = {};
  
  for (const [key, rules] of Object.entries(schema)) {
    const value = config[key];
    
    // Check if required
    if (rules.required && (value === undefined || value === null || value === '')) {
      errors.push(`${key} is required`);
      continue;
    }
    
    // Skip validation if value is undefined and not required
    if (value === undefined && !rules.required) {
      continue;
    }
    
    // Type validation
    if (rules.type && typeof value !== rules.type) {
      errors.push(`${key} must be of type ${rules.type}`);
      continue;
    }
    
    // Custom validation
    if (rules.validate && typeof rules.validate === 'function') {
      const result = rules.validate(value);
      if (!result.isValid) {
        errors.push(result.error || `${key} is invalid`);
        continue;
      }
      validatedConfig[key] = result.value;
    } else {
      validatedConfig[key] = value;
    }
  }
  
  return {
    isValid: errors.length === 0,
    config: validatedConfig,
    errors,
    error: errors.length > 0 ? errors[0] : null
  };
};

/**
 * Sanitize string input
 */
export const sanitizeString = (str, options = {}) => {
  const { maxLength = 255, allowHtml = false, trim = true } = options;
  
  if (typeof str !== 'string') return '';
  
  let sanitized = str;
  
  if (trim) {
    sanitized = sanitized.trim();
  }
  
  if (!allowHtml) {
    sanitized = sanitized.replace(/<[^>]*>/g, '');
  }
  
  if (maxLength && sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength);
  }
  
  return sanitized;
};

/**
 * Validate OHLCV data
 */
export const validateOHLCVData = (data) => {
  if (!Array.isArray(data)) {
    return { isValid: false, error: 'Data must be an array' };
  }
  
  const errors = [];
  
  data.forEach((item, index) => {
    if (!item.open || !item.high || !item.low || !item.close) {
      errors.push(`Missing OHLC data at index ${index}`);
      return;
    }
    
    const { open, high, low, close } = item;
    
    if (high < Math.max(open, close, low)) {
      errors.push(`Invalid high price at index ${index}`);
    }
    
    if (low > Math.min(open, close, high)) {
      errors.push(`Invalid low price at index ${index}`);
    }
    
    if (item.volume !== undefined && item.volume < 0) {
      errors.push(`Invalid volume at index ${index}`);
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors,
    error: errors.length > 0 ? errors[0] : null
  };
};

/**
 * Validate date range
 */
export const validateDateRange = (startDate, endDate) => {
  const start = new Date(startDate);
  const end = new Date(endDate);
  
  const isValidStart = !isNaN(start.getTime());
  const isValidEnd = !isNaN(end.getTime());
  
  if (!isValidStart || !isValidEnd) {
    return {
      isValid: false,
      error: 'Invalid date format'
    };
  }
  
  if (start >= end) {
    return {
      isValid: false,
      error: 'Start date must be before end date'
    };
  }
  
  return {
    isValid: true,
    startDate: start,
    endDate: end,
    error: null
  };
};

export default {
  validatePrice,
  validatePercentage,
  validateSymbol,
  validateTimeframe,
  validateQuantity,
  validateEmail,
  validatePassword,
  validateApiKey,
  validateConfig,
  sanitizeString,
  validateOHLCVData,
  validateDateRange,
};
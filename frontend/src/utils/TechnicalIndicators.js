/**
 * TechnicalIndicators - Advanced technical analysis indicators
 * 
 * This module provides a comprehensive collection of technical indicators
 * for trading analysis. Designed to be modular, efficient, and extensible
 * for custom indicator development.
 * 
 * Features:
 * - Built-in indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
 * - Custom indicator framework
 * - Optimized calculations for real-time data
 * - Agent-friendly output format
 * - Comprehensive validation and error handling
 */

class TechnicalIndicators {
  constructor() {
    this.cache = new Map();
    this.customIndicators = new Map();
  }

  /**
   * Calculate Simple Moving Average
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} SMA values
   */
  sma(data, period = 20) {
    if (!this._validateData(data) || period <= 0 || period > data.length) {
      return [];
    }

    const result = [];
    for (let i = period - 1; i < data.length; i++) {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      result.push({
        time: data[i].time,
        value: parseFloat((sum / period).toFixed(4))
      });
    }
    return result;
  }

  /**
   * Calculate Exponential Moving Average
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} EMA values
   */
  ema(data, period = 12) {
    if (!this._validateData(data) || period <= 0 || period > data.length) {
      return [];
    }

    const result = [];
    const multiplier = 2 / (period + 1);
    let ema = data[0].close;
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        ema = data[i].close;
      } else {
        ema = (data[i].close * multiplier) + (ema * (1 - multiplier));
      }
      
      result.push({
        time: data[i].time,
        value: parseFloat(ema.toFixed(4))
      });
    }
    return result;
  }

  /**
   * Calculate Relative Strength Index
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} RSI values
   */
  rsi(data, period = 14) {
    if (!this._validateData(data) || period <= 0 || period >= data.length) {
      return [];
    }

    const changes = [];
    for (let i = 1; i < data.length; i++) {
      changes.push(data[i].close - data[i - 1].close);
    }

    const result = [];
    for (let i = period; i < changes.length; i++) {
      let gains = 0;
      let losses = 0;
      
      for (let j = 0; j < period; j++) {
        const change = changes[i - j];
        if (change > 0) {
          gains += change;
        } else {
          losses += Math.abs(change);
        }
      }
      
      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgGain / avgLoss;
      const rsi = 100 - (100 / (1 + rs));
      
      result.push({
        time: data[i + 1].time,
        value: parseFloat(rsi.toFixed(4))
      });
    }
    return result;
  }

  /**
   * Calculate MACD (Moving Average Convergence Divergence)
   * @param {Array} data - OHLCV data
   * @param {number} fastPeriod - Fast EMA period
   * @param {number} slowPeriod - Slow EMA period
   * @param {number} signalPeriod - Signal line period
   * @returns {Object} MACD values
   */
  macd(data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
    if (!this._validateData(data) || fastPeriod >= slowPeriod) {
      return { macd: [], signal: [], histogram: [] };
    }

    const fastEMA = this.ema(data, fastPeriod);
    const slowEMA = this.ema(data, slowPeriod);
    
    // Calculate MACD line
    const macdLine = [];
    const startIndex = slowPeriod - fastPeriod;
    
    for (let i = startIndex; i < fastEMA.length; i++) {
      const fastValue = fastEMA[i].value;
      const slowValue = slowEMA[i - startIndex].value;
      
      macdLine.push({
        time: fastEMA[i].time,
        value: parseFloat((fastValue - slowValue).toFixed(4))
      });
    }
    
    // Calculate signal line (EMA of MACD)
    const signalLine = this.ema(macdLine.map(item => ({
      time: item.time,
      close: item.value
    })), signalPeriod);
    
    // Calculate histogram
    const histogram = [];
    for (let i = 0; i < signalLine.length; i++) {
      const macdValue = macdLine[i + macdLine.length - signalLine.length].value;
      const signalValue = signalLine[i].value;
      
      histogram.push({
        time: signalLine[i].time,
        value: parseFloat((macdValue - signalValue).toFixed(4))
      });
    }
    
    return {
      macd: macdLine,
      signal: signalLine,
      histogram: histogram
    };
  }

  /**
   * Calculate Bollinger Bands
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @param {number} stdDev - Standard deviation multiplier
   * @returns {Object} Bollinger Bands values
   */
  bollingerBands(data, period = 20, stdDev = 2) {
    if (!this._validateData(data) || period <= 0 || period > data.length) {
      return { upper: [], lower: [], middle: [] };
    }

    const smaData = this.sma(data, period);
    const upper = [];
    const lower = [];
    const middle = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const smaValue = smaData[i - period + 1].value;
      
      // Calculate standard deviation
      let sum = 0;
      for (let j = 0; j < period; j++) {
        const diff = data[i - j].close - smaValue;
        sum += diff * diff;
      }
      const variance = sum / period;
      const standardDeviation = Math.sqrt(variance);
      
      const upperValue = smaValue + (standardDeviation * stdDev);
      const lowerValue = smaValue - (standardDeviation * stdDev);
      
      upper.push({ time: data[i].time, value: parseFloat(upperValue.toFixed(4)) });
      lower.push({ time: data[i].time, value: parseFloat(lowerValue.toFixed(4)) });
      middle.push({ time: data[i].time, value: parseFloat(smaValue.toFixed(4)) });
    }
    
    return { upper, lower, middle };
  }

  /**
   * Calculate Stochastic Oscillator
   * @param {Array} data - OHLCV data
   * @param {number} kPeriod - %K period
   * @param {number} dPeriod - %D period
   * @returns {Object} Stochastic values
   */
  stochastic(data, kPeriod = 14, dPeriod = 3) {
    if (!this._validateData(data) || kPeriod <= 0 || kPeriod > data.length) {
      return { k: [], d: [] };
    }

    const kValues = [];
    
    for (let i = kPeriod - 1; i < data.length; i++) {
      let highest = data[i - kPeriod + 1].high;
      let lowest = data[i - kPeriod + 1].low;
      
      for (let j = i - kPeriod + 1; j <= i; j++) {
        highest = Math.max(highest, data[j].high);
        lowest = Math.min(lowest, data[j].low);
      }
      
      const k = ((data[i].close - lowest) / (highest - lowest)) * 100;
      kValues.push({
        time: data[i].time,
        value: parseFloat(k.toFixed(4))
      });
    }
    
    // Calculate %D (SMA of %K)
    const dValues = this.sma(kValues.map(item => ({
      time: item.time,
      close: item.value
    })), dPeriod);
    
    return { k: kValues, d: dValues };
  }

  /**
   * Calculate Average True Range
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} ATR values
   */
  atr(data, period = 14) {
    if (!this._validateData(data) || period <= 0 || period >= data.length) {
      return [];
    }

    const trueRanges = [];
    for (let i = 1; i < data.length; i++) {
      const high = data[i].high;
      const low = data[i].low;
      const prevClose = data[i - 1].close;
      
      const tr = Math.max(
        high - low,
        Math.abs(high - prevClose),
        Math.abs(low - prevClose)
      );
      
      trueRanges.push({
        time: data[i].time,
        value: tr
      });
    }
    
    return this.sma(trueRanges.map(item => ({
      time: item.time,
      close: item.value
    })), period);
  }

  /**
   * Calculate Williams %R
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} Williams %R values
   */
  williamsR(data, period = 14) {
    if (!this._validateData(data) || period <= 0 || period > data.length) {
      return [];
    }

    const result = [];
    
    for (let i = period - 1; i < data.length; i++) {
      let highest = data[i - period + 1].high;
      let lowest = data[i - period + 1].low;
      
      for (let j = i - period + 1; j <= i; j++) {
        highest = Math.max(highest, data[j].high);
        lowest = Math.min(lowest, data[j].low);
      }
      
      const williamsR = ((highest - data[i].close) / (highest - lowest)) * -100;
      result.push({
        time: data[i].time,
        value: parseFloat(williamsR.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Calculate Commodity Channel Index
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} CCI values
   */
  cci(data, period = 20) {
    if (!this._validateData(data) || period <= 0 || period > data.length) {
      return [];
    }

    // Calculate typical price
    const typicalPrices = data.map(item => ({
      time: item.time,
      value: (item.high + item.low + item.close) / 3
    }));
    
    const result = [];
    
    for (let i = period - 1; i < typicalPrices.length; i++) {
      // Calculate SMA of typical price
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += typicalPrices[i - j].value;
      }
      const sma = sum / period;
      
      // Calculate mean absolute deviation
      let madSum = 0;
      for (let j = 0; j < period; j++) {
        madSum += Math.abs(typicalPrices[i - j].value - sma);
      }
      const mad = madSum / period;
      
      const cci = (typicalPrices[i].value - sma) / (0.015 * mad);
      result.push({
        time: typicalPrices[i].time,
        value: parseFloat(cci.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Calculate Money Flow Index
   * @param {Array} data - OHLCV data
   * @param {number} period - Period for calculation
   * @returns {Array} MFI values
   */
  mfi(data, period = 14) {
    if (!this._validateData(data) || period <= 0 || period >= data.length) {
      return [];
    }

    const typicalPrices = [];
    const moneyFlows = [];
    
    for (let i = 0; i < data.length; i++) {
      const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3;
      typicalPrices.push(typicalPrice);
      
      if (i > 0) {
        const rawMoneyFlow = typicalPrice * data[i].volume;
        moneyFlows.push({
          time: data[i].time,
          value: rawMoneyFlow,
          positive: typicalPrice > typicalPrices[i - 1]
        });
      }
    }
    
    const result = [];
    
    for (let i = period - 1; i < moneyFlows.length; i++) {
      let positiveFlow = 0;
      let negativeFlow = 0;
      
      for (let j = 0; j < period; j++) {
        if (moneyFlows[i - j].positive) {
          positiveFlow += moneyFlows[i - j].value;
        } else {
          negativeFlow += moneyFlows[i - j].value;
        }
      }
      
      const moneyFlowRatio = positiveFlow / negativeFlow;
      const mfi = 100 - (100 / (1 + moneyFlowRatio));
      
      result.push({
        time: moneyFlows[i].time,
        value: parseFloat(mfi.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Calculate On-Balance Volume
   * @param {Array} data - OHLCV data
   * @returns {Array} OBV values
   */
  obv(data) {
    if (!this._validateData(data)) {
      return [];
    }

    const result = [];
    let obv = 0;
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        obv = data[i].volume;
      } else {
        if (data[i].close > data[i - 1].close) {
          obv += data[i].volume;
        } else if (data[i].close < data[i - 1].close) {
          obv -= data[i].volume;
        }
      }
      
      result.push({
        time: data[i].time,
        value: parseFloat(obv.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Calculate Volume Weighted Average Price
   * @param {Array} data - OHLCV data
   * @returns {Array} VWAP values
   */
  vwap(data) {
    if (!this._validateData(data)) {
      return [];
    }

    const result = [];
    let cumulativeVolume = 0;
    let cumulativeTypicalPriceVolume = 0;
    
    for (let i = 0; i < data.length; i++) {
      const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3;
      const typicalPriceVolume = typicalPrice * data[i].volume;
      
      cumulativeVolume += data[i].volume;
      cumulativeTypicalPriceVolume += typicalPriceVolume;
      
      const vwap = cumulativeTypicalPriceVolume / cumulativeVolume;
      
      result.push({
        time: data[i].time,
        value: parseFloat(vwap.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Calculate Parabolic SAR
   * @param {Array} data - OHLCV data
   * @param {number} acceleration - Acceleration factor
   * @param {number} maximum - Maximum acceleration
   * @returns {Array} SAR values
   */
  parabolicSAR(data, acceleration = 0.02, maximum = 0.2) {
    if (!this._validateData(data) || data.length < 2) {
      return [];
    }

    const result = [];
    let isUpTrend = data[1].close > data[0].close;
    let sar = isUpTrend ? data[0].low : data[0].high;
    let ep = isUpTrend ? data[1].high : data[1].low;
    let af = acceleration;
    
    result.push({
      time: data[0].time,
      value: parseFloat(sar.toFixed(4))
    });
    
    for (let i = 1; i < data.length; i++) {
      const prevSar = sar;
      sar = prevSar + af * (ep - prevSar);
      
      if (isUpTrend) {
        if (data[i].high > ep) {
          ep = data[i].high;
          af = Math.min(af + acceleration, maximum);
        }
        
        if (data[i].low < sar) {
          isUpTrend = false;
          sar = ep;
          ep = data[i].low;
          af = acceleration;
        }
      } else {
        if (data[i].low < ep) {
          ep = data[i].low;
          af = Math.min(af + acceleration, maximum);
        }
        
        if (data[i].high > sar) {
          isUpTrend = true;
          sar = ep;
          ep = data[i].high;
          af = acceleration;
        }
      }
      
      result.push({
        time: data[i].time,
        value: parseFloat(sar.toFixed(4))
      });
    }
    
    return result;
  }

  /**
   * Register a custom indicator
   * @param {string} name - Indicator name
   * @param {function} calculator - Calculation function
   */
  registerCustomIndicator(name, calculator) {
    if (typeof calculator !== 'function') {
      throw new Error('Calculator must be a function');
    }
    
    this.customIndicators.set(name, calculator);
    console.log(`✅ Registered custom indicator: ${name}`);
  }

  /**
   * Calculate custom indicator
   * @param {string} name - Indicator name
   * @param {Array} data - OHLCV data
   * @param {Object} params - Indicator parameters
   * @returns {*} Indicator result
   */
  calculateCustom(name, data, params = {}) {
    const calculator = this.customIndicators.get(name);
    if (!calculator) {
      throw new Error(`Custom indicator '${name}' not found`);
    }
    
    return calculator(data, params);
  }

  /**
   * Get all available indicators
   * @returns {Object} Available indicators
   */
  getAvailableIndicators() {
    return {
      builtin: [
        'sma', 'ema', 'rsi', 'macd', 'bollingerBands', 'stochastic',
        'atr', 'williamsR', 'cci', 'mfi', 'obv', 'vwap', 'parabolicSAR'
      ],
      custom: Array.from(this.customIndicators.keys())
    };
  }

  /**
   * Calculate multiple indicators at once
   * @param {Array} data - OHLCV data
   * @param {Object} indicators - Indicators configuration
   * @returns {Object} Calculated indicators
   */
  calculateMultiple(data, indicators) {
    const results = {};
    
    for (const [name, config] of Object.entries(indicators)) {
      if (!config.enabled) continue;
      
      try {
        if (this.customIndicators.has(name)) {
          results[name] = this.calculateCustom(name, data, config);
        } else if (typeof this[name] === 'function') {
          results[name] = this[name](data, ...Object.values(config.params || {}));
        } else {
          console.warn(`Unknown indicator: ${name}`);
        }
      } catch (error) {
        console.error(`Error calculating indicator ${name}:`, error);
        results[name] = [];
      }
    }
    
    return results;
  }

  /**
   * Validate OHLCV data
   * @private
   */
  _validateData(data) {
    if (!Array.isArray(data) || data.length === 0) {
      return false;
    }
    
    const requiredFields = ['time', 'open', 'high', 'low', 'close'];
    return data.every(item => 
      requiredFields.every(field => 
        typeof item[field] === 'number' && !isNaN(item[field])
      )
    );
  }

  /**
   * Clear calculation cache
   */
  clearCache() {
    this.cache.clear();
  }
}

export default TechnicalIndicators;

// Example custom indicator implementations
export const customIndicators = {
  /**
   * SuperTrend Indicator
   * @param {Array} data - OHLCV data
   * @param {Object} params - Parameters
   * @returns {Array} SuperTrend values
   */
  superTrend: (data, params = {}) => {
    const { period = 10, multiplier = 3 } = params;
    const indicators = new TechnicalIndicators();
    
    const atr = indicators.atr(data, period);
    const result = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) continue;
      
      const hl2 = (data[i].high + data[i].low) / 2;
      const atrValue = atr[i - period + 1].value;
      
      const upperBand = hl2 + (multiplier * atrValue);
      const lowerBand = hl2 - (multiplier * atrValue);
      
      // This is a simplified version - full implementation would track trend direction
      result.push({
        time: data[i].time,
        value: data[i].close > hl2 ? lowerBand : upperBand,
        trend: data[i].close > hl2 ? 'up' : 'down'
      });
    }
    
    return result;
  },

  /**
   * Fibonacci Retracement Levels
   * @param {Array} data - OHLCV data
   * @param {Object} params - Parameters
   * @returns {Object} Fibonacci levels
   */
  fibonacciRetracement: (data, params = {}) => {
    const { lookback = 100 } = params;
    
    if (data.length < lookback) return { levels: [] };
    
    const recentData = data.slice(-lookback);
    const high = Math.max(...recentData.map(d => d.high));
    const low = Math.min(...recentData.map(d => d.low));
    
    const diff = high - low;
    const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1].map(ratio => ({
      ratio: ratio,
      price: high - (diff * ratio),
      label: `${(ratio * 100).toFixed(1)}%`
    }));
    
    return { levels, high, low };
  }
};

// Register custom indicators
const indicators = new TechnicalIndicators();
Object.entries(customIndicators).forEach(([name, calculator]) => {
  indicators.registerCustomIndicator(name, calculator);
});

export { indicators };
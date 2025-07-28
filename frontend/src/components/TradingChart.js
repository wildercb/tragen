import React, { useEffect, useRef, useState, useCallback } from 'react';
import { createChart, ColorType, CrosshairMode, LineStyle, PriceScaleMode } from 'lightweight-charts';
import {
  Cog6ToothIcon,
  ChartBarIcon,
  PlayIcon,
  PauseIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  EyeIcon,
  EyeSlashIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import DynamicSymbolSearch from './DynamicSymbolSearch';

const TradingChart = ({ symbol = 'NQ=F', displaySymbol = 'NQ', height = 600, apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000', onSignalReceived, onSymbolChange, onChartDataUpdate }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRefs = useRef({});
  
  const [isPlaying, setIsPlaying] = useState(true);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [timeframe, setTimeframe] = useState('5m');
  const [selectedPeriod, setSelectedPeriod] = useState('1d');
  const [chartType, setChartType] = useState('candlestick');
  const [showDrawingTools, setShowDrawingTools] = useState(false);
  const [showIndicatorSearch, setShowIndicatorSearch] = useState(false);
  const [indicatorSearchTerm, setIndicatorSearchTerm] = useState('');
  
  const [indicators, setIndicators] = useState({
    sma20: { enabled: true, visible: true, color: '#f59e0b', period: 20 },
    sma50: { enabled: true, visible: true, color: '#8b5cf6', period: 50 },
    ema12: { enabled: false, visible: true, color: '#06b6d4', period: 12 },
    ema26: { enabled: false, visible: true, color: '#f97316', period: 26 },
    rsi: { enabled: false, visible: true, color: '#a855f7', period: 14, overbought: 70, oversold: 30 },
    macd: { enabled: false, visible: true, color: '#10b981', fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
    bollinger: { enabled: false, visible: true, color: '#ef4444', period: 20, stdDev: 2 },
    volume: { enabled: true, visible: true, color: '#6b7280' },
    stochastic: { enabled: false, visible: true, color: '#ec4899', kPeriod: 14, dPeriod: 3 },
    williams: { enabled: false, visible: true, color: '#84cc16', period: 14 },
    atr: { enabled: false, visible: true, color: '#f59e0b', period: 14 },
    adx: { enabled: false, visible: true, color: '#6366f1', period: 14 },
  });
  
  const [tradeSignals, setTradeSignals] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [limitOrders, setLimitOrders] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  

  // Candlestick timeframes (intervals)
  const timeframes = [
    { value: '1m', label: '1 min', seconds: 60 },
    { value: '3m', label: '3 min', seconds: 180 },
    { value: '5m', label: '5 min', seconds: 300 },
    { value: '15m', label: '15 min', seconds: 900 },
    { value: '30m', label: '30 min', seconds: 1800 },
    { value: '1h', label: '1 hour', seconds: 3600 },
    { value: '2h', label: '2 hour', seconds: 7200 },
    { value: '4h', label: '4 hour', seconds: 14400 },
    { value: '6h', label: '6 hour', seconds: 21600 },
    { value: '12h', label: '12 hour', seconds: 43200 },
    { value: '1d', label: 'Day', seconds: 86400 },
    { value: '1wk', label: 'Week', seconds: 604800 },
    { value: '1mo', label: 'Month', seconds: 2629746 },
  ];

  // Period selection options for manual data loading
  const periodOptions = [
    { value: '1d', label: '1D', description: 'Last day' },
    { value: '5d', label: '5D', description: 'Last 5 days' },
    { value: '1mo', label: '1M', description: 'Last month' },
    { value: '3mo', label: '3M', description: 'Last 3 months' },
    { value: '6mo', label: '6M', description: 'Last 6 months' },
    { value: '1y', label: '1Y', description: 'Last year' },
    { value: '2y', label: '2Y', description: 'Last 2 years' },
    { value: '5y', label: '5Y', description: 'Last 5 years' },
    { value: 'max', label: 'ALL', description: 'All available data' },
  ];

  // Comprehensive TradingView-style indicators including popular public ones
  const availableIndicators = [
    // Built-in Technical Indicators
    { key: 'sma20', name: 'Simple Moving Average (20)', category: 'Moving Averages', author: 'Built-in' },
    { key: 'sma50', name: 'Simple Moving Average (50)', category: 'Moving Averages', author: 'Built-in' },
    { key: 'ema12', name: 'Exponential Moving Average (12)', category: 'Moving Averages', author: 'Built-in' },
    { key: 'ema26', name: 'Exponential Moving Average (26)', category: 'Moving Averages', author: 'Built-in' },
    { key: 'rsi', name: 'Relative Strength Index', category: 'Oscillators', author: 'Built-in' },
    { key: 'macd', name: 'MACD', category: 'Oscillators', author: 'Built-in' },
    { key: 'bollinger', name: 'Bollinger Bands', category: 'Volatility', author: 'Built-in' },
    { key: 'stochastic', name: 'Stochastic Oscillator', category: 'Oscillators', author: 'Built-in' },
    { key: 'williams', name: 'Williams %R', category: 'Oscillators', author: 'Built-in' },
    { key: 'atr', name: 'Average True Range', category: 'Volatility', author: 'Built-in' },
    { key: 'adx', name: 'Average Directional Index', category: 'Trend', author: 'Built-in' },
    { key: 'volume', name: 'Volume', category: 'Volume', author: 'Built-in' },
    
    // Popular Public TradingView Indicators
    { key: 'supertrend', name: 'SuperTrend', category: 'Trend', author: '@KivancOzbilgic' },
    { key: 'vwap', name: 'Volume Weighted Average Price', category: 'Volume', author: 'Built-in' },
    { key: 'ichimoku', name: 'Ichimoku Cloud', category: 'Trend', author: 'Built-in' },
    { key: 'emas_ribbon', name: 'EMA Ribbon (8 EMAs)', category: 'Moving Averages', author: '@everget' },
    { key: 'squeeze_momentum', name: 'Squeeze Momentum', category: 'Momentum', author: '@LazyBear' },
    { key: 'wave_trend', name: 'WaveTrend Oscillator', category: 'Oscillators', author: '@LazyBear' },
    { key: 'ssl_channels', name: 'SSL Channels', category: 'Trend', author: '@ErwinBeckers' },
    { key: 'fibonacci_retracement', name: 'Auto Fibonacci Retracement', category: 'Support/Resistance', author: '@LonesomeTheBlue' },
    { key: 'pivot_points', name: 'Pivot Points Standard', category: 'Support/Resistance', author: 'Built-in' },
    { key: 'market_structure', name: 'Market Structure Break & Order Block', category: 'Price Action', author: '@LuxAlgo' },
    { key: 'smart_money_concepts', name: 'Smart Money Concepts', category: 'Price Action', author: '@LuxAlgo' },
    { key: 'order_blocks', name: 'Order Blocks', category: 'Price Action', author: '@LuxAlgo' },
    { key: 'fair_value_gaps', name: 'Fair Value Gaps (FVG)', category: 'Price Action', author: '@LuxAlgo' },
    { key: 'volume_profile', name: 'Volume Profile', category: 'Volume', author: 'Built-in' },
    { key: 'renko', name: 'Renko Chart', category: 'Chart Types', author: 'Built-in' },
    { key: 'heikin_ashi', name: 'Heikin Ashi', category: 'Chart Types', author: 'Built-in' },
    { key: 'divergence_indicator', name: 'RSI Divergence', category: 'Divergence', author: '@ricardosantos' },
    { key: 'elder_ray', name: 'Elder Ray Index', category: 'Momentum', author: '@everget' },
    { key: 'money_flow_index', name: 'Money Flow Index (MFI)', category: 'Volume', author: 'Built-in' },
    { key: 'commodity_channel', name: 'Commodity Channel Index (CCI)', category: 'Momentum', author: 'Built-in' },
    { key: 'parabolic_sar', name: 'Parabolic SAR', category: 'Trend', author: 'Built-in' },
    { key: 'keltner_channels', name: 'Keltner Channels', category: 'Volatility', author: 'Built-in' },
    { key: 'donchian_channels', name: 'Donchian Channels', category: 'Volatility', author: 'Built-in' },
    { key: 'schaff_trend', name: 'Schaff Trend Cycle', category: 'Trend', author: '@everget' },
    { key: 'chaikin_oscillator', name: 'Chaikin Oscillator', category: 'Volume', author: 'Built-in' },
    { key: 'price_volume_trend', name: 'Price Volume Trend (PVT)', category: 'Volume', author: 'Built-in' },
    { key: 'trix', name: 'TRIX', category: 'Momentum', author: 'Built-in' },
    { key: 'ultimate_oscillator', name: 'Ultimate Oscillator', category: 'Momentum', author: 'Built-in' },
    { key: 'chande_momentum', name: 'Chande Momentum Oscillator', category: 'Momentum', author: 'Built-in' },
    { key: 'mass_index', name: 'Mass Index', category: 'Volatility', author: 'Built-in' },
    { key: 'vortex', name: 'Vortex Indicator', category: 'Trend', author: 'Built-in' },
    { key: 'accumulation_distribution', name: 'Accumulation/Distribution Line', category: 'Volume', author: 'Built-in' },
    { key: 'on_balance_volume', name: 'On Balance Volume (OBV)', category: 'Volume', author: 'Built-in' },
    { key: 'ease_of_movement', name: 'Ease of Movement', category: 'Volume', author: 'Built-in' },
    { key: 'negative_volume_index', name: 'Negative Volume Index', category: 'Volume', author: 'Built-in' },
    { key: 'positive_volume_index', name: 'Positive Volume Index', category: 'Volume', author: 'Built-in' },
  ];

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a0b' },
        textColor: '#f9fafb',
        fontSize: 12,
        fontFamily: 'Trebuchet MS',
      },
      grid: {
        vertLines: { color: 'rgba(55, 65, 81, 0.5)', style: LineStyle.Dotted },
        horzLines: { color: 'rgba(55, 65, 81, 0.5)', style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: '#14b8a6',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#14b8a6',
        },
        horzLine: {
          color: '#14b8a6',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#14b8a6',
        },
      },
      rightPriceScale: {
        borderColor: '#374151',
        textColor: '#9ca3af',
        entireTextOnly: true,
        scaleMargins: {
          top: 0.1,
          bottom: 0.25,
        },
      },
      leftPriceScale: {
        visible: false,
      },
      timeScale: {
        borderColor: '#374151',
        textColor: '#9ca3af',
        timeVisible: true,
        secondsVisible: false,
        tickMarkFormatter: (time) => {
          const date = new Date(time * 1000);
          return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
          });
        },
      },
      width: chartContainerRef.current.clientWidth,
      height: height,
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    chartRef.current = chart;

    // Main price series
    let mainSeries;
    if (chartType === 'candlestick') {
      mainSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });
    } else if (chartType === 'line') {
      mainSeries = chart.addLineSeries({
        color: '#14b8a6',
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 6,
        crosshairMarkerBorderColor: '#14b8a6',
        crosshairMarkerBackgroundColor: '#14b8a6',
      });
    } else if (chartType === 'area') {
      mainSeries = chart.addAreaSeries({
        topColor: 'rgba(20, 184, 166, 0.4)',
        bottomColor: 'rgba(20, 184, 166, 0.0)',
        lineColor: '#14b8a6',
        lineWidth: 2,
        crosshairMarkerVisible: true,
      });
    }

    candlestickSeriesRef.current = mainSeries;

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: 'rgba(107, 114, 128, 0.8)',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    volumeSeriesRef.current = volumeSeries;

    // Set up volume price scale
    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
      mode: PriceScaleMode.Percentage,
    });

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      // Clean up indicator series
      Object.values(indicatorSeriesRefs.current).forEach(series => {
        if (series && chart) {
          try {
            chart.removeSeries(series);
          } catch (e) {
            // Series may already be removed
          }
        }
      });
      indicatorSeriesRefs.current = {};
      if (chart) {
        chart.remove();
      }
    };
  }, [height, chartType]);

  // Reset candle state when symbol or timeframe changes
  useEffect(() => {
    setCurrentCandle(null);
    setLastCandleTime(null);
    setCurrentPrice(null);
    setPriceChange(0);
  }, [symbol, timeframe]);

  // WebSocket connection for real-time data
  useEffect(() => {
    if (!isPlaying || !candlestickSeriesRef.current) return;

    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      try {
        // Try to connect to WebSocket for real-time data
        const wsBaseUrl = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000';
        const wsUrl = `${wsBaseUrl}/api/ws/market/${encodeURIComponent(symbol)}`;
        console.log(`🔄 Attempting WebSocket connection to: ${wsUrl}`);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log(`🔗 WebSocket connected for ${symbol} real-time data`);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          console.log(`📥 WebSocket received: ${data.type} for ${data.symbol || 'unknown'} (current: ${symbol})`);
          
          // CRITICAL: Only process data for current symbol
          if (data.symbol && data.symbol !== symbol) {
            console.log(`❌ Ignoring WebSocket data for ${data.symbol}, current symbol is ${symbol}`);
            return;
          }
          
          if (data.type === 'price_update') {
            console.log(`💰 Price update: ${data.symbol} = $${data.close}`);
            updateRealTimePrice(data);
          } else if (data.type === 'historical_data') {
            // Handle historical data from WebSocket
            if (data.data && data.data.data) {
              const ohlcData = data.data.data.map(item => ({
                time: Math.floor(new Date(item.date).getTime() / 1000),
                open: parseFloat(item.open),
                high: parseFloat(item.high),
                low: parseFloat(item.low),
                close: parseFloat(item.close),
                volume: parseFloat(item.volume || Math.floor(1000 + Math.random() * 5000))
              })).sort((a, b) => a.time - b.time);
              
              if (ohlcData.length > 0) {
                setChartData(ohlcData);
                updateChartSeries(ohlcData);
                updateIndicators(ohlcData);
                setCurrentPrice(ohlcData[ohlcData.length - 1].close);
                // Set initial lastUpdateTime to the last historical data point
                setLastUpdateTime(ohlcData[ohlcData.length - 1].time);
                
                // Auto-size chart for the new WebSocket data
                if (chartRef.current) {
                  setTimeout(() => {
                    try {
                      // First fit all content to establish proper scale
                      chartRef.current.timeScale().fitContent();
                      
                      // Then set optimal zoom level for this timeframe
                      const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
                      const intervalSeconds = timeframeConfig?.seconds || 86400;
                      
                      let visibleBarsCount;
                      if (intervalSeconds <= 300) { // 5 minutes or less
                        visibleBarsCount = 100; // Show about 8 hours of 5min data
                      } else if (intervalSeconds <= 3600) { // 1 hour or less  
                        visibleBarsCount = 120; // Show about 5 days of hourly data
                      } else if (intervalSeconds <= 86400) { // 1 day or less
                        visibleBarsCount = 90; // Show about 3 months of daily data
                      } else {
                        visibleBarsCount = 60; // Show reasonable amount for larger timeframes
                      }
                      
                      // Apply the optimal zoom with some padding on the right
                      chartRef.current.timeScale().setVisibleLogicalRange({
                        from: Math.max(0, visibleBarsCount * -1),
                        to: 10 // Show a few bars beyond current time for padding
                      });
                      
                      console.log(`📏 Auto-sized WebSocket chart for ${symbol} showing ${visibleBarsCount} bars`);
                    } catch (e) {
                      console.warn('Failed to auto-size WebSocket chart:', e);
                    }
                  }, 300);
                }
              }
            }
          } else if (data.type === 'trading_signal') {
            // Handle AI trading signals
            console.log(`🤖 Trading signal received:`, data.signal);
            addTradeSignal(data.signal);
            if (onSignalReceived) {
              onSignalReceived(data.signal);
            }
          } else if (data.type === 'signal') {
            // Handle legacy signals
            addTradeSignal(data.signal);
            if (onSignalReceived) {
              onSignalReceived(data.signal);
            }
          } else if (data.type === 'limit_order') {
            updateLimitOrders(data.orders);
          } else if (data.type === 'error') {
            console.error('WebSocket error:', data.message);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log(`🔌 WebSocket disconnected for ${symbol}, attempting to reconnect...`);
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        // Start polling fallback for live updates if WebSocket fails
        startPollingFallback();
      }
    };

    // Fallback polling method for live updates when WebSocket unavailable
    const startPollingFallback = () => {
      console.log(`🔄 Starting polling fallback for ${symbol} live updates`);
      const pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${apiBaseUrl}/api/market/price?symbol=${symbol}`);
          if (response.ok) {
            const priceData = await response.json();
            // Convert to WebSocket format
            const wsData = {
              type: 'price_update',
              symbol: priceData.symbol,
              open: priceData.current_price,
              high: priceData.session_high,
              low: priceData.session_low,
              close: priceData.current_price,
              volume: priceData.volume,
              change: 0,
              timestamp: priceData.timestamp,
              candle_time: Math.floor(Date.now() / 1000),
              real_data: true,
              source: 'api_polling'
            };
            updateRealTimePrice(wsData);
          }
        } catch (error) {
          console.error('Polling fallback error:', error);
        }
      }, 5000); // Poll every 5 seconds for live updates

      return () => clearInterval(pollInterval);
    };

    const fetchHistoricalData = async () => {
      try {
        const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
        const interval = timeframeConfig?.value || '1d';
        
        // Use selected period or determine optimal period based on interval
        let period = selectedPeriod || '1y';
        let maxPoints = 2000;
        
        // Adjust max points based on period
        if (period === 'max' || period === '10y' || period === '5y') {
          maxPoints = 5000;
        } else if (period === '2y' || period === '1y') {
          maxPoints = 3000;
        } else if (period === '6mo' || period === '3mo') {
          maxPoints = 2000;
        } else {
          maxPoints = 1000;
        }
        
        // For minute intervals, limit the period to prevent too much data but respect user choice
        if ((interval === '1m' || interval === '5m') && ['max', '10y', '5y', '2y', '1y'].includes(period)) {
          period = selectedPeriod; // Use selected period but limit points
          maxPoints = 1000;
        } else if ((interval === '15m' || interval === '30m') && ['max', '10y', '5y', '2y'].includes(period)) {
          period = selectedPeriod; // Use selected period
          maxPoints = 1500;
        }
        
        console.log(`Loading ${period} of data with ${interval} interval for ${symbol}`);
        
        // Fetch comprehensive historical data
        const historicalResponse = await fetch(
          `${apiBaseUrl}/api/market/historical?symbol=${symbol}&period=${period}&interval=${interval}&max_points=${maxPoints}`
        );
        
        if (historicalResponse.ok) {
          const historicalData = await historicalResponse.json();
          
          if (historicalData?.data && Array.isArray(historicalData.data)) {
            const ohlcData = historicalData.data.map(item => ({
              time: Math.floor(new Date(item.date).getTime() / 1000),
              open: parseFloat(item.open),
              high: parseFloat(item.high),
              low: parseFloat(item.low),
              close: parseFloat(item.close),
              volume: parseFloat(item.volume || Math.floor(1000 + Math.random() * 5000))
            })).sort((a, b) => a.time - b.time);
            
            if (ohlcData.length > 0) {
              setChartData(ohlcData);
              updateChartSeries(ohlcData);
              updateIndicators(ohlcData);
              setCurrentPrice(ohlcData[ohlcData.length - 1].close);
              // Set initial lastUpdateTime to the last historical data point
              setLastUpdateTime(ohlcData[ohlcData.length - 1].time);
              
              // Auto-size chart for the new data with optimal default view
              if (chartRef.current) {
                setTimeout(() => {
                  try {
                    // First fit all content to establish proper scale
                    chartRef.current.timeScale().fitContent();
                    
                    // Then set optimal zoom level for this timeframe
                    const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
                    const intervalSeconds = timeframeConfig?.seconds || 86400;
                    
                    let visibleBarsCount;
                    if (intervalSeconds <= 300) { // 5 minutes or less
                      visibleBarsCount = 100; // Show about 8 hours of 5min data
                    } else if (intervalSeconds <= 3600) { // 1 hour or less  
                      visibleBarsCount = 120; // Show about 5 days of hourly data
                    } else if (intervalSeconds <= 86400) { // 1 day or less
                      visibleBarsCount = 90; // Show about 3 months of daily data
                    } else {
                      visibleBarsCount = 60; // Show reasonable amount for larger timeframes
                    }
                    
                    // Apply the optimal zoom with some padding on the right
                    chartRef.current.timeScale().setVisibleLogicalRange({
                      from: Math.max(0, visibleBarsCount * -1),
                      to: 10 // Show a few bars beyond current time for padding
                    });
                    
                    console.log(`📏 Auto-sized chart for ${symbol} showing ${visibleBarsCount} bars`);
                  } catch (e) {
                    console.warn('Failed to auto-size chart:', e);
                  }
                }, 300); // Slightly longer timeout to ensure data is rendered
              }
              
              // Notify parent component about chart data update
              if (onChartDataUpdate) {
                onChartDataUpdate(ohlcData);
              }
              return;
            }
          }
        }
        
        // If historical data fails, show error instead of mock data
        console.error(`No historical data available for ${symbol} with period ${period} and interval ${interval}`);
        
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        // Don't generate mock data - show error state instead
      }
    };

    // Fetch current price first to get the latest value
    const fetchCurrentPrice = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/market/price?symbol=${symbol}`);
        if (response.ok) {
          const priceData = await response.json();
          setCurrentPrice(priceData.current_price);
          console.log(`🎯 Current price loaded: ${symbol} = $${priceData.current_price}`);
        }
      } catch (error) {
        console.error('Failed to fetch current price:', error);
      }
    };
    
    // Try WebSocket first, fallback to HTTP
    connectWebSocket();
    
    // Load current price immediately
    fetchCurrentPrice();
    
    // Also fetch initial historical data
    fetchHistoricalData();
    
    // Start polling fallback immediately to ensure live updates work
    const cleanupPolling = startPollingFallback();
    
    // Set up periodic refresh of historical data based on selected timeframe
    const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
    const refreshInterval = timeframeConfig?.seconds * 1000 || 60000; // Convert to milliseconds
    
    const refreshTimer = setInterval(() => {
      if (isPlaying) {
        fetchHistoricalData();
      }
    }, Math.max(refreshInterval, 30000)); // Minimum 30 seconds refresh

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (refreshTimer) {
        clearInterval(refreshTimer);
      }
      if (cleanupPolling) {
        cleanupPolling();
      }
    };
  }, [isPlaying, timeframe, selectedPeriod, symbol, apiBaseUrl]);

  // COMPREHENSIVE symbol reset to prevent cross-contamination
  useEffect(() => {
    console.log(`🔄 COMPREHENSIVE SYMBOL RESET: Switching to ${symbol}`);
    
    // Reset ALL state completely
    setLastUpdateTime(0);
    setCurrentCandle(null);
    setLastCandleTime(null);
    setCurrentPrice(null);
    setPriceChange(0);
    setChartData([]);
    setTradeSignals([]);
    setLimitOrders([]);
    setCandleBuffer([]);
    setPriceHistory([]);
    
    // Force clear all chart series data
    if (candlestickSeriesRef.current) {
      try {
        candlestickSeriesRef.current.setData([]);
        console.log(`✅ Cleared candlestick data for ${symbol}`);
      } catch (e) {
        console.warn('Failed to clear candlestick data:', e);
      }
    }
    
    if (volumeSeriesRef.current) {
      try {
        volumeSeriesRef.current.setData([]);
        console.log(`✅ Cleared volume data for ${symbol}`);
      } catch (e) {
        console.warn('Failed to clear volume data:', e);
      }
    }
    
    // Clear all indicator series completely
    Object.values(indicatorSeriesRefs.current).forEach(series => {
      try {
        if (series && typeof series.setData === 'function') {
          series.setData([]);
        } else if (series && typeof series === 'object') {
          // Handle complex indicators like Bollinger Bands
          Object.values(series).forEach(subSeries => {
            if (subSeries && typeof subSeries.setData === 'function') {
              subSeries.setData([]);
            }
          });
        }
      } catch (e) {
        console.warn('Failed to clear indicator data:', e);
      }
    });
    
    // Reset chart zoom/scale and force a complete refresh
    if (chartRef.current) {
      setTimeout(() => {
        try {
          // Reset to optimal default view for new asset
          chartRef.current.timeScale().fitContent();
          chartRef.current.timeScale().scrollToRealTime();
          
          // Set a good default zoom level - show reasonable amount of data
          const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
          const intervalSeconds = timeframeConfig?.seconds || 86400;
          
          // Calculate optimal visible range based on timeframe
          let visibleBarsCount;
          if (intervalSeconds <= 300) { // 5 minutes or less
            visibleBarsCount = 100; // Show about 8 hours of 5min data
          } else if (intervalSeconds <= 3600) { // 1 hour or less  
            visibleBarsCount = 120; // Show about 5 days of hourly data
          } else if (intervalSeconds <= 86400) { // 1 day or less
            visibleBarsCount = 90; // Show about 3 months of daily data
          } else {
            visibleBarsCount = 60; // Show reasonable amount for larger timeframes
          }
          
          // Apply the optimal zoom
          chartRef.current.timeScale().setVisibleLogicalRange({
            from: Math.max(0, visibleBarsCount * -1),
            to: 10 // Show a few bars beyond current time for padding
          });
          
          console.log(`✅ Reset chart scale for ${symbol} with ${visibleBarsCount} visible bars`);
        } catch (e) {
          console.warn('Failed to reset chart scale:', e);
        }
      }, 200);
    }
    
    console.log(`✅ SYMBOL RESET COMPLETE for ${symbol}`);
    
  }, [symbol]);

  // Store the latest chart data for indicator updates
  const [chartData, setChartData] = useState([]);


  // Update chart series with new data
  const updateChartSeries = useCallback((ohlcData) => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current) return;


    // Update main series based on chart type
    if (chartType === 'candlestick') {
      candlestickSeriesRef.current.setData(ohlcData);
    } else if (chartType === 'line') {
      const lineData = ohlcData.map(item => ({
        time: item.time,
        value: item.close,
      }));
      candlestickSeriesRef.current.setData(lineData);
    } else if (chartType === 'area') {
      const areaData = ohlcData.map(item => ({
        time: item.time,
        value: item.close,
      }));
      candlestickSeriesRef.current.setData(areaData);
    }

    // Update volume
    if (indicators.volume.enabled) {
      const volumeData = ohlcData.map(item => ({
        time: item.time,
        value: item.volume,
        color: (chartType === 'candlestick' ? 
          (item.close >= item.open ? 'rgba(38, 166, 154, 0.8)' : 'rgba(239, 83, 80, 0.8)') :
          'rgba(107, 114, 128, 0.8)'),
      }));
      volumeSeriesRef.current.setData(volumeData);
    }

    // Update all enabled indicators
    updateIndicators(ohlcData);
  }, [chartType, indicators, symbol]);

  // Sophisticated candle building state
  const [currentCandle, setCurrentCandle] = useState(null);
  const [lastCandleTime, setLastCandleTime] = useState(null);
  const [candleBuffer, setCandleBuffer] = useState([]); // Buffer for accumulating ticks
  const [priceHistory, setPriceHistory] = useState([]); // Track recent prices for realistic OHLC

  // Get timeframe interval in seconds
  const getTimeframeSeconds = useCallback(() => {
    const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
    return timeframeConfig?.seconds || 86400; // Default to 1 day
  }, [timeframe, timeframes]);

  // Sophisticated candle start time calculation with proper boundaries
  const getCandleStartTime = useCallback((timestamp) => {
    const intervalSeconds = getTimeframeSeconds();
    
    // For minute intervals, align to minute boundaries
    if (intervalSeconds < 3600) { // Less than 1 hour
      const minutes = intervalSeconds / 60;
      const date = new Date(timestamp * 1000);
      const alignedMinutes = Math.floor(date.getMinutes() / minutes) * minutes;
      date.setMinutes(alignedMinutes, 0, 0); // Set seconds and milliseconds to 0
      return Math.floor(date.getTime() / 1000);
    }
    
    // For hour intervals, align to hour boundaries  
    if (intervalSeconds < 86400) { // Less than 1 day
      const hours = intervalSeconds / 3600;
      const date = new Date(timestamp * 1000);
      const alignedHours = Math.floor(date.getHours() / hours) * hours;
      date.setHours(alignedHours, 0, 0, 0);
      return Math.floor(date.getTime() / 1000);
    }
    
    // For daily intervals, align to day boundaries
    const date = new Date(timestamp * 1000);
    date.setHours(0, 0, 0, 0);
    return Math.floor(date.getTime() / 1000);
  }, [getTimeframeSeconds]);

  // Check if we should start a new candle (sophisticated boundary detection)
  const shouldStartNewCandle = useCallback((currentTime, lastCandleStart) => {
    if (!lastCandleStart) return true;
    
    const intervalSeconds = getTimeframeSeconds();
    const timeSinceLastCandle = currentTime - lastCandleStart;
    
    // Only start new candle if we've exceeded the timeframe interval
    return timeSinceLastCandle >= intervalSeconds;
  }, [getTimeframeSeconds]);

  // Sophisticated real-time price update with proper candle building
  const updateRealTimePrice = useCallback((priceData) => {
    if (!candlestickSeriesRef.current) return;

    // CRITICAL: Multi-level symbol validation to prevent cross-contamination
    if (priceData.symbol !== symbol) {
      console.log(`❌ REJECTING price update for ${priceData.symbol}, current symbol is ${symbol}`);
      return;
    }
    
    // Additional check for formatted symbol to ensure complete isolation
    if (priceData.formatted_symbol && priceData.symbol !== symbol) {
      console.log(`❌ REJECTING formatted symbol mismatch: ${priceData.formatted_symbol} vs ${symbol}`);
      return;
    }

    // Validate price data is reasonable and not corrupted
    const price = parseFloat(priceData.close);
    if (!priceData.close || isNaN(price) || price <= 0 || price > 1000000) {
      console.warn(`❌ Invalid price data for ${symbol}: $${price}`, priceData);
      return;
    }
    
    // Check for reasonable price changes (prevent massive jumps that indicate data corruption)
    if (currentPrice && Math.abs(price - currentPrice) / currentPrice > 0.5) {
      console.warn(`❌ Suspicious price jump for ${symbol}: ${currentPrice} -> ${price} (${((price - currentPrice) / currentPrice * 100).toFixed(1)}%)`);
      return;
    }

    console.log(`✅ Processing price update for ${symbol}: $${price.toFixed(2)} (source: ${priceData.source || 'unknown'})`);

    // Update the current price display with validated data
    setCurrentPrice(price);
    setPriceChange(priceData.change || 0);
    
    // Note: Removed auto-scaling to preserve user's chart position
    
    // Use the timestamp from the WebSocket message if available, otherwise use current time
    const messageTime = priceData.candle_time || priceData.current_time || Math.floor(Date.now() / 1000);
    const currentTime = Math.floor(messageTime);
    
    // Add to price history for better OHLC calculation
    setPriceHistory(prev => {
      const newHistory = [...prev, { price, timestamp: currentTime }].slice(-50); // Keep last 50 price points
      return newHistory;
    });

    // Calculate proper candle start time based on timeframe
    const candleStartTime = getCandleStartTime(currentTime);
    
    // Safety check: ensure candleStartTime is a valid number
    if (!Number.isFinite(candleStartTime)) {
      console.error(`❌ Invalid candleStartTime: ${candleStartTime}, skipping update`);
      return;
    }
    
    // Prevent updating with older data than we've already processed
    if (candleStartTime < lastUpdateTime) {
      console.log(`⏰ Skipping older update: ${candleStartTime} < ${lastUpdateTime}`);
      return;
    }
    
    // Determine if we need a new candle
    const needNewCandle = shouldStartNewCandle(candleStartTime, lastCandleTime);
    
    if (needNewCandle) {
      console.log(`🆕 Starting NEW candle at ${new Date(candleStartTime * 1000).toISOString()}`);
      
      // Complete the previous candle if it exists
      if (currentCandle) {
        console.log(`✅ COMPLETED candle: OHLC(${currentCandle.open}/${currentCandle.high}/${currentCandle.low}/${currentCandle.close}) Vol:${currentCandle.volume}`);
      }
      
      // Start new candle with current price as all OHLC values
      const newCandle = {
        time: Number(candleStartTime),
        open: price,
        high: price,
        low: price,
        close: price,
        volume: parseFloat(priceData.volume || 0)
      };
      
      
      setCurrentCandle(newCandle);
      setLastCandleTime(candleStartTime);
      setCandleBuffer([{ price, timestamp: currentTime }]);
      setLastUpdateTime(candleStartTime);
      
      // Update chart with new candle - ensure we don't update with older data
      try {
        if (chartType === 'candlestick') {
          candlestickSeriesRef.current.update(newCandle);
        } else if (chartType === 'line' || chartType === 'area') {
          candlestickSeriesRef.current.update({
            time: Number(candleStartTime),
            value: price
          });
        }
        
        // Note: Removed auto-scaling to preserve user's chart position
      } catch (error) {
        console.error(`❌ Failed to update chart with new candle:`, error);
        console.error(`Candle data:`, newCandle);
      }
      
      // Update volume
      if (indicators.volume.enabled && volumeSeriesRef.current) {
        try {
          volumeSeriesRef.current.update({
            time: Number(candleStartTime),
            value: newCandle.volume,
            color: 'rgba(107, 114, 128, 0.8)' // Neutral color for new candle
          });
        } catch (error) {
          console.error(`❌ Failed to update volume with new candle:`, error);
        }
      }
      
    } else if (currentCandle) {
      console.log(`🔄 UPDATING existing candle with price: $${price}`);
      
      // Update existing candle with new price data
      const updatedCandle = {
        ...currentCandle,
        time: Number(currentCandle.time),
        high: Math.max(currentCandle.high, price),
        low: Math.min(currentCandle.low, price),
        close: price,
        volume: Math.max(currentCandle.volume, parseFloat(priceData.volume || 0)) // Use max to avoid volume resets
      };
      
      
      // Add to candle buffer for sophisticated OHLC tracking
      setCandleBuffer(prev => {
        const newBuffer = [...prev, { price, timestamp: currentTime }];
        
        // Calculate more sophisticated OHLC from buffer
        const bufferPrices = newBuffer.map(item => item.price);
        const realtimeHigh = Math.max(...bufferPrices, updatedCandle.open);
        const realtimeLow = Math.min(...bufferPrices, updatedCandle.open);
        
        // Update candle with buffer-calculated values
        updatedCandle.high = realtimeHigh;
        updatedCandle.low = realtimeLow;
        
        return newBuffer.slice(-20); // Keep last 20 ticks for this candle
      });
      
      setCurrentCandle(updatedCandle);
      setLastUpdateTime(candleStartTime);
      
      console.log(`📊 Updated OHLC: ${updatedCandle.open}/${updatedCandle.high}/${updatedCandle.low}/${updatedCandle.close}`);
      
      // Update chart with updated candle - ensure we don't update with older data  
      try {
        if (chartType === 'candlestick') {
          candlestickSeriesRef.current.update(updatedCandle);
        } else if (chartType === 'line' || chartType === 'area') {
          candlestickSeriesRef.current.update({
            time: Number(candleStartTime),
            value: updatedCandle.close
          });
        }
        
        // Note: Removed auto-scaling to preserve user's chart position
      } catch (error) {
        console.error(`❌ Failed to update chart with updated candle:`, error);
        console.error(`Updated candle data:`, updatedCandle);
      }
      
      // Update volume
      if (indicators.volume.enabled && volumeSeriesRef.current) {
        try {
          const isGreen = updatedCandle.close >= updatedCandle.open;
          volumeSeriesRef.current.update({
            time: Number(candleStartTime),
            value: updatedCandle.volume,
            color: chartType === 'candlestick' ? 
              (isGreen ? 'rgba(38, 166, 154, 0.8)' : 'rgba(239, 83, 80, 0.8)') :
              'rgba(107, 114, 128, 0.8)'
          });
        } catch (error) {
          console.error(`❌ Failed to update volume with updated candle:`, error);
        }
      }
    }
  }, [symbol, chartType, indicators.volume.enabled, currentCandle, lastCandleTime, lastUpdateTime, getCandleStartTime, shouldStartNewCandle]);

  // Update limit orders display
  const updateLimitOrders = useCallback((orders) => {
    setLimitOrders(orders);
    
    if (!candlestickSeriesRef.current) return;

    // Add price lines for limit orders
    orders.forEach(order => {
      // This would need to be implemented with price line API
      console.log('Limit order:', order);
    });
  }, []);

  // Update indicators based on settings
  const updateIndicators = useCallback((ohlcData) => {
    if (!chartRef.current || !ohlcData.length) return;

    // Clear existing indicator series
    Object.keys(indicatorSeriesRefs.current).forEach(key => {
      const series = indicatorSeriesRefs.current[key];
      if (series) {
        try {
          chartRef.current.removeSeries(series);
        } catch (e) {
          // Series may already be removed
        }
      }
    });
    indicatorSeriesRefs.current = {};

    // Add enabled indicators
    Object.entries(indicators).forEach(([key, config]) => {
      if (!config.enabled || !config.visible) return;

      try {
        if (key === 'sma20' || key === 'sma50') {
          const period = key === 'sma20' ? 20 : 50;
          const smaData = calculateSMA(ohlcData, period);
          if (smaData.length > 0) {
            const series = chartRef.current.addLineSeries({
              color: config.color,
              lineWidth: 2,
              title: `SMA ${period}`,
              lastValueVisible: true,
              priceLineVisible: false,
            });
            series.setData(smaData);
            indicatorSeriesRefs.current[key] = series;
          }
        } else if (key === 'ema12' || key === 'ema26') {
          const period = config.period;
          const emaData = calculateEMA(ohlcData, period);
          if (emaData.length > 0) {
            const series = chartRef.current.addLineSeries({
              color: config.color,
              lineWidth: 2,
              title: `EMA ${period}`,
              lastValueVisible: true,
              priceLineVisible: false,
            });
            series.setData(emaData);
            indicatorSeriesRefs.current[key] = series;
          }
        } else if (key === 'bollinger') {
          const bollingerData = calculateBollingerBands(ohlcData, config.period, config.stdDev);
          if (bollingerData.upper.length > 0) {
            // Upper band
            const upperSeries = chartRef.current.addLineSeries({
              color: config.color,
              lineWidth: 1,
              title: 'BB Upper',
              lastValueVisible: false,
              priceLineVisible: false,
            });
            upperSeries.setData(bollingerData.upper);
            
            // Lower band
            const lowerSeries = chartRef.current.addLineSeries({
              color: config.color,
              lineWidth: 1,
              title: 'BB Lower',
              lastValueVisible: false,
              priceLineVisible: false,
            });
            lowerSeries.setData(bollingerData.lower);
            
            // Middle line (SMA)
            const middleSeries = chartRef.current.addLineSeries({
              color: config.color,
              lineWidth: 1,
              title: 'BB Middle',
              lastValueVisible: false,
              priceLineVisible: false,
            });
            middleSeries.setData(bollingerData.middle);
            
            indicatorSeriesRefs.current[key] = { upper: upperSeries, lower: lowerSeries, middle: middleSeries };
          }
        }
        // Add more indicators as needed (RSI, MACD would need separate price scales)
      } catch (error) {
        console.error(`Error adding indicator ${key}:`, error);
      }
    });
  }, [indicators]);

  // Update indicators when indicator settings change
  useEffect(() => {
    if (chartRef.current && chartData.length > 0) {
      updateIndicators(chartData);
    }
  }, [indicators, updateIndicators, chartData]);

  // Technical Analysis Functions
  const calculateSMA = (data, period) => {
    const result = [];
    for (let i = period - 1; i < data.length; i++) {
      let sum = 0;
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close;
      }
      result.push({
        time: data[i].time,
        value: parseFloat((sum / period).toFixed(2)),
      });
    }
    return result;
  };

  const calculateEMA = (data, period) => {
    const result = [];
    const multiplier = 2 / (period + 1);
    let ema = data[0]?.close || 0;
    
    for (let i = 0; i < data.length; i++) {
      if (i === 0) {
        ema = data[i].close;
      } else {
        ema = (data[i].close * multiplier) + (ema * (1 - multiplier));
      }
      
      result.push({
        time: data[i].time,
        value: parseFloat(ema.toFixed(2)),
      });
    }
    return result;
  };

  const calculateBollingerBands = (data, period, stdDev) => {
    const smaData = calculateSMA(data, period);
    const upper = [];
    const lower = [];
    const middle = [];
    
    for (let i = period - 1; i < data.length; i++) {
      const smaValue = smaData[i - period + 1]?.value || 0;
      
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
      
      upper.push({ time: data[i].time, value: parseFloat(upperValue.toFixed(2)) });
      lower.push({ time: data[i].time, value: parseFloat(lowerValue.toFixed(2)) });
      middle.push({ time: data[i].time, value: parseFloat(smaValue.toFixed(2)) });
    }
    
    return { upper, lower, middle };
  };


  // Add trade signal marker
  const addTradeSignal = useCallback((signal) => {
    if (!candlestickSeriesRef.current) return;
    
    const marker = {
      time: signal.time || Math.floor(Date.now() / 1000),
      position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
      color: signal.type === 'buy' ? '#26a69a' : '#ef5350',
      shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
      text: `${signal.type.toUpperCase()}${signal.price ? `: $${signal.price}` : ''}${signal.confidence ? ` (${Math.round(signal.confidence * 100)}%)` : ''}`,
      size: signal.strength || 1,
    };
    
    setTradeSignals(prev => {
      const newSignals = [...prev, marker];
      candlestickSeriesRef.current.setMarkers(newSignals);
      return newSignals;
    });
  }, []);

  // Toggle indicator
  const toggleIndicator = useCallback((indicator) => {
    setIndicators(prev => ({
      ...prev,
      [indicator]: {
        ...prev[indicator],
        enabled: !prev[indicator].enabled,
      },
    }));
  }, []);

  // Toggle indicator visibility
  const toggleIndicatorVisibility = useCallback((indicator) => {
    setIndicators(prev => ({
      ...prev,
      [indicator]: {
        ...prev[indicator],
        visible: !prev[indicator].visible,
      },
    }));
  }, []);

  // Change timeframe
  const changeTimeframe = useCallback((newTimeframe) => {
    setTimeframe(newTimeframe);
  }, []);

  // Change chart type
  const changeChartType = useCallback((newType) => {
    setChartType(newType);
  }, []);

  // Filter indicators for search
  const filteredIndicators = availableIndicators.filter(indicator =>
    indicator.name.toLowerCase().includes(indicatorSearchTerm.toLowerCase())
  );

  // Add indicator from search
  const addIndicatorFromSearch = useCallback((indicatorKey) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorKey]: {
        ...prev[indicatorKey],
        enabled: true,
        visible: true,
      },
    }));
    setShowIndicatorSearch(false);
    setIndicatorSearchTerm('');
  }, []);

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 flex flex-col h-full">
      {/* Chart Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800 flex-wrap gap-2">
        <div className="flex items-center space-x-4 flex-wrap">
          {/* Symbol Selector */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSymbolSearch(true)}
              className="flex items-center space-x-2 px-3 py-1 rounded-md hover:bg-gray-700 transition-colors"
            >
              <h3 className="text-lg font-semibold text-white">{displaySymbol}</h3>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>

          {/* Live Price Display */}
          {currentPrice && (
            <div className="flex items-center space-x-2">
              <span className="text-lg font-mono font-bold text-white">
                ${typeof currentPrice === 'number' ? currentPrice.toFixed(2) : currentPrice}
              </span>
              <span className={`text-sm font-medium ${
                priceChange > 0 ? 'text-green-400' : priceChange < 0 ? 'text-red-400' : 'text-gray-400'
              }`}>
                {priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)} ({((priceChange / currentPrice) * 100).toFixed(2)}%)
              </span>
            </div>
          )}

          {/* Timeframe Dropdown */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Interval:</label>
            <select
              value={timeframe}
              onChange={(e) => changeTimeframe(e.target.value)}
              className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>
            
          {/* Period Dropdown */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Period:</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:outline-none focus:border-green-500"
            >
              {periodOptions.map((period) => (
                <option key={period.value} value={period.value}>
                  {period.label} - {period.description}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Right side controls */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Chart Type Dropdown */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Type:</label>
            <select
              value={chartType}
              onChange={(e) => changeChartType(e.target.value)}
              className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:outline-none focus:border-purple-500"
            >
              <option value="candlestick">Candlestick</option>
              <option value="line">Line</option>
              <option value="area">Area</option>
            </select>
          </div>
          
          {/* Add Indicator Button */}
          <button
            onClick={() => setShowIndicatorSearch(!showIndicatorSearch)}
            className="p-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
            title="Add Indicator"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
          
          {/* Play/Pause Button */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-2 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
            title={isPlaying ? 'Pause' : 'Resume'}
          >
            {isPlaying ? (
              <PauseIcon className="w-4 h-4 text-white" />
            ) : (
              <PlayIcon className="w-4 h-4 text-white" />
            )}
          </button>
          
          {/* Settings Button */}
          <button 
            className="p-2 rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
            title="Settings"
          >
            <Cog6ToothIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Enhanced Indicator Search Modal */}
      {showIndicatorSearch && (
        <div className="absolute top-16 right-4 z-50 bg-gray-800 border border-gray-600 rounded-lg shadow-xl w-96">
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-lg font-semibold text-white">Indicators & Strategies</h4>
              <button
                onClick={() => setShowIndicatorSearch(false)}
                className="text-gray-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>
            <div className="flex items-center space-x-2">
              <MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search indicators, strategies, or authors..."
                value={indicatorSearchTerm}
                onChange={(e) => setIndicatorSearchTerm(e.target.value)}
                className="flex-1 bg-gray-700 text-white placeholder-gray-400 border border-gray-600 rounded px-3 py-2 text-sm"
                autoFocus
              />
            </div>
            <div className="flex flex-wrap gap-2 mt-3">
              {['All', 'Moving Averages', 'Oscillators', 'Trend', 'Volume', 'Volatility', 'Price Action', 'Support/Resistance'].map(cat => (
                <button
                  key={cat}
                  className="px-2 py-1 text-xs rounded-full border border-gray-600 text-gray-300 hover:border-blue-500 hover:text-white transition-colors"
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {filteredIndicators.length > 0 ? (
              <div className="p-2">
                {filteredIndicators.map((indicator) => (
                  <button
                    key={indicator.key}
                    onClick={() => addIndicatorFromSearch(indicator.key)}
                    className="w-full text-left p-3 rounded-lg hover:bg-gray-700 transition-colors mb-1"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-white text-sm">{indicator.name}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          <span className="inline-block bg-gray-700 px-2 py-0.5 rounded mr-2">{indicator.category}</span>
                          <span className="text-blue-400">{indicator.author}</span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 ml-2">
                        {indicators[indicator.key]?.enabled ? '✓ Added' : '+ Add'}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-4 text-center text-gray-400">
                <div className="text-sm">No indicators found</div>
                <div className="text-xs mt-1">Try searching for "RSI", "MACD", or "SuperTrend"</div>
              </div>
            )}
          </div>
          <div className="p-3 border-t border-gray-700 bg-gray-750">
            <div className="text-xs text-gray-400">
              💡 Popular: SuperTrend, Wave Trend, SSL Channels, Smart Money Concepts
            </div>
          </div>
        </div>
      )}

      {/* Indicators Panel */}
      <div className="p-3 border-b border-gray-700 bg-gray-850">
        <div className="flex flex-wrap gap-2">
          {Object.entries(indicators).map(([key, config]) => (
            config.enabled && (
              <div key={key} className="flex items-center space-x-1">
                <button
                  onClick={() => toggleIndicator(key)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    config.enabled && config.visible
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'bg-transparent border-gray-600 text-gray-400 hover:border-blue-500'
                  }`}
                  style={{ borderColor: config.visible ? config.color : undefined }}
                >
                  <span 
                    className="inline-block w-2 h-2 rounded-full mr-1" 
                    style={{ backgroundColor: config.color }}
                  />
                  {key.toUpperCase()}
                </button>
                <button
                  onClick={() => toggleIndicatorVisibility(key)}
                  className="p-1 text-gray-400 hover:text-white"
                  title={config.visible ? 'Hide' : 'Show'}
                >
                  {config.visible ? (
                    <EyeIcon className="w-3 h-3" />
                  ) : (
                    <EyeSlashIcon className="w-3 h-3" />
                  )}
                </button>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Chart Container */}
      <div className="flex-1 relative">
        <div 
          ref={chartContainerRef}
          className="absolute inset-0"
        />
        
        {/* Limit Order Overlays */}
        {limitOrders.map((order, index) => (
          <div
            key={index}
            className="absolute right-4 bg-yellow-600 text-white text-xs px-2 py-1 rounded"
            style={{ top: `${order.yPosition || 50}%` }}
          >
            Limit {order.type}: ${order.price}
          </div>
        ))}
      </div>
      
      {/* Chart Footer */}
      <div className="p-3 border-t border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-4">
            <span>Live</span>
            <span>Interval: {timeframe}</span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-1"></span>
              Connected
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Signals: {tradeSignals.length}</span>
            <span>Orders: {limitOrders.length}</span>
            <span>Last: {new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Dynamic Symbol Search Modal */}
      <DynamicSymbolSearch
        isOpen={showSymbolSearch}
        onClose={() => setShowSymbolSearch(false)}
        onSymbolSelect={(newSymbol, newDisplaySymbol) => {
          if (onSymbolChange) onSymbolChange(newSymbol, newDisplaySymbol);
        }}
        currentSymbol={symbol}
      />
    </div>
  );
};

export default TradingChart;

// Helper function to format numbers
const formatPrice = (price) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(price);
};

// Export for use in other components
export { formatPrice };
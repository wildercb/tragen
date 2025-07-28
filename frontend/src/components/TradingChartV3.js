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

const TradingChartV3 = ({ 
  symbol = 'NQ=F', 
  displaySymbol = 'NQ', 
  height = 600, 
  apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000', 
  onSignalReceived, 
  onSymbolChange, 
  onChartDataUpdate 
}) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRefs = useRef({});
  
  // Chart state
  const [isPlaying, setIsPlaying] = useState(true);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [timeframe, setTimeframe] = useState('5m');
  const [selectedPeriod, setSelectedPeriod] = useState('1d');
  const [chartType, setChartType] = useState('candlestick');
  const [showDrawingTools, setShowDrawingTools] = useState(false);
  const [showIndicatorSearch, setShowIndicatorSearch] = useState(false);
  const [indicatorSearchTerm, setIndicatorSearchTerm] = useState('');
  
  // Data state
  const [chartData, setChartData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [tradeSignals, setTradeSignals] = useState([]);
  const [limitOrders, setLimitOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dataSource, setDataSource] = useState('live'); // 'live', 'cached', 'fallback'
  
  // Real-time update state
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  const [updateCount, setUpdateCount] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // WebSocket refs
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const updateIntervalRef = useRef(null);

  // Professional timeframe configuration with proper intervals
  const timeframes = [
    { value: '1m', label: '1m', seconds: 60, description: '1 Minute' },
    { value: '3m', label: '3m', seconds: 180, description: '3 Minutes' },
    { value: '5m', label: '5m', seconds: 300, description: '5 Minutes' },
    { value: '15m', label: '15m', seconds: 900, description: '15 Minutes' },
    { value: '30m', label: '30m', seconds: 1800, description: '30 Minutes' },
    { value: '1h', label: '1h', seconds: 3600, description: '1 Hour' },
    { value: '2h', label: '2h', seconds: 7200, description: '2 Hours' },
    { value: '4h', label: '4h', seconds: 14400, description: '4 Hours' },
    { value: '6h', label: '6h', seconds: 21600, description: '6 Hours' },
    { value: '12h', label: '12h', seconds: 43200, description: '12 Hours' },
    { value: '1d', label: '1D', seconds: 86400, description: '1 Day' },
    { value: '1wk', label: '1W', seconds: 604800, description: '1 Week' },
    { value: '1mo', label: '1M', seconds: 2629746, description: '1 Month' },
  ];

  // Period options optimized for each timeframe
  const getPeriodOptions = useCallback((currentTimeframe) => {
    const tf = timeframes.find(t => t.value === currentTimeframe);
    if (!tf) return [{ value: '1d', label: '1D' }];
    
    if (tf.seconds <= 300) { // 5 minutes or less
      return [
        { value: '1d', label: '1D', bars: 288 },
        { value: '3d', label: '3D', bars: 864 },
        { value: '1wk', label: '1W', bars: 2016 },
        { value: '1mo', label: '1M', bars: 8640 },
      ];
    } else if (tf.seconds <= 3600) { // 1 hour or less
      return [
        { value: '1d', label: '1D', bars: 48 },
        { value: '1wk', label: '1W', bars: 336 },
        { value: '1mo', label: '1M', bars: 1440 },
        { value: '3mo', label: '3M', bars: 4320 },
        { value: '1y', label: '1Y', bars: 17520 },
      ];
    } else if (tf.seconds <= 86400) { // 1 day or less
      return [
        { value: '1mo', label: '1M', bars: 30 },
        { value: '3mo', label: '3M', bars: 90 },
        { value: '6mo', label: '6M', bars: 180 },
        { value: '1y', label: '1Y', bars: 365 },
        { value: '2y', label: '2Y', bars: 730 },
        { value: '5y', label: '5Y', bars: 1825 },
      ];
    } else {
      return [
        { value: '1y', label: '1Y', bars: 52 },
        { value: '2y', label: '2Y', bars: 104 },
        { value: '5y', label: '5Y', bars: 260 },
        { value: '10y', label: '10Y', bars: 520 },
        { value: 'max', label: 'MAX', bars: 1000 },
      ];
    }
  }, [timeframes]);

  const [indicators, setIndicators] = useState({
    sma20: { enabled: true, visible: true, color: '#f59e0b', period: 20 },
    sma50: { enabled: true, visible: true, color: '#8b5cf6', period: 50 },
    ema12: { enabled: false, visible: true, color: '#06b6d4', period: 12 },
    ema26: { enabled: false, visible: true, color: '#f97316', period: 26 },
    volume: { enabled: true, visible: true, color: '#6b7280' },
  });

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
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      leftPriceScale: { visible: false },
      timeScale: {
        borderColor: '#374151',
        textColor: '#9ca3af',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12,
        barSpacing: 6,
        minBarSpacing: 3,
        fixLeftEdge: false,
        fixRightEdge: false,
        lockVisibleTimeRangeOnResize: true,
        tickMarkFormatter: (time) => {
          const date = new Date(time * 1000);
          const tf = timeframes.find(t => t.value === timeframe);
          
          if (tf?.seconds < 3600) { // Less than 1 hour
            return date.toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit',
              hour12: false 
            });
          } else if (tf?.seconds < 86400) { // Less than 1 day
            return date.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric',
              hour: '2-digit'
            });
          } else {
            return date.toLocaleDateString('en-US', { 
              month: 'short', 
              day: 'numeric'
            });
          }
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
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
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
    if (indicators.volume.enabled) {
      const volumeSeries = chart.addHistogramSeries({
        color: 'rgba(107, 114, 128, 0.8)',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      volumeSeriesRef.current = volumeSeries;

      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
        mode: PriceScaleMode.Percentage,
      });
    }

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
  }, [height, chartType, timeframe]);

  // Clean up on symbol change
  useEffect(() => {
    console.log(`🔄 Symbol changed to ${symbol}, resetting chart state`);
    
    // Reset all state
    setChartData([]);
    setCurrentPrice(null);
    setPriceChange(0);
    setTradeSignals([]);
    setLimitOrders([]);
    setLastUpdateTime(0);
    setUpdateCount(0);
    setDataSource('live');
    
    // Clear chart data
    if (candlestickSeriesRef.current) {
      try {
        candlestickSeriesRef.current.setData([]);
      } catch (e) {
        console.warn('Failed to clear candlestick data:', e);
      }
    }
    
    if (volumeSeriesRef.current) {
      try {
        volumeSeriesRef.current.setData([]);
      } catch (e) {
        console.warn('Failed to clear volume data:', e);
      }
    }

    // Clear indicators
    Object.values(indicatorSeriesRefs.current).forEach(series => {
      try {
        if (series && typeof series.setData === 'function') {
          series.setData([]);
        }
      } catch (e) {
        console.warn('Failed to clear indicator data:', e);
      }
    });
    
  }, [symbol]);

  // Enhanced data fetching with proper interval handling
  const fetchMarketData = useCallback(async (forceRefresh = false) => {
    if (!symbol || !timeframe) return;
    
    setIsLoading(true);
    
    try {
      console.log(`📊 Fetching data for ${symbol} at ${timeframe} interval`);
      
      // Calculate optimal period based on timeframe
      const tf = timeframes.find(t => t.value === timeframe);
      const periodOptions = getPeriodOptions(timeframe);
      const currentPeriod = selectedPeriod || periodOptions[0]?.value || '1d';
      
      // Make API request with explicit interval
      const params = new URLSearchParams({
        symbol: symbol,
        period: currentPeriod,
        interval: timeframe, // Use exact timeframe from frontend
        max_points: '2000',
        force_refresh: forceRefresh.toString()
      });
      
      const response = await fetch(`${apiBaseUrl}/api/market/historical?${params}`);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data?.data || !Array.isArray(data.data)) {
        throw new Error('Invalid data format received');
      }

      // Process and validate the data
      const ohlcData = data.data
        .map(item => ({
          time: Math.floor(new Date(item.date).getTime() / 1000),
          open: parseFloat(item.open),
          high: parseFloat(item.high),
          low: parseFloat(item.low),
          close: parseFloat(item.close),
          volume: parseFloat(item.volume || 0)
        }))
        .filter(item => 
          !isNaN(item.time) && 
          !isNaN(item.open) && 
          !isNaN(item.high) && 
          !isNaN(item.low) && 
          !isNaN(item.close) &&
          item.high >= item.low &&
          item.high >= Math.max(item.open, item.close) &&
          item.low <= Math.min(item.open, item.close)
        )
        .sort((a, b) => a.time - b.time);

      if (ohlcData.length === 0) {
        throw new Error('No valid data points received');
      }

      console.log(`✅ Loaded ${ohlcData.length} data points for ${symbol} ${timeframe}`);
      
      // Update chart data
      setChartData(ohlcData);
      setCurrentPrice(ohlcData[ohlcData.length - 1].close);
      setLastUpdateTime(ohlcData[ohlcData.length - 1].time);
      setDataSource(data.source || 'live');
      
      // Update chart series
      updateChartSeries(ohlcData);
      
      // Auto-size chart for new data
      autoSizeChart('data_load');
      
      // Notify parent component
      if (onChartDataUpdate) {
        onChartDataUpdate(ohlcData);
      }
      
    } catch (error) {
      console.error('Failed to fetch market data:', error);
      setDataSource('error');
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe, selectedPeriod, apiBaseUrl, getPeriodOptions]);

  // Get optimal visible bars for timeframe
  const getOptimalVisibleBars = useCallback((timeframe) => {
    const tf = timeframes.find(t => t.value === timeframe);
    if (!tf) return 100;
    
    if (tf.seconds <= 300) return 100; // 5min: ~8 hours
    if (tf.seconds <= 900) return 120; // 15min: ~30 hours  
    if (tf.seconds <= 3600) return 100; // 1h: ~4 days
    if (tf.seconds <= 14400) return 90; // 4h: ~15 days
    if (tf.seconds <= 86400) return 60; // 1d: ~2 months
    return 50; // Weekly/Monthly: reasonable view
  }, [timeframes]);

  // Auto-size chart with optimal zoom for current timeframe
  const autoSizeChart = useCallback((reason = 'manual') => {
    if (!chartRef.current || !chartData.length) return;
    
    setTimeout(() => {
      try {
        // First fit all content to establish proper scale
        chartRef.current.timeScale().fitContent();
        
        // Then set optimal zoom for current timeframe
        const visibleBars = getOptimalVisibleBars(timeframe);
        chartRef.current.timeScale().setVisibleLogicalRange({
          from: Math.max(0, chartData.length - visibleBars),
          to: chartData.length + 5
        });
        
        console.log(`📏 Auto-sized chart (${reason}) showing ${visibleBars} bars for ${timeframe}`);
      } catch (e) {
        console.warn(`Failed to auto-size chart (${reason}):`, e);
      }
    }, reason === 'data_load' ? 300 : 100); // Longer wait for data loads
  }, [chartRef, chartData, timeframe, getOptimalVisibleBars]);

  // Update chart series
  const updateChartSeries = useCallback((ohlcData) => {
    if (!candlestickSeriesRef.current || !ohlcData.length) return;

    try {
      // Update main series
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
      if (indicators.volume.enabled && volumeSeriesRef.current) {
        const volumeData = ohlcData.map(item => ({
          time: item.time,
          value: item.volume,
          color: chartType === 'candlestick' ? 
            (item.close >= item.open ? 'rgba(38, 166, 154, 0.8)' : 'rgba(239, 83, 80, 0.8)') :
            'rgba(107, 114, 128, 0.8)',
        }));
        volumeSeriesRef.current.setData(volumeData);
      }

      // Update indicators
      updateIndicators(ohlcData);
      
    } catch (error) {
      console.error('Failed to update chart series:', error);
    }
  }, [chartType, indicators.volume.enabled]);

  // Enhanced WebSocket connection with 5-second updates
  useEffect(() => {
    if (!isPlaying || !symbol) return;

    let ws;
    let reconnectTimeout;
    let priceUpdateInterval;

    const connectWebSocket = () => {
      try {
        const wsBaseUrl = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000';
        const wsUrl = `${wsBaseUrl}/api/ws/market/${encodeURIComponent(symbol)}`;
        
        console.log(`🔗 Connecting WebSocket for ${symbol}...`);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log(`✅ WebSocket connected for ${symbol}`);
          setConnectionStatus('connected');
          
          // Send subscription message with timeframe
          ws.send(JSON.stringify({
            type: 'subscribe',
            symbol: symbol,
            timeframe: timeframe,
            interval: 5000 // 5-second updates
          }));
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          
          if (data.symbol !== symbol) {
            console.log(`❌ Ignoring data for ${data.symbol}, current: ${symbol}`);
            return;
          }
          
          if (data.type === 'price_update') {
            handleRealTimeUpdate(data);
          } else if (data.type === 'historical_data') {
            handleHistoricalData(data);
          } else if (data.type === 'trading_signal') {
            handleTradingSignal(data);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('error');
        };

        ws.onclose = () => {
          console.log(`🔌 WebSocket disconnected for ${symbol}`);
          setConnectionStatus('disconnected');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
        
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setConnectionStatus('error');
        
        // Fallback to HTTP polling with 5-second intervals
        startPollingFallback();
      }
    };

    // HTTP polling fallback with 5-second updates
    const startPollingFallback = () => {
      console.log(`🔄 Starting 5-second polling for ${symbol}`);
      setConnectionStatus('polling');
      
      priceUpdateInterval = setInterval(async () => {
        try {
          const response = await fetch(`${apiBaseUrl}/api/market/price?symbol=${symbol}`);
          if (response.ok) {
            const priceData = await response.json();
            handleRealTimeUpdate({
              type: 'price_update',
              symbol: priceData.symbol,
              close: priceData.current_price,
              volume: priceData.volume,
              timestamp: Date.now(),
              source: 'polling'
            });
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 5000); // 5-second intervals
    };

    // Start connection
    connectWebSocket();
    
    // Also start the primary data fetch
    fetchMarketData();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (priceUpdateInterval) {
        clearInterval(priceUpdateInterval);
      }
    };
  }, [symbol, timeframe, selectedPeriod, isPlaying, apiBaseUrl, fetchMarketData]);

  // Handle real-time price updates
  const handleRealTimeUpdate = useCallback((data) => {
    if (!data.close || data.symbol !== symbol) return;
    
    const price = parseFloat(data.close);
    if (isNaN(price) || price <= 0) return;
    
    console.log(`💰 Real-time update: ${symbol} = $${price.toFixed(2)}`);
    
    setCurrentPrice(price);
    setUpdateCount(prev => prev + 1);
    setLastUpdateTime(Math.floor(Date.now() / 1000));
    
    // Update the current candle if we have chart data
    if (chartData.length > 0 && candlestickSeriesRef.current) {
      const lastCandle = chartData[chartData.length - 1];
      const now = Math.floor(Date.now() / 1000);
      const tf = timeframes.find(t => t.value === timeframe);
      const intervalSeconds = tf?.seconds || 300;
      
      // Check if we need a new candle
      const candleStartTime = Math.floor(now / intervalSeconds) * intervalSeconds;
      
      if (candleStartTime > lastCandle.time) {
        // Create new candle
        const newCandle = {
          time: candleStartTime,
          open: price,
          high: price,
          low: price,
          close: price,
          volume: parseFloat(data.volume || 0)
        };
        
        try {
          if (chartType === 'candlestick') {
            candlestickSeriesRef.current.update(newCandle);
          } else if (chartType === 'line' || chartType === 'area') {
            candlestickSeriesRef.current.update({
              time: candleStartTime,
              value: price
            });
          }
          
          console.log(`🆕 New candle created at ${new Date(candleStartTime * 1000).toISOString()}`);
        } catch (error) {
          console.error('Failed to create new candle:', error);
        }
      } else {
        // Update existing candle
        const updatedCandle = {
          time: lastCandle.time,
          open: lastCandle.open,
          high: Math.max(lastCandle.high, price),
          low: Math.min(lastCandle.low, price),
          close: price,
          volume: Math.max(lastCandle.volume, parseFloat(data.volume || 0))
        };
        
        try {
          if (chartType === 'candlestick') {
            candlestickSeriesRef.current.update(updatedCandle);
          } else if (chartType === 'line' || chartType === 'area') {
            candlestickSeriesRef.current.update({
              time: lastCandle.time,
              value: price
            });
          }
        } catch (error) {
          console.error('Failed to update candle:', error);
        }
      }
    }
  }, [symbol, chartData, timeframe, chartType, timeframes]);

  // Handle historical data from WebSocket
  const handleHistoricalData = useCallback((data) => {
    if (data.data?.data) {
      const ohlcData = data.data.data.map(item => ({
        time: Math.floor(new Date(item.date).getTime() / 1000),
        open: parseFloat(item.open),
        high: parseFloat(item.high),
        low: parseFloat(item.low),
        close: parseFloat(item.close),
        volume: parseFloat(item.volume || 0)
      })).sort((a, b) => a.time - b.time);
      
      if (ohlcData.length > 0) {
        setChartData(ohlcData);
        updateChartSeries(ohlcData);
        setCurrentPrice(ohlcData[ohlcData.length - 1].close);
        
        // Auto-size chart for WebSocket historical data
        autoSizeChart('websocket_data');
      }
    }
  }, [updateChartSeries, autoSizeChart]);

  // Handle trading signals
  const handleTradingSignal = useCallback((data) => {
    if (data.signal) {
      addTradeSignal(data.signal);
      if (onSignalReceived) {
        onSignalReceived(data.signal);
      }
    }
  }, [onSignalReceived]);

  // Add trade signal marker
  const addTradeSignal = useCallback((signal) => {
    if (!candlestickSeriesRef.current) return;
    
    const marker = {
      time: signal.time || Math.floor(Date.now() / 1000),
      position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
      color: signal.type === 'buy' ? '#26a69a' : '#ef5350',
      shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
      text: `${signal.type.toUpperCase()}${signal.price ? `: $${signal.price}` : ''}`,
      size: signal.strength || 1,
    };
    
    setTradeSignals(prev => {
      const newSignals = [...prev, marker];
      candlestickSeriesRef.current.setMarkers(newSignals);
      return newSignals;
    });
  }, []);

  // Update indicators
  const updateIndicators = useCallback((ohlcData) => {
    if (!chartRef.current || !ohlcData.length) return;

    // Clear existing indicators
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
      if (!config.enabled || !config.visible || key === 'volume') return;

      try {
        if (key === 'sma20' || key === 'sma50') {
          const period = config.period;
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
        }
      } catch (error) {
        console.error(`Error adding indicator ${key}:`, error);
      }
    });
  }, [indicators]);

  // Technical analysis functions
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

  // Control functions
  const changeTimeframe = useCallback((newTimeframe) => {
    console.log(`📊 Changing timeframe from ${timeframe} to ${newTimeframe}`);
    setTimeframe(newTimeframe);
    
    // Reset period to first available option for new timeframe
    const periodOptions = getPeriodOptions(newTimeframe);
    setSelectedPeriod(periodOptions[0]?.value || '1d');
    
    // Auto-resize chart for new timeframe after data loads
    setTimeout(() => autoSizeChart('timeframe_change'), 500);
  }, [timeframe, getPeriodOptions, autoSizeChart]);

  const changeChartType = useCallback((newType) => {
    console.log(`📊 Changing chart type from ${chartType} to ${newType}`);
    setChartType(newType);
    
    // Auto-resize chart for new chart type
    setTimeout(() => autoSizeChart('chart_type_change'), 200);
  }, [chartType, autoSizeChart]);

  const changePeriod = useCallback((newPeriod) => {
    console.log(`📊 Changing period from ${selectedPeriod} to ${newPeriod}`);
    setSelectedPeriod(newPeriod);
    
    // Auto-resize chart for new period after data loads
    setTimeout(() => autoSizeChart('period_change'), 500);
  }, [selectedPeriod, autoSizeChart]);

  const toggleIndicator = useCallback((indicator) => {
    setIndicators(prev => ({
      ...prev,
      [indicator]: {
        ...prev[indicator],
        enabled: !prev[indicator].enabled,
      },
    }));
  }, []);

  // Get connection status indicator
  const getConnectionIndicator = () => {
    switch (connectionStatus) {
      case 'connected':
        return { color: 'bg-green-400', text: 'Live WebSocket' };
      case 'polling':
        return { color: 'bg-yellow-400', text: 'Live Polling' };
      case 'error':
        return { color: 'bg-red-400', text: 'Connection Error' };
      default:
        return { color: 'bg-gray-400', text: 'Disconnected' };
    }
  };

  const connectionInfo = getConnectionIndicator();

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

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Interval:</label>
            <select
              value={timeframe}
              onChange={(e) => changeTimeframe(e.target.value)}
              className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label} - {tf.description}
                </option>
              ))}
            </select>
          </div>
            
          {/* Period Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400">Period:</label>
            <select
              value={selectedPeriod}
              onChange={(e) => changePeriod(e.target.value)}
              className="bg-gray-700 text-white text-xs px-2 py-1 rounded border border-gray-600 focus:outline-none focus:border-green-500"
            >
              {getPeriodOptions(timeframe).map((period) => (
                <option key={period.value} value={period.value}>
                  {period.label} ({period.bars} bars)
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* Right side controls */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Data Source Indicator */}
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-gray-400">Source:</span>
            <span className={`px-2 py-1 rounded text-xs ${
              dataSource === 'live' ? 'bg-green-600 text-white' :
              dataSource === 'cached' ? 'bg-yellow-600 text-white' :
              dataSource === 'fallback' ? 'bg-orange-600 text-white' :
              'bg-red-600 text-white'
            }`}>
              {dataSource.toUpperCase()}
            </span>
          </div>
          
          {/* Chart Type */}
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
          
          {/* Play/Pause */}
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

          {/* Refresh Button */}
          <button
            onClick={() => fetchMarketData(true)}
            disabled={isLoading}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Refresh Data"
          >
            <svg className={`w-4 h-4 text-gray-300 ${isLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          {/* Fit to Data Button */}
          <button
            onClick={() => autoSizeChart('manual')}
            disabled={!chartData.length}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Fit Chart to Data"
          >
            <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
      </div>

      {/* Indicators Panel */}
      <div className="p-2 border-b border-gray-700 bg-gray-850">
        <div className="flex flex-wrap gap-2 items-center">
          {Object.entries(indicators).map(([key, config]) => (
            config.enabled && key !== 'volume' && (
              <button
                key={key}
                onClick={() => toggleIndicator(key)}
                className={`px-2 py-1 text-xs rounded border transition-colors ${
                  config.visible
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
        
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-gray-800 p-4 rounded-lg flex items-center space-x-3">
              <svg className="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="text-white">Loading market data...</span>
            </div>
          </div>
        )}
      </div>
      
      {/* Chart Footer */}
      <div className="p-3 border-t border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-4">
            <span className="flex items-center">
              <span className={`w-2 h-2 ${connectionInfo.color} rounded-full mr-1`}></span>
              {connectionInfo.text}
            </span>
            <span>Interval: {timeframe}</span>
            <span>Updates: {updateCount}</span>
          </div>
          <div className="flex items-center space-x-4">
            <span>Bars: {chartData.length}</span>
            <span>Signals: {tradeSignals.length}</span>
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

export default TradingChartV3;
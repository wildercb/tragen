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
import SymbolSearch from './SymbolSearch';

const TradingChart = ({ symbol = 'NQ=F', displaySymbol = 'NQ', height = 600, apiBaseUrl = '', onSignalReceived, onSymbolChange }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRefs = useRef({});
  
  const [isPlaying, setIsPlaying] = useState(true);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [timeframe, setTimeframe] = useState('1d');
  const [selectedPeriod, setSelectedPeriod] = useState('1y');
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
  const [, setChartData] = useState([]);
  
  // Available symbols for future multi-asset support
  const availableSymbols = [
    { symbol: 'NQ=F', display: 'NQ', name: 'NASDAQ-100 E-mini Future', category: 'Futures' },
    { symbol: 'ES=F', display: 'ES', name: 'S&P 500 E-mini Future', category: 'Futures' },
    { symbol: 'YM=F', display: 'YM', name: 'Dow Jones E-mini Future', category: 'Futures' },
    { symbol: 'RTY=F', display: 'RTY', name: 'Russell 2000 E-mini Future', category: 'Futures' },
    { symbol: 'AAPL', display: 'AAPL', name: 'Apple Inc.', category: 'Stocks' },
    { symbol: 'TSLA', display: 'TSLA', name: 'Tesla Inc.', category: 'Stocks' },
    { symbol: 'NVDA', display: 'NVDA', name: 'NVIDIA Corporation', category: 'Stocks' },
    { symbol: 'SPY', display: 'SPY', name: 'SPDR S&P 500 ETF', category: 'ETFs' },
    { symbol: 'QQQ', display: 'QQQ', name: 'Invesco QQQ Trust', category: 'ETFs' },
  ];

  // Available timeframes with enhanced data coverage
  const timeframes = [
    { value: '1m', label: '1m', seconds: 60, description: '5 days' },
    { value: '5m', label: '5m', seconds: 300, description: '5 days' },
    { value: '15m', label: '15m', seconds: 900, description: '1 month' },
    { value: '30m', label: '30m', seconds: 1800, description: '1 month' },
    { value: '1h', label: '1H', seconds: 3600, description: '3 months' },
    { value: '4h', label: '4H', seconds: 14400, description: '1 year' },
    { value: '1d', label: '1D', seconds: 86400, description: 'All data' },
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

  // WebSocket connection for real-time data
  useEffect(() => {
    if (!isPlaying || !candlestickSeriesRef.current) return;

    let ws;
    let reconnectTimeout;

    const connectWebSocket = () => {
      try {
        // Try to connect to WebSocket for real-time data
        ws = new WebSocket(`ws://localhost:8001/ws/market/${symbol}`);
        
        ws.onopen = () => {
          console.log('WebSocket connected for real-time data');
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === 'price_update') {
            updateRealTimePrice(data);
          } else if (data.type === 'signal') {
            addTradeSignal(data.signal);
            if (onSignalReceived) {
              onSignalReceived(data.signal);
            }
          } else if (data.type === 'limit_order') {
            updateLimitOrders(data.orders);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected, attempting to reconnect...');
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        fetchHistoricalData();
      }
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
        
        // For minute intervals, limit the period to prevent too much data
        if ((interval === '1m' || interval === '5m') && ['max', '10y', '5y', '2y', '1y'].includes(period)) {
          period = '5d';
          maxPoints = 1000;
        } else if ((interval === '15m' || interval === '30m') && ['max', '10y', '5y', '2y'].includes(period)) {
          period = '1mo';
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
              setCurrentPrice(ohlcData[ohlcData.length - 1].close);
              return;
            }
          }
        }
        
        // Fallback to current price endpoint
        const response = await fetch(`${apiBaseUrl}/api/market/nq-price`);
        if (response.ok) {
          const data = await response.json();
          setCurrentPrice(data.current_price);
          
          // Generate mock data for demo
          const now = Date.now() / 1000;
          const mockData = generateMockOHLCData(data.current_price, now);
          setChartData(mockData);
          updateChartSeries(mockData);
        } else {
          throw new Error('Failed to fetch current price');
        }
        
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        // Generate mock data as last resort
        const now = Date.now() / 1000;
        const mockData = generateMockOHLCData(16500, now);
        setChartData(mockData);
        updateChartSeries(mockData);
        setCurrentPrice(16500);
      }
    };

    // Try WebSocket first, fallback to HTTP
    connectWebSocket();
    
    // Also fetch initial historical data
    fetchHistoricalData();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
    };
  }, [isPlaying, timeframe, selectedPeriod, symbol, apiBaseUrl]);

  // Generate mock OHLC data for demonstration
  const generateMockOHLCData = (currentPrice, endTime) => {
    const data = [];
    let price = currentPrice - Math.random() * 100;
    const timeframeConfig = timeframes.find(tf => tf.value === timeframe);
    const intervalSeconds = timeframeConfig?.seconds || 300;
    const periods = Math.min(200, Math.floor(86400 / intervalSeconds)); // Max 200 periods or 1 day
    
    for (let i = periods; i >= 0; i--) {
      const time = endTime - (i * intervalSeconds);
      const open = price;
      const volatility = 2 + Math.random() * 8; // Increased volatility for NQ
      const high = open + Math.random() * volatility;
      const low = open - Math.random() * volatility;
      const close = low + Math.random() * (high - low);
      const volume = Math.floor(500 + Math.random() * 3000);
      
      data.push({
        time: Math.floor(time),
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: volume,
      });
      
      // Add some trend to make it more realistic
      price = close + (Math.random() - 0.5) * 2;
    }
    
    return data;
  };

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
  }, [chartType, indicators]);

  // Update real-time price
  const updateRealTimePrice = useCallback((priceData) => {
    if (!candlestickSeriesRef.current) return;

    const currentTime = Math.floor(Date.now() / 1000);
    const newPoint = {
      time: currentTime,
      ...priceData,
    };

    if (chartType === 'candlestick') {
      candlestickSeriesRef.current.update(newPoint);
    } else {
      candlestickSeriesRef.current.update({
        time: currentTime,
        value: priceData.close,
      });
    }

    setCurrentPrice(priceData.close);
    setPriceChange(priceData.change || 0);
  }, [chartType]);

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
      <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="relative">
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
            <div className="flex items-center space-x-1">
              {/* Timeframe Selector */}
              {timeframes.map((tf) => (
                <button
                  key={tf.value}
                  onClick={() => changeTimeframe(tf.value)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    timeframe === tf.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  title={`${tf.label} - ${tf.description}`}
                >
                  {tf.label}
                </button>
              ))}
            </div>
            
            <div className="flex items-center space-x-1">
              {/* Period Selector */}
              <span className="text-xs text-gray-400 px-2">Period:</span>
              {periodOptions.map((period) => (
                <button
                  key={period.value}
                  onClick={() => setSelectedPeriod(period.value)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    selectedPeriod === period.value
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  title={period.description}
                >
                  {period.label}
                </button>
              ))}
            </div>
          </div>
          
          {currentPrice && (
            <div className="flex items-center space-x-3">
              <span className="text-xl font-mono text-white">
                ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className={`text-sm font-medium flex items-center ${
                priceChange >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                <span className={`mr-1 ${priceChange >= 0 ? '↗' : '↘'}`}>
                  {priceChange >= 0 ? '▲' : '▼'}
                </span>
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Chart Type Selector */}
          <div className="flex items-center space-x-1 mr-2">
            {['candlestick', 'line', 'area'].map((type) => (
              <button
                key={type}
                onClick={() => changeChartType(type)}
                className={`p-2 rounded-lg transition-colors ${
                  chartType === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title={type.charAt(0).toUpperCase() + type.slice(1)}
              >
                <ChartBarIcon className="w-4 h-4" />
              </button>
            ))}
          </div>
          
          {/* Drawing Tools Toggle */}
          <button
            onClick={() => setShowDrawingTools(!showDrawingTools)}
            className={`p-2 rounded-lg transition-colors ${
              showDrawingTools
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
            title="Drawing Tools"
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4" />
          </button>
          
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

      {/* Symbol Search Modal */}
      <SymbolSearch
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
/**
 * TradingChartV4 - Professional Trading Chart Component
 * ====================================================
 * 
 * Professional-grade trading chart with TradingView-equivalent features:
 * - Sub-second real-time updates
 * - Professional drawing tools
 * - Advanced technical indicators
 * - Agent signal integration
 * - WebGL-accelerated rendering
 * - Multi-timeframe analysis
 */

import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { createChart, ColorType, CrosshairMode, LineStyle, PriceScaleMode } from 'lightweight-charts';
import {
  ChartBarIcon,
  PencilIcon,
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  ArrowsPointingOutIcon,
  MagnifyingGlassIcon,
  BoltIcon,
  CpuChipIcon,
  SignalIcon,
  ChartPieIcon,
  CursorArrowRaysIcon,
  XMarkIcon,
  EyeIcon,
  EyeSlashIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';

// Professional Drawing Tools
import DrawingToolsPanel from './DrawingToolsPanel';
import TechnicalIndicatorsPanel from './TechnicalIndicatorsPanel';
import AgentSignalPanel from './AgentSignalPanel';
import ChartSettingsPanel from './ChartSettingsPanel';
import DynamicSymbolSearch from './DynamicSymbolSearch';
import AgentInterface from '../services/AgentInterface';

const TradingChartV4 = ({
  symbol = 'NQ=F',
  displaySymbol = 'NQ',
  height = 600,
  apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  wsBaseUrl = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000',
  onSignalReceived,
  onSymbolChange,
  onChartDataUpdate,
  onAgentRegistered,
  enableAgentMode = true,
  theme = 'dark'
}) => {
  // Refs
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const indicatorSeriesRefs = useRef({});
  const drawingToolsRef = useRef({});
  const agentInterfaceRef = useRef(null);
  const wsRef = useRef(null);
  
  // Chart State
  const [isPlaying, setIsPlaying] = useState(true);
  const [timeframe, setTimeframe] = useState('5m');
  const [selectedPeriod, setSelectedPeriod] = useState('1d');
  const [chartType, setChartType] = useState('candlestick');
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  // Data State
  const [chartData, setChartData] = useState([]);
  const [currentPrice, setCurrentPrice] = useState(null);
  const [priceChange, setPriceChange] = useState(0);
  const [priceChangePercent, setPriceChangePercent] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [dataSource, setDataSource] = useState('live');
  const [dataQuality, setDataQuality] = useState('excellent');
  
  // Real-time State
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [updateCount, setUpdateCount] = useState(0);
  const [latency, setLatency] = useState(0);
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());
  
  // UI State
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [showDrawingTools, setShowDrawingTools] = useState(false);
  const [showIndicatorPanel, setShowIndicatorPanel] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedDrawingTool, setSelectedDrawingTool] = useState(null);
  
  // Agent State
  const [connectedAgents, setConnectedAgents] = useState([]);
  const [agentSignals, setAgentSignals] = useState([]);
  const [agentPerformance, setAgentPerformance] = useState({});
  
  // Advanced Professional Timeframes
  const timeframes = useMemo(() => [
    { value: '1s', label: '1s', seconds: 1, description: '1 Second' },
    { value: '5s', label: '5s', seconds: 5, description: '5 Seconds' },
    { value: '15s', label: '15s', seconds: 15, description: '15 Seconds' },
    { value: '30s', label: '30s', seconds: 30, description: '30 Seconds' },
    { value: '1m', label: '1m', seconds: 60, description: '1 Minute' },
    { value: '2m', label: '2m', seconds: 120, description: '2 Minutes' },
    { value: '3m', label: '3m', seconds: 180, description: '3 Minutes' },
    { value: '5m', label: '5m', seconds: 300, description: '5 Minutes' },
    { value: '10m', label: '10m', seconds: 600, description: '10 Minutes' },
    { value: '15m', label: '15m', seconds: 900, description: '15 Minutes' },
    { value: '30m', label: '30m', seconds: 1800, description: '30 Minutes' },
    { value: '45m', label: '45m', seconds: 2700, description: '45 Minutes' },
    { value: '1h', label: '1h', seconds: 3600, description: '1 Hour' },
    { value: '2h', label: '2h', seconds: 7200, description: '2 Hours' },
    { value: '3h', label: '3h', seconds: 10800, description: '3 Hours' },
    { value: '4h', label: '4h', seconds: 14400, description: '4 Hours' },
    { value: '6h', label: '6h', seconds: 21600, description: '6 Hours' },
    { value: '8h', label: '8h', seconds: 28800, description: '8 Hours' },
    { value: '12h', label: '12h', seconds: 43200, description: '12 Hours' },
    { value: '1d', label: '1D', seconds: 86400, description: '1 Day' },
    { value: '2d', label: '2D', seconds: 172800, description: '2 Days' },
    { value: '3d', label: '3D', seconds: 259200, description: '3 Days' },
    { value: '1w', label: '1W', seconds: 604800, description: '1 Week' },
    { value: '2w', label: '2W', seconds: 1209600, description: '2 Weeks' },
    { value: '1M', label: '1M', seconds: 2629746, description: '1 Month' },
    { value: '3M', label: '3M', seconds: 7889238, description: '3 Months' },
    { value: '6M', label: '6M', seconds: 15778476, description: '6 Months' },
    { value: '1Y', label: '1Y', seconds: 31556952, description: '1 Year' }
  ], []);

  // Professional Technical Indicators
  const [indicators, setIndicators] = useState({
    // Moving Averages
    sma_9: { enabled: false, visible: true, color: '#ff6b6b', period: 9, type: 'overlay' },
    sma_20: { enabled: true, visible: true, color: '#4ecdc4', period: 20, type: 'overlay' },
    sma_50: { enabled: true, visible: true, color: '#45b7d1', period: 50, type: 'overlay' },
    sma_100: { enabled: false, visible: true, color: '#96ceb4', period: 100, type: 'overlay' },
    sma_200: { enabled: false, visible: true, color: '#feca57', period: 200, type: 'overlay' },
    
    ema_9: { enabled: false, visible: true, color: '#ff9ff3', period: 9, type: 'overlay' },
    ema_12: { enabled: false, visible: true, color: '#54a0ff', period: 12, type: 'overlay' },
    ema_21: { enabled: false, visible: true, color: '#5f27cd', period: 21, type: 'overlay' },
    ema_26: { enabled: false, visible: true, color: '#00d2d3', period: 26, type: 'overlay' },
    ema_50: { enabled: false, visible: true, color: '#ff6348', period: 50, type: 'overlay' },
    
    // Oscillators
    rsi: { enabled: false, visible: true, color: '#e17055', period: 14, type: 'oscillator', range: [0, 100] },
    stoch: { enabled: false, visible: true, color: '#a29bfe', period: 14, type: 'oscillator', range: [0, 100] },
    williams_r: { enabled: false, visible: true, color: '#fd79a8', period: 14, type: 'oscillator', range: [-100, 0] },
    cci: { enabled: false, visible: true, color: '#fdcb6e', period: 20, type: 'oscillator', range: [-200, 200] },
    
    // Trend Indicators
    macd: { enabled: false, visible: true, color: '#6c5ce7', type: 'oscillator' },
    adx: { enabled: false, visible: true, color: '#a29bfe', period: 14, type: 'oscillator', range: [0, 100] },
    parabolic_sar: { enabled: false, visible: true, color: '#fd79a8', type: 'overlay' },
    
    // Volume Indicators
    volume: { enabled: true, visible: true, color: '#74b9ff', type: 'volume' },
    volume_ma: { enabled: false, visible: true, color: '#0984e3', period: 20, type: 'volume' },
    obv: { enabled: false, visible: true, color: '#00b894', type: 'oscillator' },
    
    // Volatility Indicators
    bollinger_bands: { enabled: false, visible: true, color: '#e17055', period: 20, deviation: 2, type: 'overlay' },
    atr: { enabled: false, visible: true, color: '#fd79a8', period: 14, type: 'oscillator' },
    keltner_channels: { enabled: false, visible: true, color: '#fdcb6e', period: 20, type: 'overlay' },
    
    // Support/Resistance
    pivot_points: { enabled: false, visible: true, color: '#6c5ce7', type: 'overlay' },
    fibonacci: { enabled: false, visible: true, color: '#fd79a8', type: 'overlay' },
    
    // Custom Agent Indicators
    agent_sentiment: { enabled: false, visible: true, color: '#e84393', type: 'oscillator', range: [-1, 1] },
    agent_momentum: { enabled: false, visible: true, color: '#00cec9', type: 'oscillator', range: [-100, 100] },
    agent_signals: { enabled: true, visible: true, color: '#fdcb6e', type: 'signals' }
  });

  // Theme Configuration
  const chartTheme = useMemo(() => ({
    dark: {
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a0b' },
        textColor: '#f8fafc',
        fontSize: 12,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(55, 65, 81, 0.3)', style: LineStyle.Dotted },
        horzLines: { color: 'rgba(55, 65, 81, 0.3)', style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#10b981', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#10b981' },
        horzLine: { color: '#10b981', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#10b981' },
      },
      priceScale: {
        borderColor: '#374151',
        textColor: '#9ca3af',
      },
      timeScale: {
        borderColor: '#374151',
        textColor: '#9ca3af',
      }
    },
    light: {
      layout: {
        background: { type: ColorType.Solid, color: '#ffffff' },
        textColor: '#1f2937',
        fontSize: 12,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(229, 231, 235, 0.8)', style: LineStyle.Dotted },
        horzLines: { color: 'rgba(229, 231, 235, 0.8)', style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#059669', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#059669' },
        horzLine: { color: '#059669', width: 1, style: LineStyle.Dashed, labelBackgroundColor: '#059669' },
      },
      priceScale: {
        borderColor: '#d1d5db',
        textColor: '#6b7280',
      },
      timeScale: {
        borderColor: '#d1d5db',
        textColor: '#6b7280',
      }
    }
  }), []);

  // Initialize Professional Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const currentTheme = chartTheme[theme];
    
    const chart = createChart(chartContainerRef.current, {
      ...currentTheme,
      width: chartContainerRef.current.clientWidth,
      height: height,
      rightPriceScale: {
        ...currentTheme.priceScale,
        entireTextOnly: true,
        scaleMargins: { top: 0.05, bottom: 0.25 },
        borderVisible: true,
        visible: true,
      },
      leftPriceScale: { 
        visible: false 
      },
      timeScale: {
        ...currentTheme.timeScale,
        timeVisible: true,
        secondsVisible: timeframe.endsWith('s'),
        rightOffset: 12,
        barSpacing: 8,
        minBarSpacing: 2,
        fixLeftEdge: false,
        fixRightEdge: false,
        lockVisibleTimeRangeOnResize: true,
        shiftVisibleRangeOnNewBar: true,
        tickMarkFormatter: (time) => {
          const date = new Date(time * 1000);
          const tf = timeframes.find(t => t.value === timeframe);
          
          if (tf?.seconds < 60) { // Less than 1 minute
            return date.toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit',
              second: '2-digit',
              hour12: false 
            });
          } else if (tf?.seconds < 3600) { // Less than 1 hour
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
      localization: {
        priceFormatter: (price) => {
          if (price >= 1000) {
            return price.toFixed(2);
          } else if (price >= 1) {
            return price.toFixed(4);
          } else {
            return price.toFixed(6);
          }
        },
      },
    });

    chartRef.current = chart;

    // Create main price series based on chart type
    let mainSeries;
    if (chartType === 'candlestick') {
      mainSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef4444',
        priceFormat: {
          type: 'price',
          precision: 2,
          minMove: 0.01,
        },
      });
    } else if (chartType === 'line') {
      mainSeries = chart.addLineSeries({
        color: '#10b981',
        lineWidth: 2,
        lineType: 0, // Simple line
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 6,
        crosshairMarkerBorderColor: '#10b981',
        crosshairMarkerBackgroundColor: '#10b981',
        lastValueVisible: true,
        priceLineVisible: true,
      });
    } else if (chartType === 'area') {
      mainSeries = chart.addAreaSeries({
        topColor: 'rgba(16, 185, 129, 0.4)',
        bottomColor: 'rgba(16, 185, 129, 0.0)',
        lineColor: '#10b981',
        lineWidth: 2,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 6,
        lastValueVisible: true,
      });
    } else if (chartType === 'heikin_ashi') {
      // Heikin Ashi candlesticks
      mainSeries = chart.addCandlestickSeries({
        upColor: '#4ade80',
        downColor: '#f87171',
        borderVisible: false,
        wickUpColor: '#4ade80',
        wickDownColor: '#f87171',
      });
    }

    candlestickSeriesRef.current = mainSeries;

    // Add volume series if enabled
    if (indicators.volume.enabled) {
      const volumeSeries = chart.addHistogramSeries({
        color: 'rgba(116, 185, 255, 0.7)',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeriesRef.current = volumeSeries;

      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
        mode: PriceScaleMode.Percentage,
      });
    }

    // Initialize Agent Interface if enabled
    if (enableAgentMode) {
      agentInterfaceRef.current = new AgentInterface(wsBaseUrl);
      agentInterfaceRef.current.on('agentRegistered', handleAgentRegistered);
      agentInterfaceRef.current.on('signalReceived', handleAgentSignal);
      agentInterfaceRef.current.on('agentDisconnected', handleAgentDisconnected);
    }

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Handle fullscreen changes
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);

    return () => {
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      
      // Cleanup indicators
      Object.values(indicatorSeriesRefs.current).forEach(series => {
        try {
          if (series && chart) {
            chart.removeSeries(series);
          }
        } catch (e) {
          // Series may already be removed
        }
      });
      indicatorSeriesRefs.current = {};

      // Cleanup agent interface
      if (agentInterfaceRef.current) {
        agentInterfaceRef.current.disconnect();
      }

      if (chart) {
        chart.remove();
      }
    };
  }, [height, chartType, timeframe, theme, enableAgentMode]);

  // Enhanced Real-time WebSocket Connection
  useEffect(() => {
    if (!isPlaying || !symbol) return;

    let ws;
    let reconnectTimeout;
    let heartbeatInterval;
    let lastHeartbeat = Date.now();

    const connectWebSocket = () => {
      try {
        const wsUrl = `${wsBaseUrl}/api/ws/chart/${encodeURIComponent(symbol)}`;
        console.log(`🔗 Connecting to enhanced WebSocket: ${wsUrl}`);
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log(`✅ Enhanced WebSocket connected for ${symbol}`);
          setConnectionStatus('connected');
          
          // Send enhanced subscription
          ws.send(JSON.stringify({
            type: 'subscribe_enhanced',
            symbol: symbol,
            timeframe: timeframe,
            features: ['real_time_data', 'agent_signals', 'technical_analysis'],
            update_interval: getUpdateInterval(timeframe),
            quality: 'high'
          }));

          // Start heartbeat
          heartbeatInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              const now = Date.now();
              ws.send(JSON.stringify({
                type: 'heartbeat',
                timestamp: now,
                client_id: 'trading_chart_v4'
              }));
              
              // Check for stale connection
              if (now - lastHeartbeat > 30000) { // 30 seconds
                console.warn('Connection appears stale, reconnecting...');
                ws.close();
              }
            }
          }, 5000);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            const now = Date.now();
            
            // Update heartbeat
            if (data.type === 'heartbeat_response') {
              lastHeartbeat = now;
              const latency = now - data.timestamp;
              setLatency(latency);
              return;
            }
            
            // Handle different message types
            switch (data.type) {
              case 'market_data_update':
                handleRealTimeUpdate(data);
                break;
              case 'agent_signal':
                handleAgentSignal(data.signal);
                break;
              case 'technical_analysis':
                handleTechnicalAnalysis(data);
                break;
              case 'market_status':
                handleMarketStatus(data);
                break;
              case 'error':
                console.error('WebSocket error:', data.message);
                break;
              default:
                console.log('Unknown message type:', data.type);
            }
            
            setLastUpdateTime(now);
            
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('Enhanced WebSocket error:', error);
          setConnectionStatus('error');
        };

        ws.onclose = (event) => {
          console.log(`🔌 Enhanced WebSocket disconnected: ${event.code} ${event.reason}`);
          setConnectionStatus('disconnected');
          
          if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
          }
          
          // Reconnect after delay
          if (isPlaying) {
            reconnectTimeout = setTimeout(connectWebSocket, 3000);
          }
        };
        
      } catch (error) {
        console.error('Failed to connect enhanced WebSocket:', error);
        setConnectionStatus('error');
        
        // Fallback to HTTP polling
        startEnhancedPolling();
      }
    };

    // Enhanced HTTP polling fallback
    const startEnhancedPolling = () => {
      console.log(`🔄 Starting enhanced polling for ${symbol}`);
      setConnectionStatus('polling');
      
      const pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${apiBaseUrl}/api/market/realtime?symbol=${symbol}&timeframe=${timeframe}`);
          if (response.ok) {
            const data = await response.json();
            handleRealTimeUpdate({
              type: 'market_data_update',
              ...data,
              source: 'polling'
            });
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, getUpdateInterval(timeframe) * 1000);
      
      return () => clearInterval(pollInterval);
    };

    // Start connection
    connectWebSocket();
    
    // Load initial data
    fetchChartData();

    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
    };
  }, [symbol, timeframe, selectedPeriod, isPlaying, apiBaseUrl, wsBaseUrl]);

  // Get update interval based on timeframe
  const getUpdateInterval = useCallback((tf) => {
    const timeframeObj = timeframes.find(t => t.value === tf);
    if (!timeframeObj) return 1;
    
    // Update frequency based on timeframe
    if (timeframeObj.seconds <= 5) return 0.1;      // 100ms for tick data
    if (timeframeObj.seconds <= 60) return 0.5;     // 500ms for minute data
    if (timeframeObj.seconds <= 300) return 1;      // 1s for 5-minute data
    if (timeframeObj.seconds <= 3600) return 5;     // 5s for hourly data
    return 30; // 30s for daily+ data
  }, [timeframes]);

  // Enhanced data fetching
  const fetchChartData = useCallback(async (forceRefresh = false) => {
    if (!symbol || !timeframe) return;
    
    setIsLoading(true);
    
    try {
      console.log(`📊 Fetching enhanced data: ${symbol} ${timeframe} ${selectedPeriod}`);
      
      const params = new URLSearchParams({
        symbol: symbol,
        timeframe: timeframe,
        period: selectedPeriod,
        include_indicators: 'true',
        include_patterns: 'true',
        quality: 'high',
        force_refresh: forceRefresh.toString()
      });
      
      const response = await fetch(`${apiBaseUrl}/api/market/enhanced?${params}`);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (!result?.data || !Array.isArray(result.data)) {
        throw new Error('Invalid data format received');
      }

      // Process enhanced data
      const processedData = processChartData(result.data);
      setChartData(processedData);
      setDataSource(result.source || 'api');
      setDataQuality(result.quality || 'good');
      
      if (processedData.length > 0) {
        const lastCandle = processedData[processedData.length - 1];
        setCurrentPrice(lastCandle.close);
        
        if (processedData.length > 1) {
          const prevCandle = processedData[processedData.length - 2];
          const change = lastCandle.close - prevCandle.close;
          const changePercent = (change / prevCandle.close) * 100;
          setPriceChange(change);
          setPriceChangePercent(changePercent);
        }
      }
      
      // Update chart series
      updateChartSeries(processedData);
      
      // Update indicators if enabled
      updateIndicators(processedData, result.indicators);
      
      // Auto-fit chart for new data
      autoFitChart('data_load');
      
      // Notify parent
      if (onChartDataUpdate) {
        onChartDataUpdate({
          data: processedData,
          indicators: result.indicators,
          patterns: result.patterns,
          quality: result.quality
        });
      }
      
      console.log(`✅ Enhanced data loaded: ${processedData.length} points`);
      
    } catch (error) {
      console.error('Failed to fetch enhanced chart data:', error);
      setDataSource('error');
    } finally {
      setIsLoading(false);
    }
  }, [symbol, timeframe, selectedPeriod, apiBaseUrl]);

  // Process chart data with advanced validation
  const processChartData = useCallback((rawData) => {
    return rawData
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
        item.low <= Math.min(item.open, item.close) &&
        item.open > 0 && item.high > 0 && item.low > 0 && item.close > 0
      )
      .sort((a, b) => a.time - b.time);
  }, []);

  // Enhanced real-time update handler
  const handleRealTimeUpdate = useCallback((data) => {
    if (!data.price || data.symbol !== symbol) return;
    
    const price = parseFloat(data.price);
    if (isNaN(price) || price <= 0) return;
    
    console.log(`💰 Enhanced real-time update: ${symbol} = $${price.toFixed(2)}`);
    
    setCurrentPrice(price);
    setUpdateCount(prev => prev + 1);
    
    // Calculate price change
    if (chartData.length > 0) {
      const lastCandle = chartData[chartData.length - 1];
      const change = price - lastCandle.close;
      const changePercent = (change / lastCandle.close) * 100;
      setPriceChange(change);
      setPriceChangePercent(changePercent);
    }
    
    // Update current candle or create new one
    if (chartData.length > 0 && candlestickSeriesRef.current) {
      const now = Math.floor(Date.now() / 1000);
      const timeframeObj = timeframes.find(t => t.value === timeframe);
      const intervalSeconds = timeframeObj?.seconds || 300;
      
      const lastCandle = chartData[chartData.length - 1];
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
        
        updateCandleOnChart(newCandle, chartType);
        console.log(`🆕 New candle created at ${new Date(candleStartTime * 1000).toISOString()}`);
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
        
        updateCandleOnChart(updatedCandle, chartType);
      }
    }
  }, [symbol, chartData, timeframe, timeframes, chartType]);

  // Update candle on chart based on chart type
  const updateCandleOnChart = useCallback((candle, type) => {
    if (!candlestickSeriesRef.current) return;
    
    try {
      if (type === 'candlestick' || type === 'heikin_ashi') {
        candlestickSeriesRef.current.update(candle);
      } else if (type === 'line' || type === 'area') {
        candlestickSeriesRef.current.update({
          time: candle.time,
          value: candle.close
        });
      }
    } catch (error) {
      console.error('Failed to update candle on chart:', error);
    }
  }, []);

  // Update chart series with enhanced data
  const updateChartSeries = useCallback((data) => {
    if (!candlestickSeriesRef.current || !data.length) return;

    try {
      if (chartType === 'candlestick' || chartType === 'heikin_ashi') {
        const candleData = chartType === 'heikin_ashi' ? 
          convertToHeikinAshi(data) : data;
        candlestickSeriesRef.current.setData(candleData);
      } else if (chartType === 'line') {
        const lineData = data.map(item => ({
          time: item.time,
          value: item.close,
        }));
        candlestickSeriesRef.current.setData(lineData);
      } else if (chartType === 'area') {
        const areaData = data.map(item => ({
          time: item.time,
          value: item.close,
        }));
        candlestickSeriesRef.current.setData(areaData);
      }

      // Update volume if enabled
      if (indicators.volume.enabled && volumeSeriesRef.current) {
        const volumeData = data.map(item => ({
          time: item.time,
          value: item.volume,
          color: chartType === 'candlestick' ? 
            (item.close >= item.open ? 'rgba(38, 166, 154, 0.7)' : 'rgba(239, 68, 68, 0.7)') :
            'rgba(116, 185, 255, 0.7)',
        }));
        volumeSeriesRef.current.setData(volumeData);
      }
      
    } catch (error) {
      console.error('Failed to update chart series:', error);
    }
  }, [chartType, indicators.volume.enabled]);

  // Convert regular OHLC to Heikin Ashi
  const convertToHeikinAshi = useCallback((data) => {
    if (data.length === 0) return [];
    
    const haData = [];
    let prevHA = null;
    
    for (let i = 0; i < data.length; i++) {
      const current = data[i];
      
      if (i === 0) {
        // First candle
        const haCandle = {
          time: current.time,
          open: (current.open + current.close) / 2,
          high: current.high,
          low: current.low,
          close: (current.open + current.high + current.low + current.close) / 4,
          volume: current.volume
        };
        haData.push(haCandle);
        prevHA = haCandle;
      } else {
        const haClose = (current.open + current.high + current.low + current.close) / 4;
        const haOpen = (prevHA.open + prevHA.close) / 2;
        const haHigh = Math.max(current.high, haOpen, haClose);
        const haLow = Math.min(current.low, haOpen, haClose);
        
        const haCandle = {
          time: current.time,
          open: haOpen,
          high: haHigh,
          low: haLow,
          close: haClose,
          volume: current.volume
        };
        
        haData.push(haCandle);
        prevHA = haCandle;
      }
    }
    
    return haData;
  }, []);

  // Update technical indicators
  const updateIndicators = useCallback((data, serverIndicators = {}) => {
    if (!chartRef.current || !data.length) return;

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
      if (!config.enabled || !config.visible) return;

      try {
        if (config.type === 'overlay') {
          addOverlayIndicator(key, config, data, serverIndicators);
        } else if (config.type === 'oscillator') {
          addOscillatorIndicator(key, config, data, serverIndicators);
        } else if (config.type === 'volume') {
          // Volume already handled in main series
        }
      } catch (error) {
        console.error(`Error adding indicator ${key}:`, error);
      }
    });
  }, [indicators]);

  // Add overlay indicators (MA, BB, etc.)
  const addOverlayIndicator = useCallback((key, config, data, serverIndicators) => {
    const indicatorData = serverIndicators[key] || calculateIndicator(key, config, data);
    if (!indicatorData || indicatorData.length === 0) return;

    if (key.startsWith('sma_') || key.startsWith('ema_')) {
      // Moving averages
      const series = chartRef.current.addLineSeries({
        color: config.color,
        lineWidth: 2,
        title: key.toUpperCase(),
        lastValueVisible: true,
        priceLineVisible: false,
      });
      
      const seriesData = indicatorData.map((value, index) => ({
        time: data[index]?.time,
        value: value
      })).filter(item => item.time && !isNaN(item.value) && item.value > 0);
      
      series.setData(seriesData);
      indicatorSeriesRefs.current[key] = series;
      
    } else if (key === 'bollinger_bands') {
      // Bollinger Bands - three lines
      const { upper, middle, lower } = indicatorData;
      
      ['upper', 'middle', 'lower'].forEach((band, index) => {
        const bandData = indicatorData[band];
        if (!bandData) return;
        
        const series = chartRef.current.addLineSeries({
          color: index === 0 ? config.color : 
                 index === 1 ? config.color : 
                 config.color,
          lineWidth: index === 1 ? 2 : 1,
          lineStyle: index === 1 ? LineStyle.Solid : LineStyle.Dashed,
          title: `BB ${band.toUpperCase()}`,
          lastValueVisible: index === 1,
          priceLineVisible: false,
        });
        
        const seriesData = bandData.map((value, idx) => ({
          time: data[idx]?.time,
          value: value
        })).filter(item => item.time && !isNaN(item.value));
        
        series.setData(seriesData);
        indicatorSeriesRefs.current[`${key}_${band}`] = series;
      });
    }
  }, []);

  // Add oscillator indicators (RSI, MACD, etc.)
  const addOscillatorIndicator = useCallback((key, config, data, serverIndicators) => {
    // Create separate pane for oscillators
    const indicatorData = serverIndicators[key] || calculateIndicator(key, config, data);
    if (!indicatorData || indicatorData.length === 0) return;

    if (key === 'rsi') {
      const series = chartRef.current.addLineSeries({
        color: config.color,
        lineWidth: 2,
        title: 'RSI',
        priceScaleId: 'rsi',
      });
      
      const seriesData = indicatorData.map((value, index) => ({
        time: data[index]?.time,
        value: value
      })).filter(item => item.time && !isNaN(item.value));
      
      series.setData(seriesData);
      indicatorSeriesRefs.current[key] = series;
      
      // Configure RSI price scale
      chartRef.current.priceScale('rsi').applyOptions({
        scaleMargins: { top: 0.1, bottom: 0.1 },
        drawTicks: false,
      });
      
    } else if (key === 'macd') {
      const { macd, signal, histogram } = indicatorData;
      
      // MACD line
      if (macd) {
        const macdSeries = chartRef.current.addLineSeries({
          color: config.color,
          lineWidth: 2,
          title: 'MACD',
          priceScaleId: 'macd',
        });
        
        const macdData = macd.map((value, index) => ({
          time: data[index]?.time,
          value: value
        })).filter(item => item.time && !isNaN(item.value));
        
        macdSeries.setData(macdData);
        indicatorSeriesRefs.current['macd_line'] = macdSeries;
      }
      
      // Signal line
      if (signal) {
        const signalSeries = chartRef.current.addLineSeries({
          color: '#ff6b6b',
          lineWidth: 1,
          title: 'Signal',
          priceScaleId: 'macd',
        });
        
        const signalData = signal.map((value, index) => ({
          time: data[index]?.time,
          value: value
        })).filter(item => item.time && !isNaN(item.value));
        
        signalSeries.setData(signalData);
        indicatorSeriesRefs.current['macd_signal'] = signalSeries;
      }
      
      // Histogram
      if (histogram) {
        const histogramSeries = chartRef.current.addHistogramSeries({
          color: '#74b9ff',
          priceScaleId: 'macd',
        });
        
        const histogramData = histogram.map((value, index) => ({
          time: data[index]?.time,
          value: value,
          color: value >= 0 ? '#26a69a' : '#ef4444'
        })).filter(item => item.time && !isNaN(item.value));
        
        histogramSeries.setData(histogramData);
        indicatorSeriesRefs.current['macd_histogram'] = histogramSeries;
      }
    }
  }, []);

  // Calculate indicators client-side if not provided by server
  const calculateIndicator = useCallback((key, config, data) => {
    const closes = data.map(d => d.close);
    const highs = data.map(d => d.high);
    const lows = data.map(d => d.low);
    
    switch (key) {
      case 'sma_20':
      case 'sma_50':
      case 'sma_100':
      case 'sma_200':
        return calculateSMA(closes, config.period);
      
      case 'ema_12':
      case 'ema_26':
      case 'ema_50':
        return calculateEMA(closes, config.period);
      
      case 'rsi':
        return calculateRSI(closes, config.period);
      
      case 'macd':
        return calculateMACD(closes);
      
      default:
        return [];
    }
  }, []);

  // Technical analysis functions
  const calculateSMA = useCallback((prices, period) => {
    const result = [];
    for (let i = 0; i < prices.length; i++) {
      if (i < period - 1) {
        result.push(NaN);
      } else {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
      }
    }
    return result;
  }, []);

  const calculateEMA = useCallback((prices, period) => {
    const result = [];
    const multiplier = 2 / (period + 1);
    let ema = prices[0];
    
    for (let i = 0; i < prices.length; i++) {
      if (i === 0) {
        result.push(prices[i]);
        ema = prices[i];
      } else {
        ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
        result.push(ema);
      }
    }
    return result;
  }, []);

  const calculateRSI = useCallback((prices, period = 14) => {
    const result = [];
    const gains = [];
    const losses = [];
    
    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? -change : 0);
    }
    
    for (let i = 0; i < gains.length; i++) {
      if (i < period - 1) {
        result.push(NaN);
      } else {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b) / period;
        
        if (avgLoss === 0) {
          result.push(100);
        } else {
          const rs = avgGain / avgLoss;
          const rsi = 100 - (100 / (1 + rs));
          result.push(rsi);
        }
      }
    }
    
    return [NaN, ...result]; // Add NaN for first price (no change)
  }, []);

  const calculateMACD = useCallback((prices, fast = 12, slow = 26, signal = 9) => {
    const emaFast = calculateEMA(prices, fast);
    const emaSlow = calculateEMA(prices, slow);
    
    const macdLine = emaFast.map((fast, i) => fast - emaSlow[i]);
    const signalLine = calculateEMA(macdLine.filter(x => !isNaN(x)), signal);
    
    // Pad signal line with NaNs to match length
    const paddedSignal = [
      ...Array(macdLine.length - signalLine.length).fill(NaN),
      ...signalLine
    ];
    
    const histogram = macdLine.map((macd, i) => 
      !isNaN(macd) && !isNaN(paddedSignal[i]) ? macd - paddedSignal[i] : NaN
    );
    
    return {
      macd: macdLine,
      signal: paddedSignal,
      histogram: histogram
    };
  }, [calculateEMA]);

  // Auto-fit chart to data
  const autoFitChart = useCallback((reason = 'manual') => {
    if (!chartRef.current || !chartData.length) return;
    
    setTimeout(() => {
      try {
        if (reason === 'data_load' || reason === 'symbol_change') {
          // Fit all content first
          chartRef.current.timeScale().fitContent();
        } else {
          // Just fit visible range
          chartRef.current.timeScale().scrollToRealTime();
        }
        
        console.log(`📏 Chart auto-fitted (${reason})`);
      } catch (e) {
        console.warn(`Failed to auto-fit chart (${reason}):`, e);
      }
    }, reason === 'data_load' ? 500 : 100);
  }, [chartData]);

  // Handle agent registration
  const handleAgentRegistered = useCallback((agent) => {
    setConnectedAgents(prev => [...prev.filter(a => a.id !== agent.id), agent]);
    console.log(`🤖 Agent registered: ${agent.name}`);
    
    if (onAgentRegistered) {
      onAgentRegistered(agent);
    }
  }, [onAgentRegistered]);

  // Handle agent signals
  const handleAgentSignal = useCallback((signal) => {
    if (!signal || signal.symbol !== symbol) return;
    
    setAgentSignals(prev => [...prev.slice(-99), signal]); // Keep last 100 signals
    
    // Add signal marker to chart
    if (candlestickSeriesRef.current) {
      const marker = {
        time: signal.timestamp || Math.floor(Date.now() / 1000),
        position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
        color: signal.type === 'buy' ? '#26a69a' : '#ef4444',
        shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
        text: `${signal.type.toUpperCase()}\n${signal.agent_name}\nConf: ${(signal.confidence * 100).toFixed(0)}%`,
        size: Math.max(0.5, Math.min(2.0, signal.confidence * 2)),
      };
      
      try {
        candlestickSeriesRef.current.setMarkers([...agentSignals.slice(-20).map(s => ({
          time: s.timestamp || Math.floor(Date.now() / 1000),
          position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
          color: s.type === 'buy' ? '#26a69a' : '#ef4444',
          shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
          text: `${s.type.toUpperCase()}\n${s.agent_name}`,
          size: Math.max(0.5, Math.min(2.0, s.confidence * 2)),
        })), marker]);
      } catch (error) {
        console.error('Failed to add signal marker:', error);
      }
    }
    
    console.log(`📡 Agent signal: ${signal.type} ${signal.symbol} by ${signal.agent_name}`);
    
    if (onSignalReceived) {
      onSignalReceived(signal);
    }
  }, [symbol, agentSignals, onSignalReceived]);

  // Handle agent disconnection
  const handleAgentDisconnected = useCallback((agentId) => {
    setConnectedAgents(prev => prev.filter(a => a.id !== agentId));
    console.log(`🤖 Agent disconnected: ${agentId}`);
  }, []);

  // Handle technical analysis updates
  const handleTechnicalAnalysis = useCallback((data) => {
    if (data.patterns) {
      console.log('📈 Pattern detected:', data.patterns);
      // TODO: Highlight patterns on chart
    }
  }, []);

  // Handle market status updates
  const handleMarketStatus = useCallback((data) => {
    console.log('🏛️ Market status:', data.status);
    // TODO: Update market status indicator
  }, []);

  // Control functions
  const changeTimeframe = useCallback((newTimeframe) => {
    console.log(`📊 Changing timeframe: ${timeframe} → ${newTimeframe}`);
    setTimeframe(newTimeframe);
    setTimeout(() => autoFitChart('timeframe_change'), 100);
  }, [timeframe, autoFitChart]);

  const changeChartType = useCallback((newType) => {
    console.log(`📊 Changing chart type: ${chartType} → ${newType}`);
    setChartType(newType);
    setTimeout(() => autoFitChart('chart_type_change'), 100);
  }, [chartType, autoFitChart]);

  const changePeriod = useCallback((newPeriod) => {
    console.log(`📊 Changing period: ${selectedPeriod} → ${newPeriod}`);
    setSelectedPeriod(newPeriod);
  }, [selectedPeriod]);

  const toggleIndicator = useCallback((indicatorKey) => {
    setIndicators(prev => ({
      ...prev,
      [indicatorKey]: {
        ...prev[indicatorKey],
        enabled: !prev[indicatorKey].enabled,
      },
    }));
  }, []);

  const toggleFullscreen = useCallback(async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await chartContainerRef.current?.requestFullscreen();
      }
    } catch (error) {
      console.error('Fullscreen toggle failed:', error);
    }
  }, []);

  // Get connection status info
  const getConnectionInfo = useCallback(() => {
    switch (connectionStatus) {
      case 'connected':
        return { 
          color: 'bg-green-400', 
          text: 'Live WebSocket',
          icon: BoltIcon 
        };
      case 'polling':
        return { 
          color: 'bg-yellow-400', 
          text: 'Live Polling',
          icon: SignalIcon 
        };
      case 'error':
        return { 
          color: 'bg-red-400', 
          text: 'Connection Error',
          icon: XMarkIcon 
        };
      default:
        return { 
          color: 'bg-gray-400', 
          text: 'Disconnected',
          icon: XMarkIcon 
        };
    }
  }, [connectionStatus]);

  const connectionInfo = getConnectionInfo();

  // Get data quality info
  const getDataQualityInfo = useCallback(() => {
    switch (dataQuality) {
      case 'excellent':
        return { color: 'text-green-400', text: 'EXCELLENT' };
      case 'good':
        return { color: 'text-blue-400', text: 'GOOD' };
      case 'fair':
        return { color: 'text-yellow-400', text: 'FAIR' };
      case 'poor':
        return { color: 'text-red-400', text: 'POOR' };
      default:
        return { color: 'text-gray-400', text: 'UNKNOWN' };
    }
  }, [dataQuality]);

  const qualityInfo = getDataQualityInfo();

  return (
    <div className={`bg-gray-900 rounded-lg border border-gray-700 flex flex-col h-full ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      {/* Professional Chart Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-700 bg-gray-800 flex-wrap gap-2">
        <div className="flex items-center space-x-4 flex-wrap">
          {/* Symbol and Price Display */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowSymbolSearch(true)}
              className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-gray-700 transition-colors"
            >
              <h3 className="text-xl font-bold text-white">{displaySymbol}</h3>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            {currentPrice && (
              <div className="flex items-center space-x-3">
                <span className="text-2xl font-mono font-bold text-white">
                  ${currentPrice.toFixed(2)}
                </span>
                <div className="flex flex-col">
                  <span className={`text-sm font-medium ${
                    priceChange > 0 ? 'text-green-400' : priceChange < 0 ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    {priceChange > 0 ? '+' : ''}{priceChange.toFixed(2)}
                  </span>
                  <span className={`text-xs ${
                    priceChangePercent > 0 ? 'text-green-400' : priceChangePercent < 0 ? 'text-red-400' : 'text-gray-400'
                  }`}>
                    ({priceChangePercent > 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400 font-medium">Interval:</label>
            <select
              value={timeframe}
              onChange={(e) => changeTimeframe(e.target.value)}
              className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label} - {tf.description}
                </option>
              ))}
            </select>
          </div>
          
          {/* Chart Type Selector */}
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-400 font-medium">Type:</label>
            <select
              value={chartType}
              onChange={(e) => changeChartType(e.target.value)}
              className="bg-gray-700 text-white text-sm px-3 py-1 rounded border border-gray-600 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
            >
              <option value="candlestick">Candlestick</option>
              <option value="line">Line</option>
              <option value="area">Area</option>
              <option value="heikin_ashi">Heikin Ashi</option>
            </select>
          </div>
        </div>
        
        {/* Professional Controls */}
        <div className="flex items-center space-x-2 flex-wrap">
          {/* Connection Status */}
          <div className="flex items-center space-x-2 text-xs">
            <connectionInfo.icon className="w-4 h-4" />
            <span className={`w-2 h-2 ${connectionInfo.color} rounded-full`}></span>
            <span className="text-gray-300">{connectionInfo.text}</span>
            {latency > 0 && (
              <span className="text-gray-500">({latency}ms)</span>
            )}
          </div>

          {/* Data Quality */}
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-gray-400">Quality:</span>
            <span className={`${qualityInfo.color} font-medium`}>
              {qualityInfo.text}
            </span>
          </div>

          {/* Drawing Tools */}
          <button
            onClick={() => setShowDrawingTools(!showDrawingTools)}
            className={`p-2 rounded-lg transition-colors ${
              showDrawingTools ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
            }`}
            title="Drawing Tools"
          >
            <PencilIcon className="w-4 h-4" />
          </button>

          {/* Technical Indicators */}
          <button
            onClick={() => setShowIndicatorPanel(!showIndicatorPanel)}
            className={`p-2 rounded-lg transition-colors ${
              showIndicatorPanel ? 'bg-purple-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
            }`}
            title="Technical Indicators"
          >
            <ChartPieIcon className="w-4 h-4" />
          </button>

          {/* Agent Panel */}
          {enableAgentMode && (
            <button
              onClick={() => setShowAgentPanel(!showAgentPanel)}
              className={`p-2 rounded-lg transition-colors ${
                showAgentPanel ? 'bg-green-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
              title="AI Agents"
            >
              <CpuChipIcon className="w-4 h-4" />
              {connectedAgents.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                  {connectedAgents.length}
                </span>
              )}
            </button>
          )}

          {/* Play/Pause */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`p-2 rounded-lg transition-colors ${
              isPlaying ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-600 hover:bg-gray-500'
            }`}
            title={isPlaying ? 'Pause' : 'Resume'}
          >
            {isPlaying ? (
              <PauseIcon className="w-4 h-4 text-white" />
            ) : (
              <PlayIcon className="w-4 h-4 text-white" />
            )}
          </button>

          {/* Refresh */}
          <button
            onClick={() => fetchChartData(true)}
            disabled={isLoading}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Refresh Data"
          >
            <svg className={`w-4 h-4 text-gray-300 ${isLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>

          {/* Auto-fit */}
          <button
            onClick={() => autoFitChart('manual')}
            disabled={!chartData.length}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors disabled:opacity-50"
            title="Fit Chart to Data"
          >
            <ArrowsPointingOutIcon className="w-4 h-4 text-gray-300" />
          </button>

          {/* Fullscreen */}
          <button
            onClick={toggleFullscreen}
            className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
            title="Toggle Fullscreen"
          >
            <svg className="w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>

          {/* Settings */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-lg transition-colors ${
              showSettings ? 'bg-gray-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
            title="Chart Settings"
          >
            <Cog6ToothIcon className="w-4 h-4 text-gray-300" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 relative">
        {/* Side Panels */}
        {showDrawingTools && (
          <DrawingToolsPanel
            onToolSelect={setSelectedDrawingTool}
            selectedTool={selectedDrawingTool}
            onClose={() => setShowDrawingTools(false)}
          />
        )}

        {showIndicatorPanel && (
          <TechnicalIndicatorsPanel
            indicators={indicators}
            onToggleIndicator={toggleIndicator}
            onIndicatorSettingsChange={(key, settings) => {
              setIndicators(prev => ({
                ...prev,
                [key]: { ...prev[key], ...settings }
              }));
            }}
            onClose={() => setShowIndicatorPanel(false)}
          />
        )}

        {showAgentPanel && enableAgentMode && (
          <AgentSignalPanel
            agents={connectedAgents}
            signals={agentSignals}
            performance={agentPerformance}
            onAgentAction={(action, agentId) => {
              if (agentInterfaceRef.current) {
                agentInterfaceRef.current.sendAgentCommand(agentId, action);
              }
            }}
            onClose={() => setShowAgentPanel(false)}
          />
        )}

        {/* Chart Container */}
        <div className="flex-1 relative">
          <div 
            ref={chartContainerRef}
            className="absolute inset-0"
            style={{ background: theme === 'dark' ? '#0a0a0b' : '#ffffff' }}
          />
          
          {/* Loading Overlay */}
          {isLoading && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-10">
              <div className="bg-gray-800 p-6 rounded-lg flex items-center space-x-4">
                <svg className="animate-spin h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-white font-medium">Loading enhanced market data...</span>
              </div>
            </div>
          )}

          {/* Performance Stats Overlay */}
          <div className="absolute top-4 right-4 bg-black bg-opacity-70 rounded-lg p-3 text-xs text-gray-300 space-y-1">
            <div>Updates: {updateCount}</div>
            <div>Bars: {chartData.length}</div>
            <div>Signals: {agentSignals.length}</div>
            <div>Agents: {connectedAgents.length}</div>
            <div>Latency: {latency}ms</div>
          </div>
        </div>
      </div>
      
      {/* Professional Footer */}
      <div className="p-3 border-t border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center space-x-6">
            <span className="flex items-center space-x-2">
              <connectionInfo.icon className="w-3 h-3" />
              <span>{connectionInfo.text}</span>
            </span>
            <span>TF: {timeframe}</span>
            <span>Updates: {updateCount}</span>
            <span>Quality: {qualityInfo.text}</span>
          </div>
          <div className="flex items-center space-x-6">
            <span>Bars: {chartData.length}</span>
            <span>Signals: {agentSignals.length}</span>
            <span>Agents: {connectedAgents.length}</span>
            <span>Last: {new Date(lastUpdateTime).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Modal Components */}
      <DynamicSymbolSearch
        isOpen={showSymbolSearch}
        onClose={() => setShowSymbolSearch(false)}
        onSymbolSelect={(newSymbol, newDisplaySymbol) => {
          if (onSymbolChange) onSymbolChange(newSymbol, newDisplaySymbol);
        }}
        currentSymbol={symbol}
      />

      {showSettings && (
        <ChartSettingsPanel
          theme={theme}
          settings={{
            enableRealTime: isPlaying,
            updateInterval: getUpdateInterval(timeframe),
            maxDataPoints: 5000,
            enableAgentMode: enableAgentMode
          }}
          onSettingsChange={(newSettings) => {
            // Handle settings changes
            console.log('Settings changed:', newSettings);
          }}
          onClose={() => setShowSettings(false)}
        />
      )}
    </div>
  );
};

export default TradingChartV4;
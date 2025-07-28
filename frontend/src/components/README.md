# TradingChart V2 - Advanced Trading Chart Component

A complete rewrite of the trading chart component that provides a robust, TradingView-like experience with AI agent integration capabilities.

## 🚀 Key Features

- **Single Source of Truth**: Unified data provider eliminates inconsistencies
- **Real-time Data**: WebSocket-based live updates with proper fallback mechanisms
- **AI Agent Integration**: Comprehensive API for agents to interact with chart data
- **Advanced Indicators**: 15+ built-in technical indicators + custom indicator support
- **TradingView-Style Interface**: Professional trading interface with modern UX
- **High Performance**: Optimized for real-time trading environments
- **Extensible Architecture**: Modular design for easy customization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  TradingChartV2                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │   ChartCore     │  │  IndicatorPanel │              │
│  │   (Canvas)      │  │   (Controls)    │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │  DataProvider   │  │  AgentInterface │              │
│  │  (WebSocket)    │  │   (API Bridge)  │              │
│  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## 📦 Components

### Core Components

- **TradingChartV2**: Main chart component with full TradingView-like functionality
- **MarketDataProvider**: Unified data service for consistent market data
- **ChartAgentInterface**: AI agent integration API
- **TechnicalIndicators**: Advanced technical analysis indicators
- **DynamicSymbolSearch**: Symbol search and selection component

### Supporting Services

- **Data Provider**: Handles WebSocket connections and HTTP fallbacks
- **Indicator System**: Modular indicator calculation and rendering
- **Agent Interface**: API for AI agents to interact with chart data
- **Cache Management**: Efficient caching for performance optimization

## 🔧 Installation & Setup

1. **Install Dependencies**:
```bash
npm install lightweight-charts @heroicons/react
```

2. **Import Components**:
```javascript
import TradingChartV2 from './components/TradingChartV2';
import MarketDataProvider from './services/MarketDataProvider';
import ChartAgentInterface from './services/ChartAgentInterface';
```

3. **Basic Usage**:
```javascript
const App = () => {
  return (
    <TradingChartV2
      symbol="NQ=F"
      displaySymbol="NQ"
      height={600}
      onSignalReceived={(signal) => console.log('Signal:', signal)}
      onSymbolChange={(symbol, display) => console.log('Symbol changed:', symbol)}
    />
  );
};
```

## 🎯 Key Improvements Over V1

### Data Consistency
- **Single Data Source**: Eliminates conflicts between multiple data providers
- **Proper Cache Isolation**: Symbol-specific caching prevents data contamination
- **Unified WebSocket/HTTP**: Consistent data processing pipeline
- **Symbol Validation**: Strict symbol handling prevents format mismatches

### Real-time Performance
- **Optimized WebSocket**: Efficient real-time data handling
- **Smart Caching**: Reduces API calls while maintaining data freshness
- **Proper Candle Building**: Accurate OHLC data construction
- **Memory Management**: Efficient cleanup and resource management

### Agent Integration
- **Comprehensive API**: Full access to chart data and analysis tools
- **Real-time Streaming**: Live data feeds for AI agents
- **Performance Metrics**: Monitoring and optimization for agent interactions
- **Custom Indicators**: Extensible indicator system for agent-specific needs

## 📊 Technical Indicators

### Built-in Indicators

| Indicator | Description | Parameters |
|-----------|-------------|------------|
| SMA | Simple Moving Average | period (20, 50) |
| EMA | Exponential Moving Average | period (12, 26) |
| RSI | Relative Strength Index | period (14) |
| MACD | Moving Average Convergence Divergence | fast (12), slow (26), signal (9) |
| Bollinger Bands | Price volatility bands | period (20), stdDev (2) |
| Stochastic | Momentum oscillator | %K (14), %D (3) |
| ATR | Average True Range | period (14) |
| Williams %R | Momentum indicator | period (14) |
| CCI | Commodity Channel Index | period (20) |
| MFI | Money Flow Index | period (14) |
| OBV | On-Balance Volume | - |
| VWAP | Volume Weighted Average Price | - |
| Parabolic SAR | Stop and Reverse | acceleration (0.02), maximum (0.2) |

### Custom Indicators

```javascript
import { indicators } from './utils/TechnicalIndicators';

// Register custom indicator
indicators.registerCustomIndicator('myIndicator', (data, params) => {
  // Custom calculation logic
  return calculatedData;
});

// Use in chart
const customData = indicators.calculateCustom('myIndicator', chartData, { period: 20 });
```

## 🤖 AI Agent Integration

### Basic Agent Registration

```javascript
import ChartAgentInterface from './services/ChartAgentInterface';

const agentInterface = new ChartAgentInterface(marketDataProvider);

// Register agent
const agentId = agentInterface.registerAgent('trading-agent-1', {
  name: 'Trading Agent',
  type: 'trading',
  permissions: ['read', 'analyze'],
  indicators: ['sma20', 'rsi', 'macd'],
  updateFrequency: 'realtime'
});
```

### Real-time Data Access

```javascript
// Subscribe to real-time data
agentInterface.subscribeToSymbol(agentId, 'NQ=F', (update) => {
  console.log('Real-time update:', update);
  // Process update for AI model
});

// Get historical data
const chartData = await agentInterface.getChartData(agentId, 'NQ=F', {
  period: '1d',
  interval: '5m',
  includeIndicators: true,
  format: 'ml_ready'
});
```

### Signal Generation

```javascript
// Generate trading signals
const signals = await agentInterface.generateSignals(agentId, 'NQ=F', {
  strategy: 'momentum',
  lookback: '1d',
  timeframe: '5m'
});

// Backtest strategy
const backtest = await agentInterface.backtestStrategy(agentId, 'NQ=F', {
  name: 'RSI Strategy',
  generator: 'rsi_momentum'
}, {
  startDate: new Date('2024-01-01'),
  initialCapital: 10000
});
```

## 📈 Usage Examples

### Basic Chart

```javascript
const BasicChart = () => {
  const [symbol, setSymbol] = useState('NQ=F');
  
  return (
    <TradingChartV2
      symbol={symbol}
      displaySymbol={symbol.replace('=F', '')}
      height={600}
      onSymbolChange={setSymbol}
    />
  );
};
```

### Advanced Chart with Agent

```javascript
const AdvancedChart = () => {
  const [dataProvider] = useState(new MarketDataProvider());
  const [agentInterface] = useState(new ChartAgentInterface(dataProvider));
  
  useEffect(() => {
    // Register AI agent
    const agentId = agentInterface.registerAgent('my-agent', {
      indicators: ['sma20', 'rsi', 'macd'],
      patterns: ['breakout', 'reversal']
    });
    
    // Subscribe to signals
    agentInterface.subscribeToSymbol(agentId, 'NQ=F', handleSignal);
    
    return () => {
      agentInterface.unregisterAgent(agentId);
    };
  }, []);
  
  const handleSignal = (signal) => {
    console.log('AI Signal:', signal);
    // Process signal for trading decisions
  };
  
  return (
    <TradingChartV2
      symbol="NQ=F"
      displaySymbol="NQ"
      height={600}
      agentConfig={{ 
        enabled: true,
        agentInterface: agentInterface 
      }}
    />
  );
};
```

### Custom Indicator Implementation

```javascript
import TechnicalIndicators from './utils/TechnicalIndicators';

const indicators = new TechnicalIndicators();

// Register SuperTrend indicator
indicators.registerCustomIndicator('superTrend', (data, params = {}) => {
  const { period = 10, multiplier = 3 } = params;
  
  // Calculate ATR
  const atr = indicators.atr(data, period);
  const result = [];
  
  for (let i = period - 1; i < data.length; i++) {
    const hl2 = (data[i].high + data[i].low) / 2;
    const atrValue = atr[i - period + 1].value;
    
    const upperBand = hl2 + (multiplier * atrValue);
    const lowerBand = hl2 - (multiplier * atrValue);
    
    result.push({
      time: data[i].time,
      value: data[i].close > hl2 ? lowerBand : upperBand,
      trend: data[i].close > hl2 ? 'up' : 'down'
    });
  }
  
  return result;
});

// Use in chart
const Chart = () => {
  const [indicators, setIndicators] = useState({
    superTrend: { enabled: true, period: 10, multiplier: 3 }
  });
  
  return (
    <TradingChartV2
      symbol="NQ=F"
      customIndicators={indicators}
    />
  );
};
```

## 🔧 Configuration Options

### Chart Configuration

```javascript
const chartConfig = {
  symbol: 'NQ=F',           // Trading symbol
  displaySymbol: 'NQ',      // Display name
  height: 600,              // Chart height
  timeframe: '5m',          // Data timeframe
  period: '1d',             // Data period
  chartType: 'candlestick', // Chart type (candlestick, line, area)
  theme: 'dark',            // Chart theme
  enableRealTime: true,     // Real-time updates
  enableIndicators: true,   // Technical indicators
  enableSignals: true,      // Trading signals
  enableAgentApi: true      // AI agent integration
};
```

### Data Provider Configuration

```javascript
const providerConfig = {
  apiBaseUrl: 'http://localhost:8000',
  wsBaseUrl: 'ws://localhost:8000',
  reconnectInterval: 3000,
  maxReconnectAttempts: 5,
  cacheTimeout: 30000,
  enableCaching: true
};
```

### Agent Interface Configuration

```javascript
const agentConfig = {
  maxDataPoints: 10000,
  refreshInterval: 1000,
  enableCaching: true,
  agentTimeout: 30000,
  permissions: ['read', 'analyze', 'signal'],
  indicators: ['sma20', 'sma50', 'rsi', 'macd'],
  patterns: ['breakout', 'reversal', 'trend']
};
```

## 🐛 Troubleshooting

### Common Issues

1. **Data Inconsistency**: Clear cache and restart data provider
2. **WebSocket Connection**: Check network and server status
3. **Performance Issues**: Reduce data points or disable heavy indicators
4. **Agent Errors**: Verify agent registration and permissions

### Debug Mode

```javascript
// Enable debug logging
const dataProvider = new MarketDataProvider({ debug: true });
const agentInterface = new ChartAgentInterface(dataProvider, { debug: true });
```

### Performance Monitoring

```javascript
// Get performance metrics
const metrics = agentInterface.getAgentMetrics(agentId);
console.log('Agent Performance:', metrics);
```

## 🚀 Performance Optimizations

1. **Data Caching**: Intelligent caching reduces API calls
2. **WebSocket Optimization**: Efficient real-time data handling
3. **Memory Management**: Proper cleanup prevents memory leaks
4. **Lazy Loading**: Indicators loaded on demand
5. **Batch Processing**: Multiple calculations in single pass

## 🛡️ Security Considerations

1. **Agent Permissions**: Strict permission-based access control
2. **Data Validation**: All inputs validated before processing
3. **Rate Limiting**: Prevents API abuse
4. **Secure WebSocket**: WSS support for production environments

## 📝 Contributing

1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Documentation

- [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/)
- [WebSocket API Reference](../docs/websocket-api.md)
- [Technical Indicators Guide](../docs/indicators.md)
- [Agent Integration Tutorial](../docs/agent-integration.md)
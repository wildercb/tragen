# Agent Configuration Guide

Learn how to configure your AI trading agents through the web interface without any coding. This guide covers everything from basic setup to advanced agent personality configuration.

## 🎯 What is Agent Configuration?

Agent configuration is how you teach your AI trading agents:
- **How to think** about markets (conservative vs aggressive)
- **What risks to take** (position sizes, stop losses)
- **When to trade** (market conditions, timeframes)
- **How to analyze** (technical indicators, AI models)

## 🚀 Quick Agent Setup (5 Minutes)

### Step 1: Access Agent Creation
1. **Go to your dashboard**: `http://localhost:8000`
2. **Click "Create Agent"** button (usually top-right)
3. **Choose setup method**:
   - **Use Template** (Recommended for beginners)
   - **Custom Setup** (For experienced users)

### Step 2: Choose Agent Template

#### Conservative Trader Template
```
✅ Best for: Beginners, capital preservation
📊 Risk Level: Low (1-2% per trade)
⏰ Trading Style: Swing trading, trend following
🎯 Goal: Steady, consistent profits
```

#### Balanced Trader Template
```
✅ Best for: Intermediate users, balanced approach
📊 Risk Level: Medium (2-3% per trade)
⏰ Trading Style: Day trading, multiple timeframes
🎯 Goal: Good returns with manageable risk
```

#### Aggressive Trader Template
```
✅ Best for: Experienced users, higher returns
📊 Risk Level: High (3-5% per trade)
⏰ Trading Style: Scalping, high frequency
🎯 Goal: Maximum profits with higher risk
```

### Step 3: Basic Information
```
Agent Name: [Enter a memorable name]
Description: [Optional description of agent's purpose]
```

**Naming Tips**:
- Use descriptive names: "Conservative NQ Trader", "Scalping Bot 1"
- Avoid generic names: "Agent1", "Bot"
- Include strategy type: "Swing Trader", "Day Trader"

## 🎛️ Detailed Configuration Options

### Personality Configuration

#### Trading Style
```
📈 Scalping (1-5 minute trades)
- Quick in-and-out trades
- High frequency, small profits
- Requires constant monitoring

📊 Day Trading (5 minute - 4 hour trades)  
- Intraday positions
- Multiple trades per day
- Balance of frequency and profit size

📉 Swing Trading (4 hour - daily trades)
- Multi-day positions
- Fewer, larger moves
- Less frequent monitoring needed
```

#### Risk Tolerance (1-10 Scale)
```
1-3: Conservative
- Maximum 1-2% risk per trade
- Requires high confidence signals
- Emphasis on capital preservation

4-6: Balanced
- Maximum 2-3% risk per trade
- Moderate confidence requirements
- Balance risk and reward

7-10: Aggressive
- Maximum 3-5% risk per trade
- Lower confidence thresholds
- Focus on maximum returns
```

#### Analysis Style
```
🔍 Conservative Analysis
- Requires 3+ confirming indicators
- Only trades with clear trends
- Waits for high-probability setups

⚖️ Balanced Analysis
- Requires 2+ confirming indicators
- Trades with and against trends
- Moderate setup requirements

⚡ Aggressive Analysis
- Single strong indicator sufficient
- Quick decision making
- Acts on early signals
```

### Risk Management Settings

#### Position Sizing
```yaml
# Basic Position Sizing
max_loss_per_trade: 2.0%        # Maximum loss per single trade
max_daily_loss: 5.0%            # Maximum loss per day
max_weekly_loss: 10.0%          # Maximum loss per week
max_position_value: $50,000     # Maximum dollar value per position
```

#### Stop Loss Configuration
```yaml
# Stop Loss Settings
stop_loss_type: "percentage"    # "percentage", "atr", "technical"
stop_loss_percentage: 1.0%      # Fixed percentage stop
atr_multiplier: 2.0             # If using ATR-based stops
trailing_stop: true             # Enable trailing stops
trailing_percentage: 0.5%       # Trailing stop distance
```

#### Take Profit Settings
```yaml
# Take Profit Configuration
take_profit_ratio: 2.0          # Risk:Reward ratio (2:1 minimum)
partial_profit_levels:          # Take partial profits
  - 50%: 1.5                    # Take 50% profit at 1.5R
  - 25%: 2.5                    # Take 25% more at 2.5R
scale_out_enabled: true         # Enable position scaling
```

### Trading Parameters

#### Market Conditions
```yaml
# When to Trade
trading_hours:
  start: "09:30"                # Market open (ET)
  end: "16:00"                  # Market close (ET)
  lunch_break: "12:00-13:00"    # Reduce activity during lunch

volume_requirements:
  min_volume_ratio: 1.2         # Minimum 120% of average volume
  
volatility_limits:
  min_volatility: 15            # Don't trade if VIX < 15
  max_volatility: 40            # Reduce size if VIX > 40
```

#### Trade Frequency
```yaml
# Trading Frequency Controls
max_trades_per_day: 10          # Maximum daily trades
max_trades_per_hour: 3          # Maximum hourly trades
min_time_between_trades: 5      # Minimum minutes between trades
cooldown_after_loss: 15         # Minutes to wait after loss
```

## 🧠 AI Model Configuration

### Analysis Methods

#### Technical Analysis Weight
```
🔧 Technical Analysis: 60%
- Moving averages, RSI, MACD
- Support/resistance levels
- Chart patterns and trends
- Volume analysis
```

#### AI Model Weight
```
🤖 AI Analysis: 40%
- Machine learning predictions
- Pattern recognition
- Sentiment analysis
- Market regime detection
```

### Model Selection
```yaml
# Primary AI Models
primary_model: "claude-3-sonnet"    # Main reasoning model
analysis_model: "gpt-4"             # Technical analysis
sentiment_model: "local-llama"      # Market sentiment

# Fallback Models
fallback_models:
  - "claude-3-haiku"                # If primary fails
  - "gpt-3.5-turbo"                 # Secondary fallback
```

### Confidence Thresholds
```yaml
# Confidence Requirements
min_confidence_to_trade: 70%       # Minimum confidence to enter
min_confidence_to_hold: 60%        # Minimum to maintain position
confidence_boost_indicators:       # Boost confidence when:
  - volume_confirmation: +10%       # Volume confirms signal
  - multiple_timeframes: +15%       # Multiple timeframes align
  - low_volatility: +5%             # Low market volatility
```

## 📊 Advanced Configuration

### Multi-Timeframe Analysis
```yaml
# Timeframe Configuration
timeframes:
  trend_analysis: "4h"             # Overall trend direction
  entry_timing: "15m"              # Entry signal timing
  exit_timing: "5m"                # Exit signal timing

analysis_weights:
  trend_timeframe: 50%             # Trend gets highest weight
  entry_timeframe: 30%             # Entry timing important
  exit_timeframe: 20%              # Exit timing least weight
```

### Strategy Combinations
```yaml
# Multiple Strategy Setup
strategies:
  primary: "trend_following"        # Main strategy (70% weight)
  secondary: "mean_reversion"       # Secondary (30% weight)
  
strategy_switching:
  market_regime_based: true        # Switch based on market conditions
  performance_based: true          # Switch based on recent performance
  volatility_based: true           # Switch based on volatility
```

### Learning Configuration
```yaml
# Agent Learning Settings
learning_enabled: true             # Enable continuous learning
learning_rate: 0.1                # How fast agent adapts
memory_period: 30                 # Days of memory to maintain
feedback_weight: 0.3              # Weight of user feedback
performance_weight: 0.7           # Weight of actual performance
```

## 🎨 Agent Personality Templates

### Conservative Swing Trader
```yaml
personality:
  name: "Conservative Swing Trader"
  risk_tolerance: 3
  analysis_style: "conservative"
  confidence_threshold: 80%
  max_trades_per_day: 3
  
trading_rules:
  - "Only trade with primary trend"
  - "Require 3+ confirming indicators"  
  - "Never risk more than 1% per trade"
  - "Hold positions 1-5 days"
  - "Take profits at first reversal sign"
```

### Aggressive Scalper
```yaml
personality:
  name: "Aggressive Scalper"
  risk_tolerance: 8
  analysis_style: "aggressive"
  confidence_threshold: 60%
  max_trades_per_day: 50
  
trading_rules:
  - "Trade 1-5 minute timeframes"
  - "Quick in-and-out (max 15 minutes)"
  - "Risk up to 3% per trade"
  - "Target 10-20 point moves"
  - "Use tight stops (5-10 points)"
```

### Balanced Day Trader
```yaml
personality:
  name: "Balanced Day Trader"
  risk_tolerance: 5
  analysis_style: "balanced"
  confidence_threshold: 70%
  max_trades_per_day: 15
  
trading_rules:
  - "Use 15m-1h timeframes"
  - "Hold positions 1-6 hours"
  - "Risk 2% per trade"
  - "Target 50-100 point moves"
  - "Use 20-30 point stops"
```

## 🔧 Configuration Validation

### Required Settings Checklist
- [ ] **Agent Name**: Unique, descriptive name
- [ ] **Trading Style**: Scalping, day trading, or swing trading
- [ ] **Risk Level**: Appropriate for your comfort level
- [ ] **Paper Trading**: ALWAYS enabled for new agents
- [ ] **Stop Loss**: Always configured (never trade without)
- [ ] **Position Size**: Appropriate for account size

### Safety Checks
- [ ] **Maximum loss per trade** ≤ 5% of account
- [ ] **Maximum daily loss** ≤ 10% of account  
- [ ] **Paper trading enabled** for testing
- [ ] **Stop loss configured** for all trades
- [ ] **Position size limits** set appropriately

### Performance Optimization
- [ ] **Confidence thresholds** not too high/low
- [ ] **Trade frequency** appropriate for strategy
- [ ] **Timeframes** aligned with trading style
- [ ] **Risk-reward ratio** minimum 2:1
- [ ] **Analysis methods** properly weighted

## 📋 Configuration Best Practices

### Starting Configuration
1. **Always start conservative**: Lower risk, higher confidence thresholds
2. **Enable paper trading**: Test thoroughly before real money
3. **Use templates**: They're pre-configured for safety
4. **Start with single strategy**: Don't overcomplicate initially

### Gradual Optimization
1. **Run for 1-2 weeks**: Let agent establish baseline performance
2. **Analyze results**: Look at win rate, profit factor, drawdown
3. **Make small adjustments**: Change one parameter at a time
4. **Test changes**: Run for another week before more changes

### Common Mistakes to Avoid
❌ **Setting risk too high initially**
❌ **Changing multiple settings at once**
❌ **Not using stop losses**
❌ **Skipping paper trading phase**
❌ **Over-optimizing based on short-term results**

## 🔄 Managing Multiple Agents

### Agent Portfolio Strategy
```yaml
# Example 3-Agent Portfolio
agents:
  conservative_agent:
    allocation: 50%              # 50% of capital
    risk_per_trade: 1%
    style: "swing_trading"
    
  balanced_agent:
    allocation: 30%              # 30% of capital
    risk_per_trade: 2%
    style: "day_trading"
    
  aggressive_agent:
    allocation: 20%              # 20% of capital
    risk_per_trade: 3%
    style: "scalping"
```

### Coordination Settings
```yaml
# Agent Coordination
coordination:
  prevent_overlap: true          # Prevent agents from taking same trades
  max_total_exposure: 10%        # Maximum combined portfolio exposure
  correlation_limits: 0.7        # Maximum correlation between agents
  
risk_distribution:
  diversify_by_timeframe: true   # Spread across different timeframes
  diversify_by_strategy: true    # Use different strategies
  rebalance_frequency: "weekly"  # Rebalance allocations weekly
```

## 🔍 Monitoring Agent Configuration

### Performance Metrics to Track
```yaml
# Key Performance Indicators
metrics:
  win_rate: "> 60%"             # Target win rate
  profit_factor: "> 1.5"        # Profit factor target
  sharpe_ratio: "> 1.0"         # Risk-adjusted returns
  max_drawdown: "< 10%"         # Maximum drawdown limit
  
behavioral_metrics:
  rule_adherence: "> 95%"       # How well agent follows rules
  trade_frequency: "as_expected" # Trading frequency vs target
  confidence_accuracy: "> 70%"  # Confidence calibration
```

### Configuration Alerts
```yaml
# Alert Conditions
alerts:
  performance_degradation:       # If performance drops
    trigger: "profit_factor < 1.0"
    action: "pause_agent"
    
  risk_rule_violations:          # If risk rules broken
    trigger: "loss > max_daily_loss"
    action: "halt_trading"
    
  configuration_drift:           # If behavior changes unexpectedly
    trigger: "trade_frequency > 150% of target"
    action: "review_required"
```

## 📚 Configuration Examples

### Example 1: New User Setup
```yaml
# Perfect for someone just starting
agent_config:
  name: "My First Conservative Trader"
  template: "conservative"
  paper_trading_only: true
  
  risk_settings:
    max_loss_per_trade: 1.0%
    max_daily_loss: 2.0%
    stop_loss_percentage: 0.5%
    
  trading_settings:
    max_trades_per_day: 3
    confidence_threshold: 80%
    timeframe: "1h"
    
  analysis:
    technical_weight: 70%
    ai_weight: 30%
```

### Example 2: Experienced User Setup
```yaml
# For users comfortable with higher risk
agent_config:
  name: "Balanced Multi-Timeframe Trader"
  template: "custom"
  paper_trading_only: false      # Ready for live trading
  
  risk_settings:
    max_loss_per_trade: 2.5%
    max_daily_loss: 5.0%
    stop_loss_type: "atr"
    atr_multiplier: 2.0
    
  trading_settings:
    max_trades_per_day: 15
    confidence_threshold: 65%
    timeframes: ["15m", "1h", "4h"]
    
  analysis:
    technical_weight: 50%
    ai_weight: 50%
    
  advanced:
    learning_enabled: true
    strategy_switching: true
    correlation_monitoring: true
```

---

**💡 Remember**: Good configuration is the foundation of successful AI trading. Start conservative, test thoroughly, and gradually optimize based on real performance data.

**Next**: [Trading Settings](trading-settings.md) | [Training Agents](training-agents.md) | [Risk Management](../configuration/risk-management.md)
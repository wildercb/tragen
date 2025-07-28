# Prompts & Context Configuration

Learn how to customize your AI trading agents' behavior through prompts and context without any coding. This is where you teach your agents how to think and make decisions.

## 🎯 What Are Prompts & Context?

### Prompts
**Prompts** are instructions you give to your AI agent. Think of them as:
- 📋 **Trading Rules**: "Always check volume before buying"
- 🎯 **Strategy Instructions**: "Focus on trend-following strategies"
- 🧠 **Decision Logic**: "Be more conservative during high volatility"

### Context
**Context** is background information your agent uses:
- 📊 **Market Data**: Current prices, volume, indicators
- 📈 **Historical Patterns**: Past market behavior
- 🎛️ **Agent Settings**: Risk tolerance, trading style
- 📚 **Market Knowledge**: Trading concepts and strategies

## 🔧 How to Configure Prompts (No Coding Required)

### Method 1: Web Interface (Easiest)

#### Step 1: Access Agent Configuration
1. **Go to your dashboard**: `http://localhost:8000`
2. **Find your agent** in the "Active Agents" list
3. **Click the settings icon** (⚙️) next to your agent
4. **Select "Prompts & Guides"** tab

#### Step 2: Basic Prompt Setup
```
Trading Personality Prompt:
You are a [CONSERVATIVE/BALANCED/AGGRESSIVE] trading agent specializing in NQ futures.

Your primary goals:
- Protect capital above all else
- Make consistent, profitable trades
- Follow strict risk management rules
- Learn from market patterns

Your trading style:
- Risk tolerance: [LOW/MEDIUM/HIGH]
- Time horizon: [SCALPING/DAY/SWING]
- Preferred timeframes: [1m, 5m, 15m, 1h, 4h, 1d]
```

#### Step 3: Analysis Instructions
```
Market Analysis Instructions:
When analyzing the market, always:

1. Check multiple timeframes (5m, 15m, 1h)
2. Look for confluence between indicators
3. Assess market volatility and volume
4. Consider overall market trend
5. Evaluate risk-reward ratio (minimum 2:1)

Never trade when:
- Volume is below average
- Volatility is extremely high
- Near major news events
- Risk-reward is less than 2:1
```

### Method 2: Configuration Files

#### Step 1: Find Prompt Files
Navigate to: `mcp_trading_agent/prompts/`

#### Step 2: Edit Prompt Files
Create or edit files like:
- `analysis_prompt.txt` - Main analysis instructions
- `risk_prompt.txt` - Risk management guidance
- `strategy_prompt.txt` - Trading strategy instructions

#### Example: analysis_prompt.txt
```
You are an expert NQ futures trading analyst with 20 years of experience.

ANALYSIS FRAMEWORK:
1. Trend Analysis
   - Identify primary trend direction (1h, 4h charts)
   - Look for trend continuation or reversal signals
   - Use moving averages (20, 50, 200) for trend confirmation

2. Technical Indicators
   - RSI: Look for overbought (>70) or oversold (<30) conditions
   - MACD: Check for bullish/bearish crossovers
   - Volume: Confirm moves with above-average volume

3. Support and Resistance
   - Identify key levels from previous highs/lows
   - Look for psychological levels (round numbers)
   - Watch for breakouts or bounces at these levels

4. Risk Assessment
   - Calculate position size based on account risk (max 2%)
   - Set stop loss at logical technical level
   - Ensure minimum 2:1 risk-reward ratio

DECISION MAKING:
Only recommend trades when:
- Clear trend direction identified
- Multiple indicators align
- Good risk-reward ratio available
- Volume supports the move

Always explain your reasoning clearly and provide specific entry, stop loss, and take profit levels.
```

## 📚 Prompt Templates Library

### Conservative Trading Prompt
```
PERSONALITY: Conservative Trend Follower
RISK TOLERANCE: Low (1-3% of account per trade)
STRATEGY: Only trade with the trend, require high confirmation

RULES:
- Never trade against the primary trend
- Require at least 3 confirming indicators
- Maximum 2 trades per day
- Stop loss always set before entering
- Take profits at first sign of reversal

MARKET CONDITIONS:
- Avoid trading during first/last 30 minutes of session
- No trading during major news events
- Increase position size only after 5 consecutive wins
```

### Aggressive Scalping Prompt
```
PERSONALITY: Aggressive Scalper
RISK TOLERANCE: High (up to 5% per trade)
STRATEGY: Quick in-and-out trades, capture small moves

RULES:
- Focus on 1-5 minute charts
- Trade range bounces and breakouts
- Maximum hold time: 15 minutes
- Take quick profits (10-20 points)
- Use tight stops (5-10 points)

MARKET CONDITIONS:
- Best during high volume periods
- Focus on first 2 hours of session
- Avoid during low volatility
- Scale up during trending markets
```

### Swing Trading Prompt
```
PERSONALITY: Patient Swing Trader
RISK TOLERANCE: Medium (2-4% per trade)
STRATEGY: Hold positions for 1-5 days, capture larger moves

RULES:
- Use 4h and daily charts for analysis
- Look for weekly trend continuation
- Hold through minor pullbacks
- Target 100-300 point moves
- Use wider stops (50-100 points)

MARKET CONDITIONS:
- Best during trending markets
- Avoid during choppy/sideways action
- Focus on momentum breakouts
- Consider fundamental factors
```

## 🎛️ Context Configuration

### Market Context Setup

#### Economic Calendar Integration
```yaml
# config/market_context.yaml
economic_events:
  high_impact:
    - "FOMC Meeting"
    - "Non-Farm Payrolls"
    - "CPI Release"
    - "GDP Report"
  
  trading_rules:
    before_high_impact: "reduce_position_size_50%"
    during_high_impact: "no_new_trades"
    after_high_impact: "wait_30_minutes"
```

#### Market Hours Context
```yaml
# config/trading_hours.yaml
market_sessions:
  pre_market:
    start: "04:00"
    end: "09:30"
    strategy: "conservative"
    max_position_size: "50%"
  
  regular_hours:
    start: "09:30"
    end: "16:00"
    strategy: "normal"
    max_position_size: "100%"
  
  after_hours:
    start: "16:00"
    end: "20:00"
    strategy: "very_conservative"
    max_position_size: "25%"
```

### Historical Context

#### Pattern Recognition Context
```
HISTORICAL PATTERNS TO RECOGNIZE:

1. Morning Gaps
   - Gaps > 20 points often fill within first hour
   - Fade large gaps, follow small gaps
   - Higher probability during earnings season

2. Lunch Hour Trading (11:30-13:30 ET)
   - Typically lower volume and choppiness
   - Avoid new positions unless strong trend
   - Good time for position management

3. Power Hour (15:00-16:00 ET)
   - Increased volume and volatility
   - Trend acceleration common
   - Good for breakout trades

4. Weekly Patterns
   - Monday: Often continuation of Friday's move
   - Tuesday-Thursday: Best trending days
   - Friday: Profit taking, position squaring
```

## 🔄 Dynamic Context Updates

### Real-Time Market Adaptation
```python
# Example: Dynamic volatility adjustment
VOLATILITY_CONTEXT = """
Current Market Volatility: {volatility_level}

VOLATILITY RULES:
- Low Volatility (<15): Increase position size 25%, look for breakouts
- Normal Volatility (15-25): Standard position sizing and rules
- High Volatility (25-40): Reduce position size 25%, use wider stops
- Extreme Volatility (>40): Reduce position size 50%, be very selective

Current Recommendation: {volatility_action}
"""
```

### News Impact Context
```python
# Example: News-aware trading
NEWS_CONTEXT = """
Recent Market News Impact: {news_sentiment}

NEWS TRADING RULES:
- Positive News: Look for continuation moves, buy dips
- Negative News: Look for selling opportunities, fade rallies
- Mixed/Unclear News: Stay neutral, wait for price action
- Major Breaking News: Halt new trades, manage existing positions

Current Market Sentiment: {sentiment_score}
Action: {recommended_action}
"""
```

## 🎯 Prompt Optimization Strategies

### A/B Testing Your Prompts

#### Step 1: Create Variations
```
Version A (Conservative):
"Only trade when 3+ indicators align and trend is clear"

Version B (Balanced): 
"Trade when 2+ indicators align, consider counter-trend on strong signals"

Version C (Aggressive):
"Trade on single strong signal, use quick stops and targets"
```

#### Step 2: Test Performance
1. **Run each version** for 1 week in paper trading
2. **Track metrics**:
   - Total trades
   - Win rate
   - Average profit/loss
   - Maximum drawdown
3. **Choose the best performer**

### Prompt Improvement Process

#### Weekly Review Process
1. **Analyze Trading Results**
   - Which trades were profitable?
   - Which trades lost money?
   - What patterns do you see?

2. **Update Prompts Based on Results**
   ```
   # Example improvement
   Old: "Buy on RSI oversold"
   New: "Buy on RSI oversold + volume confirmation + trend alignment"
   ```

3. **Document Changes**
   - Keep a log of prompt changes
   - Note the reasoning for each change
   - Track performance impact

## 📋 Prompt Best Practices

### Writing Effective Prompts

#### Be Specific
❌ **Vague**: "Trade carefully"
✅ **Specific**: "Use maximum 2% risk per trade with 2:1 minimum risk-reward ratio"

#### Use Action-Oriented Language
❌ **Passive**: "The market might be good for buying"
✅ **Active**: "BUY when RSI < 30 AND price above 20-period MA AND volume > average"

#### Include Context
❌ **No Context**: "Buy NQ futures"
✅ **With Context**: "Buy NQ futures during uptrend when price pulls back to 20-period MA with RSI showing bullish divergence"

### Prompt Structure Template
```
[AGENT PERSONALITY]
You are a [STYLE] trader with [RISK_LEVEL] risk tolerance.

[CORE STRATEGY]
Your primary strategy is [STRATEGY_DESCRIPTION].

[ENTRY RULES]
Enter trades when:
1. [CONDITION_1]
2. [CONDITION_2]
3. [CONDITION_3]

[EXIT RULES]
Exit trades when:
1. [STOP_LOSS_RULE]
2. [TAKE_PROFIT_RULE]
3. [TIME_BASED_EXIT]

[RISK MANAGEMENT]
- Maximum risk per trade: [PERCENTAGE]
- Maximum daily risk: [PERCENTAGE]
- Position sizing: [METHOD]

[MARKET CONDITIONS]
Avoid trading when:
- [CONDITION_1]
- [CONDITION_2]

Increase activity when:
- [CONDITION_1]
- [CONDITION_2]
```

## 🔧 Advanced Context Configuration

### Multi-Timeframe Context
```yaml
# config/timeframe_context.yaml
timeframe_analysis:
  primary: "15m"  # Main trading timeframe
  trend: "1h"     # Trend identification
  entry: "5m"     # Entry timing
  
analysis_rules:
  trend_timeframe:
    - "Identify overall market direction"
    - "Determine support/resistance levels"
    - "Assess momentum strength"
  
  entry_timeframe:
    - "Fine-tune entry timing"
    - "Confirm signals from primary timeframe"
    - "Set precise stop loss levels"
```

### Seasonal Context
```yaml
# config/seasonal_context.yaml
seasonal_patterns:
  january:
    characteristics: "New year momentum, increased volatility"
    strategy_adjustments: "Increase position size 10%, focus on breakouts"
  
  december:
    characteristics: "Holiday trading, lower volume"
    strategy_adjustments: "Reduce position size 20%, avoid major moves"
  
  quarterly_end:
    characteristics: "Institutional rebalancing, increased activity"
    strategy_adjustments: "Expect higher volatility, use wider stops"
```

## 📊 Measuring Prompt Effectiveness

### Key Metrics to Track

#### Performance Metrics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total profits ÷ Total losses
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest losing streak

#### Behavioral Metrics
- **Trade Frequency**: Trades per day/week
- **Average Hold Time**: How long positions are held
- **Risk Consistency**: Variation in position sizes
- **Rule Adherence**: How often the agent follows prompts

### Optimization Dashboard
```python
# Track these metrics in your monitoring dashboard
prompt_metrics = {
    "total_trades": 150,
    "win_rate": 0.62,
    "profit_factor": 1.45,
    "sharpe_ratio": 1.2,
    "max_drawdown": 0.08,
    "avg_hold_time": "2.5 hours",
    "rule_violations": 3,
    "prompt_version": "v2.1"
}
```

## 🚀 Scaling Prompt Management

### For Multiple Agents

#### Shared Prompt Library
```
prompts/
├── shared/
│   ├── risk_management.txt      # Common risk rules
│   ├── market_hours.txt         # Trading hours rules
│   └── news_trading.txt         # News impact rules
├── strategies/
│   ├── conservative.txt         # Conservative strategy
│   ├── aggressive.txt           # Aggressive strategy
│   └── scalping.txt            # Scalping strategy
└── agents/
    ├── agent_001_prompts.txt    # Agent-specific prompts
    ├── agent_002_prompts.txt
    └── agent_003_prompts.txt
```

#### Prompt Version Control
```yaml
# prompt_versions.yaml
version_history:
  v1.0:
    date: "2024-01-15"
    changes: "Initial conservative strategy"
    performance: "Win rate: 58%, Profit factor: 1.2"
  
  v2.0:
    date: "2024-01-22"
    changes: "Added volume confirmation requirement"
    performance: "Win rate: 65%, Profit factor: 1.4"
  
  v2.1:
    date: "2024-01-29"
    changes: "Refined entry timing rules"
    performance: "Win rate: 67%, Profit factor: 1.6"
```

---

**💡 Remember**: Good prompts are the foundation of successful AI trading. Start simple, test thoroughly, and iterate based on results.

**Next**: [Risk Management Configuration](risk-management.md) | [Trading Strategies](trading-strategies.md) | [Agent Configuration](../user-guides/agent-configuration.md)
# Trading Settings Guide

Learn how to configure trading parameters, risk limits, and operational settings for your Tragen AI trading system. All settings can be configured through the web interface without coding.

## 🎯 What Are Trading Settings?

Trading settings control:
- **When** your agents can trade (market hours, conditions)
- **How much** they can risk (position sizes, limits)
- **How often** they trade (frequency controls)
- **What markets** they access (symbols, exchanges)

## 🚀 Quick Settings Overview (2 Minutes)

### Access Trading Settings
1. **Go to dashboard**: `http://localhost:8000`
2. **Click "System Settings"** or gear icon
3. **Select "Trading Settings"** tab
4. **Choose your configuration level**:
   - **Basic** (Recommended for beginners)
   - **Advanced** (For experienced users)

### Critical Safety Settings ⚠️
```yaml
# These MUST be configured first
trading_mode: "paper"           # ALWAYS start with paper trading
emergency_halt_enabled: true    # Enable emergency stop
max_daily_loss: 5.0%           # Maximum 5% daily loss
position_size_limit: 2.0%      # Maximum 2% per position
stop_loss_required: true       # Never trade without stops
```

## 📊 Basic Trading Settings

### Trading Mode Configuration

#### Paper Trading Mode (Recommended Start)
```yaml
# Safe virtual trading
trading_mode: "paper"
paper_trading:
  virtual_balance: 100000       # $100,000 virtual account
  realistic_slippage: true      # Simulate real trading costs
  commission_simulation: true   # Include commission costs
  delay_simulation: true       # Simulate execution delays
```

#### Live Trading Modes
```yaml
# Only after thorough testing
trading_modes:
  live_minimal:                 # Conservative live trading
    max_position_value: 10000   # $10,000 max position
    max_trades_per_day: 5       # Limited trade frequency
    additional_confirmations: true
    
  live_normal:                  # Standard live trading
    max_position_value: 50000   # $50,000 max position
    max_trades_per_day: 20      # Normal frequency
    
  live_aggressive:              # High-volume trading
    max_position_value: 100000  # $100,000 max position
    max_trades_per_day: 100     # High frequency
```

### Position Size Management

#### Fixed Dollar Amount
```yaml
# Simple fixed sizing
position_sizing:
  method: "fixed_dollar"
  amount: 10000                 # $10,000 per trade
  
  safety_limits:
    max_single_position: 50000  # Never exceed $50,000
    max_total_exposure: 200000  # Never exceed $200,000 total
```

#### Percentage of Account
```yaml
# Risk-based sizing
position_sizing:
  method: "percentage"
  percentage: 2.0               # 2% of account per trade
  
  account_balance: 500000       # $500,000 account
  max_risk_per_trade: 1.0       # 1% max risk (stop loss)
```

#### Kelly Criterion Sizing
```yaml
# Advanced mathematical sizing
position_sizing:
  method: "kelly"
  kelly_fraction: 0.25          # Conservative Kelly fraction
  
  calculation_period: 100       # Use last 100 trades
  max_kelly_position: 5.0       # Never exceed 5% of account
  min_kelly_position: 0.5       # Minimum 0.5% position
```

### Risk Limits

#### Daily Risk Limits
```yaml
# Daily trading limits
daily_limits:
  max_loss_amount: 5000         # $5,000 maximum daily loss
  max_loss_percentage: 2.0      # 2% of account maximum
  max_trades: 20                # Maximum 20 trades per day
  max_exposure: 100000          # $100,000 maximum exposure
  
  # Actions when limits hit
  limit_actions:
    halt_trading: true          # Stop all trading
    close_positions: false      # Keep existing positions
    alert_user: true           # Send immediate alert
```

#### Weekly Risk Limits
```yaml
# Weekly risk management
weekly_limits:
  max_loss_amount: 15000        # $15,000 maximum weekly loss
  max_loss_percentage: 5.0      # 5% of account maximum
  max_trades: 100               # Maximum 100 trades per week
  
  reset_day: "monday"           # Reset limits on Monday
```

#### Monthly Risk Limits
```yaml
# Monthly risk controls
monthly_limits:
  max_loss_amount: 50000        # $50,000 maximum monthly loss
  max_loss_percentage: 10.0     # 10% of account maximum
  max_drawdown: 15.0            # 15% maximum drawdown
```

## ⏰ Trading Hours & Schedule

### Market Hours Configuration
```yaml
# NQ Futures Trading Hours
market_hours:
  regular_session:
    start: "09:30"              # 9:30 AM ET
    end: "16:00"                # 4:00 PM ET
    timezone: "America/New_York"
    
  extended_hours:
    pre_market:
      start: "04:00"            # 4:00 AM ET
      end: "09:30"              # 9:30 AM ET
      reduced_size: true        # Use smaller positions
      
    after_hours:
      start: "16:00"            # 4:00 PM ET  
      end: "20:00"              # 8:00 PM ET
      reduced_size: true        # Use smaller positions
```

### Holiday Schedule
```yaml
# Market holidays (auto-updated)
holiday_settings:
  respect_market_holidays: true
  early_close_days:
    - "thanksgiving_friday"     # Day after Thanksgiving
    - "christmas_eve"           # December 24th
    - "new_years_eve"          # December 31st
    
  # Custom trading rules for holidays
  holiday_rules:
    reduced_size: 50%           # Half normal position size
    max_trades: 5               # Limited trades on holidays
```

### Session-Based Rules
```yaml
# Different rules for different sessions
session_rules:
  pre_market:
    max_position_percentage: 50%    # Half normal size
    confidence_boost: 10%           # Require higher confidence
    avoid_news_times: true          # Skip during news
    
  regular_hours:
    max_position_percentage: 100%   # Full position size
    standard_rules: true            # Normal operation
    
  lunch_hour:                       # 12:00-13:00 ET
    max_position_percentage: 25%    # Quarter size
    reduce_frequency: true          # Fewer trades
    
  power_hour:                       # 15:00-16:00 ET
    max_position_percentage: 75%    # Reduced size
    increased_monitoring: true      # Watch closely
```

## 📈 Market Condition Settings

### Volatility-Based Rules
```yaml
# Adjust trading based on market volatility
volatility_rules:
  vix_thresholds:
    low_volatility:               # VIX < 15
      threshold: 15
      actions:
        increase_position_size: 25%
        reduce_stop_distance: 10%
        look_for_breakouts: true
        
    normal_volatility:            # VIX 15-25
      threshold: 25
      actions:
        standard_operation: true
        
    high_volatility:              # VIX 25-40
      threshold: 40
      actions:
        reduce_position_size: 25%
        increase_stop_distance: 50%
        be_more_selective: true
        
    extreme_volatility:           # VIX > 40
      threshold: 100
      actions:
        reduce_position_size: 50%
        halt_new_entries: true
        focus_on_exits: true
```

### Volume-Based Rules
```yaml
# Trading based on volume conditions
volume_rules:
  minimum_volume:
    relative_volume: 1.2          # 120% of average volume
    absolute_minimum: 100000      # Minimum 100k contracts
    
  high_volume_rules:
    threshold: 200%               # 200% of average volume
    actions:
      increase_position_size: 15%
      reduce_confidence_threshold: 5%
      expect_continuation: true
      
  low_volume_rules:
    threshold: 80%                # 80% of average volume
    actions:
      reduce_position_size: 25%
      increase_confidence_threshold: 10%
      avoid_breakout_trades: true
```

### News Event Management
```yaml
# Handle major news events
news_event_rules:
  high_impact_events:
    - "FOMC_meeting"
    - "NFP_release"               # Non-Farm Payrolls
    - "CPI_data"                  # Inflation data
    - "GDP_release"
    
  event_rules:
    before_event:                 # 30 minutes before
      reduce_position_size: 50%
      halt_new_entries: true
      
    during_event:                 # During announcement
      halt_all_trading: true
      monitor_only: true
      
    after_event:                  # 15 minutes after
      gradual_resume: true
      increased_monitoring: true
      wider_stops: true
```

## 🎯 Order Management Settings

### Order Types Configuration
```yaml
# Available order types
order_types:
  market_orders:
    enabled: true
    slippage_tolerance: 0.1%      # 0.1% maximum slippage
    
  limit_orders:
    enabled: true
    default_offset: 0.05%         # 0.05% better than market
    timeout: 300                  # 5-minute timeout
    
  stop_orders:
    enabled: true
    guaranteed_stops: false       # Use regular stops (cheaper)
    
  stop_limit_orders:
    enabled: true
    limit_offset: 0.1%           # Limit 0.1% worse than stop
```

### Order Execution Rules
```yaml
# How orders are executed
execution_rules:
  default_order_type: "limit"     # Prefer limit orders
  
  market_order_conditions:        # When to use market orders
    - "high_urgency_exit"
    - "stop_loss_triggered"
    - "emergency_close"
    
  order_sizing:
    partial_fills_allowed: true
    minimum_fill_size: 100        # Minimum 100 shares
    
  retry_logic:
    max_retries: 3               # Try 3 times
    retry_delay: 5               # 5 seconds between retries
    price_adjustment: 0.05%      # Adjust price by 0.05% each retry
```

### Stop Loss Settings
```yaml
# Stop loss configuration
stop_loss:
  always_required: true          # Never trade without stops
  
  default_type: "percentage"     # "percentage", "atr", "technical"
  default_percentage: 1.0%       # 1% stop loss
  
  trailing_stops:
    enabled: true
    trail_percentage: 0.5%       # Trail by 0.5%
    activation_profit: 1.0%      # Start trailing at 1% profit
    
  atr_stops:
    multiplier: 2.0              # 2x ATR stop distance
    period: 14                   # 14-period ATR
    minimum_distance: 0.5%       # Minimum 0.5% stop
```

### Take Profit Settings
```yaml
# Take profit configuration
take_profit:
  default_ratio: 2.0             # 2:1 risk-reward minimum
  
  partial_profits:
    enabled: true
    levels:
      - percentage: 50           # Take 50% profit at 1.5R
        ratio: 1.5
      - percentage: 25           # Take 25% more at 2.5R
        ratio: 2.5
        
  trailing_profits:
    enabled: true
    trail_percentage: 1.0%       # Trail profits by 1%
    activation_ratio: 2.0        # Start trailing at 2R
```

## 🔧 Advanced Trading Settings

### Position Management
```yaml
# Advanced position handling
position_management:
  scaling_in:
    enabled: false               # Disabled by default (safer)
    max_scale_ins: 2            # Maximum 2 additional entries
    scale_distance: 0.5%        # 0.5% between entries
    
  scaling_out:
    enabled: true               # Take partial profits
    scale_points: [1.5, 2.0, 3.0]  # At 1.5R, 2R, 3R
    scale_percentages: [40, 30, 30]  # 40%, 30%, 30%
    
  position_monitoring:
    unrealized_pnl_alerts: true
    time_based_exits: true
    max_hold_time: "24h"        # Maximum 24 hours
```

### Risk Correlation Management
```yaml
# Manage correlated positions
correlation_management:
  max_correlation: 0.7          # Maximum 70% correlation
  
  correlation_checks:
    - "SPY"                     # S&P 500 ETF
    - "QQQ"                     # NASDAQ ETF
    - "IWM"                     # Russell 2000 ETF
    
  correlation_actions:
    reduce_size_if_correlated: true
    size_reduction: 50%         # Reduce by 50%
    diversification_bonus: 10%  # Increase size if uncorrelated
```

### Portfolio Heat Management
```yaml
# Overall portfolio risk
portfolio_heat:
  max_total_heat: 10%           # Maximum 10% portfolio risk
  
  heat_calculation:
    method: "sum_of_risks"      # Add up all position risks
    correlation_adjustment: true # Adjust for correlation
    
  heat_actions:
    warning_threshold: 7%       # Warn at 7%
    halt_threshold: 10%         # Halt at 10%
    reduce_threshold: 8%        # Start reducing at 8%
```

## 📱 Notification Settings

### Alert Configuration
```yaml
# Trading alerts
alerts:
  trade_execution:
    enabled: true
    channels: ["email", "dashboard"]
    
  risk_limit_warnings:
    enabled: true
    channels: ["email", "sms", "dashboard"]
    threshold: 80%              # Alert at 80% of limit
    
  emergency_situations:
    enabled: true
    channels: ["email", "sms", "phone", "dashboard"]
    immediate: true
```

### Performance Notifications
```yaml
# Performance-based alerts
performance_alerts:
  daily_pnl:
    positive_threshold: 2%      # Alert on +2% days
    negative_threshold: -1%     # Alert on -1% days
    
  weekly_performance:
    summary_enabled: true
    send_day: "sunday"
    
  monthly_reports:
    detailed_report: true
    include_analytics: true
```

## 🎛️ System Performance Settings

### Resource Management
```yaml
# System resource allocation
resources:
  max_concurrent_analyses: 10   # Maximum parallel analyses
  analysis_timeout: 30          # 30-second timeout
  
  memory_management:
    max_memory_per_agent: "512MB"
    cleanup_frequency: 300      # Clean up every 5 minutes
    
  cpu_management:
    max_cpu_per_agent: 25%      # 25% CPU per agent
    throttle_on_high_load: true
```

### Data Feed Settings
```yaml
# Market data configuration
data_feeds:
  primary_provider: "interactive_brokers"
  backup_provider: "tradingview"
  
  update_frequency: 1           # 1-second updates
  failover_time: 10            # 10-second failover
  
  quality_checks:
    validate_prices: true
    check_staleness: true
    max_stale_time: 5           # 5 seconds max stale data
```

## 📋 Settings Templates

### Conservative Settings Template
```yaml
# Perfect for beginners or capital preservation
conservative_template:
  trading_mode: "paper"
  max_daily_loss: 1.0%
  max_position_size: 1.0%
  stop_loss_required: true
  default_stop_percentage: 0.5%
  max_trades_per_day: 5
  confidence_threshold: 80%
  risk_reward_minimum: 3.0
```

### Balanced Settings Template
```yaml
# Good for intermediate users
balanced_template:
  trading_mode: "paper"          # Start with paper
  max_daily_loss: 2.0%
  max_position_size: 2.0%
  stop_loss_required: true
  default_stop_percentage: 1.0%
  max_trades_per_day: 15
  confidence_threshold: 70%
  risk_reward_minimum: 2.0
```

### Aggressive Settings Template
```yaml
# For experienced traders only
aggressive_template:
  trading_mode: "paper"          # Always test first
  max_daily_loss: 5.0%
  max_position_size: 3.0%
  stop_loss_required: true
  default_stop_percentage: 1.5%
  max_trades_per_day: 50
  confidence_threshold: 60%
  risk_reward_minimum: 1.5
```

## 🔍 Settings Validation

### Required Settings Checklist
- [ ] **Trading mode set** (start with paper)
- [ ] **Daily loss limit** configured
- [ ] **Position size limits** set
- [ ] **Stop loss required** enabled
- [ ] **Market hours** defined
- [ ] **Emergency halt** enabled

### Safety Validation Rules
```yaml
# Automatic safety checks
validation_rules:
  max_position_vs_account:
    rule: "position_size <= 5% of account"
    error: "Position size too large for account"
    
  stop_loss_vs_position:
    rule: "stop_loss_distance <= 50% of position"
    error: "Stop loss too wide"
    
  daily_risk_vs_account:
    rule: "daily_risk <= 10% of account"
    error: "Daily risk too high"
```

## 🚨 Emergency Procedures

### Emergency Settings
```yaml
# Emergency response configuration
emergency_procedures:
  emergency_halt:
    enabled: true
    hotkey: "CTRL+ALT+H"        # Quick halt hotkey
    confirm_required: false     # No confirmation for speed
    
  emergency_close_all:
    enabled: true
    hotkey: "CTRL+ALT+C"        # Close all positions
    confirm_required: true      # Confirmation required
    
  panic_mode:
    trigger_conditions:
      - "account_loss > 10%"
      - "system_errors > 5_per_minute"
      - "data_feed_failure > 30_seconds"
    
    panic_actions:
      - "halt_all_trading"
      - "close_all_positions"
      - "alert_all_channels"
      - "log_emergency_event"
```

---

**🚨 Critical Safety Reminder**: Always start with paper trading mode and conservative settings. Real money should only be used after thorough testing and validation.

**Next**: [Training Agents](training-agents.md) | [Risk Management](../configuration/risk-management.md) | [Emergency Controls](emergency-controls.md)
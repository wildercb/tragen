# Risk Management Configuration

Learn how to configure the multi-layer risk management system that protects your capital and prevents catastrophic losses. This is the most critical configuration for safe trading.

## 🎯 What is Risk Management?

Risk management is your **financial safety net** that:
- **Limits losses** on individual trades and daily activity
- **Prevents catastrophic drawdowns** that could wipe out your account
- **Automatically halts trading** when risk thresholds are exceeded
- **Protects your capital** so you can trade another day

**🚨 Critical**: Risk management is not optional. It's what keeps you in business when things go wrong.

## 🚀 Quick Risk Setup (5 Minutes)

### Step 1: Access Risk Configuration
1. **Go to dashboard**: `http://localhost:8000`
2. **Click "Settings"** → **"Risk Management"**
3. **Choose configuration level**:
   - **Basic** (Recommended for beginners)
   - **Advanced** (For experienced traders)

### Step 2: Set Core Risk Limits
```yaml
# Essential risk limits (start here)
core_risk_limits:
  max_loss_per_trade: 1.0%      # Never risk more than 1% per trade
  max_daily_loss: 2.0%          # Never lose more than 2% in one day  
  max_weekly_loss: 5.0%         # Never lose more than 5% in one week
  max_monthly_loss: 10.0%       # Never lose more than 10% in one month
  max_drawdown: 15.0%           # Never let account drop more than 15%
```

### Step 3: Enable Circuit Breakers
```yaml
# Automatic safety systems
circuit_breakers:
  daily_loss_breaker: true      # Auto-halt on daily loss limit
  consecutive_loss_breaker: true # Auto-halt after 5 consecutive losses
  volatility_breaker: true      # Auto-halt in extreme volatility
  system_error_breaker: true    # Auto-halt on system errors
```

## 🛡️ Multi-Layer Risk Management System

### Layer 1: Position Risk Management

#### Individual Trade Risk Limits
```yaml
# Control risk on each individual trade
position_risk:
  max_position_size:
    percentage: 2.0%            # Maximum 2% of account per position
    dollar_amount: 10000        # OR maximum $10,000 per position
    
  position_sizing_method:
    method: "fixed_percentage"   # "fixed_percentage", "kelly", "volatility_adjusted"
    percentage: 1.0%            # Risk 1% of account per trade
    
  stop_loss_requirements:
    always_required: true       # NEVER trade without a stop loss
    max_stop_distance: 2.0%     # Stop loss never more than 2% away
    min_stop_distance: 0.3%     # Stop loss never less than 0.3% away
```

#### Stop Loss Configuration
```yaml
# How stop losses are calculated and managed
stop_loss_config:
  default_method: "percentage"  # "percentage", "atr", "technical"
  
  percentage_stops:
    default_percentage: 1.0%    # Default 1% stop loss
    max_percentage: 2.0%        # Never wider than 2%
    min_percentage: 0.3%        # Never tighter than 0.3%
    
  atr_stops:
    multiplier: 2.0             # 2x ATR for stop distance
    period: 14                  # 14-period ATR calculation
    min_multiplier: 1.5         # Minimum 1.5x ATR
    max_multiplier: 3.0         # Maximum 3.0x ATR
    
  technical_stops:
    use_support_resistance: true # Use technical levels
    buffer_percentage: 0.1%     # 0.1% buffer beyond technical level
```

#### Position Size Calculation
```yaml
# How position sizes are calculated
position_sizing:
  account_balance: 100000       # $100,000 account
  risk_per_trade: 1.0%         # Risk 1% per trade ($1,000)
  
  calculation_example:
    entry_price: 15750          # NQ entry at 15,750
    stop_loss: 15600           # Stop loss at 15,600
    risk_per_point: 150        # Risk = 150 points
    position_size: 6.67        # $1,000 ÷ 150 points ÷ $1 per point = 6.67 contracts
    
  size_adjustments:
    round_down: true            # Always round down for safety
    min_position_size: 1        # Minimum 1 contract
    max_position_size: 50       # Maximum 50 contracts
```

### Layer 2: Portfolio Risk Management

#### Aggregate Position Limits
```yaml
# Control total exposure across all positions
portfolio_risk:
  max_total_exposure:
    percentage: 10.0%           # Never have more than 10% total exposure
    dollar_amount: 100000       # OR never more than $100,000 exposure
    
  max_positions:
    total_positions: 5          # Maximum 5 open positions
    per_symbol: 2              # Maximum 2 positions per symbol
    per_strategy: 3            # Maximum 3 positions per strategy
    
  correlation_limits:
    max_correlation: 0.7        # Don't hold highly correlated positions
    correlation_period: 30      # Calculate correlation over 30 days
```

#### Diversification Rules
```yaml
# Ensure portfolio diversification
diversification:
  by_timeframe:
    max_scalping_percentage: 30%     # Max 30% in scalping strategies
    max_day_trading_percentage: 50%   # Max 50% in day trading
    max_swing_trading_percentage: 40% # Max 40% in swing trading
    
  by_direction:
    max_long_percentage: 70%         # Max 70% long positions
    max_short_percentage: 70%        # Max 70% short positions
    
  by_strategy:
    max_per_strategy: 40%           # Max 40% in any single strategy
    min_strategies: 2               # Must use at least 2 strategies
```

#### Risk Budget Allocation
```yaml
# How to allocate risk across different activities
risk_budget:
  total_daily_risk: 2.0%          # 2% total daily risk budget
  
  allocation:
    conservative_strategies: 40%   # 40% to low-risk strategies
    balanced_strategies: 40%       # 40% to medium-risk strategies  
    aggressive_strategies: 20%     # 20% to high-risk strategies
    
  dynamic_allocation:
    increase_conservative_if: "recent_losses > 3"
    increase_aggressive_if: "recent_wins > 5"
    rebalance_frequency: "daily"
```

### Layer 3: Drawdown Protection

#### Maximum Drawdown Limits
```yaml
# Protect against large account drawdowns
drawdown_protection:
  max_drawdown_limits:
    daily: 2.0%                 # 2% maximum daily drawdown
    weekly: 5.0%                # 5% maximum weekly drawdown  
    monthly: 10.0%              # 10% maximum monthly drawdown
    peak_to_trough: 15.0%       # 15% maximum peak-to-trough drawdown
    
  drawdown_actions:
    warning_threshold: 50%      # Warn at 50% of drawdown limit
    reduce_size_threshold: 75%  # Reduce position sizes at 75%
    halt_threshold: 100%        # Halt trading at 100% of limit
    
  recovery_requirements:
    profitable_days: 3          # Need 3 profitable days before resuming
    profit_threshold: 1.0%      # Need 1% profit before resuming full size
```

#### Drawdown Recovery Protocol  
```yaml
# How to recover from drawdowns safely
recovery_protocol:
  drawdown_5_percent:
    action: "reduce_position_size"
    reduction: 25%              # Reduce positions by 25%
    
  drawdown_10_percent:
    action: "conservative_mode"
    max_risk_per_trade: 0.5%    # Reduce risk to 0.5% per trade
    require_higher_confidence: 10% # Need 10% higher confidence
    
  drawdown_15_percent:
    action: "emergency_halt"
    manual_restart_required: true
    full_system_review: true
```

### Layer 4: Volatility-Based Risk Management

#### Volatility Monitoring
```yaml
# Adjust risk based on market volatility
volatility_risk:
  volatility_measures:
    primary: "VIX"              # Use VIX as primary volatility measure
    secondary: "ATR"            # Use ATR as secondary measure
    
  volatility_thresholds:
    low_volatility: 15          # VIX < 15 = low volatility
    normal_volatility: 25       # VIX 15-25 = normal
    high_volatility: 35         # VIX 25-35 = high volatility
    extreme_volatility: 50      # VIX > 35 = extreme volatility
```

#### Volatility Adjustments
```yaml
# How to adjust risk based on volatility
volatility_adjustments:
  low_volatility:               # VIX < 15
    position_size_adjustment: 1.2 # Increase position size 20%
    stop_loss_adjustment: 0.8   # Tighter stops (20% closer)
    confidence_adjustment: -5%  # Lower confidence threshold
    
  normal_volatility:            # VIX 15-25
    position_size_adjustment: 1.0 # Normal position sizing
    stop_loss_adjustment: 1.0   # Normal stop distances
    confidence_adjustment: 0%   # Normal confidence threshold
    
  high_volatility:              # VIX 25-35
    position_size_adjustment: 0.7 # Reduce position size 30%
    stop_loss_adjustment: 1.5   # Wider stops (50% further)
    confidence_adjustment: 10%  # Higher confidence required
    
  extreme_volatility:           # VIX > 35
    position_size_adjustment: 0.5 # Reduce position size 50%
    stop_loss_adjustment: 2.0   # Much wider stops
    confidence_adjustment: 20%  # Much higher confidence required
    halt_new_trades: true      # Consider halting new trades
```

## 🚨 Circuit Breaker System

### Daily Loss Circuit Breaker
```yaml
# Automatic halt on excessive daily losses
daily_loss_breaker:
  enabled: true
  
  thresholds:
    warning: 1.5%               # Warn at 1.5% daily loss
    critical: 2.0%              # Halt at 2.0% daily loss
    
  actions:
    warning_actions:
      - "send_alert"
      - "reduce_position_sizes_25%"
      - "increase_monitoring"
      
    critical_actions:
      - "halt_all_trading"
      - "send_emergency_alert"
      - "close_new_positions_only"  # Keep existing positions
      
  reset_conditions:
    reset_time: "00:00"         # Reset at midnight
    manual_reset_required: true # Require manual confirmation
```

### Consecutive Loss Circuit Breaker
```yaml
# Halt after too many consecutive losses
consecutive_loss_breaker:
  enabled: true
  
  thresholds:
    consecutive_losses: 5       # Halt after 5 consecutive losses
    loss_amount: 1000          # OR halt if consecutive losses > $1,000
    
  actions:
    - "halt_trading"
    - "require_manual_review"
    - "send_detailed_report"
    
  reset_conditions:
    profitable_trade_required: true  # Need 1 profitable trade
    manual_review_required: true     # Need manual review
    cooldown_period: 3600           # 1 hour cooldown minimum
```

### Volatility Circuit Breaker
```yaml
# Halt during extreme market volatility
volatility_breaker:
  enabled: true
  
  triggers:
    vix_spike: 40               # Halt if VIX > 40
    price_move: 3.0%           # Halt if NQ moves > 3% in 15 minutes
    volume_spike: 300%         # Halt if volume > 300% of average
    
  actions:
    immediate:
      - "halt_new_trades"
      - "alert_all_users"
      - "monitor_existing_positions"
      
    after_5_minutes:
      - "reassess_market_conditions"
      - "consider_position_reductions"
      
  resume_conditions:
    volatility_normalized: true # VIX back under 30
    time_elapsed: 900          # At least 15 minutes
    manual_approval: true      # Manual approval required
```

### System Error Circuit Breaker
```yaml
# Halt on system malfunctions
system_error_breaker:
  enabled: true
  
  triggers:
    api_errors: 5              # 5 API errors per minute
    data_feed_failure: 30      # 30 seconds without data
    execution_failures: 3      # 3 failed trade executions
    memory_usage: 95%          # 95% memory usage
    
  actions:
    immediate:
      - "halt_all_trading"
      - "alert_system_admin"
      - "save_system_state"
      
    diagnostic:
      - "run_system_diagnostics"
      - "check_all_connections"
      - "verify_data_integrity"
      
  recovery_procedure:
    fix_errors: true           # Fix identified errors
    system_test: true          # Test system functionality
    gradual_restart: true      # Restart gradually with monitoring
```

## ⚙️ Advanced Risk Configuration

### Dynamic Risk Adjustment
```yaml
# Automatically adjust risk based on performance
dynamic_risk:
  performance_based_adjustment:
    enabled: true
    
    good_performance:          # Win rate > 70% for 20 trades
      trigger: "win_rate > 0.7 AND trades >= 20"
      adjustment: "increase_risk_10%"
      max_increase: 25%        # Never increase more than 25%
      
    poor_performance:          # Win rate < 40% for 20 trades
      trigger: "win_rate < 0.4 AND trades >= 20"
      adjustment: "decrease_risk_20%"
      min_risk: 0.5%          # Never go below 0.5% risk per trade
      
  market_condition_adjustment:
    trending_market:           # Clear trend identified
      risk_multiplier: 1.1     # Increase risk 10%
      
    ranging_market:            # Sideways market
      risk_multiplier: 0.9     # Decrease risk 10%
      
    uncertain_market:          # Mixed signals
      risk_multiplier: 0.7     # Decrease risk 30%
```

### Risk Correlation Management
```yaml
# Manage risk across correlated positions
correlation_management:
  correlation_monitoring:
    enabled: true
    symbols: ["NQ", "ES", "QQQ", "SPY"]  # Monitor these correlations
    lookback_period: 30        # 30-day correlation calculation
    
  correlation_adjustments:
    high_correlation:          # > 0.8 correlation
      threshold: 0.8
      action: "reduce_combined_size_50%"
      
    moderate_correlation:      # 0.5-0.8 correlation  
      threshold: 0.5
      action: "reduce_combined_size_25%"
      
    low_correlation:           # < 0.5 correlation
      threshold: 0.5
      action: "allow_normal_sizing"
      
  diversification_bonus:
    uncorrelated_positions: 10% # 10% size bonus for uncorrelated positions
    negative_correlation: 15%   # 15% bonus for negatively correlated positions
```

### Time-Based Risk Management
```yaml
# Adjust risk based on time of day/week/month
time_based_risk:
  intraday_adjustments:
    market_open:               # First 30 minutes
      time: "09:30-10:00"
      risk_multiplier: 0.5     # Half normal risk
      reason: "High volatility period"
      
    lunch_hour:                # Lunch hour
      time: "12:00-13:00" 
      risk_multiplier: 0.7     # Reduced risk
      reason: "Lower volume, choppier price action"
      
    close:                     # Last 30 minutes
      time: "15:30-16:00"
      risk_multiplier: 0.6     # Reduced risk
      reason: "End of day volatility"
      
  weekly_adjustments:
    monday:
      risk_multiplier: 0.8     # Reduced risk (gap risk)
      
    friday:
      risk_multiplier: 0.9     # Slightly reduced (weekend risk)
      
  monthly_adjustments:
    options_expiration_week:
      risk_multiplier: 0.7     # Reduced risk (higher volatility)
      
    month_end:
      risk_multiplier: 0.8     # Reduced risk (rebalancing flows)
```

## 📊 Risk Monitoring and Reporting

### Real-Time Risk Dashboard
```yaml
# Key risk metrics to monitor
risk_dashboard:
  current_risk_metrics:
    daily_pnl: "-$750"         # Current daily P&L
    daily_risk_used: "37.5%"   # Percentage of daily risk budget used
    open_positions: 3          # Number of open positions
    total_exposure: "$45,000"  # Total dollar exposure
    portfolio_beta: 1.15       # Portfolio beta to market
    
  risk_limits_status:
    daily_loss_limit: "75% used"      # 75% of daily limit used
    position_size_limit: "40% used"   # 40% of max position size used
    drawdown_limit: "25% used"        # 25% of max drawdown used
    
  circuit_breaker_status:
    daily_loss_breaker: "armed"      # Ready to trigger
    consecutive_loss_breaker: "3/5"  # 3 of 5 losses toward trigger
    volatility_breaker: "normal"     # Normal market conditions
    system_error_breaker: "armed"    # Ready to trigger
```

### Risk Alerts Configuration
```yaml
# When to send risk alerts
risk_alerts:
  real_time_alerts:
    position_risk_exceeded:
      threshold: "position > 2.5% of account"
      channel: ["email", "dashboard", "sms"]
      priority: "high"
      
    daily_risk_warning:
      threshold: "daily_loss > 1.5%"
      channel: ["email", "dashboard"]
      priority: "medium"
      
    correlation_spike:
      threshold: "correlation > 0.8"
      channel: ["dashboard"]
      priority: "low"
      
  summary_alerts:
    daily_risk_report:
      time: "16:30"              # After market close
      content: ["daily_pnl", "risk_usage", "limit_status"]
      
    weekly_risk_review:
      day: "sunday"
      time: "20:00"
      content: ["weekly_performance", "risk_analysis", "recommendations"]
```

## 🔧 Risk Configuration Templates

### Conservative Risk Template
```yaml
# For beginners or those prioritizing capital preservation
conservative_risk_template:
  position_risk:
    max_risk_per_trade: 0.5%    # Very small risk per trade
    max_position_size: 1.0%     # Small position sizes
    stop_loss_required: true    # Always use stops
    
  portfolio_risk:
    max_daily_loss: 1.0%        # Small daily loss limit
    max_total_exposure: 5.0%    # Limited total exposure
    max_positions: 3            # Few positions at once
    
  circuit_breakers:
    daily_loss_threshold: 0.8%  # Halt early
    consecutive_losses: 3       # Halt after 3 losses
    volatility_threshold: 25    # Halt at moderate volatility
```

### Balanced Risk Template
```yaml
# For intermediate traders seeking balanced approach
balanced_risk_template:
  position_risk:
    max_risk_per_trade: 1.0%    # Standard risk per trade
    max_position_size: 2.0%     # Moderate position sizes
    stop_loss_required: true    # Always use stops
    
  portfolio_risk:
    max_daily_loss: 2.0%        # Reasonable daily loss limit
    max_total_exposure: 10.0%   # Moderate total exposure
    max_positions: 5            # Several positions allowed
    
  circuit_breakers:
    daily_loss_threshold: 2.0%  # Standard halt threshold
    consecutive_losses: 5       # Halt after 5 losses
    volatility_threshold: 35    # Halt at high volatility
```

### Aggressive Risk Template
```yaml
# For experienced traders comfortable with higher risk
aggressive_risk_template:
  position_risk:
    max_risk_per_trade: 2.0%    # Higher risk per trade
    max_position_size: 3.0%     # Larger position sizes
    stop_loss_required: true    # Still always use stops
    
  portfolio_risk:
    max_daily_loss: 5.0%        # Higher daily loss limit
    max_total_exposure: 20.0%   # Higher total exposure
    max_positions: 8            # More positions allowed
    
  circuit_breakers:
    daily_loss_threshold: 5.0%  # Higher halt threshold
    consecutive_losses: 7       # More losses before halt
    volatility_threshold: 45    # Halt only at extreme volatility
```

## 🎯 Risk Management Best Practices

### Essential Risk Rules
1. **Never trade without stops** - every position needs a predefined exit
2. **Never risk more than you can afford** - use position sizing
3. **Diversify your risk** - don't put all eggs in one basket  
4. **Respect your limits** - when hit, stop and reassess
5. **Always have an exit plan** - know when and how you'll exit

### Common Risk Management Mistakes
❌ **Setting stops too tight** - getting stopped out by normal volatility
❌ **Setting stops too wide** - risking too much on individual trades
❌ **Moving stops against you** - turning winners into losers
❌ **Ignoring correlation** - having multiple similar positions
❌ **Risking more after losses** - trying to "get even" quickly

### Position Sizing Guidelines
```yaml
# How much to risk based on account size
position_sizing_guidelines:
  small_account: "$10K-50K"
    max_risk_per_trade: 1.0%    # $100-500 per trade
    max_daily_risk: 2.0%        # $200-1000 per day
    
  medium_account: "$50K-500K"
    max_risk_per_trade: 1.5%    # $750-7500 per trade
    max_daily_risk: 3.0%        # $1500-15000 per day
    
  large_account: "$500K+"
    max_risk_per_trade: 2.0%    # $10000+ per trade
    max_daily_risk: 4.0%        # $20000+ per day
```

---

**🚨 Critical Remember**: Risk management is what separates successful traders from those who lose everything. No trading strategy is worth risking your entire account. When in doubt, risk less, not more.

**Next**: [Data Sources](data-sources.md) | [Emergency Controls](../user-guides/emergency-controls.md) | [Trading Settings](../user-guides/trading-settings.md)
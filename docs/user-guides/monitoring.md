# Monitoring & Alerts Guide

Learn how to monitor your AI trading agents, set up alerts, and understand system performance metrics. Everything can be configured through the web interface without coding.

## 🎯 What is Monitoring?

Monitoring helps you:
- **Track agent performance** in real-time
- **Get alerts** for important events
- **Identify problems** before they become serious
- **Optimize your trading** based on data

Think of it as your trading system's "mission control" - keeping watch over everything.

## 🚀 Quick Monitoring Setup (3 Minutes)

### Step 1: Access Monitoring Dashboard
1. **Go to your main dashboard**: `http://localhost:8000`
2. **Click "Monitoring"** in the navigation menu
3. **You'll see the main monitoring interface**

### Step 2: Enable Basic Alerts
1. **Click "Alert Settings"** (🔔 icon)
2. **Enable essential alerts**:
   - ✅ Trading halts
   - ✅ Large losses
   - ✅ System errors
   - ✅ Agent performance issues
3. **Choose notification methods**:
   - ✅ Email alerts
   - ✅ Dashboard notifications
   - ⬜ SMS (optional, requires setup)

### Step 3: Verify Everything is Working
- **Green status indicators** across the dashboard
- **Agent heartbeats** showing regular activity  
- **No critical alerts** in the alert panel
- **Real-time data updates** every few seconds

## 📊 Monitoring Dashboard Overview

### Main Dashboard Sections

#### System Status Panel
```
🟢 System Status: Healthy
├── 🔄 Trading Engine: Running
├── 💾 Database: Connected  
├── 📡 Data Feeds: Active
├── 🤖 AI Models: Available
└── ⚡ API Status: Normal
```

#### Agent Overview
```
👥 Active Agents: 3/5
├── Agent 1: 🟢 Trading (Paper)
├── Agent 2: 🟡 Paused (Risk Limit)
├── Agent 3: 🟢 Analyzing
├── Agent 4: ⚪ Stopped
└── Agent 5: ⚪ Inactive
```

#### Performance Summary
```
📈 Today's Performance:
├── Total PnL: +$1,247 (Paper)
├── Trades: 23 (15 wins, 8 losses)
├── Win Rate: 65.2%
├── Profit Factor: 1.84
└── Max Drawdown: -$312
```

#### Recent Activity Feed
```
📰 Recent Activity:
├── 10:15 - Agent 1 opened NQ long position
├── 10:12 - Risk limit warning (Agent 2)
├── 10:08 - Market volatility spike detected
├── 10:05 - Agent 3 closed profitable trade
└── 10:01 - System health check completed
```

## 🔔 Alert System Configuration

### Alert Types and Priorities

#### Critical Alerts (Red) 🚨
```yaml
critical_alerts:
  emergency_halt:
    description: "Trading halted due to emergency"
    immediate_action: "Review system status immediately"
    
  system_failure:
    description: "Core system component failed"
    immediate_action: "Check system logs and restart if needed"
    
  large_loss:
    threshold: "> 5% daily loss"
    description: "Significant trading loss detected"
    immediate_action: "Review trading decisions and risk settings"
    
  data_feed_failure:
    description: "Market data feed disconnected"
    immediate_action: "Check data connections and backup feeds"
```

#### Warning Alerts (Yellow) ⚠️
```yaml
warning_alerts:
  approaching_risk_limit:
    threshold: "> 80% of daily loss limit"
    description: "Approaching daily risk limit"
    action: "Monitor closely, consider reducing positions"
    
  low_performance:
    threshold: "Win rate < 40% over 20 trades"
    description: "Agent performance below expectations"
    action: "Review agent configuration and training"
    
  high_volatility:
    threshold: "VIX > 30"
    description: "Market volatility elevated"
    action: "Consider reducing position sizes"
    
  api_latency:
    threshold: "> 500ms response time"
    description: "Trading API responding slowly"
    action: "Monitor execution quality"
```

#### Info Alerts (Blue) ℹ️
```yaml
info_alerts:
  trade_execution:
    description: "Trade executed successfully"
    action: "No action required"
    
  daily_summary:
    description: "End of day performance summary"
    action: "Review daily results"
    
  agent_learning:
    description: "Agent completed training session"
    action: "Review training results"
    
  system_maintenance:
    description: "Scheduled maintenance completed"
    action: "Verify system is functioning normally"
```

### Notification Channels

#### Email Notifications
```yaml
# Email setup
email_notifications:
  enabled: true
  email_address: "your-email@example.com"
  
  alert_levels:
    - "critical"        # Always send critical alerts
    - "warning"         # Send warnings during trading hours
    
  frequency_limits:
    max_per_hour: 10    # Don't spam with too many emails
    digest_mode: false  # Send individual emails (not digest)
    
  template_settings:
    include_charts: true      # Include performance charts
    include_recommendations: true  # Include suggested actions
```

#### Dashboard Notifications
```yaml
# In-app notifications
dashboard_notifications:
  enabled: true
  
  display_settings:
    show_popup: true          # Show popup for critical alerts
    auto_dismiss: false       # Don't auto-dismiss important alerts
    sound_enabled: true       # Play sound for alerts
    
  history_retention: 168      # Keep 7 days of alert history
```

#### SMS Notifications (Optional)
```yaml
# SMS setup (requires SMS provider)
sms_notifications:
  enabled: false              # Disabled by default
  phone_number: "+1234567890"
  
  alert_levels:
    - "critical"              # Only critical alerts via SMS
    
  rate_limiting:
    max_per_day: 5           # Maximum 5 SMS per day
    cooldown_minutes: 30     # 30 minutes between SMS
```

## 📈 Performance Monitoring

### Key Performance Indicators (KPIs)

#### Trading Performance Metrics
```yaml
# What to monitor for trading success
trading_kpis:
  profitability:
    total_pnl: "$2,450"           # Total profit/loss
    daily_pnl: "+$125"            # Today's profit/loss  
    win_rate: "68%"               # Percentage of winning trades
    profit_factor: "1.85"         # Total wins ÷ total losses
    
  risk_management:
    max_drawdown: "-$890"         # Largest losing streak
    sharpe_ratio: "1.42"          # Risk-adjusted returns
    average_win: "$275"           # Average winning trade
    average_loss: "-$145"         # Average losing trade
    
  efficiency:
    trades_per_day: "12"          # Trading frequency
    hit_rate: "65%"               # Profitable vs unprofitable
    expectancy: "$18.50"          # Expected value per trade
```

#### System Performance Metrics
```yaml
# Technical system performance
system_kpis:
  reliability:
    uptime: "99.8%"               # System availability
    error_rate: "0.2%"            # Error frequency
    data_quality: "99.9%"         # Data accuracy
    
  performance:
    avg_response_time: "45ms"     # API response speed
    trade_execution_time: "120ms" # Time to execute trades
    analysis_time: "2.3s"        # Time for market analysis
    
  resource_usage:
    cpu_usage: "45%"              # CPU utilization
    memory_usage: "67%"           # Memory utilization
    disk_usage: "23%"             # Storage utilization
```

### Performance Dashboards

#### Real-Time Trading Dashboard
```
📍 Real-Time Performance (Updating every 5 seconds)

Current Positions:        Portfolio Value:
├── NQ Long: +$245       ├── Total: $152,450
├── NQ Short: -$87       ├── Available: $47,550
└── Cash: $47,550        └── Margin Used: $104,900

Today's Activity:         Risk Metrics:
├── Trades: 8            ├── Daily Risk: 2.3%
├── PnL: +$158          ├── Position Risk: 1.8%
├── Win Rate: 75%        └── Portfolio Heat: 4.1%
```

#### Historical Performance Dashboard
```
📊 Historical Performance (Last 30 Days)

Monthly Summary:          Best/Worst Days:
├── Total PnL: +$4,890   ├── Best: +$890 (Feb 15)
├── Trading Days: 22     ├── Worst: -$456 (Feb 08)
├── Win Rate: 63%        ├── Avg Win: +$285
└── Profit Factor: 1.67  └── Avg Loss: -$165

Weekly Breakdown:
├── Week 1: +$1,245 (4 days)
├── Week 2: +$890 (5 days)  
├── Week 3: -$235 (5 days)
└── Week 4: +$2,990 (5 days)
```

## 🚨 Alert Configuration Examples

### Conservative Alert Setup
```yaml
# Good for beginners or risk-averse traders
conservative_alerts:
  loss_alerts:
    daily_loss_warning: 1.0%     # Warn at 1% daily loss
    daily_loss_critical: 2.0%    # Critical at 2% daily loss
    
  position_alerts:
    large_position_warning: 1.5% # Warn at 1.5% position size
    max_position_critical: 2.0%  # Critical at 2% position size
    
  performance_alerts:
    low_win_rate: 50%            # Alert if win rate < 50%
    consecutive_losses: 3        # Alert after 3 losses in a row
```

### Aggressive Alert Setup  
```yaml
# For experienced traders comfortable with higher risk
aggressive_alerts:
  loss_alerts:
    daily_loss_warning: 3.0%     # Warn at 3% daily loss
    daily_loss_critical: 5.0%    # Critical at 5% daily loss
    
  position_alerts:
    large_position_warning: 3.0% # Warn at 3% position size
    max_position_critical: 5.0%  # Critical at 5% position size
    
  performance_alerts:
    low_win_rate: 35%            # Alert if win rate < 35%
    consecutive_losses: 5        # Alert after 5 losses in a row
```

### Balanced Alert Setup
```yaml
# Good middle ground for most traders
balanced_alerts:
  loss_alerts:
    daily_loss_warning: 2.0%     # Warn at 2% daily loss
    daily_loss_critical: 3.5%    # Critical at 3.5% daily loss
    
  position_alerts:
    large_position_warning: 2.0% # Warn at 2% position size  
    max_position_critical: 3.0%  # Critical at 3% position size
    
  performance_alerts:
    low_win_rate: 45%            # Alert if win rate < 45%
    consecutive_losses: 4        # Alert after 4 losses in a row
```

## 📱 Mobile Monitoring Setup

### Dashboard Mobile View
The monitoring dashboard is mobile-responsive, allowing you to:
- **Check system status** from anywhere
- **View current positions** and PnL
- **Receive push notifications** for critical alerts
- **Execute emergency controls** if needed

### Mobile Alert Setup
```yaml
# Mobile-specific settings
mobile_alerts:
  push_notifications:
    enabled: true
    critical_only: true          # Only critical alerts on mobile
    
  location_based:
    trading_hours_only: true     # Only during market hours
    timezone_aware: true         # Respect your timezone
    
  battery_optimization:
    reduce_frequency: true       # Less frequent updates to save battery
    essential_only: true         # Only essential information
```

## 🔍 Advanced Monitoring Features

### Custom Dashboards

#### Create Performance Dashboard
1. **Click "Create Dashboard"** in monitoring section
2. **Choose widgets** to include:
   - Real-time PnL chart
   - Win rate gauge
   - Recent trades list
   - Risk metrics panel
3. **Arrange layout** by dragging widgets
4. **Save dashboard** with descriptive name

#### Widget Options
```yaml
available_widgets:
  charts:
    - "pnl_chart"              # Profit/loss over time
    - "equity_curve"           # Account balance curve
    - "drawdown_chart"         # Drawdown visualization
    
  gauges:
    - "win_rate_gauge"         # Win rate percentage
    - "profit_factor_gauge"    # Profit factor meter
    - "risk_meter"             # Current risk level
    
  tables:
    - "recent_trades"          # Latest trade history
    - "active_positions"       # Current open positions
    - "agent_performance"      # Agent comparison table
    
  metrics:
    - "key_statistics"         # Important numbers
    - "system_health"          # Technical metrics
    - "alert_summary"          # Recent alerts
```

### Automated Reports

#### Daily Performance Reports
```yaml
# Automated daily email report
daily_report:
  enabled: true
  send_time: "17:00"            # 5 PM ET (after market close)
  
  content:
    - "daily_pnl_summary"       # Today's profit/loss
    - "trade_breakdown"         # Individual trade details
    - "risk_metrics"            # Risk management stats
    - "agent_performance"       # How each agent performed
    - "tomorrow_outlook"        # Market outlook for next day
```

#### Weekly Summary Reports  
```yaml
# Weekly comprehensive report
weekly_report:
  enabled: true
  send_day: "sunday"
  send_time: "20:00"            # Sunday evening
  
  content:
    - "weekly_performance"      # Week's trading results
    - "strategy_analysis"       # Which strategies worked best
    - "risk_analysis"           # Risk metrics and compliance
    - "agent_comparison"        # Compare agent performance
    - "improvement_suggestions" # Recommendations for next week
```

### Log Monitoring

#### System Log Alerts
```yaml
# Monitor system logs for issues
log_monitoring:
  error_patterns:
    - "connection.*failed"      # Connection failures
    - "timeout.*occurred"       # Timeout issues  
    - "insufficient.*funds"     # Account balance issues
    - "invalid.*order"          # Order problems
    
  alert_thresholds:
    error_rate: 5               # Alert if > 5 errors per minute
    warning_rate: 20            # Alert if > 20 warnings per minute
    
  log_retention:
    keep_days: 30               # Keep 30 days of logs
    compress_after: 7           # Compress logs after 7 days
```

## 🎯 Monitoring Best Practices

### What to Monitor Daily
- [ ] **System status** - all components green
- [ ] **Agent performance** - trading as expected
- [ ] **Risk metrics** - within acceptable limits
- [ ] **Alert history** - no critical issues
- [ ] **Market conditions** - volatility and volume

### Weekly Review Checklist
- [ ] **Performance analysis** - review weekly results
- [ ] **Risk analysis** - check risk metrics and compliance
- [ ] **Agent optimization** - identify improvement opportunities
- [ ] **System health** - review technical performance
- [ ] **Alert optimization** - adjust alert thresholds if needed

### Monthly Deep Dive
- [ ] **Comprehensive performance review** - detailed analysis
- [ ] **Strategy effectiveness** - which strategies work best
- [ ] **Risk management effectiveness** - how well risk is controlled
- [ ] **System optimization** - technical improvements needed
- [ ] **Training needs** - agent training requirements

## 🚨 Troubleshooting Monitoring Issues

### Common Problems and Solutions

#### Problem: Not Receiving Alerts
```yaml
troubleshooting_steps:
  1. Check alert settings are enabled
  2. Verify email address is correct
  3. Check spam folder for emails
  4. Test alert system with manual trigger
  5. Review notification channel settings
```

#### Problem: Dashboard Not Updating
```yaml
troubleshooting_steps:
  1. Refresh browser page (Ctrl+F5)
  2. Check internet connection
  3. Verify system status is healthy
  4. Clear browser cache and cookies
  5. Try different browser or device
```

#### Problem: Performance Metrics Seem Wrong
```yaml
troubleshooting_steps:
  1. Check if in paper trading vs live mode
  2. Verify time period for calculations
  3. Check for data feed issues
  4. Review trade history for accuracy
  5. Compare with broker statements
```

### Emergency Monitoring Procedures

#### If Critical Alert is Triggered
1. **Immediately assess** the situation
2. **Check system status** dashboard
3. **Review recent trades** and positions
4. **Consider emergency halt** if necessary
5. **Document the incident** for analysis

#### If System Appears Unresponsive
1. **Try refreshing** the dashboard
2. **Check system logs** for errors
3. **Verify network connectivity**
4. **Use emergency controls** if available
5. **Contact support** if problem persists

---

**💡 Remember**: Good monitoring is like having a co-pilot - it helps you stay aware of everything happening with your trading system and alerts you to issues before they become problems.

**Next**: [Emergency Controls](emergency-controls.md) | [Risk Management](../configuration/risk-management.md) | [Agent Configuration](agent-configuration.md)
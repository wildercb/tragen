# Emergency Controls Guide

Learn how to use emergency controls to immediately halt trading, close positions, and protect your capital in critical situations. These controls are designed for instant access without any delays.

## 🚨 Critical: Emergency Controls Overview

Emergency controls are your **last line of defense** when:
- **System is malfunctioning** and trading incorrectly
- **Market conditions** become extreme and dangerous
- **Large losses** are occurring rapidly
- **You need to stop everything** immediately

**⚠️ Important**: Emergency controls should only be used in true emergencies. They will immediately halt all trading and may cause some temporary disruption.

## 🚀 Quick Emergency Access (30 Seconds)

### Emergency Controls Location
**Three ways to access emergency controls:**

#### Method 1: Dashboard Emergency Panel
1. **Go to dashboard**: `http://localhost:8000`
2. **Look for red "EMERGENCY" panel** (always visible)
3. **Big red buttons** for immediate action

#### Method 2: Keyboard Shortcuts (Fastest)
```
🔴 Emergency Halt: Ctrl + Alt + H
🔴 Close All Positions: Ctrl + Alt + C  
🔴 System Shutdown: Ctrl + Alt + S
```

#### Method 3: Emergency URL (If Dashboard Fails)
```
Direct emergency halt: http://localhost:8000/emergency/halt
Close all positions: http://localhost:8000/emergency/close-all
System status: http://localhost:8000/emergency/status
```

### Primary Emergency Actions

#### 🛑 Emergency Halt (Most Common)
```
What it does:
✅ Stops all new trades immediately
✅ Cancels pending orders
✅ Keeps existing positions open
✅ Prevents any new decisions
✅ Logs the emergency event

Use when:
- System is making bad decisions
- Market conditions are extreme
- You need time to assess situation
```

#### 🔴 Close All Positions (Nuclear Option)
```
What it does:
✅ Immediately closes ALL open positions
✅ Cancels all pending orders  
✅ Halts all trading activity
✅ Locks down the entire system
✅ Requires manual restart

Use when:
- Large losses occurring rapidly
- System completely malfunctioning
- Critical data feed failures
- True financial emergency
```

## 🎯 Emergency Scenarios and Responses

### Scenario 1: Agent Making Bad Trades
```
🚨 Situation: Your agent opened 5 losing trades in 10 minutes

Immediate Action:
1. Press Ctrl + Alt + H (Emergency Halt)
2. Review open positions in dashboard
3. Manually close losing positions if needed
4. Check system logs for errors
5. Review agent configuration before restarting

Why Emergency Halt (not Close All):
- Keeps profitable positions open
- Gives you time to assess each position
- Less disruptive than closing everything
```

### Scenario 2: System Freezing/Crashing
```
🚨 Situation: Dashboard not responding, trades not executing properly

Immediate Action:
1. Try Ctrl + Alt + H first
2. If no response, use emergency URL
3. If still no response, use Ctrl + Alt + C (Close All)
4. Check system status externally
5. Restart system if necessary

Why Close All Positions:
- Unknown system state is dangerous
- Better to exit everything safely
- Can reassess and re-enter later
```

### Scenario 3: Market Flash Crash
```
🚨 Situation: Market dropping 10% in minutes, massive volatility

Immediate Action:  
1. Press Ctrl + Alt + C (Close All Positions)
2. Wait for market stabilization
3. Review account status
4. Check for any system errors
5. Plan re-entry strategy when market calms

Why Close All Positions:
- Extreme market moves are unpredictable
- Protect capital is priority #1
- Can re-enter when conditions normalize
```

### Scenario 4: Data Feed Failure
```
🚨 Situation: Price data is stale or incorrect, agents trading on bad data

Immediate Action:
1. Press Ctrl + Alt + H (Emergency Halt)
2. Check data feed status in system panel  
3. Verify current market prices externally
4. Close positions if data is significantly wrong
5. Fix data feeds before resuming

Why Emergency Halt:
- Bad data leads to bad decisions
- Need to verify position values with correct data
- Can resume once data feeds are fixed
```

## 🛠️ Emergency Control Configurations

### Emergency Control Settings
```yaml
# Configure emergency controls
emergency_settings:
  confirmation_required:
    emergency_halt: false        # No confirmation - instant action
    close_all_positions: true    # Requires confirmation (destructive)
    system_shutdown: true        # Requires confirmation
    
  auto_notifications:
    email_immediately: true      # Send email when emergency triggered
    sms_if_configured: true      # Send SMS if phone number set
    log_all_actions: true        # Log every emergency action
    
  timeout_settings:
    halt_timeout: 30             # 30 seconds to execute halt
    close_timeout: 60            # 60 seconds to close all positions
    status_check_interval: 5     # Check status every 5 seconds
```

### Emergency Authorization
```yaml
# Who can use emergency controls
authorization:
  emergency_halt:
    required_level: "user"       # Any user can halt
    
  close_all_positions:
    required_level: "admin"      # Admin only for closing all
    confirmation_phrase: "CLOSE ALL POSITIONS"  # Must type this phrase
    
  system_shutdown:
    required_level: "admin"      # Admin only
    two_factor_required: true    # Requires 2FA if enabled
```

### Recovery Procedures
```yaml
# After emergency action, how to recover
recovery_settings:
  auto_restart:
    enabled: false               # Never auto-restart after emergency
    
  manual_restart_required:
    system_check: true           # Check all systems before restart
    user_confirmation: true      # User must confirm restart
    log_review: true            # Review logs before restart
    
  restart_safety_mode:
    paper_trading_only: true     # Restart in paper mode first
    reduced_position_sizes: true # Use smaller positions initially
    increased_monitoring: true   # Extra monitoring after restart
```

## 🔧 Advanced Emergency Features

### Partial Emergency Controls

#### Halt Specific Agent
```yaml
# Stop just one problematic agent
agent_emergency_halt:
  target: "agent_id_123"
  action: "halt"
  reason: "Poor performance - 5 consecutive losses"
  
  result:
    agent_status: "halted"
    positions: "maintained"      # Keep existing positions
    new_trades: "blocked"        # No new trades allowed
```

#### Halt Specific Strategy
```yaml
# Stop a particular trading strategy
strategy_emergency_halt:
  target: "scalping_strategy"
  action: "halt"
  reason: "Strategy not working in current market conditions"
  
  result:
    affected_agents: ["agent_1", "agent_3", "agent_5"]
    other_strategies: "continue"  # Other strategies keep running
```

#### Reduce All Position Sizes
```yaml
# Emergency position size reduction
emergency_position_reduction:
  action: "reduce_all_positions"
  reduction_factor: 0.5          # Cut all positions in half
  reason: "High market volatility detected"
  
  result:
    position_sizes: "reduced_50%"
    trading: "continues"         # Trading continues with smaller sizes
    risk: "reduced"              # Overall risk reduced
```

### Automated Emergency Triggers

#### Loss-Based Triggers
```yaml
# Automatic emergency actions based on losses
automated_triggers:
  daily_loss_halt:
    threshold: 5.0%              # 5% daily loss
    action: "emergency_halt"
    reason: "Daily loss limit exceeded"
    
  portfolio_drawdown_halt:
    threshold: 10.0%             # 10% portfolio drawdown
    action: "close_all_positions"
    reason: "Excessive portfolio drawdown"
    
  rapid_loss_halt:
    threshold: 2.0%              # 2% loss in 15 minutes
    timeframe: 15                # 15 minutes
    action: "emergency_halt"
    reason: "Rapid loss detected"
```

#### System-Based Triggers
```yaml
# Automatic triggers based on system health
system_triggers:
  data_feed_failure:
    trigger: "no_data_updates > 30_seconds"
    action: "emergency_halt"
    reason: "Market data feed failure"
    
  high_error_rate:
    trigger: "errors_per_minute > 10"
    action: "emergency_halt"
    reason: "High system error rate"
    
  memory_exhaustion:
    trigger: "memory_usage > 95%"
    action: "emergency_halt"
    reason: "System memory critical"
```

## 📱 Mobile Emergency Controls

### Mobile Emergency Access
If you're away from your computer, you can still access emergency controls:

#### Mobile Dashboard
1. **Open browser** on your phone
2. **Go to**: `http://your-server:8000/mobile`
3. **Emergency controls** are prominently displayed
4. **Same functionality** as desktop version

#### Emergency SMS Commands
```yaml
# If configured, send SMS commands
sms_emergency_commands:
  halt: "HALT"                   # Text "HALT" to emergency number
  close: "CLOSE ALL"            # Text "CLOSE ALL" to emergency number
  status: "STATUS"              # Text "STATUS" for system status
```

#### Emergency Phone Number
```yaml
# Optional: Emergency phone line
emergency_phone:
  enabled: false                 # Disabled by default
  number: "+1-800-EMERGENCY"    # Dedicated emergency line
  available: "24/7"             # Always available
  actions: ["halt", "close_all", "status_check"]
```

## 🔍 Post-Emergency Procedures

### Immediate Post-Emergency Checklist
After triggering emergency controls:

#### Within 5 Minutes
- [ ] **Confirm emergency action worked** - check dashboard
- [ ] **Assess current positions** - what's still open?
- [ ] **Check account balance** - current P&L status
- [ ] **Review system logs** - what triggered the emergency?
- [ ] **Document the incident** - when, why, what happened

#### Within 30 Minutes  
- [ ] **Analyze root cause** - why did this happen?
- [ ] **Check market conditions** - was it market-related?
- [ ] **Review agent behavior** - were agents malfunctioning?
- [ ] **Assess system health** - are all components working?
- [ ] **Plan recovery strategy** - how to safely restart

#### Within 2 Hours
- [ ] **Fix identified problems** - address root causes
- [ ] **Test system functionality** - ensure everything works
- [ ] **Update emergency procedures** - learn from incident
- [ ] **Prepare restart plan** - step-by-step recovery
- [ ] **Consider position adjustments** - what to do with remaining positions

### Emergency Incident Report
```yaml
# Document every emergency for learning
incident_report:
  timestamp: "2024-02-15 10:45:23"
  trigger: "manual"              # manual, automatic, or system
  action_taken: "emergency_halt"
  reason: "Agent making consecutive bad trades"
  
  pre_emergency_state:
    active_agents: 3
    open_positions: 5
    account_balance: "$152,450"
    daily_pnl: "-$1,250"
    
  post_emergency_state:
    active_agents: 0             # All halted
    open_positions: 5            # Positions maintained
    account_balance: "$152,450"  # No change (positions not closed)
    
  root_cause_analysis:
    cause: "Agent configuration error"
    details: "Risk tolerance set too high after recent update"
    
  corrective_actions:
    - "Reset agent risk tolerance to conservative levels"
    - "Add additional risk checks before trade execution"
    - "Implement gradual configuration changes with testing"
    
  lessons_learned:
    - "Always test agent configuration changes in paper mode first"
    - "Monitor more closely after any configuration changes"
    - "Set up automated alerts for unusual trading patterns"
```

## 🎯 Emergency Preparedness

### Regular Emergency Drills
Practice using emergency controls regularly:

#### Monthly Emergency Drill
1. **Schedule drill time** when markets are closed
2. **Practice emergency halt** - make sure it works
3. **Test all emergency methods** - keyboard, dashboard, URL
4. **Time your response** - how quickly can you act?
5. **Review and improve** procedures based on drill results

#### Emergency Contact List
```yaml
# Keep this information easily accessible
emergency_contacts:
  primary_user: "John Smith - +1-555-0101"
  system_admin: "Jane Doe - +1-555-0102"
  broker_support: "Broker Support - +1-800-BROKER"
  technical_support: "Tech Support - support@tragen.com"
  
  escalation_order:
    1. "Try emergency controls first"
    2. "Contact primary user if controls fail"  
    3. "Contact system admin for technical issues"
    4. "Contact broker for account/position issues"
```

### Emergency Equipment Check
Ensure you can access emergency controls from multiple devices:

#### Device Access Check
- [ ] **Primary computer** - desktop/laptop with full access
- [ ] **Mobile phone** - mobile-optimized emergency interface  
- [ ] **Tablet** - backup mobile access
- [ ] **Alternative computer** - friend's computer, public computer, etc.

#### Network Access Check
- [ ] **Home internet** - primary connection
- [ ] **Mobile data** - cellular backup
- [ ] **Public WiFi** - coffee shop, library, etc.
- [ ] **VPN access** - if system requires VPN

## 📚 Emergency Scenarios Practice

### Practice Scenario 1: Bad Agent Behavior
```
Setup: Agent starts making trades against clear trend
Your Task: Use emergency halt, assess situation, fix configuration
Time Limit: 2 minutes to halt, 10 minutes to analyze and fix
```

### Practice Scenario 2: System Unresponsive
```
Setup: Dashboard stops updating, trades may still be executing
Your Task: Use emergency URL or close all positions
Time Limit: 1 minute to take action
```

### Practice Scenario 3: Market Volatility Spike
```
Setup: VIX jumps from 20 to 45 in 10 minutes
Your Task: Decide between halt or close all, execute decision
Time Limit: 30 seconds to decide and act
```

## 🚨 When NOT to Use Emergency Controls

### Avoid Emergency Controls For:
❌ **Normal market volatility** - use regular risk management instead
❌ **Small temporary losses** - let risk management systems work
❌ **Minor system hiccups** - try regular restart first
❌ **Emotional reactions** - take a breath and assess objectively
❌ **Testing purposes** - use practice mode or paper trading

### Use Regular Controls Instead:
✅ **Agent pause/resume** - for temporary issues
✅ **Position size reduction** - for increased caution
✅ **Strategy adjustments** - for changing market conditions
✅ **Risk limit adjustments** - for tighter control
✅ **System restart** - for minor technical issues

---

**🚨 Critical Remember**: Emergency controls are powerful tools that can save your account in true emergencies. Practice using them regularly, but only use them in real emergencies. When in doubt, err on the side of caution - it's better to halt unnecessarily than to let losses run.

**Next**: [Risk Management](../configuration/risk-management.md) | [Monitoring](monitoring.md) | [Safety Guide](../getting-started/safety.md)
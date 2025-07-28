# Training Your Agents Guide

Learn how to train your AI trading agents using real market data, interactive charts, and feedback systems. No coding required - everything is done through the web interface.

## 🎯 What is Agent Training?

Agent training is how you teach your AI agents to:
- **Recognize patterns** in market data
- **Make better decisions** based on your feedback
- **Learn from mistakes** and improve over time
- **Adapt to changing** market conditions

Think of it like teaching a student - you show them examples, give feedback, and they gradually improve.

## 🚀 Quick Training Start (5 Minutes)

### Step 1: Access Training Interface
1. **Go to your dashboard**: `http://localhost:8000`
2. **Find your agent** in the "Active Agents" list
3. **Click the training icon** (🎓) next to your agent
4. **Select "Start Training Session"**

### Step 2: Choose Training Mode
```
🔍 Observation Mode
- Agent watches your actions
- You make decisions, agent learns
- Best for: New agents, showing examples

🤖 Simulation Mode  
- Agent makes decisions, you give feedback
- Agent suggests trades, you approve/reject
- Best for: Testing agent decision-making

🤝 Collaborative Mode
- You and agent work together
- Real-time discussion and decision-making
- Best for: Complex market analysis

📊 Evaluation Mode
- Test agent performance
- No feedback given, just assessment
- Best for: Checking agent readiness
```

### Step 3: Start Your First Session
1. **Choose "Simulation Mode"** (recommended for beginners)
2. **Select timeframe**: Start with 15-minute charts
3. **Choose symbol**: NQ=F (NQ Futures)
4. **Click "Begin Training"**

## 📊 Interactive Chart Training

### Chart Interface Overview

#### Main Chart Area
- **Price Chart**: Live or historical price data
- **Volume Bars**: Trading volume at bottom
- **Indicators**: Technical indicators (RSI, MACD, etc.)
- **Drawing Tools**: Lines, arrows, annotations

#### Training Controls
```
🎮 Training Controls Panel:
├── Mode Selector (Observation/Simulation/Collaborative)
├── Timeframe Selector (1m, 5m, 15m, 1h, 4h, 1d)
├── Symbol Selector (NQ=F, ES=F, etc.)
├── Training Speed (Real-time, 2x, 5x, 10x)
└── Session Controls (Play, Pause, Reset)
```

#### Feedback Panel
```
💬 Feedback Panel:
├── Agent Decisions (What agent wants to do)
├── Confidence Level (Agent's confidence %)
├── Reasoning (Why agent made this decision)
├── Your Response (Approve/Reject/Modify)
└── Learning Notes (What agent should remember)
```

### Using Chart Annotations

#### Drawing Support/Resistance Levels
1. **Click the line tool** in the chart toolbar
2. **Draw horizontal lines** at key price levels
3. **Label the lines**: "Support", "Resistance", "Key Level"
4. **Agent learns** to recognize these levels

#### Marking Entry/Exit Points
1. **Click the arrow tool**
2. **Place green arrows** at good entry points
3. **Place red arrows** at good exit points
4. **Add notes** explaining why these are good points

#### Pattern Recognition Training
1. **Use the rectangle tool** to highlight patterns
2. **Common patterns to mark**:
   - Triangles (ascending, descending, symmetrical)
   - Head and shoulders
   - Double tops/bottoms
   - Flags and pennants

## 🎓 Training Modes Detailed

### Observation Mode Training

#### How It Works
1. **You control everything** - make all decisions
2. **Agent watches and learns** from your actions
3. **No pressure** - perfect for showing examples
4. **Agent asks questions** about your decisions

#### Example Observation Session
```
📈 Market Scenario: NQ trending up, approaching resistance

Your Action: Draw resistance line at 15,800
Agent Question: "Why is 15,800 important?"
Your Response: "Previous high from last week, expect selling pressure"

Your Action: Wait for pullback before buying
Agent Question: "Why not buy the breakout?"
Your Response: "Want to see volume confirmation first"

Agent Learning: "Wait for volume confirmation on breakouts"
```

#### Best Practices for Observation Mode
- **Explain your reasoning** for every action
- **Point out key levels** and why they matter
- **Show different market conditions** (trending, ranging, volatile)
- **Demonstrate risk management** (where to place stops)

### Simulation Mode Training

#### How It Works
1. **Agent makes suggestions** based on current analysis
2. **You approve, reject, or modify** the suggestions
3. **Agent learns** from your feedback
4. **Gradual improvement** over time

#### Example Simulation Session
```
📊 Agent Analysis: "I see a bullish flag pattern forming"
🤖 Agent Suggestion: "BUY at 15,750, Stop at 15,725, Target 15,800"
📈 Confidence Level: 75%

Your Options:
✅ Approve: "Good analysis, execute the trade"
❌ Reject: "Pattern not clear enough, wait for better setup"
🔧 Modify: "Good pattern but stop too tight, use 15,720 instead"

Agent Response: "Learning: Use wider stops in volatile conditions"
```

#### Feedback Types in Simulation Mode
```yaml
Rating Feedback (1-5 stars):
  analysis_quality: 4/5      # How good was the analysis?
  timing: 3/5               # Was the timing right?
  risk_management: 5/5      # Were stops/targets appropriate?

Categorical Feedback:
  decision: "approve/reject/modify"
  reasoning: "good_analysis/poor_timing/risk_too_high"
  
Detailed Feedback:
  comment: "Good pattern recognition but wait for volume confirmation"
  suggestion: "Look for above-average volume before entering"
```

### Collaborative Mode Training

#### How It Works
1. **Real-time discussion** between you and agent
2. **Both contribute** to analysis and decisions
3. **Agent asks questions** and provides insights
4. **Most interactive** training mode

#### Example Collaborative Session
```
🤖 Agent: "I'm seeing RSI oversold at 25, what do you think?"
👤 You: "RSI is oversold but trend is still down, be careful"
🤖 Agent: "Good point. Should we wait for trend confirmation?"
👤 You: "Yes, wait for higher high or break above moving average"
🤖 Agent: "I'll watch for price above 15,760 (20-period MA)"
👤 You: "Perfect, that's the confirmation we need"

Learning Outcome: "Don't trade oversold signals in downtrends without trend confirmation"
```

#### Collaborative Mode Features
- **Real-time chat** with your agent
- **Shared decision making** on trades
- **Agent asks for clarification** when uncertain
- **Builds agent's reasoning** abilities

### Evaluation Mode Training

#### How It Works
1. **Agent trades independently** (paper trading)
2. **You observe** without giving feedback
3. **Performance is measured** and recorded
4. **Identifies areas** needing improvement

#### Evaluation Metrics
```yaml
Performance Metrics:
  total_trades: 25
  win_rate: 64%              # 16 wins out of 25 trades
  profit_factor: 1.45        # Total profits ÷ total losses
  average_win: $875          # Average winning trade
  average_loss: -$425        # Average losing trade
  max_drawdown: -$2,150      # Largest losing streak

Behavioral Metrics:
  rule_adherence: 92%        # How well agent follows rules
  confidence_accuracy: 78%   # How well confidence predicts success
  pattern_recognition: 85%   # Accuracy in identifying patterns
```

## 🔧 Advanced Training Techniques

### Scenario-Based Training

#### Create Custom Scenarios
1. **Load historical data** from specific market events
2. **Train on different conditions**:
   - Trending markets
   - Range-bound markets
   - High volatility periods
   - News-driven events

#### Example Scenarios
```yaml
Trend Following Scenario:
  date_range: "2023-10-01 to 2023-10-15"
  market_condition: "strong_uptrend"
  learning_focus: "trend_continuation_patterns"

Range Trading Scenario:
  date_range: "2023-11-15 to 2023-11-30"
  market_condition: "sideways_range"
  learning_focus: "support_resistance_bounces"

Volatility Scenario:
  date_range: "2023-12-01 to 2023-12-05"
  market_condition: "high_volatility"
  learning_focus: "risk_management_volatile_markets"
```

### Progressive Training Program

#### Week 1: Pattern Recognition
```yaml
Day 1-2: Basic Patterns
  - Support and resistance
  - Trend lines
  - Moving average interactions

Day 3-4: Intermediate Patterns
  - Triangles and wedges
  - Flags and pennants
  - Double tops/bottoms

Day 5-7: Advanced Patterns
  - Head and shoulders
  - Complex corrections
  - Multi-timeframe analysis
```

#### Week 2: Risk Management
```yaml
Day 1-2: Stop Loss Placement
  - Technical stop levels
  - ATR-based stops
  - Percentage stops

Day 3-4: Position Sizing
  - Fixed dollar amount
  - Percentage of account
  - Volatility-based sizing

Day 5-7: Portfolio Management
  - Correlation awareness
  - Total exposure limits
  - Risk-reward optimization
```

### Multi-Timeframe Training

#### Timeframe Hierarchy
```yaml
Training Progression:
  1. Start with 15-minute charts    # Learn basic patterns
  2. Add 1-hour timeframe          # Understand trend context
  3. Include 4-hour charts         # See bigger picture
  4. Incorporate daily view        # Major trend direction

Multi-Timeframe Rules:
  - Trade in direction of higher timeframe trend
  - Use lower timeframes for entry timing
  - Higher timeframes for stop placement
  - Confirm signals across timeframes
```

## 📈 Training Performance Tracking

### Learning Progress Metrics

#### Skill Development Tracking
```yaml
Pattern Recognition Skills:
  support_resistance: 85%     # Accuracy in identifying levels
  trend_patterns: 78%         # Trend line accuracy
  reversal_patterns: 65%      # Reversal pattern accuracy
  continuation_patterns: 82%   # Continuation pattern accuracy

Decision Making Skills:
  entry_timing: 74%           # Good entry point selection
  exit_timing: 69%            # Good exit point selection
  risk_management: 91%        # Proper stop loss placement
  position_sizing: 88%        # Appropriate position sizes
```

#### Improvement Over Time
```yaml
# 30-day training progress
training_history:
  week_1:
    win_rate: 45%
    profit_factor: 0.85
    confidence_accuracy: 60%
    
  week_2:
    win_rate: 52%
    profit_factor: 1.15
    confidence_accuracy: 68%
    
  week_3:
    win_rate: 58%
    profit_factor: 1.32
    confidence_accuracy: 75%
    
  week_4:
    win_rate: 63%
    profit_factor: 1.48
    confidence_accuracy: 81%
```

### Training Session Analytics

#### Session Summary Reports
```yaml
# Example training session report
session_report:
  date: "2024-02-15"
  duration: "2h 15m"
  mode: "simulation"
  
  scenarios_completed: 12
  feedback_given: 47
  patterns_identified: 23
  
  performance:
    correct_decisions: 9/12     # 75% accuracy
    improvement_areas:
      - "Entry timing in ranging markets"
      - "Volume confirmation usage"
      - "Stop loss adjustment in volatility"
```

## 🎯 Training Best Practices

### Effective Training Principles

#### Start Simple, Build Complexity
1. **Begin with clear trends** - easy to identify patterns
2. **Add ranging markets** - more complex decision making
3. **Include volatile periods** - advanced risk management
4. **Mix different conditions** - well-rounded training

#### Consistent Feedback
```yaml
Feedback Guidelines:
  be_specific: "Good support level identification at 15,750"
  explain_reasoning: "Stop too tight because market is volatile"
  encourage_improvement: "Better pattern recognition, now work on timing"
  stay_positive: "Great progress on risk management!"
```

#### Regular Assessment
- **Weekly evaluation sessions** to measure progress
- **Monthly comprehensive reviews** of all skills
- **Quarterly training plan updates** based on performance

### Common Training Mistakes

#### Avoid These Pitfalls
❌ **Inconsistent feedback** - confuses the learning process
❌ **Too complex too quickly** - overwhelming for new agents
❌ **Only training in one market condition** - limited adaptability
❌ **Skipping evaluation phases** - no progress measurement
❌ **Not explaining reasoning** - agent can't understand why

#### Better Approaches
✅ **Consistent, clear feedback** on every decision
✅ **Progressive difficulty** - gradually increase complexity
✅ **Diverse market conditions** - bull, bear, sideways markets
✅ **Regular evaluation** - weekly progress checks
✅ **Detailed explanations** - always explain your reasoning

## 🔄 Training Workflows

### Daily Training Routine (30 minutes)
```yaml
Daily Training Schedule:
  0-5 minutes: Review previous session results
  5-20 minutes: Active training (observation/simulation)
  20-25 minutes: Evaluation mode testing
  25-30 minutes: Review progress and plan next session
```

### Weekly Training Program
```yaml
Monday: Pattern Recognition Focus
Tuesday: Entry Timing Practice
Wednesday: Risk Management Training
Thursday: Multi-timeframe Analysis
Friday: Evaluation and Performance Review
Weekend: Plan next week's training focus
```

### Training Session Templates

#### Pattern Recognition Session
```yaml
session_template:
  name: "Pattern Recognition Training"
  duration: 30_minutes
  mode: "observation"
  focus: "support_resistance_identification"
  
  steps:
    1. Load historical chart with clear patterns
    2. Have agent identify support/resistance levels
    3. Provide feedback on accuracy
    4. Show correct levels if missed
    5. Explain why these levels are important
    6. Test on different timeframes
```

#### Decision Making Session
```yaml
session_template:
  name: "Decision Making Training"
  duration: 45_minutes
  mode: "simulation"
  focus: "trade_entry_decisions"
  
  steps:
    1. Present market scenario
    2. Agent analyzes and suggests trade
    3. You evaluate the suggestion
    4. Provide detailed feedback
    5. Discuss alternative approaches
    6. Agent adjusts decision-making process
```

## 📚 Training Resources

### Market Scenarios Library
```yaml
# Pre-built training scenarios
scenarios:
  trending_markets:
    - "strong_uptrend_breakout"
    - "downtrend_with_pullbacks"
    - "trend_channel_trading"
    
  ranging_markets:
    - "horizontal_support_resistance"
    - "declining_volatility_squeeze"
    - "range_expansion_breakout"
    
  volatile_markets:
    - "news_driven_volatility"
    - "gap_up_fade_pattern"
    - "intraday_reversal_spikes"
```

### Training Checklists

#### Pre-Training Checklist
- [ ] Agent is in paper trading mode
- [ ] Training interface is working properly
- [ ] Historical data is loaded correctly
- [ ] Chart tools are functioning
- [ ] Feedback system is responsive

#### Post-Training Checklist
- [ ] Session results are saved
- [ ] Performance metrics are updated
- [ ] Learning notes are documented
- [ ] Next session is planned
- [ ] Agent improvements are noted

---

**💡 Remember**: Training is an ongoing process. The more time you spend training your agents, the better they become at making profitable trading decisions.

**Next**: [Monitoring & Alerts](monitoring.md) | [Agent Configuration](agent-configuration.md) | [Emergency Controls](emergency-controls.md)
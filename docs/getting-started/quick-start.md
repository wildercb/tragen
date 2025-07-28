# Quick Start Guide

Get your Tragen AI Trading System up and running in 10 minutes! This guide will help you start trading with AI agents safely.

## 🎯 What You'll Accomplish

By the end of this guide, you'll have:
- ✅ A running Tragen trading system
- ✅ Your first AI trading agent created
- ✅ Safe paper trading enabled
- ✅ Basic monitoring dashboard active

## 🚀 Step 1: Start the System (2 minutes)

### Option A: Simple Startup (Recommended)
1. **Open your terminal/command prompt**
2. **Navigate to your Tragen folder**:
   ```bash
   cd /path/to/tragen
   ```
3. **Start the system**:
   ```bash
   python3 start_production.py
   ```
4. **Wait for the green checkmarks** - you'll see:
   ```
   ✅ Tragen Production Trading Backend started successfully
   🎯 Tragen Production Trading System ready!
   ```

### Option B: Custom Configuration
```bash
# Start with custom settings
python3 start_production.py --host 0.0.0.0 --port 8000 --log-level INFO
```

💡 **Tip**: Leave the terminal window open - this is where you'll see system messages.

## 🌐 Step 2: Access the Dashboard (1 minute)

1. **Open your web browser**
2. **Go to**: `http://localhost:8000`
3. **You should see**: The Tragen Trading Dashboard

### If the dashboard doesn't load:
- Check that the terminal shows "ready" messages
- Try `http://127.0.0.1:8000` instead
- Make sure no other programs are using port 8000

## 🤖 Step 3: Create Your First Agent (3 minutes)

### Using the Web Interface (No Coding Required)

1. **Click "Create Agent"** on the dashboard
2. **Choose a template** (recommended for beginners):
   - **Conservative Trader**: Low risk, steady approach
   - **Balanced Trader**: Moderate risk and reward
   - **Scalper**: Quick, frequent trades
3. **Click "Use Template"** on your preferred style

### Configure Your Agent

The setup wizard will guide you through 5 simple steps:

#### Step 1: Basic Information
```
Agent Name: [Enter a name like "My First Trader"]
```

#### Step 2: Trading Style & Risk
- **Trading Style**: Leave as template default
- **Risk Level**: Start with "Low" or "Moderate"
- **Max Loss Per Trade**: Start with 1.0%
- **Max Daily Loss**: Start with 3.0%
- **Confidence Required**: Start with 70%

#### Step 3: Analysis Methods
- **Technical Analysis**: ✅ Keep enabled
- **AI Analysis**: ✅ Keep enabled
- **Weights**: Use default 60% Technical, 40% AI

#### Step 4: Trading Settings
- **Paper Trading Only**: ✅ **MUST BE ENABLED** for safety
- **Max Trades Per Day**: Start with 5-10
- **Max Position Value**: Start with $10,000

#### Step 5: Review & Create
- **Review your settings**
- **Click "Create Agent"**

🚨 **Critical**: Always keep "Paper Trading Only" enabled when starting!

## 📊 Step 4: Verify Your Agent (2 minutes)

### Check Agent Status
1. **Look for your agent** in the "Active Agents" section
2. **Status should show**: 🟢 Active
3. **You should see**: "Paper" chip next to the agent name

### Test Your Agent
1. **Click the chart icon** next to your agent
2. **Click "Get Analysis"** to see what your agent thinks about the market
3. **You should see**: Analysis with confidence percentage and reasoning

## 📈 Step 5: Monitor Your System (2 minutes)

### Dashboard Overview
Your dashboard shows:
- **Total Agents**: How many agents you have
- **Active Agents**: How many are currently running
- **Paper Trading**: How many are in safe mode (should be all of them)
- **System Status**: Overall health

### What to Watch
- **System Status**: Should be "Healthy" (green)
- **Active Agents**: Should match your created agents
- **No critical alerts**: Alert area should be empty or show only info messages

## 🎉 Success! You're Now Running Tragen

### What You've Achieved
- ✅ **Safe Trading Environment**: Your agent trades with virtual money
- ✅ **AI-Powered Analysis**: Your agent analyzes markets automatically
- ✅ **Real-Time Monitoring**: You can see what your agent is doing
- ✅ **Professional Safety Systems**: Multiple layers of protection active

## 🔜 Next Steps

### Immediate Next Steps (Optional)
1. **[Set Up Training](../user-guides/training-agents.md)**: Teach your agent with real charts
2. **[Configure Alerts](../user-guides/monitoring.md)**: Get notified of important events
3. **[Understand Risk Settings](../configuration/risk-management.md)**: Learn about safety systems

### Before Using Real Money
1. **[Read the Safety Guide](safety.md)**: Essential safety information
2. **[Test Thoroughly](../user-guides/training-agents.md)**: Train and evaluate your agents
3. **[Understand Risks](../configuration/risk-management.md)**: Know the safety systems

## 🆘 Common Quick Start Issues

### Problem: "Connection Refused" Error
**Solution**: 
1. Check if the system is still starting (wait 30 seconds)
2. Try a different port: `python3 start_production.py --port 8001`
3. Check if another program is using port 8000

### Problem: Agent Won't Create
**Solution**:
1. Check the agent name is unique
2. Ensure "Paper Trading" is enabled
3. Try using a template instead of custom configuration

### Problem: Dashboard Shows Errors
**Solution**:
1. Check the terminal for error messages
2. Restart the system: Stop (Ctrl+C) and run `python3 start_production.py` again
3. Check the [Troubleshooting Guide](../maintenance/troubleshooting.md)

### Problem: Agent Status Shows "Error"
**Solution**:
1. Click on the agent to see error details
2. Try stopping and starting the agent
3. Check risk settings aren't too restrictive

## 💡 Quick Start Tips

### Best Practices
- **Start Small**: Begin with 1-2 agents maximum
- **Use Templates**: They're pre-configured for safety
- **Paper Trade First**: Never start with real money
- **Monitor Actively**: Watch your agents for the first hour

### Performance Tips
- **Close Unused Browser Tabs**: Keeps the dashboard responsive
- **Check System Resources**: Monitor CPU and memory usage
- **Regular Restarts**: Restart daily for optimal performance

### Safety Reminders
- **Paper Trading First**: Always start with virtual money
- **Small Position Sizes**: Start with small amounts even in paper trading
- **Understand Settings**: Know what each setting does before changing it
- **Emergency Stop**: Know how to halt trading immediately (see [Emergency Controls](../user-guides/emergency-controls.md))

## 📞 Getting Help

### If You Get Stuck
1. **Check this guide again**: Re-read the relevant section
2. **Look at system messages**: Check the terminal for clues
3. **Try the troubleshooting guide**: [Common Issues](../maintenance/troubleshooting.md)
4. **Restart if needed**: Sometimes a fresh start helps

### Support Resources
- **[Troubleshooting Guide](../maintenance/troubleshooting.md)**: Solutions to common problems
- **[User Guides](../user-guides/)**: Detailed guides for each feature
- **[Safety Guide](safety.md)**: Important safety information

---

**🎉 Congratulations!** You've successfully set up your first AI trading agent. Remember to always prioritize safety and start with paper trading.

**Next**: [Create Your First Agent](first-agent.md) | [Safety Guide](safety.md) | [Agent Configuration](../user-guides/agent-configuration.md)
# Tragen Production Trading System

🏛️ **Advanced AI Trading Agent Platform with Comprehensive Safety Systems**

## Overview

The Tragen Production Trading System is a comprehensive, production-ready platform for AI-powered trading agents with real-money safety controls, interactive training capabilities, and enterprise-grade monitoring.

## 🚀 Quick Start

### Option 1: Production Server (Recommended)
```bash
# Start the full production system
python3 start_production.py

# Or with custom configuration
python3 start_production.py --config config.yaml --host 0.0.0.0 --port 8000
```

### Option 2: Backend Integration
```bash
# Start through the integrated backend
cd backend
python3 main.py
```

### Accessing the System
- **Dashboard**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **System Status**: http://localhost:8000/api/system/status
- **Agent Configuration**: http://localhost:8000/api/agents/
- **Live Training**: http://localhost:8000/api/training/

## 🏗️ Architecture Overview

### Core Components

#### 1. Production Controller (`ProductionTradingController`)
- **Purpose**: Master orchestrator for all trading operations
- **Features**:
  - Multi-layer risk management
  - Circuit breaker integration
  - Emergency halt capabilities
  - Comprehensive audit logging
  - Real-time position tracking

#### 2. Agent Controller (`ProductionAgentController`) 
- **Purpose**: Centralized agent lifecycle management
- **Features**:
  - Agent creation, configuration, and monitoring
  - Performance tracking
  - Resource allocation
  - Template-based setup
  - Bulk operations

#### 3. Risk Management System
- **Components**:
  - `RiskManager`: Multi-layer risk assessment
  - `CircuitBreakerSystem`: Emergency halt mechanisms
  - Position size limits
  - Daily loss limits
  - Volatility protection

#### 4. Data Management
- **Components**:
  - `DataSourceManager`: Multi-source data aggregation
  - `DataQualityManager`: Real-time data validation
  - Consensus-based data validation
  - Quality scoring and anomaly detection

#### 5. Production Monitoring (`ProductionMonitor`)
- **Features**:
  - Real-time system metrics
  - Performance tracking
  - Alert management
  - Health monitoring
  - Resource usage tracking

#### 6. Audit System (`AuditLogger`)
- **Features**:
  - Comprehensive event logging
  - Structured audit trails
  - Log rotation and compression
  - Query capabilities
  - Compliance support

#### 7. Training System
- **Components**:
  - `LiveTrainingInterface`: Interactive agent training
  - `ChartInteractionManager`: Chart-based training
  - `FeedbackCollector`: User feedback processing
  - Real-time WebSocket communication

## 🤖 Agent System

### Agent Types
- **Production Trading Agent**: Full-featured trading agent
- **Scalping Agent**: High-frequency trading specialist
- **Swing Trading Agent**: Medium-term position trader
- **Custom Agents**: User-defined specializations

### Agent Configuration
```python
# Example agent configuration
agent_config = {
    "personality": {
        "name": "Conservative Trader",
        "risk_tolerance": 3.0,
        "analysis_style": "conservative", 
        "confidence_threshold": 0.8,
        "max_trades_per_day": 5
    },
    "risk_profile": {
        "max_loss_per_trade": 0.01,  # 1%
        "max_daily_loss": 0.02,      # 2%
        "stop_loss_percentage": 0.005 # 0.5%
    },
    "decision_engine": {
        "analysis_models": ["technical", "ai_model"],
        "ensemble_method": "weighted_average"
    }
}
```

### Easy Configuration System
The `AgentConfigBuilder` provides a user-friendly interface:

```python
# Quick configuration
config = builder.create_quick_config(
    agent_name="My Trader",
    trading_style="balanced",
    risk_level="moderate",
    paper_trading_only=True
)

# Convert to production format
production_config = builder.convert_to_production_config(config)
```

## 📊 Live Training Interface

### Training Modes
1. **Observation**: Agent watches user actions
2. **Simulation**: Agent makes decisions, user provides feedback
3. **Collaborative**: User and agent work together
4. **Evaluation**: Test agent performance

### Chart Interaction
- Real-time chart annotations
- Pattern identification
- Support/resistance level marking
- Entry/exit point marking
- Interactive feedback collection

### Feedback System
- Rating-based feedback (1-5 scale)
- Categorical feedback (timing, analysis, risk management)
- Correction feedback for wrong decisions
- Suggestion feedback for improvements

## 🛡️ Safety Systems

### Multi-Layer Risk Management
1. **Position Risk**: Individual trade risk limits
2. **Portfolio Risk**: Overall portfolio exposure
3. **Drawdown Risk**: Maximum account drawdown
4. **Volatility Risk**: Market volatility protection

### Circuit Breakers
1. **Daily Loss Breaker**: Halt on excessive daily losses
2. **Consecutive Loss Breaker**: Stop after multiple losses
3. **Volatility Breaker**: Pause during high volatility
4. **System Error Breaker**: Halt on system errors

### Emergency Controls
- **Emergency Halt**: Immediate trading stop
- **Emergency Position Closure**: Close all positions
- **Manual Override**: Human intervention capabilities

## 📈 Monitoring & Alerting

### Real-Time Metrics
- Trades per minute
- API response times
- Error rates
- System resource usage
- Agent performance

### Alert System
- **Critical**: Emergency situations requiring immediate action
- **Warning**: Potential issues requiring attention
- **Info**: General system notifications

### Health Checks
- Memory usage monitoring
- Disk space monitoring
- API health checks
- Database connectivity

## 🔧 Configuration Management

### Environment Variables
```bash
# Server configuration
TRAGEN_HOST=0.0.0.0
TRAGEN_PORT=8000

# Database configuration  
DATABASE_URL=postgresql://...

# LLM Provider configuration
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=your_key_here
```

### Configuration Files
```yaml
# config.yaml
production:
  trading_mode: "paper"
  max_trades_per_minute: 10
  max_daily_trades: 100
  max_position_value: 100000
  
circuit_breakers:
  daily_loss:
    enabled: true
    threshold: 0.05  # 5%
    warning_threshold: 0.03  # 3%
    
monitoring:
  check_interval: 30
  alert_max_per_hour: 10
```

## 🌐 API Reference

### Agent Management
```http
POST /api/agents/create
GET /api/agents/status
POST /api/agents/{agent_id}/start
POST /api/agents/{agent_id}/stop
PUT /api/agents/{agent_id}/config
DELETE /api/agents/{agent_id}
```

### Trading Operations
```http
POST /api/trading/execute
POST /api/trading/mode
POST /api/emergency/halt
POST /api/emergency/close-all
```

### Training Interface
```http
POST /api/training/start
POST /api/training/end/{session_id}
POST /api/training/annotate/{session_id}
POST /api/training/feedback/{session_id}
POST /api/training/question/{session_id}
```

### Monitoring
```http
GET /api/system/status
GET /api/monitoring/dashboard
WebSocket: /ws/monitoring
```

## 📝 Usage Examples

### 1. Create and Start an Agent
```python
# Create agent configuration
config = {
    "agent_name": "Conservative Trader",
    "trading_style": "conservative",
    "risk_level": "low",
    "paper_trading_only": True
}

# Create agent via API
response = requests.post("/api/agents/create", json=config)
agent_id = response.json()["agent_id"]

# Start the agent
requests.post(f"/api/agents/{agent_id}/start")
```

### 2. Execute a Trading Task
```python
# Define trading task
task = {
    "type": "market_analysis",
    "parameters": {
        "symbol": "NQ=F",
        "timeframe": "15m"
    }
}

# Execute task
response = requests.post(f"/api/agents/{agent_id}/task", json=task)
decision = response.json()["decision"]
```

### 3. Start a Training Session
```python
# Start training session
session_data = {
    "agent_id": agent_id,
    "mode": "simulation",
    "symbol": "NQ=F",
    "timeframe": "15m"
}

response = requests.post("/api/training/start", json=session_data)
session_id = response.json()["session_id"]

# Provide feedback
feedback = {
    "type": "rating",
    "rating": 4,
    "category": "analysis_quality",
    "comment": "Good analysis but could improve timing"
}

requests.post(f"/api/training/feedback/{session_id}", json=feedback)
```

## 🔒 Security Considerations

### Production Safety
- All agents start in paper trading mode by default  
- Multiple confirmation layers for live trading
- Emergency halt mechanisms always available
- Comprehensive audit logging
- Position and loss limits strictly enforced

### API Security
- Authentication and authorization (implement as needed)
- Rate limiting on critical endpoints
- Input validation and sanitization
- CORS configuration for frontend access

### Data Protection
- Secure handling of API keys
- Encrypted storage of sensitive configuration
- Audit trail for all trading decisions
- Compliance with financial regulations

## 🐛 Troubleshooting

### Common Issues

#### 1. Agent Creation Fails
```python
# Check agent configuration
response = requests.post("/api/config/validate", json=config)
if not response.json()["valid"]:
    print("Issues:", response.json()["issues"])
```

#### 2. Training Session Not Starting
- Verify agent is in active state
- Check WebSocket connection
- Review system status for alerts

#### 3. Risk Manager Rejecting Trades
- Check daily trade limits
- Verify position size limits
- Review risk configuration
- Check circuit breaker status

### Monitoring and Debugging
```python
# Check system status
status = requests.get("/api/system/status").json()
print("System Status:", status["system_status"])
print("Active Agents:", status["active_agents"])

# Check monitoring dashboard
dashboard = requests.get("/api/monitoring/dashboard").json()
print("Health Status:", dashboard["health_status"])
print("Recent Alerts:", dashboard["alerts"]["active"])
```

## 📚 Development Guide

### Adding New Agent Types
1. Create agent class inheriting from `ProductionTradingAgent`
2. Register in `AgentFactory`
3. Add configuration templates
4. Update API documentation

### Adding New Risk Layers
1. Implement `RiskLayer` interface
2. Register in `RiskManager`
3. Add configuration options
4. Update monitoring dashboards

### Extending Training Interface
1. Add new event types to `TrainingEvent`
2. Implement event handlers
3. Update WebSocket message handling
4. Add frontend components

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python3", "start_production.py", "--host", "0.0.0.0"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  tragen:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./logs:/app/logs
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tragen-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tragen
  template:
    metadata:
      labels:
        app: tragen
    spec:
      containers:
      - name: tragen
        image: tragen:latest
        ports:
        - containerPort: 8000
```

## 📋 System Requirements

### Minimum Requirements
- Python 3.11+
- 4GB RAM
- 2 CPU cores
- 10GB disk space

### Recommended Requirements
- Python 3.11+
- 16GB RAM
- 8 CPU cores
- 100GB SSD storage
- Dedicated GPU for AI models

### Dependencies
- FastAPI
- Uvicorn
- Asyncio
- Pandas
- NumPy
- Scikit-learn
- WebSocket support
- Database driver (PostgreSQL recommended)

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/tragen.git
cd tragen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
python3 start_production.py --dev-mode
```

### Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests  
pytest tests/integration/

# Run performance tests
pytest tests/performance/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Ollama for local LLM capabilities
- The trading and AI communities for inspiration and guidance

---

**⚠️ IMPORTANT DISCLAIMER**: This system is designed for educational and research purposes. Trading involves substantial risk and is not suitable for all investors. Always thoroughly test any trading system before using real money, and never risk more than you can afford to lose. The developers are not responsible for any financial losses incurred through the use of this system.
#!/usr/bin/env python3
"""
Comprehensive MCP System Tests
=============================

Test suite for the MCP Trading Agent system components:
- MCP server functionality
- API endpoints
- Agent creation and management
- Data ingestion tools
- Real-time market data
"""

import asyncio
import requests
import time
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Mock pytest.fixture for standalone execution
    def pytest_fixture(func):
        return func
    pytest = type('MockPytest', (), {'fixture': pytest_fixture})()

try:
    from mcp_trading_agent.server import TradingMCPServer
    from mcp_trading_agent.config import TradingConfig
    MCP_MODULES_AVAILABLE = True
except ImportError:
    MCP_MODULES_AVAILABLE = False

class TestMCPSystem:
    """Test suite for MCP Trading Agent system."""
    
    def get_mcp_server(self):
        """Create MCP server instance for testing."""
        if not MCP_MODULES_AVAILABLE:
            return None
        config = TradingConfig()
        server = TradingMCPServer()
        return server
    
    def test_api_health_endpoint(self):
        """Test API health endpoint."""
        response = requests.get("http://localhost:8001/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_api_status_endpoint(self):
        """Test API status endpoint."""
        response = requests.get("http://localhost:8001/api/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["service"] == "mcp-trading-agent"
    
    def test_nq_price_endpoint(self):
        """Test NQ futures price endpoint."""
        response = requests.get("http://localhost:8001/api/market/nq-price", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "symbol" in data
        assert "current_price" in data
        assert "session_high" in data
        assert "session_low" in data
        assert "volume" in data
        assert "timestamp" in data
        assert data["symbol"] == "NQ=F"
        assert data["current_price"] > 0
    
    def test_agents_list_endpoint(self):
        """Test agents listing endpoint."""
        response = requests.get("http://localhost:8001/api/agents", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)
    
    def test_agent_creation(self):
        """Test agent creation via API."""
        payload = {
            "agent_type": "analysis",
            "config": {"symbol": "NQ=F", "test": True}
        }
        response = requests.post(
            "http://localhost:8001/api/agents",
            json=payload,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "agent_id" in data
        assert "status" in data
        assert data["status"] in ["created", "initialized"]
    
    def test_mcp_server_initialization(self):
        """Test MCP server can be initialized."""
        mcp_server = self.get_mcp_server()
        if not mcp_server:
            print("⚠️  MCP modules not available, skipping server tests")
            return
        assert mcp_server is not None
        assert hasattr(mcp_server, 'config')
        assert hasattr(mcp_server, 'mcp')
        assert hasattr(mcp_server, 'provider_manager')
        assert hasattr(mcp_server, 'agent_manager')
    
    def test_provider_status(self):
        """Test LLM provider status."""
        mcp_server = self.get_mcp_server()
        if not mcp_server:
            print("⚠️  MCP modules not available, skipping provider tests")
            return
        status = mcp_server.get_provider_status()
        assert isinstance(status, dict)
        assert "providers" in status
    
    def test_available_tools(self):
        """Test MCP tools are available."""
        mcp_server = self.get_mcp_server()
        if not mcp_server:
            print("⚠️  MCP modules not available, skipping tools tests")
            return
        tools = mcp_server.get_available_tools()
        assert isinstance(tools, list)
        # Should have at least data ingestion tools
        tool_names = [tool.get("name", "") for tool in tools]
        assert any("price" in name.lower() or "data" in name.lower() for name in tool_names)

def test_frontend_accessibility():
    """Test frontend is accessible."""
    response = requests.get("http://localhost:3001", timeout=5)
    assert response.status_code == 200
    assert "NQ Trading Agent" in response.text

def test_nginx_proxy():
    """Test nginx proxy is working."""
    response = requests.get("http://localhost", timeout=5)
    assert response.status_code == 200
    assert "NQ Trading Agent" in response.text

async def test_real_time_data_integration():
    """Test real-time data integration capabilities."""
    import yfinance as yf
    
    # Test direct data access
    ticker = yf.Ticker("NQ=F")
    data = ticker.history(period="1d", interval="1m")
    assert not data.empty
    assert len(data) > 0
    
    # Test via API
    response = requests.get("http://localhost:8001/api/market/nq-price", timeout=10)
    assert response.status_code == 200
    api_data = response.json()
    
    # Data should be reasonably current
    assert api_data["current_price"] > 10000  # NQ should be above 10k
    assert api_data["session_high"] >= api_data["current_price"]
    assert api_data["session_low"] <= api_data["current_price"]

if __name__ == "__main__":
    """Run tests directly."""
    print("Running MCP System Tests...")
    
    # Test basic endpoints
    try:
        test_frontend_accessibility()
        print("✅ Frontend accessibility test passed")
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
    
    try:
        test_nginx_proxy()
        print("✅ Nginx proxy test passed")
    except Exception as e:
        print(f"❌ Nginx test failed: {e}")
    
    # Test API endpoints
    test_suite = TestMCPSystem()
    
    try:
        test_suite.test_api_health_endpoint()
        print("✅ API health test passed")
    except Exception as e:
        print(f"❌ API health test failed: {e}")
    
    try:
        test_suite.test_nq_price_endpoint()
        print("✅ NQ price endpoint test passed")
    except Exception as e:
        print(f"❌ NQ price test failed: {e}")
    
    try:
        test_suite.test_agents_list_endpoint()
        print("✅ Agents list test passed")
    except Exception as e:
        print(f"❌ Agents list test failed: {e}")
    
    try:
        test_suite.test_agent_creation()
        print("✅ Agent creation test passed")
    except Exception as e:
        print(f"❌ Agent creation test failed: {e}")
    
    # Test real-time data
    try:
        asyncio.run(test_real_time_data_integration())
        print("✅ Real-time data integration test passed")
    except Exception as e:
        print(f"❌ Real-time data test failed: {e}")
    
    print("\nMCP System Tests Complete!")
"""
FastAPI Web Application for MCP Trading Agent
=============================================

Modern web interface with real-time updates, agent management, and trading tools.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..server import TradingMCPServer
from .websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

# Pydantic models for API
class AgentCreateRequest(BaseModel):
    agent_type: str
    config: Dict[str, Any] = {}

class TaskRequest(BaseModel):
    task_type: str
    parameters: Dict[str, Any] = {}

class ConfigUpdateRequest(BaseModel):
    updates: Dict[str, Any]

def create_app(mcp_server: TradingMCPServer) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="NQ Trading Agent",
        description="Advanced NQ futures trading with AI analysis",
        version="2.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # WebSocket manager
    ws_manager = WebSocketManager()
    
    # Mount static files
    # app.mount("/static", StaticFiles(directory="ui/static"), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def read_root():
        """Serve the main application page."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>NQ Trading Agent</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="bg-gray-900 text-white">
            <div id="app">
                <nav class="bg-gray-800 p-4">
                    <h1 class="text-2xl font-bold">NQ Trading Agent</h1>
                </nav>
                
                <div class="container mx-auto p-4">
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <!-- Market Data Panel -->
                        <div class="bg-gray-800 p-6 rounded-lg">
                            <h2 class="text-xl font-semibold mb-4">Market Data</h2>
                            <div v-if="marketData">
                                <div class="space-y-2">
                                    <div class="flex justify-between">
                                        <span>Current Price:</span>
                                        <span class="font-mono">${{ marketData.current_price?.toLocaleString() }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Session High:</span>
                                        <span class="font-mono">${{ marketData.session_high?.toLocaleString() }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Session Low:</span>
                                        <span class="font-mono">${{ marketData.session_low?.toLocaleString() }}</span>
                                    </div>
                                    <div class="flex justify-between">
                                        <span>Volume:</span>
                                        <span class="font-mono">{{ marketData.volume?.toLocaleString() }}</span>
                                    </div>
                                </div>
                                <button @click="refreshMarketData" 
                                        class="mt-4 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded w-full">
                                    Refresh Data
                                </button>
                            </div>
                            <div v-else class="text-center">
                                <button @click="refreshMarketData" 
                                        class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded">
                                    Load Market Data
                                </button>
                            </div>
                        </div>
                        
                        <!-- Agents Panel -->
                        <div class="bg-gray-800 p-6 rounded-lg">
                            <h2 class="text-xl font-semibold mb-4">Active Agents</h2>
                            <div class="space-y-3">
                                <div v-for="agent in agents" :key="agent.agent_id" 
                                     class="bg-gray-700 p-3 rounded">
                                    <div class="flex justify-between items-center">
                                        <span class="font-semibold">{{ agent.agent_type }}</span>
                                        <span class="text-sm" :class="getStatusColor(agent.status)">
                                            {{ agent.status }}
                                        </span>
                                    </div>
                                    <div class="text-sm text-gray-300 mt-1">
                                        {{ agent.agent_id.substring(0, 8) }}...
                                    </div>
                                </div>
                            </div>
                            <div class="mt-4">
                                <select v-model="newAgentType" class="bg-gray-700 text-white p-2 rounded w-full mb-2">
                                    <option value="">Select Agent Type</option>
                                    <option value="analysis">Analysis Agent</option>
                                    <option value="execution">Execution Agent</option>
                                    <option value="risk">Risk Agent</option>
                                </select>
                                <button @click="createAgent" 
                                        :disabled="!newAgentType"
                                        class="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 px-4 py-2 rounded w-full">
                                    Create Agent
                                </button>
                            </div>
                        </div>
                        
                        <!-- Analysis Panel -->
                        <div class="bg-gray-800 p-6 rounded-lg">
                            <h2 class="text-xl font-semibold mb-4">AI Analysis</h2>
                            <div class="space-y-3">
                                <textarea v-model="analysisPrompt" 
                                          placeholder="Enter analysis request..."
                                          class="bg-gray-700 text-white p-3 rounded w-full h-24 resize-none">
                                </textarea>
                                <button @click="runAnalysis" 
                                        :disabled="!analysisPrompt || analyzing"
                                        class="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 px-4 py-2 rounded w-full">
                                    {{ analyzing ? 'Analyzing...' : 'Run Analysis' }}
                                </button>
                            </div>
                            <div v-if="analysisResult" class="mt-4 bg-gray-700 p-3 rounded">
                                <h3 class="font-semibold mb-2">Analysis Result:</h3>
                                <pre class="text-sm whitespace-pre-wrap">{{ analysisResult }}</pre>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Status and Logs -->
                    <div class="mt-6 bg-gray-800 p-6 rounded-lg">
                        <h2 class="text-xl font-semibold mb-4">System Status</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="bg-gray-700 p-3 rounded">
                                <div class="text-sm text-gray-300">MCP Server</div>
                                <div class="font-semibold text-green-400">Running</div>
                            </div>
                            <div class="bg-gray-700 p-3 rounded">
                                <div class="text-sm text-gray-300">LLM Providers</div>
                                <div class="font-semibold">{{ providerStatus.healthy_providers || 0 }}/{{ providerStatus.total_providers || 0 }}</div>
                            </div>
                            <div class="bg-gray-700 p-3 rounded">
                                <div class="text-sm text-gray-300">Active Agents</div>
                                <div class="font-semibold">{{ agents.length }}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                const { createApp } = Vue;
                
                createApp({
                    data() {
                        return {
                            marketData: null,
                            agents: [],
                            providerStatus: {},
                            newAgentType: '',
                            analysisPrompt: '',
                            analysisResult: '',
                            analyzing: false,
                            ws: null
                        }
                    },
                    methods: {
                        async refreshMarketData() {
                            try {
                                const response = await fetch('/api/market/nq-price');
                                this.marketData = await response.json();
                            } catch (error) {
                                console.error('Error fetching market data:', error);
                            }
                        },
                        
                        async createAgent() {
                            if (!this.newAgentType) return;
                            
                            try {
                                const response = await fetch('/api/agents', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        agent_type: this.newAgentType,
                                        config: {}
                                    })
                                });
                                
                                if (response.ok) {
                                    this.newAgentType = '';
                                    this.refreshAgents();
                                }
                            } catch (error) {
                                console.error('Error creating agent:', error);
                            }
                        },
                        
                        async refreshAgents() {
                            try {
                                const response = await fetch('/api/agents');
                                this.agents = await response.json();
                            } catch (error) {
                                console.error('Error fetching agents:', error);
                            }
                        },
                        
                        async runAnalysis() {
                            if (!this.analysisPrompt) return;
                            
                            this.analyzing = true;
                            this.analysisResult = '';
                            
                            try {
                                const response = await fetch('/api/analysis', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        prompt: this.analysisPrompt
                                    })
                                });
                                
                                const result = await response.json();
                                this.analysisResult = result.response || result.error || 'No response';
                            } catch (error) {
                                this.analysisResult = `Error: ${error.message}`;
                            } finally {
                                this.analyzing = false;
                            }
                        },
                        
                        async refreshProviderStatus() {
                            try {
                                const response = await fetch('/api/providers/status');
                                this.providerStatus = await response.json();
                            } catch (error) {
                                console.error('Error fetching provider status:', error);
                            }
                        },
                        
                        getStatusColor(status) {
                            const colors = {
                                'initialized': 'text-blue-400',
                                'running': 'text-green-400',
                                'error': 'text-red-400',
                                'stopped': 'text-gray-400'
                            };
                            return colors[status] || 'text-gray-400';
                        },
                        
                        setupWebSocket() {
                            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                            const wsUrl = `${protocol}//${window.location.host}/ws`;
                            
                            this.ws = new WebSocket(wsUrl);
                            
                            this.ws.onmessage = (event) => {
                                const data = JSON.parse(event.data);
                                console.log('WebSocket message:', data);
                                
                                if (data.type === 'market_update') {
                                    this.marketData = data.data;
                                } else if (data.type === 'agent_update') {
                                    this.refreshAgents();
                                }
                            };
                            
                            this.ws.onclose = () => {
                                console.log('WebSocket closed, attempting to reconnect...');
                                setTimeout(() => this.setupWebSocket(), 5000);
                            };
                        }
                    },
                    
                    mounted() {
                        this.refreshMarketData();
                        this.refreshAgents();
                        this.refreshProviderStatus();
                        this.setupWebSocket();
                        
                        // Refresh data every 30 seconds
                        setInterval(() => {
                            this.refreshMarketData();
                            this.refreshProviderStatus();
                        }, 30000);
                    }
                }).mount('#app');
            </script>
        </body>
        </html>
        """
    
    # API Routes
    @app.get("/api/market/nq-price")
    async def get_nq_price():
        """Get current NQ futures price."""
        try:
            result = await mcp_server.mcp.call_tool("get_nq_price")
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/market/historical")
    async def get_historical_data(symbol: str = "NQ=F", period: str = "1d", interval: str = "5m"):
        """Get historical market data."""
        try:
            result = await mcp_server.mcp.call_tool(
                "get_historical_data",
                symbol=symbol,
                period=period,
                interval=interval
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/agents")
    async def list_agents():
        """Get list of active agents."""
        try:
            return mcp_server.list_agents()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/agents")
    async def create_agent(request: AgentCreateRequest):
        """Create a new agent."""
        try:
            agent_id = await mcp_server.create_agent(request.agent_type, request.config)
            return {"agent_id": agent_id, "status": "created"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/agents/{agent_id}/tasks")
    async def execute_agent_task(agent_id: str, request: TaskRequest):
        """Execute a task using a specific agent."""
        try:
            result = await mcp_server.execute_agent_task(agent_id, {
                "type": request.task_type,
                "parameters": request.parameters
            })
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/analysis")
    async def run_analysis(request: dict):
        """Run AI analysis on current market data."""
        try:
            # Get current market data
            market_data = await mcp_server.mcp.call_tool("get_nq_price")
            
            # Create a temporary analysis agent if none exists
            agents = mcp_server.list_agents()
            analysis_agent = None
            
            for agent in agents:
                if agent['type'] == 'analysis':
                    analysis_agent = agent['id']
                    break
            
            if not analysis_agent:
                analysis_agent = await mcp_server.create_agent('analysis', {})
            
            # Execute analysis task
            result = await mcp_server.execute_agent_task(analysis_agent, {
                "type": "market_analysis",
                "parameters": {
                    "prompt": request.get("prompt", "Analyze current market conditions"),
                    "market_data": market_data
                }
            })
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/providers/status")
    async def get_provider_status():
        """Get LLM provider status."""
        try:
            return mcp_server.get_provider_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/tools")
    async def list_tools():
        """Get list of available MCP tools."""
        try:
            return mcp_server.get_available_tools()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        await ws_manager.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                # Echo back for now - can extend for bidirectional communication
                await websocket.send_text(f"Echo: {data}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            ws_manager.disconnect(websocket)
    
    # Background task to send real-time updates
    @app.on_event("startup")
    async def startup_event():
        """Start background tasks."""
        asyncio.create_task(send_periodic_updates())
    
    async def send_periodic_updates():
        """Send periodic updates to connected WebSocket clients."""
        while True:
            try:
                # Get current market data
                market_data = await mcp_server.mcp.call_tool("get_nq_price")
                
                # Send to all connected clients
                await ws_manager.broadcast({
                    "type": "market_update",
                    "data": market_data,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error sending periodic updates: {e}")
                await asyncio.sleep(60)  # Wait longer if there's an error
    
    return app
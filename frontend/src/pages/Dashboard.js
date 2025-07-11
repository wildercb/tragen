import React, { useState, useEffect, useContext } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import Plot from 'react-plotly.js';
import { WebSocketContext } from '../context/WebSocketContext';
import { fetchMarketData, fetchAgents } from '../store/slices/tradingSlice';
import MarketDataCard from '../components/MarketDataCard';
import AgentStatusCard from '../components/AgentStatusCard';
import SystemStatusCard from '../components/SystemStatusCard';
import TradingChart from '../components/TradingChart';

const Dashboard = () => {
  const dispatch = useDispatch();
  const { marketData, agents, systemStatus, loading } = useSelector(state => state.trading);
  const { socket, isConnected } = useContext(WebSocketContext);
  
  useEffect(() => {
    // Load initial data
    dispatch(fetchMarketData());
    dispatch(fetchAgents());
    
    // Set up periodic data refresh
    const interval = setInterval(() => {
      dispatch(fetchMarketData());
    }, 30000); // Refresh every 30 seconds
    
    return () => clearInterval(interval);
  }, [dispatch]);
  
  useEffect(() => {
    // Listen for WebSocket updates
    if (socket) {
      socket.on('market_update', (data) => {
        dispatch({ type: 'trading/updateMarketData', payload: data });
      });
      
      socket.on('agent_update', (data) => {
        dispatch({ type: 'trading/updateAgent', payload: data });
      });
      
      socket.on('system_update', (data) => {
        dispatch({ type: 'trading/updateSystemStatus', payload: data });
      });
    }
  }, [socket, dispatch]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">NQ Trading Agent Dashboard</h1>
        <div className="flex items-center space-x-4">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>
      
      {/* Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <MarketDataCard data={marketData} loading={loading.marketData} />
        <AgentStatusCard agents={agents} loading={loading.agents} />
        <SystemStatusCard status={systemStatus} loading={loading.systemStatus} />
      </div>
      
      {/* Trading Chart */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">NQ Futures Chart</h2>
        <TradingChart symbol="NQ=F" />
      </div>
      
      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Trades</h3>
          <div className="space-y-3">
            {/* Trade history would go here */}
            <p className="text-gray-400">No recent trades</p>
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Analysis</h3>
          <div className="space-y-3">
            {/* Analysis history would go here */}
            <p className="text-gray-400">No recent analysis</p>
          </div>
        </div>
      </div>
      
      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="bg-blue-600 hover:bg-blue-700 px-4 py-3 rounded-lg transition-colors">
            Run Analysis
          </button>
          <button className="bg-green-600 hover:bg-green-700 px-4 py-3 rounded-lg transition-colors">
            Create Agent
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 px-4 py-3 rounded-lg transition-colors">
            Start Backtest
          </button>
          <button className="bg-gray-600 hover:bg-gray-700 px-4 py-3 rounded-lg transition-colors">
            View Logs
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
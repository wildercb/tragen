import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  CircleStackIcon,
  UsersIcon,
  ServerIcon,
  ChartBarSquareIcon,
  CogIcon,
  DocumentArrowDownIcon,
  TrashIcon,
  PencilIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [systemStats, setSystemStats] = useState({});
  const [agentLogs, setAgentLogs] = useState([]);
  const [tradingData, setTradingData] = useState([]);
  const [systemHealth, setSystemHealth] = useState({});

  useEffect(() => {
    fetchSystemStats();
    fetchAgentLogs();
    fetchTradingData();
    fetchSystemHealth();
  }, []);

  const fetchSystemStats = async () => {
    // Mock system statistics
    setSystemStats({
      totalAgents: 12,
      activeAgents: 8,
      totalSignals: 247,
      successfulTrades: 156,
      totalVolume: 2845000,
      uptime: '12d 4h 23m',
      memoryUsage: 68,
      cpuUsage: 45,
    });
  };

  const fetchAgentLogs = async () => {
    // Mock agent logs
    const logs = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      timestamp: new Date(Date.now() - Math.random() * 86400000),
      agent: `Agent_${Math.floor(Math.random() * 10) + 1}`,
      type: ['analysis', 'execution', 'risk'][Math.floor(Math.random() * 3)],
      action: ['Signal Generated', 'Trade Executed', 'Risk Checked', 'Market Analysis'][Math.floor(Math.random() * 4)],
      details: 'Detailed log information about the action performed',
      status: ['success', 'warning', 'error'][Math.floor(Math.random() * 3)],
    }));
    setAgentLogs(logs);
  };

  const fetchTradingData = async () => {
    // Mock trading data
    const trades = Array.from({ length: 30 }, (_, i) => ({
      id: i + 1,
      timestamp: new Date(Date.now() - Math.random() * 86400000 * 7),
      symbol: 'NQ=F',
      side: ['buy', 'sell'][Math.floor(Math.random() * 2)],
      quantity: Math.floor(Math.random() * 10) + 1,
      price: 22800 + Math.random() * 400,
      pnl: (Math.random() - 0.5) * 1000,
      agent: `Agent_${Math.floor(Math.random() * 10) + 1}`,
      status: ['filled', 'pending', 'cancelled'][Math.floor(Math.random() * 3)],
    }));
    setTradingData(trades);
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch('/api/providers/status');
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const filteredLogs = agentLogs.filter(log =>
    log.agent.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.details.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredTrades = tradingData.filter(trade =>
    trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
    trade.agent.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
      case 'filled':
        return 'text-trading-buy bg-trading-buy bg-opacity-20';
      case 'warning':
      case 'pending':
        return 'text-yellow-500 bg-yellow-500 bg-opacity-20';
      case 'error':
      case 'cancelled':
        return 'text-trading-sell bg-trading-sell bg-opacity-20';
      default:
        return 'text-dim-grey-400 bg-dim-grey-400 bg-opacity-20';
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarSquareIcon },
    { id: 'agents', label: 'Agent Logs', icon: CircleStackIcon },
    { id: 'trades', label: 'Trading Data', icon: UsersIcon },
    { id: 'system', label: 'System Health', icon: ServerIcon },
    { id: 'settings', label: 'Settings', icon: CogIcon },
  ];

  return (
    <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700">
      {/* Header */}
      <div className="p-6 border-b border-dim-grey-700">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Admin Dashboard</h2>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dim-grey-400" />
              <input
                type="text"
                placeholder="Search logs, trades, agents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 bg-eerie-black-secondary border border-dim-grey-600 rounded-lg text-white placeholder-dim-grey-400 focus:border-robin-egg-500 focus:outline-none w-64"
              />
            </div>
            
            <button className="flex items-center space-x-2 px-4 py-2 bg-robin-egg-500 hover:bg-robin-egg-600 rounded-lg text-white transition-colors">
              <DocumentArrowDownIcon className="w-4 h-4" />
              <span>Export Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-dim-grey-700">
        <nav className="flex space-x-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-6 py-4 border-b-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-robin-egg-500 text-robin-egg-500 bg-robin-egg-500 bg-opacity-10'
                  : 'border-transparent text-dim-grey-400 hover:text-white hover:border-dim-grey-600'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-dim-grey-400">Total Agents</p>
                      <p className="text-2xl font-bold text-white">{systemStats.totalAgents}</p>
                    </div>
                    <UsersIcon className="w-8 h-8 text-robin-egg-500" />
                  </div>
                </div>
                
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-dim-grey-400">Active Agents</p>
                      <p className="text-2xl font-bold text-trading-buy">{systemStats.activeAgents}</p>
                    </div>
                    <ServerIcon className="w-8 h-8 text-trading-buy" />
                  </div>
                </div>
                
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-dim-grey-400">Total Signals</p>
                      <p className="text-2xl font-bold text-white">{systemStats.totalSignals}</p>
                    </div>
                    <ChartBarSquareIcon className="w-8 h-8 text-robin-egg-500" />
                  </div>
                </div>
                
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-dim-grey-400">Uptime</p>
                      <p className="text-2xl font-bold text-white">{systemStats.uptime}</p>
                    </div>
                    <CircleStackIcon className="w-8 h-8 text-robin-egg-500" />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'agents' && (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-dim-grey-700">
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Timestamp</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Agent</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Type</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Action</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Status</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLogs.slice(0, 20).map((log) => (
                        <tr key={log.id} className="border-b border-dim-grey-800 hover:bg-eerie-black-secondary transition-colors">
                          <td className="py-3 px-4 text-sm text-dim-grey-300">
                            {log.timestamp.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-sm text-white font-mono">
                            {log.agent}
                          </td>
                          <td className="py-3 px-4 text-sm text-dim-grey-300 capitalize">
                            {log.type}
                          </td>
                          <td className="py-3 px-4 text-sm text-white">
                            {log.action}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                              {log.status}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center space-x-2">
                              <button className="p-1 text-dim-grey-400 hover:text-robin-egg-500 transition-colors">
                                <EyeIcon className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-dim-grey-400 hover:text-yellow-500 transition-colors">
                                <PencilIcon className="w-4 h-4" />
                              </button>
                              <button className="p-1 text-dim-grey-400 hover:text-trading-sell transition-colors">
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'trades' && (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-dim-grey-700">
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Time</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Symbol</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Side</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Quantity</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Price</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">P&L</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Agent</th>
                        <th className="text-left py-3 px-4 text-dim-grey-400 font-medium">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTrades.slice(0, 20).map((trade) => (
                        <tr key={trade.id} className="border-b border-dim-grey-800 hover:bg-eerie-black-secondary transition-colors">
                          <td className="py-3 px-4 text-sm text-dim-grey-300">
                            {trade.timestamp.toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-sm text-white font-mono">
                            {trade.symbol}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                              trade.side === 'buy' ? 'text-trading-buy bg-trading-buy bg-opacity-20' : 'text-trading-sell bg-trading-sell bg-opacity-20'
                            }`}>
                              {trade.side.toUpperCase()}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-white">
                            {trade.quantity}
                          </td>
                          <td className="py-3 px-4 text-sm text-white font-mono">
                            ${trade.price.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-sm font-mono">
                            <span className={trade.pnl >= 0 ? 'text-trading-profit' : 'text-trading-loss'}>
                              {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-dim-grey-300 font-mono">
                            {trade.agent}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(trade.status)}`}>
                              {trade.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'system' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <h3 className="text-lg font-semibold text-white mb-4">System Resources</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm text-dim-grey-400 mb-1">
                        <span>Memory Usage</span>
                        <span>{systemStats.memoryUsage}%</span>
                      </div>
                      <div className="w-full bg-dim-grey-700 rounded-full h-2">
                        <div 
                          className="bg-robin-egg-500 h-2 rounded-full"
                          style={{ width: `${systemStats.memoryUsage}%` }}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm text-dim-grey-400 mb-1">
                        <span>CPU Usage</span>
                        <span>{systemStats.cpuUsage}%</span>
                      </div>
                      <div className="w-full bg-dim-grey-700 rounded-full h-2">
                        <div 
                          className="bg-trading-buy h-2 rounded-full"
                          style={{ width: `${systemStats.cpuUsage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-eerie-black-secondary rounded-lg p-4 border border-dim-grey-600">
                  <h3 className="text-lg font-semibold text-white mb-4">Provider Health</h3>
                  <div className="space-y-3">
                    {Object.entries(systemHealth.providers || {}).map(([name, status]) => (
                      <div key={name} className="flex items-center justify-between">
                        <span className="text-dim-grey-300 capitalize">{name}</span>
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            status.health?.healthy ? 'bg-trading-buy' : 'bg-trading-sell'
                          }`} />
                          <span className={`text-sm ${
                            status.health?.healthy ? 'text-trading-buy' : 'text-trading-sell'
                          }`}>
                            {status.health?.healthy ? 'Healthy' : 'Unhealthy'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="bg-eerie-black-secondary rounded-lg p-6 border border-dim-grey-600">
                  <h3 className="text-lg font-semibold text-white mb-4">System Configuration</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-dim-grey-400 mb-2">
                        Default Update Interval (seconds)
                      </label>
                      <input
                        type="number"
                        defaultValue="5"
                        className="w-full px-3 py-2 bg-eerie-black-primary border border-dim-grey-600 rounded-lg text-white focus:border-robin-egg-500 focus:outline-none"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-dim-grey-400 mb-2">
                        Max Log Retention (days)
                      </label>
                      <input
                        type="number"
                        defaultValue="30"
                        className="w-full px-3 py-2 bg-eerie-black-primary border border-dim-grey-600 rounded-lg text-white focus:border-robin-egg-500 focus:outline-none"
                      />
                    </div>
                  </div>
                  
                  <button className="mt-4 px-4 py-2 bg-robin-egg-500 hover:bg-robin-egg-600 rounded-lg text-white transition-colors">
                    Save Settings
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default AdminDashboard;
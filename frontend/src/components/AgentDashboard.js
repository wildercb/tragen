/**
 * AgentDashboard - Professional AI Agent Monitoring and Control Panel
 * ===================================================================
 * 
 * Advanced dashboard for managing AI trading agents with real-time monitoring,
 * performance analytics, and professional trading features.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  CpuChipIcon,
  BoltIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ClockIcon,
  SignalIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

const AgentDashboard = ({
  agents = [],
  signals = [],
  performance = {},
  onAgentAction,
  onAgentCreate,
  onAgentEdit,
  onAgentDelete,
  onClose,
  className = ''
}) => {
  // State
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // 'grid', 'list', 'detailed'
  const [filterStatus, setFilterStatus] = useState('all'); // 'all', 'active', 'inactive', 'error'
  const [sortBy, setSortBy] = useState('performance'); // 'name', 'performance', 'signals', 'created'
  const [searchTerm, setSearchTerm] = useState('');
  
  // Real-time metrics
  const [systemMetrics, setSystemMetrics] = useState({
    totalAgents: 0,
    activeAgents: 0,
    totalSignals: 0,
    avgPerformance: 0,
    systemLoad: 0
  });

  // Calculate real-time metrics
  useEffect(() => {
    const totalAgents = agents.length;
    const activeAgents = agents.filter(a => a.status === 'active').length;
    const totalSignals = signals.length;
    const avgPerformance = agents.length > 0 
      ? agents.reduce((sum, agent) => sum + (performance[agent.id]?.winRate || 0), 0) / agents.length
      : 0;
    
    setSystemMetrics({
      totalAgents,
      activeAgents,
      totalSignals,
      avgPerformance,
      systemLoad: (activeAgents / Math.max(totalAgents, 1)) * 100
    });
  }, [agents, signals, performance]);

  // Filter and sort agents
  const filteredAndSortedAgents = useMemo(() => {
    let filtered = agents;
    
    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(agent => 
        agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
        agent.strategy.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(agent => {
        switch (filterStatus) {
          case 'active':
            return agent.status === 'active';
          case 'inactive':
            return agent.status === 'inactive' || agent.status === 'paused';
          case 'error':
            return agent.status === 'error';
          default:
            return true;
        }
      });
    }
    
    // Sort agents
    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'performance':
          const perfA = performance[a.id]?.winRate || 0;
          const perfB = performance[b.id]?.winRate || 0;
          return perfB - perfA;
        case 'signals':
          const signalsA = performance[a.id]?.totalSignals || 0;
          const signalsB = performance[b.id]?.totalSignals || 0;
          return signalsB - signalsA;
        case 'created':
          return new Date(b.registeredAt || 0) - new Date(a.registeredAt || 0);
        default:
          return 0;
      }
    });
  }, [agents, searchTerm, filterStatus, sortBy, performance]);

  // Get agent status color and icon
  const getAgentStatusInfo = useCallback((status) => {
    switch (status) {
      case 'active':
        return { 
          color: 'text-green-400 bg-green-400/10 border-green-400/20', 
          icon: CheckCircleIcon,
          label: 'Active'
        };
      case 'inactive':
      case 'paused':
        return { 
          color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20', 
          icon: PauseIcon,
          label: 'Paused'
        };
      case 'error':
        return { 
          color: 'text-red-400 bg-red-400/10 border-red-400/20', 
          icon: XCircleIcon,
          label: 'Error'
        };
      default:
        return { 
          color: 'text-gray-400 bg-gray-400/10 border-gray-400/20', 
          icon: InformationCircleIcon,
          label: 'Unknown'
        };
    }
  }, []);

  // Get performance color
  const getPerformanceColor = useCallback((winRate) => {
    if (winRate >= 70) return 'text-green-400';
    if (winRate >= 50) return 'text-yellow-400';
    if (winRate >= 30) return 'text-orange-400';
    return 'text-red-400';
  }, []);

  // Handle agent actions
  const handleAgentAction = useCallback((action, agentId) => {
    if (onAgentAction) {
      onAgentAction(action, agentId);
    }
  }, [onAgentAction]);

  // Get recent signals for agent
  const getAgentSignals = useCallback((agentId, limit = 5) => {
    return signals
      .filter(signal => signal.agentId === agentId)
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
      .slice(0, limit);
  }, [signals]);

  // System Health Indicators
  const SystemHealthBar = () => (
    <div className="grid grid-cols-4 gap-4 mb-6">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Total Agents</p>
            <p className="text-2xl font-bold text-white">{systemMetrics.totalAgents}</p>
          </div>
          <CpuChipIcon className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Active Agents</p>
            <p className="text-2xl font-bold text-green-400">{systemMetrics.activeAgents}</p>
          </div>
          <BoltIcon className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Total Signals</p>
            <p className="text-2xl font-bold text-purple-400">{systemMetrics.totalSignals}</p>
          </div>
          <SignalIcon className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-400">Avg Performance</p>
            <p className={`text-2xl font-bold ${getPerformanceColor(systemMetrics.avgPerformance)}`}>
              {systemMetrics.avgPerformance.toFixed(1)}%
            </p>
          </div>
          <ChartBarIcon className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
    </div>
  );

  // Agent Card Component
  const AgentCard = ({ agent }) => {
    const agentPerf = performance[agent.id] || {};
    const statusInfo = getAgentStatusInfo(agent.status);
    const recentSignals = getAgentSignals(agent.id, 3);
    const StatusIcon = statusInfo.icon;

    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors">
        {/* Agent Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className={`w-10 h-10 rounded-lg ${statusInfo.color} flex items-center justify-center`}>
              <CpuChipIcon className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-semibold text-white">{agent.name}</h3>
              <p className="text-xs text-gray-400">{agent.type} • {agent.strategy}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`flex items-center space-x-1 px-2 py-1 rounded-md border ${statusInfo.color}`}>
              <StatusIcon className="w-3 h-3" />
              <span className="text-xs font-medium">{statusInfo.label}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <button
                onClick={() => handleAgentAction(agent.status === 'active' ? 'pause' : 'resume', agent.id)}
                className="p-1 rounded hover:bg-gray-700 transition-colors"
                title={agent.status === 'active' ? 'Pause' : 'Resume'}
              >
                {agent.status === 'active' ? (
                  <PauseIcon className="w-4 h-4 text-yellow-400" />
                ) : (
                  <PlayIcon className="w-4 h-4 text-green-400" />
                )}
              </button>
              
              <button
                onClick={() => handleAgentAction('stop', agent.id)}
                className="p-1 rounded hover:bg-gray-700 transition-colors"
                title="Stop"
              >
                <StopIcon className="w-4 h-4 text-red-400" />
              </button>
              
              <button
                onClick={() => {
                  setSelectedAgent(agent);
                  setShowEditDialog(true);
                }}
                className="p-1 rounded hover:bg-gray-700 transition-colors"
                title="Settings"
              >
                <Cog6ToothIcon className="w-4 h-4 text-gray-400" />
              </button>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div className="text-center">
            <p className="text-xs text-gray-400">Win Rate</p>
            <p className={`text-sm font-bold ${getPerformanceColor(agentPerf.winRate || 0)}`}>
              {(agentPerf.winRate || 0).toFixed(1)}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-400">Signals</p>
            <p className="text-sm font-bold text-white">{agentPerf.totalSignals || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-400">Return</p>
            <p className={`text-sm font-bold ${
              (agentPerf.avgReturn || 0) >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              {(agentPerf.avgReturn || 0) >= 0 ? '+' : ''}{(agentPerf.avgReturn || 0).toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Recent Signals */}
        <div className="border-t border-gray-700 pt-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-400">Recent Signals</p>
            <span className="text-xs text-gray-500">{recentSignals.length}</span>
          </div>
          
          <div className="space-y-1">
            {recentSignals.length > 0 ? (
              recentSignals.map((signal, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      signal.type === 'buy' ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-gray-300">{signal.symbol}</span>
                    <span className={`font-medium ${
                      signal.type === 'buy' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {signal.type.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <span className="text-gray-400">{(signal.confidence * 100).toFixed(0)}%</span>
                    <span className="text-gray-500">
                      {new Date(signal.timestamp).toLocaleTimeString('en-US', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-gray-500 italic">No recent signals</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Agent List Row Component
  const AgentListRow = ({ agent }) => {
    const agentPerf = performance[agent.id] || {};
    const statusInfo = getAgentStatusInfo(agent.status);
    const StatusIcon = statusInfo.icon;

    return (
      <tr className="border-b border-gray-700 hover:bg-gray-800/50">
        <td className="px-4 py-3">
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-lg ${statusInfo.color} flex items-center justify-center`}>
              <CpuChipIcon className="w-4 h-4" />
            </div>
            <div>
              <p className="font-medium text-white">{agent.name}</p>
              <p className="text-xs text-gray-400">{agent.type}</p>
            </div>
          </div>
        </td>
        
        <td className="px-4 py-3">
          <div className={`flex items-center space-x-1 px-2 py-1 rounded-md border ${statusInfo.color} w-fit`}>
            <StatusIcon className="w-3 h-3" />
            <span className="text-xs font-medium">{statusInfo.label}</span>
          </div>
        </td>
        
        <td className="px-4 py-3">
          <span className={`text-sm font-medium ${getPerformanceColor(agentPerf.winRate || 0)}`}>
            {(agentPerf.winRate || 0).toFixed(1)}%
          </span>
        </td>
        
        <td className="px-4 py-3">
          <span className="text-sm text-white">{agentPerf.totalSignals || 0}</span>
        </td>
        
        <td className="px-4 py-3">
          <span className={`text-sm font-medium ${
            (agentPerf.avgReturn || 0) >= 0 ? 'text-green-400' : 'text-red-400'
          }`}>
            {(agentPerf.avgReturn || 0) >= 0 ? '+' : ''}{(agentPerf.avgReturn || 0).toFixed(2)}%
          </span>
        </td>
        
        <td className="px-4 py-3">
          <span className="text-xs text-gray-400">
            {agent.registeredAt ? new Date(agent.registeredAt).toLocaleDateString() : 'Unknown'}
          </span>
        </td>
        
        <td className="px-4 py-3">
          <div className="flex items-center space-x-1">
            <button
              onClick={() => handleAgentAction(agent.status === 'active' ? 'pause' : 'resume', agent.id)}
              className="p-1 rounded hover:bg-gray-700 transition-colors"
              title={agent.status === 'active' ? 'Pause' : 'Resume'}
            >
              {agent.status === 'active' ? (
                <PauseIcon className="w-4 h-4 text-yellow-400" />
              ) : (
                <PlayIcon className="w-4 h-4 text-green-400" />
              )}
            </button>
            
            <button
              onClick={() => handleAgentAction('stop', agent.id)}
              className="p-1 rounded hover:bg-gray-700 transition-colors"
              title="Stop"
            >
              <StopIcon className="w-4 h-4 text-red-400" />
            </button>
            
            <button
              onClick={() => {
                setSelectedAgent(agent);
                setShowEditDialog(true);
              }}
              className="p-1 rounded hover:bg-gray-700 transition-colors"
              title="Settings"
            >
              <Cog6ToothIcon className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </td>
      </tr>
    );
  };

  return (
    <div className={`bg-gray-900 border-l border-gray-700 w-96 max-w-md flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <CpuChipIcon className="w-6 h-6 text-blue-400" />
          <div>
            <h2 className="text-lg font-semibold text-white">AI Agents</h2>
            <p className="text-sm text-gray-400">{systemMetrics.activeAgents} active of {systemMetrics.totalAgents}</p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCreateDialog(true)}
            className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            title="Create New Agent"
          >
            <PlusIcon className="w-4 h-4 text-white" />
          </button>
          
          <button
            onClick={onClose}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            title="Close"
          >
            <XCircleIcon className="w-4 h-4 text-gray-300" />
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="p-4 border-b border-gray-700 space-y-3">
        {/* Search */}
        <div className="relative">
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 pl-9 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="error">Error</option>
          </select>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            <option value="performance">Performance</option>
            <option value="name">Name</option>
            <option value="signals">Signals</option>
            <option value="created">Created</option>
          </select>
        </div>

        {/* View Mode */}
        <div className="flex items-center space-x-1 bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            List
          </button>
        </div>
      </div>

      {/* System Health */}
      <div className="p-4 border-b border-gray-700">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Active</span>
              <span className="text-sm font-bold text-green-400">{systemMetrics.activeAgents}</span>
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Signals</span>
              <span className="text-sm font-bold text-purple-400">{systemMetrics.totalSignals}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto">
        {filteredAndSortedAgents.length > 0 ? (
          <div className="p-4 space-y-3">
            {viewMode === 'grid' ? (
              filteredAndSortedAgents.map(agent => (
                <AgentCard key={agent.id} agent={agent} />
              ))
            ) : (
              <div className="bg-gray-800 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Agent</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Status</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Win %</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Signals</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Return</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAndSortedAgents.map(agent => (
                      <AgentListRow key={agent.id} agent={agent} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center">
              <CpuChipIcon className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 mb-2">No agents found</p>
              <p className="text-sm text-gray-500 mb-4">
                {searchTerm || filterStatus !== 'all' 
                  ? 'Try adjusting your filters'
                  : 'Create your first AI trading agent'
                }
              </p>
              {!searchTerm && filterStatus === 'all' && (
                <button
                  onClick={() => setShowCreateDialog(true)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Create Agent
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>System Load: {systemMetrics.systemLoad.toFixed(1)}%</span>
          <span>Avg Performance: {systemMetrics.avgPerformance.toFixed(1)}%</span>
        </div>
      </div>

      {/* Create Agent Dialog */}
      {showCreateDialog && (
        <CreateAgentDialog
          onClose={() => setShowCreateDialog(false)}
          onCreate={(agentConfig) => {
            if (onAgentCreate) onAgentCreate(agentConfig);
            setShowCreateDialog(false);
          }}
        />
      )}

      {/* Edit Agent Dialog */}
      {showEditDialog && selectedAgent && (
        <EditAgentDialog
          agent={selectedAgent}
          onClose={() => {
            setShowEditDialog(false);
            setSelectedAgent(null);
          }}
          onSave={(agentConfig) => {
            if (onAgentEdit) onAgentEdit(selectedAgent.id, agentConfig);
            setShowEditDialog(false);
            setSelectedAgent(null);
          }}
          onDelete={() => {
            if (onAgentDelete) onAgentDelete(selectedAgent.id);
            setShowEditDialog(false);
            setSelectedAgent(null);
          }}
        />
      )}
    </div>
  );
};

// Create Agent Dialog Component
const CreateAgentDialog = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'trading',
    strategy: '',
    symbols: ['NQ=F'],
    timeframes: ['5m'],
    riskTolerance: 0.02,
    maxSignalsPerHour: 10,
    indicators: ['sma20', 'rsi', 'macd'],
    permissions: ['read_data', 'send_signals']
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
        <h3 className="text-lg font-semibold text-white mb-4">Create New Agent</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              placeholder="My Trading Agent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Strategy</label>
            <input
              type="text"
              value={formData.strategy}
              onChange={(e) => setFormData(prev => ({ ...prev, strategy: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              placeholder="Momentum Trading"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Risk Tolerance</label>
            <select
              value={formData.riskTolerance}
              onChange={(e) => setFormData(prev => ({ ...prev, riskTolerance: parseFloat(e.target.value) }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value={0.01}>Conservative (1%)</option>
              <option value={0.02}>Moderate (2%)</option>
              <option value={0.05}>Aggressive (5%)</option>
            </select>
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Create Agent
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Edit Agent Dialog Component
const EditAgentDialog = ({ agent, onClose, onSave, onDelete }) => {
  const [formData, setFormData] = useState({
    name: agent.name || '',
    strategy: agent.strategy || '',
    riskTolerance: agent.riskTolerance || 0.02,
    maxSignalsPerHour: agent.maxSignalsPerHour || 10,
    status: agent.status || 'active'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-96 max-w-full mx-4">
        <h3 className="text-lg font-semibold text-white mb-4">Edit Agent: {agent.name}</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Strategy</label>
            <input
              type="text"
              value={formData.strategy}
              onChange={(e) => setFormData(prev => ({ ...prev, strategy: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Status</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          
          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={() => {
                if (window.confirm('Are you sure you want to delete this agent?')) {
                  onDelete();
                }
              }}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
            >
              Delete
            </button>
            
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentDashboard;
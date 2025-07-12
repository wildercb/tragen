import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  CpuChipIcon,
  Cog6ToothIcon,
  DocumentChartBarIcon,
  EyeIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline';
import TradingChart from '../components/TradingChart';
import LiveDataPanel from '../components/LiveDataPanel';
import AgentPipeline from '../components/AgentPipeline';
import AdminDashboard from '../components/AdminDashboard';

const TradingDashboard = () => {
  const [activeView, setActiveView] = useState('trading');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState('NQ=F');
  const [currentDisplaySymbol, setCurrentDisplaySymbol] = useState('NQ');

  const views = [
    {
      id: 'trading',
      label: 'Live Trading',
      icon: ChartBarIcon,
      description: 'Real-time charts and market data',
    },
    {
      id: 'agents',
      label: 'AI Agents',
      icon: CpuChipIcon,
      description: 'Agent pipeline and analysis',
    },
    {
      id: 'admin',
      label: 'Admin Panel',
      icon: Cog6ToothIcon,
      description: 'System management and logs',
    },
  ];

  const renderActiveView = () => {
    switch (activeView) {
      case 'trading':
        return <TradingView isFullscreen={isFullscreen} currentSymbol={currentSymbol} currentDisplaySymbol={currentDisplaySymbol} setCurrentSymbol={setCurrentSymbol} setCurrentDisplaySymbol={setCurrentDisplaySymbol} />;
      case 'agents':
        return <AgentsView />;
      case 'admin':
        return <AdminView />;
      default:
        return <TradingView isFullscreen={isFullscreen} currentSymbol={currentSymbol} currentDisplaySymbol={currentDisplaySymbol} setCurrentSymbol={setCurrentSymbol} setCurrentDisplaySymbol={setCurrentDisplaySymbol} />;
    }
  };

  return (
    <div className="min-h-screen bg-eerie-black-primary">
      {/* Header */}
      <header className="bg-eerie-black-secondary border-b border-dim-grey-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <BuildingOffice2Icon className="w-8 h-8 text-robin-egg-500" />
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    NQ Trading Agent
                  </h1>
                  <p className="text-sm text-dim-grey-400">
                    Advanced AI-Powered Futures Trading
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* View Selector */}
              <nav className="flex space-x-1 bg-eerie-black-tertiary rounded-lg p-1">
                {views.map((view) => (
                  <button
                    key={view.id}
                    onClick={() => setActiveView(view.id)}
                    className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeView === view.id
                        ? 'bg-robin-egg-500 text-white'
                        : 'text-dim-grey-400 hover:text-white hover:bg-eerie-black-secondary'
                    }`}
                  >
                    <view.icon className="w-4 h-4" />
                    <span>{view.label}</span>
                  </button>
                ))}
              </nav>

              {/* Fullscreen Toggle */}
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="p-2 rounded-lg bg-eerie-black-tertiary hover:bg-dim-grey-700 transition-colors"
                title="Toggle Fullscreen"
              >
                <EyeIcon className="w-5 h-5 text-dim-grey-400" />
              </button>
            </div>
          </div>

          {/* Active View Description */}
          <div className="mt-4">
            <p className="text-dim-grey-400 text-sm">
              {views.find(v => v.id === activeView)?.description}
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <motion.div
          key={activeView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
        >
          {renderActiveView()}
        </motion.div>
      </main>
    </div>
  );
};

// Trading View Component
const TradingView = ({ isFullscreen, currentSymbol, currentDisplaySymbol, setCurrentSymbol, setCurrentDisplaySymbol }) => {
  return (
    <div className={`grid gap-6 ${isFullscreen ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-4'}`}>
      {/* Live Data Panel */}
      {!isFullscreen && (
        <div className="lg:col-span-1">
          <LiveDataPanel symbol={currentSymbol} displaySymbol={currentDisplaySymbol} />
        </div>
      )}

      {/* Trading Chart */}
      <div className={isFullscreen ? 'col-span-1' : 'lg:col-span-3'}>
        <TradingChart 
          symbol={currentSymbol}
          displaySymbol={currentDisplaySymbol}
          height={isFullscreen ? 800 : 600} 
          apiBaseUrl="http://localhost:8001"
          onSignalReceived={(signal) => console.log('Signal received:', signal)}
          onSymbolChange={(newSymbol, newDisplaySymbol) => {
            setCurrentSymbol(newSymbol);
            setCurrentDisplaySymbol(newDisplaySymbol);
          }}
        />
      </div>

      {/* Additional Trading Info */}
      {!isFullscreen && (
        <div className="lg:col-span-4 grid grid-cols-1 md:grid-cols-3 gap-6">
          <TradingStatsCard title="Today's P&L" value="+$1,247.50" trend="up" />
          <TradingStatsCard title="Win Rate" value="68.4%" trend="up" />
          <TradingStatsCard title="Total Trades" value="24" trend="neutral" />
        </div>
      )}
    </div>
  );
};

// Agents View Component
const AgentsView = () => {
  return (
    <div>
      <AgentPipeline />
    </div>
  );
};

// Admin View Component
const AdminView = () => {
  return (
    <div>
      <AdminDashboard />
    </div>
  );
};

// Trading Stats Card Component
const TradingStatsCard = ({ title, value, trend }) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-trading-profit';
      case 'down':
        return 'text-trading-loss';
      default:
        return 'text-dim-grey-400';
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-dim-grey-400 mb-1">{title}</p>
          <p className={`text-2xl font-bold ${getTrendColor()}`}>{value}</p>
        </div>
        <DocumentChartBarIcon className={`w-8 h-8 ${getTrendColor()}`} />
      </div>
    </motion.div>
  );
};

export default TradingDashboard;
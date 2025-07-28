import React from 'react';
import MarketDataCard from '../components/MarketDataCard';
import LiveTradingSignals from '../components/LiveTradingSignals';

const Dashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">NQ Trading Agent Dashboard</h1>
      
      {/* Market Data Overview */}
      <MarketDataCard data={{current_price: 0, session_high: 0, session_low: 0}} loading={false} />
      
      {/* Live Trading Signals */}
      <LiveTradingSignals />
    </div>
  );
};

export default Dashboard;
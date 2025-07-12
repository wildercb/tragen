import React from 'react';
import MarketDataCard from '../components/MarketDataCard';

const Dashboard = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">NQ Trading Agent Dashboard</h1>
      <MarketDataCard data={{current_price: 0, session_high: 0, session_low: 0}} loading={false} />
    </div>
  );
};

export default Dashboard;
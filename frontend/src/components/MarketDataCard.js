import React from 'react';
import { TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';

const MarketDataCard = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 animate-pulse">
        <h3 className="text-lg font-semibold mb-4">Market Data</h3>
        <div className="space-y-3">
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          <div className="h-4 bg-gray-700 rounded w-1/2"></div>
          <div className="h-4 bg-gray-700 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Market Data</h3>
        <p className="text-gray-400">No market data available</p>
      </div>
    );
  }

  const priceChange = data.current_price - (data.session_low + (data.session_high - data.session_low) / 2);
  const isPositive = priceChange >= 0;

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">NQ Futures</h3>
        <div className="flex items-center">
          {isPositive ? (
            <TrendingUpIcon className="w-5 h-5 text-green-500" />
          ) : (
            <TrendingDownIcon className="w-5 h-5 text-red-500" />
          )}
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400">Current Price:</span>
          <span className="font-mono text-xl">
            ${data.current_price?.toLocaleString()}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Session High:</span>
          <span className="font-mono text-green-400">
            ${data.session_high?.toLocaleString()}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Session Low:</span>
          <span className="font-mono text-red-400">
            ${data.session_low?.toLocaleString()}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Volume:</span>
          <span className="font-mono">
            {data.volume?.toLocaleString()}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-400">Range:</span>
          <span className="font-mono">
            {data.range_pct?.toFixed(2)}%
          </span>
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="text-sm text-gray-400 mb-2">Position in Range</div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${data.position_in_range || 0}%` }}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {data.position_in_range?.toFixed(1)}%
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <button 
          className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition-colors"
          onClick={() => window.location.reload()}
        >
          Refresh Data
        </button>
      </div>
    </div>
  );
};

export default MarketDataCard;
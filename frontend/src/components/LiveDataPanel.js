import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BoltIcon,
  ClockIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

const LiveDataPanel = ({ symbol = 'NQ=F', displaySymbol = 'NQ' }) => {
  const [marketData, setMarketData] = useState(null);
  const [prevPrice, setPrevPrice] = useState(null);
  const [priceDirection, setPriceDirection] = useState('neutral');
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Fetch live market data
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/market/price?symbol=${symbol}`);
        const data = await response.json();
        
        if (marketData) {
          setPrevPrice(marketData.current_price);
          if (data.current_price > marketData.current_price) {
            setPriceDirection('up');
          } else if (data.current_price < marketData.current_price) {
            setPriceDirection('down');
          } else {
            setPriceDirection('neutral');
          }
        }
        
        setMarketData(data);
        setLastUpdate(new Date());
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        setLoading(false);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, [marketData]);

  if (loading) {
    return (
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-dim-grey-700 rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-12 bg-dim-grey-700 rounded"></div>
            <div className="h-6 bg-dim-grey-700 rounded w-2/3"></div>
            <div className="h-6 bg-dim-grey-700 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!marketData) {
    return (
      <div className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700 p-6">
        <div className="text-center text-dim-grey-400">
          <ChartBarIcon className="w-12 h-12 mx-auto mb-4" />
          <p>Failed to load market data</p>
        </div>
      </div>
    );
  }

  const priceChange = prevPrice ? marketData.current_price - prevPrice : 0;
  const priceChangePercent = prevPrice ? ((priceChange / prevPrice) * 100) : 0;
  const sessionRange = marketData.session_high - marketData.session_low;
  const positionInRange = sessionRange > 0 
    ? ((marketData.current_price - marketData.session_low) / sessionRange) * 100 
    : 50;

  const getDirectionIcon = () => {
    switch (priceDirection) {
      case 'up':
        return <ArrowTrendingUpIcon className="w-6 h-6 text-trading-buy" />;
      case 'down':
        return <ArrowTrendingDownIcon className="w-6 h-6 text-trading-sell" />;
      default:
        return <BoltIcon className="w-6 h-6 text-dim-grey-400" />;
    }
  };

  const getDirectionColor = () => {
    switch (priceDirection) {
      case 'up':
        return 'text-trading-buy';
      case 'down':
        return 'text-trading-sell';
      default:
        return 'text-white';
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-eerie-black-tertiary rounded-lg border border-dim-grey-700"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-dim-grey-700">
        <div className="flex items-center space-x-3">
          <motion.div
            key={priceDirection}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            {getDirectionIcon()}
          </motion.div>
          <h3 className="text-lg font-semibold text-white">{displaySymbol}</h3>
        </div>
        
        <div className="flex items-center space-x-2 text-sm text-dim-grey-400">
          <ClockIcon className="w-4 h-4" />
          <span>
            {lastUpdate?.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Current Price */}
      <div className="p-6">
        <div className="text-center mb-6">
          <motion.div
            key={marketData.current_price}
            initial={{ scale: 1.1 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2 }}
            className={`text-4xl font-mono font-bold ${getDirectionColor()}`}
          >
            ${marketData.current_price?.toLocaleString()}
          </motion.div>
          
          <AnimatePresence>
            {priceChange !== 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`text-lg font-medium mt-2 ${
                  priceChange >= 0 ? 'text-trading-profit' : 'text-trading-loss'
                }`}
              >
                {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}
                <span className="text-sm ml-2">
                  ({priceChangePercent >= 0 ? '+' : ''}{priceChangePercent.toFixed(3)}%)
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Session Data */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-eerie-black-secondary rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-dim-grey-400">Session High</span>
              <ArrowTrendingUpIcon className="w-4 h-4 text-trading-buy" />
            </div>
            <div className="text-xl font-mono font-semibold text-trading-buy mt-1">
              ${marketData.session_high?.toLocaleString()}
            </div>
          </div>
          
          <div className="bg-eerie-black-secondary rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-dim-grey-400">Session Low</span>
              <ArrowTrendingDownIcon className="w-4 h-4 text-trading-sell" />
            </div>
            <div className="text-xl font-mono font-semibold text-trading-sell mt-1">
              ${marketData.session_low?.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Range Indicator */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-dim-grey-400 mb-2">
            <span>Position in Range</span>
            <span>{positionInRange.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-dim-grey-700 rounded-full h-3 relative overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${positionInRange}%` }}
              transition={{ duration: 0.5 }}
              className="bg-gradient-to-r from-trading-sell via-robin-egg-500 to-trading-buy h-full rounded-full"
            />
            <div 
              className="absolute top-0 w-1 h-full bg-white shadow-lg"
              style={{ left: `${positionInRange}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-dim-grey-500 mt-1">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>

        {/* Volume */}
        <div className="bg-eerie-black-secondary rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-dim-grey-400">Volume</span>
            <ChartBarIcon className="w-4 h-4 text-robin-egg-500" />
          </div>
          <div className="text-xl font-mono font-semibold text-white mt-1">
            {marketData.volume?.toLocaleString()}
          </div>
          <div className="text-xs text-dim-grey-500 mt-1">
            contracts traded
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-dim-grey-700 bg-eerie-black-secondary rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-dim-grey-500">
          <span>Real-time data</span>
          <span>Delayed by 15 minutes</span>
        </div>
      </div>
    </motion.div>
  );
};

export default LiveDataPanel;
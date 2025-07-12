import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  GlobeAltIcon,
  BuildingLibraryIcon,
  FireIcon,
  StarIcon,
} from '@heroicons/react/24/outline';

const SymbolSearch = ({ isOpen, onClose, onSymbolSelect, currentSymbol }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedBroker, setSelectedBroker] = useState('all');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const searchInputRef = useRef(null);

  // Categories for symbol classification
  const categories = [
    { id: 'all', name: 'All', icon: ChartBarIcon },
    { id: 'crypto', name: 'Crypto', icon: CurrencyDollarIcon },
    { id: 'stocks', name: 'Stocks', icon: BuildingLibraryIcon },
    { id: 'futures', name: 'Futures', icon: FireIcon },
    { id: 'forex', name: 'Forex', icon: GlobeAltIcon },
    { id: 'indices', name: 'Indices', icon: ChartBarIcon },
  ];

  // Brokers/Exchanges similar to TradingView
  const brokers = [
    { id: 'all', name: 'All Brokers', description: 'All available sources' },
    { id: 'binance', name: 'Binance', description: 'Cryptocurrency exchange' },
    { id: 'coinbase', name: 'Coinbase', description: 'Cryptocurrency exchange' },
    { id: 'kraken', name: 'Kraken', description: 'Cryptocurrency exchange' },
    { id: 'nasdaq', name: 'NASDAQ', description: 'US stock exchange' },
    { id: 'nyse', name: 'NYSE', description: 'US stock exchange' },
    { id: 'cme', name: 'CME', description: 'Futures exchange' },
    { id: 'forex', name: 'FOREX.com', description: 'Forex broker' },
    { id: 'oanda', name: 'OANDA', description: 'Forex broker' },
    { id: 'yahoo', name: 'Yahoo Finance', description: 'Financial data provider' },
  ];

  // Comprehensive symbol database
  const symbolDatabase = [
    // Cryptocurrencies
    { symbol: 'BTCUSDT', display: 'BTCUSDT', name: 'Bitcoin / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'ETHUSDT', display: 'ETHUSDT', name: 'Ethereum / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'ADAUSDT', display: 'ADAUSDT', name: 'Cardano / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'BNBUSDT', display: 'BNBUSDT', name: 'Binance Coin / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'XRPUSDT', display: 'XRPUSDT', name: 'XRP / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'SOLUSDT', display: 'SOLUSDT', name: 'Solana / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'DOTUSDT', display: 'DOTUSDT', name: 'Polkadot / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'DOGEUSDT', display: 'DOGEUSDT', name: 'Dogecoin / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'AVAXUSDT', display: 'AVAXUSDT', name: 'Avalanche / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'MATICUSDT', display: 'MATICUSDT', name: 'Polygon / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'LTCUSDT', display: 'LTCUSDT', name: 'Litecoin / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    { symbol: 'LINKUSDT', display: 'LINKUSDT', name: 'Chainlink / Tether USD', category: 'crypto', broker: 'binance', type: 'cryptocurrency' },
    
    // Coinbase Pro symbols
    { symbol: 'BTC-USD', display: 'BTC-USD', name: 'Bitcoin / US Dollar', category: 'crypto', broker: 'coinbase', type: 'cryptocurrency' },
    { symbol: 'ETH-USD', display: 'ETH-USD', name: 'Ethereum / US Dollar', category: 'crypto', broker: 'coinbase', type: 'cryptocurrency' },
    
    // US Stocks
    { symbol: 'AAPL', display: 'AAPL', name: 'Apple Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'MSFT', display: 'MSFT', name: 'Microsoft Corporation', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'GOOGL', display: 'GOOGL', name: 'Alphabet Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'AMZN', display: 'AMZN', name: 'Amazon.com Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'TSLA', display: 'TSLA', name: 'Tesla Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'NVDA', display: 'NVDA', name: 'NVIDIA Corporation', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'META', display: 'META', name: 'Meta Platforms Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'NFLX', display: 'NFLX', name: 'Netflix Inc.', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'AMD', display: 'AMD', name: 'Advanced Micro Devices', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    { symbol: 'INTC', display: 'INTC', name: 'Intel Corporation', category: 'stocks', broker: 'nasdaq', type: 'stock' },
    
    // NYSE Stocks
    { symbol: 'JPM', display: 'JPM', name: 'JPMorgan Chase & Co.', category: 'stocks', broker: 'nyse', type: 'stock' },
    { symbol: 'JNJ', display: 'JNJ', name: 'Johnson & Johnson', category: 'stocks', broker: 'nyse', type: 'stock' },
    { symbol: 'V', display: 'V', name: 'Visa Inc.', category: 'stocks', broker: 'nyse', type: 'stock' },
    { symbol: 'PG', display: 'PG', name: 'Procter & Gamble Co.', category: 'stocks', broker: 'nyse', type: 'stock' },
    { symbol: 'UNH', display: 'UNH', name: 'UnitedHealth Group Inc.', category: 'stocks', broker: 'nyse', type: 'stock' },
    
    // Futures
    { symbol: 'NQ=F', display: 'NQ', name: 'NASDAQ-100 E-mini Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'ES=F', display: 'ES', name: 'S&P 500 E-mini Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'YM=F', display: 'YM', name: 'Dow Jones E-mini Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'RTY=F', display: 'RTY', name: 'Russell 2000 E-mini Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'CL=F', display: 'CL', name: 'Crude Oil Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'GC=F', display: 'GC', name: 'Gold Future', category: 'futures', broker: 'cme', type: 'future' },
    { symbol: 'SI=F', display: 'SI', name: 'Silver Future', category: 'futures', broker: 'cme', type: 'future' },
    
    // Forex
    { symbol: 'EURUSD=X', display: 'EUR/USD', name: 'Euro / US Dollar', category: 'forex', broker: 'forex', type: 'currency' },
    { symbol: 'GBPUSD=X', display: 'GBP/USD', name: 'British Pound / US Dollar', category: 'forex', broker: 'forex', type: 'currency' },
    { symbol: 'USDJPY=X', display: 'USD/JPY', name: 'US Dollar / Japanese Yen', category: 'forex', broker: 'forex', type: 'currency' },
    { symbol: 'AUDUSD=X', display: 'AUD/USD', name: 'Australian Dollar / US Dollar', category: 'forex', broker: 'forex', type: 'currency' },
    { symbol: 'USDCAD=X', display: 'USD/CAD', name: 'US Dollar / Canadian Dollar', category: 'forex', broker: 'forex', type: 'currency' },
    
    // ETFs and Indices
    { symbol: 'SPY', display: 'SPY', name: 'SPDR S&P 500 ETF', category: 'indices', broker: 'nasdaq', type: 'etf' },
    { symbol: 'QQQ', display: 'QQQ', name: 'Invesco QQQ Trust', category: 'indices', broker: 'nasdaq', type: 'etf' },
    { symbol: 'IWM', display: 'IWM', name: 'iShares Russell 2000 ETF', category: 'indices', broker: 'nasdaq', type: 'etf' },
    { symbol: 'VTI', display: 'VTI', name: 'Vanguard Total Stock Market ETF', category: 'indices', broker: 'nasdaq', type: 'etf' },
    { symbol: 'DIA', display: 'DIA', name: 'SPDR Dow Jones Industrial Average ETF', category: 'indices', broker: 'nasdaq', type: 'etf' },
  ];

  // Popular/trending symbols
  const popularSymbols = [
    'BTCUSDT', 'ETHUSDT', 'NQ=F', 'ES=F', 'AAPL', 'TSLA', 'NVDA', 'SPY'
  ];

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    if (searchTerm.length === 0) {
      // Show popular symbols when no search term
      const popular = symbolDatabase.filter(symbol => 
        popularSymbols.includes(symbol.symbol)
      );
      setResults(popular);
    } else {
      // Filter symbols based on search term
      const filtered = symbolDatabase.filter(symbol => {
        const matchesSearch = 
          symbol.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
          symbol.display.toLowerCase().includes(searchTerm.toLowerCase()) ||
          symbol.name.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesCategory = selectedCategory === 'all' || symbol.category === selectedCategory;
        const matchesBroker = selectedBroker === 'all' || symbol.broker === selectedBroker;
        
        return matchesSearch && matchesCategory && matchesBroker;
      });
      
      setResults(filtered.slice(0, 50)); // Limit results for performance
    }
  }, [searchTerm, selectedCategory, selectedBroker]);

  const handleSymbolSelect = (symbol) => {
    onSymbolSelect(symbol.symbol, symbol.display);
    onClose();
  };

  const getCategoryIcon = (category) => {
    const cat = categories.find(c => c.id === category);
    return cat ? cat.icon : ChartBarIcon;
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'cryptocurrency':
        return 'text-yellow-400';
      case 'stock':
        return 'text-blue-400';
      case 'future':
        return 'text-red-400';
      case 'currency':
        return 'text-green-400';
      case 'etf':
        return 'text-purple-400';
      default:
        return 'text-dim-grey-400';
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-eerie-black-secondary rounded-lg border border-dim-grey-700 w-full max-w-4xl max-h-[80vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-dim-grey-700">
            <h3 className="text-xl font-semibold text-white">Symbol Search</h3>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-dim-grey-700 transition-colors"
            >
              <XMarkIcon className="w-5 h-5 text-dim-grey-400" />
            </button>
          </div>

          {/* Search Input */}
          <div className="p-6 border-b border-dim-grey-700">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-dim-grey-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search symbols (e.g., BTCUSDT, AAPL, NQ, EUR/USD)..."
                className="w-full pl-10 pr-4 py-3 bg-eerie-black-tertiary border border-dim-grey-600 rounded-lg text-white placeholder-dim-grey-400 focus:outline-none focus:border-robin-egg-500"
              />
            </div>
          </div>

          {/* Filters */}
          <div className="p-6 border-b border-dim-grey-700">
            {/* Categories */}
            <div className="mb-4">
              <h4 className="text-sm font-medium text-dim-grey-400 mb-3">Categories</h4>
              <div className="flex flex-wrap gap-2">
                {categories.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedCategory === category.id
                        ? 'bg-robin-egg-500 text-white'
                        : 'bg-eerie-black-tertiary text-dim-grey-400 hover:text-white hover:bg-dim-grey-700'
                    }`}
                  >
                    <category.icon className="w-4 h-4" />
                    <span>{category.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Brokers */}
            <div>
              <h4 className="text-sm font-medium text-dim-grey-400 mb-3">Brokers & Exchanges</h4>
              <select
                value={selectedBroker}
                onChange={(e) => setSelectedBroker(e.target.value)}
                className="bg-eerie-black-tertiary border border-dim-grey-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-robin-egg-500"
              >
                {brokers.map((broker) => (
                  <option key={broker.id} value={broker.id}>
                    {broker.name} - {broker.description}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Results */}
          <div className="p-6 max-h-96 overflow-y-auto">
            {searchTerm.length === 0 && (
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <FireIcon className="w-4 h-4 text-orange-400" />
                  <h4 className="text-sm font-medium text-dim-grey-400">Popular & Trending</h4>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {results.map((symbol, index) => {
                const IconComponent = getCategoryIcon(symbol.category);
                const isCurrentSymbol = symbol.symbol === currentSymbol;
                
                return (
                  <motion.div
                    key={symbol.symbol}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => handleSymbolSelect(symbol)}
                    className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
                      isCurrentSymbol
                        ? 'bg-robin-egg-500 bg-opacity-20 border border-robin-egg-500'
                        : 'hover:bg-eerie-black-tertiary'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <IconComponent className={`w-5 h-5 ${getTypeColor(symbol.type)}`} />
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-white">{symbol.display}</span>
                          {isCurrentSymbol && (
                            <StarIcon className="w-4 h-4 text-robin-egg-500" />
                          )}
                          {popularSymbols.includes(symbol.symbol) && (
                            <FireIcon className="w-4 h-4 text-orange-400" />
                          )}
                        </div>
                        <p className="text-sm text-dim-grey-400">{symbol.name}</p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-xs text-dim-grey-500 uppercase">
                        {brokers.find(b => b.id === symbol.broker)?.name || symbol.broker}
                      </p>
                      <p className={`text-xs uppercase ${getTypeColor(symbol.type)}`}>
                        {symbol.type}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {results.length === 0 && searchTerm.length > 0 && (
              <div className="text-center py-8 text-dim-grey-400">
                <ChartBarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No symbols found matching "{searchTerm}"</p>
                <p className="text-sm mt-2">Try adjusting your search or filters</p>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default SymbolSearch;
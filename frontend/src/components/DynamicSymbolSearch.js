import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  ClockIcon,
} from '@heroicons/react/24/outline';

const DynamicSymbolSearch = ({ isOpen, onClose, onSymbolSelect, currentSymbol }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recentSymbols, setRecentSymbols] = useState([]);
  const searchInputRef = useRef(null);
  const debounceTimer = useRef(null);

  // Load recent symbols from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentTradingSymbols');
    if (stored) {
      try {
        setRecentSymbols(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent symbols:', e);
      }
    }
  }, []);

  // Save recent symbols to localStorage
  const saveRecentSymbol = useCallback((symbol) => {
    const newRecent = [symbol, ...recentSymbols.filter(s => s.symbol !== symbol.symbol)].slice(0, 10);
    setRecentSymbols(newRecent);
    localStorage.setItem('recentTradingSymbols', JSON.stringify(newRecent));
  }, [recentSymbols]);

  // Search symbols via our backend API (which proxies TradingView)
  const searchSymbols = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Use our backend API which proxies TradingView's symbol search
      const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001';
      const response = await fetch(
        `${apiBaseUrl}/api/market/search-symbols?query=${encodeURIComponent(query)}&limit=50`
      );
      
      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setResults(data.results || []);
      
    } catch (error) {
      console.error('Symbol search failed:', error);
      // Fallback to a basic symbol list if backend API fails
      setResults(getFallbackResults(query));
    } finally {
      setLoading(false);
    }
  }, []);

  // Fallback results if TradingView API is unavailable
  const getFallbackResults = (query) => {
    const fallbackSymbols = [
      { symbol: 'AAPL', display: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', type: 'stock' },
      { symbol: 'TSLA', display: 'TSLA', name: 'Tesla Inc.', exchange: 'NASDAQ', type: 'stock' },
      { symbol: 'NVDA', display: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NASDAQ', type: 'stock' },
      { symbol: 'BTC-USD', display: 'BTC-USD', name: 'Bitcoin USD', exchange: 'CCC', type: 'cryptocurrency' },
      { symbol: 'ETH-USD', display: 'ETH-USD', name: 'Ethereum USD', exchange: 'CCC', type: 'cryptocurrency' },
      { symbol: 'NQ=F', display: 'NQ', name: 'NASDAQ-100 E-mini Future', exchange: 'CME', type: 'future' },
      { symbol: 'ES=F', display: 'ES', name: 'S&P 500 E-mini Future', exchange: 'CME', type: 'future' },
    ];

    return fallbackSymbols.filter(symbol => 
      symbol.symbol.toLowerCase().includes(query.toLowerCase()) ||
      symbol.name.toLowerCase().includes(query.toLowerCase())
    );
  };

  // Debounced search
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      searchSymbols(searchTerm);
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [searchTerm, searchSymbols]);

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleSymbolSelect = (symbol) => {
    // Save to recent symbols
    saveRecentSymbol(symbol);
    
    // Call the parent's onSymbolSelect with appropriate format
    const displaySymbol = symbol.display || symbol.symbol;
    onSymbolSelect(symbol.symbol, displaySymbol);
    onClose();
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'cryptocurrency':
        return CurrencyDollarIcon;
      case 'stock':
        return BuildingLibraryIcon;
      case 'future':
        return FireIcon;
      case 'currency':
        return GlobeAltIcon;
      default:
        return ChartBarIcon;
    }
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

  const displayResults = searchTerm.length < 2 ? recentSymbols : results;

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
                placeholder="Search any symbol (e.g., AAPL, BTCUSD, NASDAQ:AAPL)..."
                className="w-full pl-10 pr-4 py-3 bg-eerie-black-tertiary border border-dim-grey-600 rounded-lg text-white placeholder-dim-grey-400 focus:outline-none focus:border-robin-egg-500"
              />
              {loading && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-robin-egg-500"></div>
                </div>
              )}
            </div>
          </div>

          {/* Results */}
          <div className="p-6 max-h-96 overflow-y-auto">
            {searchTerm.length < 2 && recentSymbols.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-3">
                  <ClockIcon className="w-4 h-4 text-dim-grey-400" />
                  <h4 className="text-sm font-medium text-dim-grey-400">Recent Searches</h4>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {displayResults.map((symbol, index) => {
                const IconComponent = getTypeIcon(symbol.type);
                const isCurrentSymbol = symbol.symbol === currentSymbol;
                
                return (
                  <motion.div
                    key={`${symbol.symbol}-${symbol.exchange}-${index}`}
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
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-white">{symbol.display || symbol.symbol}</span>
                          {isCurrentSymbol && (
                            <StarIcon className="w-4 h-4 text-robin-egg-500" />
                          )}
                          {symbol.exchange && (
                            <span className="text-xs px-2 py-1 bg-dim-grey-700 rounded text-dim-grey-300">
                              {symbol.exchange}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-dim-grey-400 truncate">{symbol.name}</p>
                        {symbol.country && (
                          <p className="text-xs text-dim-grey-500">{symbol.country}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="text-right flex-shrink-0">
                      <p className={`text-xs uppercase font-medium ${getTypeColor(symbol.type)}`}>
                        {symbol.type}
                      </p>
                      {symbol.currency && (
                        <p className="text-xs text-dim-grey-500">{symbol.currency}</p>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>

            {searchTerm.length >= 2 && results.length === 0 && !loading && (
              <div className="text-center py-8 text-dim-grey-400">
                <ChartBarIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No symbols found matching "{searchTerm}"</p>
                <p className="text-sm mt-2">Try a different search term or check the spelling</p>
              </div>
            )}

            {searchTerm.length < 2 && recentSymbols.length === 0 && (
              <div className="text-center py-8 text-dim-grey-400">
                <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Start typing to search for any symbol</p>
                <p className="text-sm mt-2">Search stocks, crypto, futures, forex and more</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 border-t border-dim-grey-700 bg-eerie-black-secondary rounded-b-lg">
            <div className="flex items-center justify-between text-xs text-dim-grey-500">
              <span>Powered by TradingView symbol database</span>
              <span>{displayResults.length} results</span>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default DynamicSymbolSearch;
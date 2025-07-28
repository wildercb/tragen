/**
 * ChartTestPage - Testing page for TradingChart V2 components
 * 
 * This page provides comprehensive testing for the new chart implementation
 * to verify consistency, performance, and functionality.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import TradingChartV2 from '../components/TradingChartV2';
import TradingChart from '../components/TradingChart'; // Original chart for comparison
import MarketDataProvider from '../services/MarketDataProvider';
import ChartAgentInterface from '../services/ChartAgentInterface';
import { ChartExamples } from '../examples/ChartExamples';

const ChartTestPage = () => {
  // Test state
  const [testResults, setTestResults] = useState({});
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [selectedTest, setSelectedTest] = useState('consistency');
  const [testLogs, setTestLogs] = useState([]);
  
  // Chart instances for comparison
  const [v1ChartData, setV1ChartData] = useState(null);
  const [v2ChartData, setV2ChartData] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  
  // Services
  const [dataProvider] = useState(new MarketDataProvider());
  const [agentInterface] = useState(new ChartAgentInterface(dataProvider));
  
  // Test configuration
  const testSymbols = ['NQ=F', 'ES=F', 'BTC-USD', 'AAPL'];
  const testTimeframes = ['1m', '5m', '15m', '1h', '1d'];
  
  const logMessage = useCallback((message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setTestLogs(prev => [...prev, { timestamp, message, type }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  }, []);

  const clearLogs = () => {
    setTestLogs([]);
  };

  // Test 1: Data Consistency Test
  const runConsistencyTest = useCallback(async () => {
    logMessage('Starting data consistency test...', 'info');
    const results = { passed: 0, failed: 0, details: [] };
    
    for (const symbol of testSymbols) {
      try {
        logMessage(`Testing consistency for ${symbol}`, 'info');
        
        // Test multiple requests for same data
        const requests = Array(5).fill().map(() => 
          dataProvider.getHistoricalData(symbol, { period: '1d', interval: '5m' })
        );
        
        const responses = await Promise.all(requests);
        
        // Check if all responses are identical
        const firstResponse = JSON.stringify(responses[0]);
        const allIdentical = responses.every(response => 
          JSON.stringify(response) === firstResponse
        );
        
        if (allIdentical) {
          results.passed++;
          results.details.push({ symbol, status: 'PASS', message: 'Data consistent across requests' });
          logMessage(`✅ ${symbol}: Data consistency PASSED`, 'success');
        } else {
          results.failed++;
          results.details.push({ symbol, status: 'FAIL', message: 'Data inconsistent across requests' });
          logMessage(`❌ ${symbol}: Data consistency FAILED`, 'error');
        }
        
        // Test cache behavior
        const cached1 = await dataProvider.getHistoricalData(symbol, { period: '1d', interval: '5m' });
        const cached2 = await dataProvider.getHistoricalData(symbol, { period: '1d', interval: '5m' });
        
        if (JSON.stringify(cached1) === JSON.stringify(cached2)) {
          logMessage(`✅ ${symbol}: Cache consistency PASSED`, 'success');
        } else {
          logMessage(`❌ ${symbol}: Cache consistency FAILED`, 'error');
          results.failed++;
        }
        
      } catch (error) {
        results.failed++;
        results.details.push({ symbol, status: 'ERROR', message: error.message });
        logMessage(`❌ ${symbol}: Error - ${error.message}`, 'error');
      }
    }
    
    return results;
  }, [dataProvider, logMessage]);

  // Test 2: Performance Test
  const runPerformanceTest = useCallback(async () => {
    logMessage('Starting performance test...', 'info');
    const results = { metrics: {}, details: [] };
    
    for (const symbol of testSymbols.slice(0, 2)) { // Limit for performance
      try {
        logMessage(`Testing performance for ${symbol}`, 'info');
        
        // Test data loading performance
        const startTime = performance.now();
        await dataProvider.getHistoricalData(symbol, { period: '1y', interval: '1h', maxPoints: 1000 });
        const loadTime = performance.now() - startTime;
        
        // Test cache performance
        const cacheStartTime = performance.now();
        await dataProvider.getHistoricalData(symbol, { period: '1y', interval: '1h', maxPoints: 1000 });
        const cacheTime = performance.now() - cacheStartTime;
        
        results.metrics[symbol] = {
          loadTime: Math.round(loadTime),
          cacheTime: Math.round(cacheTime),
          cacheSpeedup: Math.round(loadTime / cacheTime * 100) / 100
        };
        
        logMessage(`📊 ${symbol}: Load ${loadTime.toFixed(0)}ms, Cache ${cacheTime.toFixed(0)}ms`, 'info');
        
      } catch (error) {
        logMessage(`❌ ${symbol}: Performance test error - ${error.message}`, 'error');
      }
    }
    
    return results;
  }, [dataProvider, logMessage]);

  // Test 3: Agent Integration Test
  const runAgentIntegrationTest = useCallback(async () => {
    logMessage('Starting agent integration test...', 'info');
    const results = { passed: 0, failed: 0, details: [] };
    
    try {
      // Register test agent
      const agentId = agentInterface.registerAgent('test-agent', {
        name: 'Test Agent',
        permissions: ['read', 'analyze'],
        indicators: ['sma20', 'rsi']
      });
      
      logMessage(`✅ Agent registration: PASSED`, 'success');
      results.passed++;
      
      // Test data access
      const chartData = await agentInterface.getChartData(agentId, 'NQ=F', {
        period: '1d',
        interval: '5m',
        includeIndicators: true
      });
      
      if (chartData && chartData.data && chartData.indicators) {
        logMessage(`✅ Agent data access: PASSED`, 'success');
        results.passed++;
      } else {
        logMessage(`❌ Agent data access: FAILED`, 'error');
        results.failed++;
      }
      
      // Test signal generation
      const signals = await agentInterface.generateSignals(agentId, 'NQ=F');
      logMessage(`📈 Generated ${signals.length} signals`, 'info');
      
      // Test real-time analysis
      const analysis = await agentInterface.getRealTimeAnalysis(agentId, 'NQ=F');
      if (analysis && analysis.currentPrice) {
        logMessage(`✅ Real-time analysis: PASSED`, 'success');
        results.passed++;
      } else {
        logMessage(`❌ Real-time analysis: FAILED`, 'error');
        results.failed++;
      }
      
      // Cleanup
      agentInterface.unregisterAgent(agentId);
      logMessage(`✅ Agent cleanup: PASSED`, 'success');
      
    } catch (error) {
      logMessage(`❌ Agent integration error: ${error.message}`, 'error');
      results.failed++;
    }
    
    return results;
  }, [agentInterface, logMessage]);

  // Test 4: WebSocket Connection Test
  const runWebSocketTest = useCallback(async () => {
    logMessage('Starting WebSocket connection test...', 'info');
    const results = { connections: 0, errors: 0, details: [] };
    
    return new Promise((resolve) => {
      let connectionCount = 0;
      let errorCount = 0;
      const testPromises = [];
      
      for (const symbol of testSymbols.slice(0, 2)) {
        const promise = new Promise((resolveSymbol) => {
          const subscription = dataProvider.subscribe(
            symbol,
            { timeframe: '1m' },
            (update) => {
              if (update.type === 'price_update' || update.type === 'historical_data') {
                connectionCount++;
                logMessage(`📡 ${symbol}: WebSocket data received`, 'success');
                dataProvider.unsubscribe(subscription);
                resolveSymbol({ symbol, status: 'success' });
              }
            }
          );
          
          // Timeout after 10 seconds
          setTimeout(() => {
            errorCount++;
            logMessage(`❌ ${symbol}: WebSocket timeout`, 'error');
            dataProvider.unsubscribe(subscription);
            resolveSymbol({ symbol, status: 'timeout' });
          }, 10000);
        });
        
        testPromises.push(promise);
      }
      
      Promise.all(testPromises).then(() => {
        results.connections = connectionCount;
        results.errors = errorCount;
        logMessage(`WebSocket test complete: ${connectionCount} connections, ${errorCount} errors`, 'info');
        resolve(results);
      });
    });
  }, [dataProvider, logMessage]);

  // Test 5: Memory Usage Test
  const runMemoryTest = useCallback(async () => {
    logMessage('Starting memory usage test...', 'info');
    const results = { initial: 0, peak: 0, final: 0 };
    
    // Get initial memory usage
    if (performance.memory) {
      results.initial = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
      logMessage(`Initial memory: ${results.initial}MB`, 'info');
    }
    
    // Load large dataset
    try {
      for (const symbol of testSymbols) {
        await dataProvider.getHistoricalData(symbol, { 
          period: '1y', 
          interval: '1m', 
          maxPoints: 5000 
        });
      }
      
      if (performance.memory) {
        results.peak = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
        logMessage(`Peak memory: ${results.peak}MB`, 'info');
      }
      
      // Clear cache and check cleanup
      dataProvider.clearCache();
      
      // Force garbage collection if available
      if (window.gc) {
        window.gc();
      }
      
      if (performance.memory) {
        results.final = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
        logMessage(`Final memory: ${results.final}MB`, 'info');
      }
      
      const memoryIncrease = results.final - results.initial;
      if (memoryIncrease < 50) { // Less than 50MB increase is acceptable
        logMessage(`✅ Memory test: PASSED (${memoryIncrease}MB increase)`, 'success');
      } else {
        logMessage(`⚠️ Memory test: WARNING (${memoryIncrease}MB increase)`, 'warning');
      }
      
    } catch (error) {
      logMessage(`❌ Memory test error: ${error.message}`, 'error');
    }
    
    return results;
  }, [dataProvider, logMessage]);

  // Run all tests
  const runAllTests = useCallback(async () => {
    setIsRunningTests(true);
    clearLogs();
    logMessage('🚀 Starting comprehensive test suite...', 'info');
    
    const allResults = {};
    
    try {
      // Run tests sequentially to avoid conflicts
      allResults.consistency = await runConsistencyTest();
      allResults.performance = await runPerformanceTest();
      allResults.agentIntegration = await runAgentIntegrationTest();
      allResults.webSocket = await runWebSocketTest();
      allResults.memory = await runMemoryTest();
      
      setTestResults(allResults);
      
      // Calculate overall score
      const totalPassed = Object.values(allResults).reduce((sum, result) => {
        return sum + (result.passed || result.connections || 0);
      }, 0);
      
      const totalFailed = Object.values(allResults).reduce((sum, result) => {
        return sum + (result.failed || result.errors || 0);
      }, 0);
      
      const successRate = Math.round((totalPassed / (totalPassed + totalFailed)) * 100);
      
      logMessage(`🎯 Test suite complete! Success rate: ${successRate}%`, 'info');
      
    } catch (error) {
      logMessage(`❌ Test suite error: ${error.message}`, 'error');
    } finally {
      setIsRunningTests(false);
    }
  }, [runConsistencyTest, runPerformanceTest, runAgentIntegrationTest, runWebSocketTest, runMemoryTest, logMessage]);

  // Run specific test
  const runSpecificTest = useCallback(async (testName) => {
    setIsRunningTests(true);
    clearLogs();
    
    try {
      let result;
      switch (testName) {
        case 'consistency':
          result = await runConsistencyTest();
          break;
        case 'performance':
          result = await runPerformanceTest();
          break;
        case 'agent':
          result = await runAgentIntegrationTest();
          break;
        case 'websocket':
          result = await runWebSocketTest();
          break;
        case 'memory':
          result = await runMemoryTest();
          break;
        default:
          throw new Error(`Unknown test: ${testName}`);
      }
      
      setTestResults(prev => ({ ...prev, [testName]: result }));
      
    } catch (error) {
      logMessage(`❌ Test error: ${error.message}`, 'error');
    } finally {
      setIsRunningTests(false);
    }
  }, [runConsistencyTest, runPerformanceTest, runAgentIntegrationTest, runWebSocketTest, runMemoryTest, logMessage]);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">TradingChart V2 - Test Suite</h1>
        
        {/* Test Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Controls</h2>
          
          <div className="flex flex-wrap gap-4 mb-4">
            <button
              onClick={runAllTests}
              disabled={isRunningTests}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRunningTests ? 'Running Tests...' : 'Run All Tests'}
            </button>
            
            <select
              value={selectedTest}
              onChange={(e) => setSelectedTest(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded"
            >
              <option value="consistency">Data Consistency</option>
              <option value="performance">Performance</option>
              <option value="agent">Agent Integration</option>
              <option value="websocket">WebSocket</option>
              <option value="memory">Memory Usage</option>
            </select>
            
            <button
              onClick={() => runSpecificTest(selectedTest)}
              disabled={isRunningTests}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              Run Selected Test
            </button>
            
            <button
              onClick={clearLogs}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Clear Logs
            </button>
          </div>
        </div>

        {/* Test Results Summary */}
        {Object.keys(testResults).length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Test Results Summary</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(testResults).map(([testName, result]) => (
                <div key={testName} className="border border-gray-200 rounded p-4">
                  <h3 className="font-semibold capitalize mb-2">{testName}</h3>
                  
                  {result.passed !== undefined && (
                    <div className="space-y-1">
                      <div className="text-green-600">✅ Passed: {result.passed}</div>
                      <div className="text-red-600">❌ Failed: {result.failed}</div>
                      <div className="text-sm text-gray-600">
                        Success Rate: {Math.round((result.passed / (result.passed + result.failed)) * 100)}%
                      </div>
                    </div>
                  )}
                  
                  {result.connections !== undefined && (
                    <div className="space-y-1">
                      <div className="text-green-600">📡 Connections: {result.connections}</div>
                      <div className="text-red-600">❌ Errors: {result.errors}</div>
                    </div>
                  )}
                  
                  {result.metrics && (
                    <div className="space-y-1">
                      {Object.entries(result.metrics).map(([symbol, metrics]) => (
                        <div key={symbol} className="text-sm">
                          <div className="font-medium">{symbol}</div>
                          <div>Load: {metrics.loadTime}ms</div>
                          <div>Cache: {metrics.cacheTime}ms</div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {result.initial !== undefined && (
                    <div className="space-y-1">
                      <div>Initial: {result.initial}MB</div>
                      <div>Peak: {result.peak}MB</div>
                      <div>Final: {result.final}MB</div>
                      <div className="text-sm">
                        Increase: {result.final - result.initial}MB
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Test Logs */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Logs</h2>
          
          <div className="bg-gray-900 text-green-400 font-mono text-sm p-4 rounded h-64 overflow-y-auto">
            {testLogs.map((log, index) => (
              <div key={index} className={`mb-1 ${
                log.type === 'error' ? 'text-red-400' :
                log.type === 'success' ? 'text-green-400' :
                log.type === 'warning' ? 'text-yellow-400' :
                'text-gray-300'
              }`}>
                <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
              </div>
            ))}
            {testLogs.length === 0 && (
              <div className="text-gray-500">No logs yet. Run a test to see output.</div>
            )}
          </div>
        </div>

        {/* Chart Comparison */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Chart Comparison (V1 vs V2)</h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Original Chart V1 */}
            <div>
              <h3 className="text-lg font-medium mb-2">Original Chart (V1)</h3>
              <div className="border border-gray-200 rounded">
                <TradingChart
                  symbol="NQ=F"
                  displaySymbol="NQ"
                  height={400}
                  onChartDataUpdate={setV1ChartData}
                />
              </div>
            </div>
            
            {/* New Chart V2 */}
            <div>
              <h3 className="text-lg font-medium mb-2">New Chart (V2)</h3>
              <div className="border border-gray-200 rounded">
                <TradingChartV2
                  symbol="NQ=F"
                  displaySymbol="NQ"
                  height={400}
                  onChartDataUpdate={setV2ChartData}
                />
              </div>
            </div>
          </div>
          
          {/* Data Comparison */}
          {v1ChartData && v2ChartData && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h4 className="font-medium mb-2">Data Comparison</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <strong>V1 Data Points:</strong> {v1ChartData.length}
                </div>
                <div>
                  <strong>V2 Data Points:</strong> {v2ChartData.length}
                </div>
                <div>
                  <strong>V1 Latest Price:</strong> ${v1ChartData[v1ChartData.length - 1]?.close?.toFixed(2)}
                </div>
                <div>
                  <strong>V2 Latest Price:</strong> ${v2ChartData[v2ChartData.length - 1]?.close?.toFixed(2)}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Example Components */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Interactive Examples</h2>
          
          <div className="space-y-8">
            <ChartExamples.BasicChartExample />
            <ChartExamples.AIAgentExample />
            <ChartExamples.PerformanceComparisonExample />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChartTestPage;
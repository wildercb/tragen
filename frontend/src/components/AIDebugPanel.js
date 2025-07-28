import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  EyeIcon,
  EyeSlashIcon,
  TrashIcon,
  DocumentTextIcon,
  ClockIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline';

const AIDebugPanel = ({ symbol }) => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [logs, setLogs] = useState([]);
  const [isMinimized, setIsMinimized] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef(null);
  const wsRef = useRef(null);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // WebSocket connection for real-time AI debug data
  useEffect(() => {
    if (!isEnabled) return;

    const wsUrl = `ws://localhost:8001/api/ws/ai-debug/${encodeURIComponent(symbol)}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('🔧 AI Debug WebSocket connected');
      addLog('system', 'Debug WebSocket connected', '', 'connection');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'ai_prompt') {
          addLog('prompt', data.prompt, data.model || 'unknown', 'prompt', data.timestamp);
        } else if (data.type === 'ai_response') {
          addLog('response', data.response, data.model || 'unknown', 'response', data.timestamp);
        } else if (data.type === 'ai_error') {
          addLog('error', data.error, data.model || 'unknown', 'error', data.timestamp);
        }
      } catch (e) {
        console.error('Failed to parse AI debug message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('AI Debug WebSocket error:', error);
      addLog('system', 'WebSocket connection error', '', 'error');
    };

    ws.onclose = () => {
      console.log('🔧 AI Debug WebSocket disconnected');
      addLog('system', 'Debug WebSocket disconnected', '', 'connection');
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [isEnabled, symbol]);

  const addLog = (type, content, model, category, timestamp) => {
    const logEntry = {
      id: Date.now() + Math.random(),
      type,
      content,
      model,
      category,
      timestamp: timestamp || new Date().toISOString(),
      localTime: new Date().toLocaleTimeString()
    };

    setLogs(prev => {
      const newLogs = [...prev, logEntry];
      // Keep only last 100 logs to prevent memory issues
      return newLogs.slice(-100);
    });
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const getLogIcon = (category) => {
    switch (category) {
      case 'prompt':
        return <DocumentTextIcon className="w-4 h-4 text-blue-400" />;
      case 'response':
        return <CpuChipIcon className="w-4 h-4 text-green-400" />;
      case 'error':
        return <TrashIcon className="w-4 h-4 text-red-400" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  const getLogStyle = (category) => {
    switch (category) {
      case 'prompt':
        return 'border-l-4 border-blue-400 bg-blue-900 bg-opacity-20';
      case 'response':
        return 'border-l-4 border-green-400 bg-green-900 bg-opacity-20';
      case 'error':
        return 'border-l-4 border-red-400 bg-red-900 bg-opacity-20';
      default:
        return 'border-l-4 border-gray-400 bg-gray-900 bg-opacity-20';
    }
  };

  if (!isEnabled) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={() => setIsEnabled(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg shadow-lg transition-colors flex items-center space-x-2"
          title="Enable AI Debug Panel"
        >
          <EyeIcon className="w-4 h-4" />
          <span className="text-sm">AI Debug</span>
        </button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed bottom-4 right-4 z-50 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl max-w-2xl"
      style={{ 
        width: isMinimized ? '300px' : '800px', 
        height: isMinimized ? '60px' : '500px' 
      }}
    >
      {/* Header */}
      <div className="bg-purple-800 text-white p-3 rounded-t-lg flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <CpuChipIcon className="w-5 h-5" />
          <span className="font-semibold">AI Debug Panel</span>
          <span className="text-xs bg-purple-900 px-2 py-1 rounded">
            {symbol}
          </span>
          <span className="text-xs text-purple-200">
            {logs.length} logs
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 rounded text-xs ${autoScroll ? 'bg-purple-600' : 'bg-gray-600'}`}
            title="Auto-scroll"
          >
            Auto
          </button>
          
          <button
            onClick={clearLogs}
            className="p-1 text-purple-200 hover:text-white"
            title="Clear logs"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 text-purple-200 hover:text-white"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? '▲' : '▼'}
          </button>
          
          <button
            onClick={() => setIsEnabled(false)}
            className="p-1 text-purple-200 hover:text-white"
            title="Close debug panel"
          >
            <EyeSlashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logs Content */}
      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <div className="h-96 overflow-y-auto bg-gray-950 p-3 space-y-2">
              {logs.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <CpuChipIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Waiting for AI interactions...</p>
                  <p className="text-xs mt-1">
                    Press "Analyze" in the AI panel to see prompts and responses
                  </p>
                </div>
              ) : (
                logs.map((log) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-3 rounded-lg ${getLogStyle(log.category)}`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getLogIcon(log.category)}
                        <span className="text-xs font-semibold text-white uppercase">
                          {log.type}
                        </span>
                        {log.model && (
                          <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                            {log.model}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-400">
                        {log.localTime}
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-200 font-mono whitespace-pre-wrap break-words">
                      {log.content}
                    </div>
                  </motion.div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer with stats */}
      {!isMinimized && (
        <div className="bg-gray-800 text-xs text-gray-400 p-2 rounded-b-lg flex justify-between items-center">
          <span>
            Real-time AI prompt/response monitoring for {symbol}
          </span>
          <div className="flex items-center space-x-3">
            <span>
              Prompts: {logs.filter(l => l.category === 'prompt').length}
            </span>
            <span>
              Responses: {logs.filter(l => l.category === 'response').length}
            </span>
            <span>
              Errors: {logs.filter(l => l.category === 'error').length}
            </span>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default AIDebugPanel;
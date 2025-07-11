import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import Analysis from './pages/Analysis';
import Configuration from './pages/Configuration';
import Backtesting from './pages/Backtesting';
import { WebSocketProvider } from './context/WebSocketContext';
import './App.css';

function App() {
  return (
    <Provider store={store}>
      <WebSocketProvider>
        <Router>
          <div className="min-h-screen bg-gray-900 text-white">
            <Navigation />
            <main className="container mx-auto px-4 py-6">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agents" element={<Agents />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/configuration" element={<Configuration />} />
                <Route path="/backtesting" element={<Backtesting />} />
              </Routes>
            </main>
          </div>
        </Router>
      </WebSocketProvider>
    </Provider>
  );
}

export default App;
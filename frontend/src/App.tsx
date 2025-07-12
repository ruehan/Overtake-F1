import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { WebSocketProvider } from './contexts/WebSocketContext';
import './App.css';
import Dashboard from './pages/Dashboard';
import LiveMapPage from './pages/LiveMapPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AlertsPage from './components/Alerts/AlertsPage';

function App() {
  return (
    <WebSocketProvider>
      <div className="App">
      <nav style={{ 
        padding: '1rem', 
        background: '#f8f9fa', 
        borderBottom: '1px solid #dee2e6',
        marginBottom: '1rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem', color: '#333' }}>OpenF1 Dashboard</h1>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link 
              to="/" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Dashboard
            </Link>
            <Link 
              to="/live-map" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Live Map
            </Link>
            <Link 
              to="/analytics" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Analytics
            </Link>
            <Link 
              to="/alerts" 
              style={{ 
                textDecoration: 'none', 
                color: '#007bff', 
                fontWeight: '500',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                transition: 'background-color 0.2s'
              }}
            >
              Alerts
            </Link>
          </div>
        </div>
      </nav>

      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/live-map" element={<LiveMapPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
        </Routes>
      </div>
      
      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: '500',
            padding: '12px 16px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
      </div>
    </WebSocketProvider>
  );
}

export default App;
